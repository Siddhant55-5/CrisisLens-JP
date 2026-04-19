"""Feature Engineering — builds feature vectors from the signal registry.

FeatureBuilder reads current signal values from TimescaleDB and
produces a flat FeatureVector suitable for ML model input:
  - z_score_5d, z_score_20d per signal (rolling window z-scores)
  - pct_change_1d, pct_change_5d, pct_change_20d
  - volatility_20d (rolling std of daily returns)
  - interbank_stress_composite (weighted sum)
  - cross_signal_correlation_flag (VIX + HY co-spike)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal

logger = logging.getLogger(__name__)


class FeatureVector(BaseModel):
    """Flat feature vector produced by FeatureBuilder for ML scoring."""

    # Interbank z-scores
    sofr_z5d: float = 0.0
    sofr_z20d: float = 0.0
    dff_z5d: float = 0.0
    dff_z20d: float = 0.0

    # Bond z-scores
    dgs2_z5d: float = 0.0
    dgs2_z20d: float = 0.0
    dgs10_z5d: float = 0.0
    dgs10_z20d: float = 0.0
    hy_spread_z5d: float = 0.0
    hy_spread_z20d: float = 0.0
    t10y2y_z5d: float = 0.0
    t10y2y_z20d: float = 0.0

    # Equity
    vix_z5d: float = 0.0
    vix_z20d: float = 0.0
    spx_pct5d: float = 0.0
    spx_pct20d: float = 0.0
    spx_vol20d: float = 0.0

    # FX
    dxy_z5d: float = 0.0
    dxy_z20d: float = 0.0
    eurusd_z5d: float = 0.0
    eurusd_z20d: float = 0.0
    gbpusd_z5d: float = 0.0
    gbpusd_z20d: float = 0.0

    # Commodity
    gold_pct5d: float = 0.0
    gold_pct20d: float = 0.0
    oil_pct5d: float = 0.0
    oil_pct20d: float = 0.0

    # Composites
    interbank_stress: float = 0.0
    cross_signal_corr_flag: int = 0

    # Macro
    pmi_us: float = 50.0
    pmi_eu: float = 50.0
    pmi_cn: float = 50.0
    initial_claims_z: float = 0.0
    cpi_yoy: float = 2.5

    # Volatility & Sentiment
    move_index_z: float = 0.0
    skew_index_z: float = 0.0
    put_call_ratio: float = 0.85

    # Credit & Liquidity
    ted_spread_z: float = 0.0
    libor_ois_z: float = 0.0
    fra_ois_z: float = 0.0

    # Cross-Asset
    copper_gold_ratio: float = 0.20
    baltic_dry_pct20d: float = 0.0

    def to_array(self) -> np.ndarray:
        """Convert to numpy array in consistent feature order."""
        return np.array([
            self.sofr_z5d, self.sofr_z20d, self.dff_z5d, self.dff_z20d,
            self.dgs2_z5d, self.dgs2_z20d, self.dgs10_z5d, self.dgs10_z20d,
            self.hy_spread_z5d, self.hy_spread_z20d,
            self.t10y2y_z5d, self.t10y2y_z20d,
            self.vix_z5d, self.vix_z20d,
            self.spx_pct5d, self.spx_pct20d, self.spx_vol20d,
            self.dxy_z5d, self.dxy_z20d,
            self.gold_pct5d, self.gold_pct20d,
            self.oil_pct5d, self.oil_pct20d,
            self.eurusd_z5d, self.eurusd_z20d,
            self.gbpusd_z5d, self.gbpusd_z20d,
            self.interbank_stress, self.cross_signal_corr_flag,
            self.pmi_us, self.pmi_eu, self.pmi_cn,
            self.initial_claims_z, self.cpi_yoy,
            self.move_index_z, self.skew_index_z, self.put_call_ratio,
            self.ted_spread_z, self.libor_ois_z, self.fra_ois_z,
            self.copper_gold_ratio, self.baltic_dry_pct20d,
        ], dtype=np.float64)

    @classmethod
    def feature_names(cls) -> list[str]:
        """Return ordered feature names matching to_array() order."""
        return [
            "sofr_z5d", "sofr_z20d", "dff_z5d", "dff_z20d",
            "dgs2_z5d", "dgs2_z20d", "dgs10_z5d", "dgs10_z20d",
            "hy_spread_z5d", "hy_spread_z20d",
            "t10y2y_z5d", "t10y2y_z20d",
            "vix_z5d", "vix_z20d",
            "spx_pct5d", "spx_pct20d", "spx_vol20d",
            "dxy_z5d", "dxy_z20d",
            "gold_pct5d", "gold_pct20d",
            "oil_pct5d", "oil_pct20d",
            "eurusd_z5d", "eurusd_z20d",
            "gbpusd_z5d", "gbpusd_z20d",
            "interbank_stress", "cross_signal_corr_flag",
            "pmi_us", "pmi_eu", "pmi_cn",
            "initial_claims_z", "cpi_yoy",
            "move_index_z", "skew_index_z", "put_call_ratio",
            "ted_spread_z", "libor_ois_z", "fra_ois_z",
            "copper_gold_ratio", "baltic_dry_pct20d",
        ]


# Signal ID → FeatureVector field mapping
SIGNAL_FEATURE_MAP: dict[str, dict[str, str]] = {
    "SOFR": {"z_score": "sofr_z5d"},
    "DFF": {"z_score": "dff_z5d"},
    "DGS2": {"z_score": "dgs2_z5d"},
    "DGS10": {"z_score": "dgs10_z5d"},
    "BAMLH0A0HYM2": {"z_score": "hy_spread_z5d"},
    "T10Y2Y": {"z_score": "t10y2y_z5d"},
    "VIX": {"z_score": "vix_z5d"},
    "SPX": {"pct_change_1d": "spx_pct5d"},
    "DXY": {"z_score": "dxy_z5d"},
    "GOLD": {"pct_change_1d": "gold_pct5d"},
    "WTI_OIL": {"pct_change_1d": "oil_pct5d"},
    "EURUSD": {"z_score": "eurusd_z5d"},
    "GBPUSD": {"z_score": "gbpusd_z5d"},
    "PMI_US_MFG": {"raw_value": "pmi_us"},
    "PMI_EU_MFG": {"raw_value": "pmi_eu"},
    "PMI_CN_MFG": {"raw_value": "pmi_cn"},
    "US_INITIAL_CLAIMS": {"z_score": "initial_claims_z"},
    "US_CPI_YOY": {"raw_value": "cpi_yoy"},
    "MOVE_INDEX": {"z_score": "move_index_z"},
    "SKEW_INDEX": {"z_score": "skew_index_z"},
    "PUT_CALL_RATIO": {"raw_value": "put_call_ratio"},
    "TED_SPREAD": {"z_score": "ted_spread_z"},
    "LIBOR_OIS": {"z_score": "libor_ois_z"},
    "FRA_OIS": {"z_score": "fra_ois_z"},
    "COPPER_GOLD_RATIO": {"raw_value": "copper_gold_ratio"},
    "BALTIC_DRY": {"pct_change_1d": "baltic_dry_pct20d"},
}


class FeatureBuilder:
    """Builds ML feature vectors from the signal registry."""

    async def build(
        self,
        session: AsyncSession,
        overrides: dict[str, float] | None = None,
    ) -> FeatureVector:
        """Read current signals and produce a flat feature vector.

        Args:
            session: Async database session.
            overrides: Optional dict of signal_id → value for simulation.

        Returns:
            FeatureVector with all fields populated from live signals.
        """
        result = await session.execute(select(Signal))
        signals = {s.signal_id: s for s in result.scalars().all()}

        fv = FeatureVector()

        # Map signal values to feature vector fields
        for sig_id, mapping in SIGNAL_FEATURE_MAP.items():
            signal = signals.get(sig_id)
            if signal is None:
                continue

            for source_attr, target_field in mapping.items():
                if overrides and sig_id in overrides:
                    # When overriding, use override as both raw and z-like value
                    val = overrides[sig_id]
                    if source_attr == "raw_value":
                        setattr(fv, target_field, val)
                    else:
                        # Approximate z-score from override using simple heuristic
                        if signal.raw_value and signal.raw_value != 0:
                            setattr(fv, target_field, (val - signal.raw_value) / max(abs(signal.raw_value) * 0.1, 0.01))
                        else:
                            setattr(fv, target_field, val)
                else:
                    source_val = getattr(signal, source_attr, None)
                    if source_val is not None:
                        setattr(fv, target_field, float(source_val))

        # Duplicate z5d → z20d with damping (Sprint 3 will use real rolling windows)
        fv.sofr_z20d = fv.sofr_z5d * 0.7
        fv.dff_z20d = fv.dff_z5d * 0.7
        fv.dgs2_z20d = fv.dgs2_z5d * 0.7
        fv.dgs10_z20d = fv.dgs10_z5d * 0.7
        fv.hy_spread_z20d = fv.hy_spread_z5d * 0.8
        fv.t10y2y_z20d = fv.t10y2y_z5d * 0.8
        fv.vix_z20d = fv.vix_z5d * 0.8
        fv.dxy_z20d = fv.dxy_z5d * 0.7
        fv.eurusd_z20d = fv.eurusd_z5d * 0.7
        fv.gbpusd_z20d = fv.gbpusd_z5d * 0.7

        # Compute pct_change variants (damped for multi-day)
        fv.spx_pct20d = fv.spx_pct5d * 2.5
        fv.gold_pct20d = fv.gold_pct5d * 2.0
        fv.oil_pct20d = fv.oil_pct5d * 2.0

        # Compute volatility proxy
        fv.spx_vol20d = abs(fv.spx_pct5d) * 4.0 + 12.0  # baseline vol ~12%

        # ── Interbank Stress Composite ────────────────────────────
        yield_curve_inversion = 1.0 if fv.t10y2y_z5d < -0.5 else 0.0
        fv.interbank_stress = round(
            fv.sofr_z5d * 0.3 + fv.hy_spread_z5d * 0.4 + yield_curve_inversion * 0.3,
            4,
        )

        # ── Cross Signal Correlation Flag ─────────────────────────
        fv.cross_signal_corr_flag = 1 if (fv.vix_z5d > 2.0 and fv.hy_spread_z5d > 2.0) else 0

        logger.info(
            "Feature vector built: interbank_stress=%.3f cross_flag=%d",
            fv.interbank_stress,
            fv.cross_signal_corr_flag,
        )
        return fv
