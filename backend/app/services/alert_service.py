"""Alert Engine — generates and persists alerts on threshold crossings.

Runs custom rules:
  GLOBAL_RISK: >70 HIGH (Iran USA war)
  BANKING_INSTABILITY: >50 MED, >80 HIGH (Bank news)
  MARKET_CRASH: >60 MED, >80 HIGH
  LIQUIDITY_SHORTAGE: >50 MED, >80 HIGH

Also generates feature-contribution-based AI reasons.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.alert import Alert, AlertSeverity, CrisisType
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

ALERT_STREAM = "alerts.live"

# InfluxDB Configuration
INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = "secret-token-crisislens"
INFLUX_ORG = "crisislens"
INFLUX_BUCKET = "alerts"

# Track last triggered severity per crisis type to detect crossings
_last_severity: dict[str, AlertSeverity | None] = {}

# ── Feature-based reason generation ──────────────────────────────────


FEATURE_REASONS = {
    "vix_z5d": ("VIX", "Market volatility (VIX) is elevated"),
    "hy_spread_z5d": ("HY Spread", "Credit spreads indicate financial stress"),
    "t10y2y_z5d": ("Yield Curve", "Yield curve inversion signals recession risk"),
    "dxy_z5d": ("DXY", "Strong dollar indicates global liquidity tightening"),
    "spx_pct5d": ("SPX", "Equity markets are declining sharply"),
    "sofr_z5d": ("SOFR", "Interbank funding rates are spiking"),
    "ted_spread_z": ("TED Spread", "TED spread widening signals bank funding stress"),
    "put_call_ratio": ("Put/Call", "Options market shows elevated fear (put/call ratio)"),
    "gold_pct5d": ("Gold", "Safe-haven demand for gold is surging"),
    "libor_ois_z": ("LIBOR-OIS", "Interbank lending stress is rising"),
    "fra_ois_z": ("FRA-OIS", "Forward rate agreements signal liquidity concerns"),
    "baltic_dry_pct20d": ("Baltic Dry", "Global trade activity is contracting"),
    "pmi_us": ("PMI", "Manufacturing activity is weakening"),
    "copper_gold_ratio": ("Cu/Au Ratio", "Copper-gold ratio signals risk-off sentiment"),
}


def generate_reason_from_shap(crisis_type: str, score: float, top_shap: list[dict] | None) -> str:
    """Generate a human-readable AI reason from SHAP feature contributions."""
    # Base context reason (always present)
    base_reasons = {
        "GLOBAL_RISK": "geopolitical tensions including Iran-USA conflict escalation",
        "BANKING_INSTABILITY": "deteriorating bank credit conditions and interbank stress",
        "MARKET_CRASH": "elevated volatility and negative market momentum",
        "LIQUIDITY_SHORTAGE": "tightening interbank funding and repo market stress",
    }

    if not top_shap:
        base = base_reasons.get(crisis_type, "elevated risk parameters across multiple indicators")
        if score > 80:
            return f"High risk driven by {base}."
        elif score > 50:
            return f"Moderate risk due to {base}."
        return f"Low-level signals from {base}."

    # Build reason from actual contributing features
    contributing = []
    for feat in top_shap[:3]:  # Top 3 contributors
        fname = feat.get("feature_name", "")
        direction = feat.get("direction", "up")
        if fname in FEATURE_REASONS:
            contributing.append(FEATURE_REASONS[fname][1])
        elif fname:
            pretty = fname.replace("_", " ").replace("z5d", "").strip()
            verb = "rising" if direction == "up" else "falling"
            contributing.append(f"{pretty} is {verb}")

    if contributing:
        joined = ", ".join(contributing[:-1])
        if len(contributing) > 1:
            joined += f", and {contributing[-1]}"
        else:
            joined = contributing[0]

        severity_word = "High" if score > 80 else "Moderate" if score > 50 else "Low"
        return f"{severity_word} risk driven by {joined}."

    base = base_reasons.get(crisis_type, "elevated risk across financial indicators")
    return f"Risk driven by {base}."


# ── Threshold evaluation ────────────────────────────────────────────


def evaluate_thresholds(crisis_type: str, score: float) -> tuple[AlertSeverity | None, str]:
    if crisis_type == "GLOBAL_RISK":
        if score > 70:
            return AlertSeverity.HIGH, ""  # reason will be generated from SHAP
    elif crisis_type == "BANKING_INSTABILITY":
        if score > 80:
            return AlertSeverity.HIGH, ""
        elif score > 50:
            return AlertSeverity.MEDIUM, ""
    elif crisis_type == "MARKET_CRASH":
        if score > 80:
            return AlertSeverity.HIGH, ""
        elif score > 60:
            return AlertSeverity.MEDIUM, ""
    elif crisis_type == "LIQUIDITY_SHORTAGE":
        if score > 80:
            return AlertSeverity.HIGH, ""
        elif score > 50:
            return AlertSeverity.MEDIUM, ""

    return None, ""


class AlertEngine:
    """Evaluates risk scores and triggers alerts on threshold crossings."""

    def __init__(self):
        try:
            self.influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
            self.write_api = self.influx.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.write_api = None

    async def evaluate(
        self,
        session: AsyncSession,
        crisis_type: str,
        score: float,
        ci_lower: float,
        ci_upper: float,
        top_shap: list[dict] | None = None,
        historical_analog: dict | None = None,
        all_scores: dict | None = None,
    ) -> Alert | None:

        current_severity, _ = evaluate_thresholds(crisis_type, score)
        previous_severity = _last_severity.get(crisis_type)

        if current_severity is None:
            _last_severity[crisis_type] = None
            return None

        # Generate AI reason from SHAP features
        reason = generate_reason_from_shap(crisis_type, score, top_shap)

        # Fire alert when:
        # 1. Severity level CHANGES (threshold crossing) — always
        # 2. Score is HIGH — alert every time to keep alert panel active
        # 3. Score is MEDIUM — alert on crossing or every ~3 cycles
        is_crossing = current_severity != previous_severity
        is_high = current_severity == AlertSeverity.HIGH

        if not is_crossing and not is_high:
            # For MEDIUM: track a counter and only fire occasionally
            counter_key = f"_counter_{crisis_type}"
            count = _last_severity.get(counter_key, 0)
            _last_severity[counter_key] = count + 1
            if count % 4 != 0:  # Fire every 4th cycle (~20 sec) for MEDIUM
                return None

        _last_severity[crisis_type] = current_severity

        try:
            ct_enum = CrisisType(crisis_type) if crisis_type != "GLOBAL_RISK" else CrisisType.BANKING_INSTABILITY
        except ValueError:
            ct_enum = CrisisType.MARKET_CRASH

        actions = [reason] if reason else []

        alert = Alert(
            crisis_type=CrisisType.MARKET_CRASH if crisis_type == "GLOBAL_RISK" else ct_enum,
            score=score,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            severity=current_severity,
            top_shap=top_shap or [],
            historical_analog=historical_analog,
            recommended_actions=actions,
            triggered_at=datetime.now(timezone.utc),
        )

        if crisis_type != "GLOBAL_RISK":
            session.add(alert)
            await session.flush()

        # Publish to Redis
        await self._publish_alert(alert, crisis_type, reason)
        self._write_to_influx(crisis_type, score, current_severity.value, reason, all_scores or {})

        return alert

    def _write_to_influx(self, crisis_type: str, score: float, severity_str: str, reason: str, scores_dict: dict):
        if not self.write_api:
            return
        try:
            point = Point("alert_events") \
                .tag("crisis_type", crisis_type) \
                .tag("severity", severity_str) \
                .field("score", float(score)) \
                .field("reason", reason)

            for k, v in scores_dict.items():
                try:
                    point.field(f"risk_{k}", float(v))
                except (ValueError, TypeError):
                    pass
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            logger.info("Successfully wrote alert to InfluxDB: %s=%s (%s)", crisis_type, score, severity_str)
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    async def _publish_alert(self, alert: Alert, crisis_str: str, reason: str) -> None:
        try:
            r = await get_redis()
            await r.xadd(
                ALERT_STREAM,
                {
                    "alert_id": str(alert.id) if alert.id else "global_1",
                    "crisis_type": crisis_str,
                    "score": str(alert.score),
                    "ci_lower": str(alert.ci_lower),
                    "ci_upper": str(alert.ci_upper),
                    "severity": alert.severity.value,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "reason": reason,
                },
                maxlen=5000,
            )
        except Exception:
            logger.exception("Failed to publish alert to Redis")

    async def get_alerts(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Alert]:
        result = await session.execute(
            select(Alert).order_by(desc(Alert.triggered_at)).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_alert_by_id(
        self,
        session: AsyncSession,
        alert_id: int,
    ) -> Alert | None:
        result = await session.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

alert_engine = AlertEngine()
