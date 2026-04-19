"""Cascade Mapper — models cross-asset contagion propagation using NetworkX.

Directed graph where:
  - Nodes: asset classes (CURRENCY, COMMODITY, EQUITY, BOND, SOVEREIGN)
  - Edges: historical impact coefficients from crisis research data
  - Provides cascade paths and full graph export for D3 Sankey
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


# Historical impact lookup: (source, target) → edge attributes
# Based on research from 2008 GFC, 2011 EU Debt, 2020 COVID crises
IMPACT_TABLE: list[dict[str, Any]] = [
    {"source": "CURRENCY", "target": "EQUITY", "impact_strength": "High", "avg_lag_days": 2, "confidence": 0.85, "description": "FX stress transmits via trade channels and risk sentiment"},
    {"source": "CURRENCY", "target": "COMMODITY", "impact_strength": "High", "avg_lag_days": 1, "confidence": 0.82, "description": "USD strength depresses commodity prices globally"},
    {"source": "CURRENCY", "target": "BOND", "impact_strength": "Medium", "avg_lag_days": 3, "confidence": 0.71, "description": "Capital flows adjust fixed income positions"},
    {"source": "CURRENCY", "target": "SOVEREIGN", "impact_strength": "Medium", "avg_lag_days": 5, "confidence": 0.68, "description": "EM sovereign risk rises with local currency weakness"},
    {"source": "EQUITY", "target": "BOND", "impact_strength": "High", "avg_lag_days": 0, "confidence": 0.88, "description": "Flight to quality drives bond rally during equity stress"},
    {"source": "EQUITY", "target": "COMMODITY", "impact_strength": "Medium", "avg_lag_days": 1, "confidence": 0.72, "description": "Demand destruction narrative weighs on industrial commodities"},
    {"source": "EQUITY", "target": "CURRENCY", "impact_strength": "Medium", "avg_lag_days": 1, "confidence": 0.69, "description": "Risk-off triggers safe-haven FX flows"},
    {"source": "BOND", "target": "EQUITY", "impact_strength": "High", "avg_lag_days": 1, "confidence": 0.81, "description": "Rate shock reprices equity risk premium"},
    {"source": "BOND", "target": "SOVEREIGN", "impact_strength": "High", "avg_lag_days": 2, "confidence": 0.87, "description": "Core rate moves cascade to sovereign spreads"},
    {"source": "BOND", "target": "CURRENCY", "impact_strength": "Medium", "avg_lag_days": 1, "confidence": 0.74, "description": "Yield differentials drive carry trade unwinds"},
    {"source": "COMMODITY", "target": "CURRENCY", "impact_strength": "Medium", "avg_lag_days": 2, "confidence": 0.66, "description": "Commodity exporters' currencies track resource prices"},
    {"source": "COMMODITY", "target": "EQUITY", "impact_strength": "Medium", "avg_lag_days": 1, "confidence": 0.63, "description": "Energy costs squeeze corporate margins"},
    {"source": "COMMODITY", "target": "SOVEREIGN", "impact_strength": "Low", "avg_lag_days": 7, "confidence": 0.55, "description": "Resource-dependent sovereigns affected by price swings"},
    {"source": "SOVEREIGN", "target": "BOND", "impact_strength": "High", "avg_lag_days": 0, "confidence": 0.91, "description": "Sovereign stress directly widens credit spreads"},
    {"source": "SOVEREIGN", "target": "EQUITY", "impact_strength": "High", "avg_lag_days": 1, "confidence": 0.84, "description": "Banking sector exposure propagates to equity markets"},
    {"source": "SOVEREIGN", "target": "CURRENCY", "impact_strength": "High", "avg_lag_days": 0, "confidence": 0.89, "description": "Sovereign risk instantly depresses local currency"},
]

ASSET_CLASSES = ["CURRENCY", "COMMODITY", "EQUITY", "BOND", "SOVEREIGN"]

ASSET_COLORS = {
    "CURRENCY": "#3b82f6",   # Blue
    "COMMODITY": "#f59e0b",  # Amber
    "EQUITY": "#6366f1",     # Purple
    "BOND": "#14b8a6",       # Teal
    "SOVEREIGN": "#ef4444",  # Red
}


class CascadeMapper:
    """Models cross-asset contagion using directed graph."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self) -> None:
        """Build NetworkX graph from impact table."""
        # Add nodes
        for ac in ASSET_CLASSES:
            self.graph.add_node(ac, color=ASSET_COLORS[ac])

        # Add edges
        for edge in IMPACT_TABLE:
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                impact_strength=edge["impact_strength"],
                avg_lag_days=edge["avg_lag_days"],
                confidence=edge["confidence"],
                description=edge["description"],
            )

    def get_cascade_path(
        self,
        source: str,
        active_score: float = 75.0,
    ) -> list[dict]:
        """Get cascade propagation path from a source asset class.

        Returns ordered list of impacted nodes with impact probability and lag.
        """
        if source not in self.graph:
            logger.warning("Unknown source asset class: %s", source)
            return []

        results = []
        visited = {source}
        queue = [(source, 0, 1.0)]  # (node, total_lag, cumulative_probability)

        while queue:
            current, total_lag, cum_prob = queue.pop(0)

            for neighbor in self.graph.successors(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)

                edge = self.graph[current][neighbor]
                lag = edge["avg_lag_days"]
                conf = edge["confidence"]
                strength = edge["impact_strength"]

                # Attenuate probability through chain
                impact_prob = cum_prob * conf
                if impact_prob < 0.1:
                    continue  # Too attenuated

                cascaded_lag = total_lag + lag

                results.append({
                    "asset_class": neighbor,
                    "impact_strength": strength,
                    "impact_probability": round(impact_prob, 3),
                    "expected_lag_days": cascaded_lag,
                    "transmission_from": current,
                    "description": edge["description"],
                    "color": ASSET_COLORS.get(neighbor, "#888"),
                })

                # Continue cascade from this node
                queue.append((neighbor, cascaded_lag, impact_prob * 0.8))

        # Sort by probability descending
        results.sort(key=lambda x: x["impact_probability"], reverse=True)
        return results

    def get_full_graph(self, active_source: str | None = None) -> dict:
        """Export full graph as D3-compatible JSON (nodes[] + links[]).

        If active_source is provided, marks active cascade paths.
        """
        active_path = set()
        if active_source:
            cascade = self.get_cascade_path(active_source)
            active_path = {active_source} | {c["asset_class"] for c in cascade}

        nodes = []
        for node in self.graph.nodes:
            nodes.append({
                "id": node,
                "color": ASSET_COLORS.get(node, "#888"),
                "active": node in active_path,
            })

        links = []
        for source, target, data in self.graph.edges(data=True):
            is_active = active_source and source in active_path and target in active_path
            links.append({
                "source": source,
                "target": target,
                "impact_strength": data["impact_strength"],
                "avg_lag_days": data["avg_lag_days"],
                "confidence": data["confidence"],
                "description": data["description"],
                "value": {"High": 8, "Medium": 5, "Low": 2}[data["impact_strength"]],
                "active": bool(is_active),
            })

        return {"nodes": nodes, "links": links}

    def get_sector_scorecard(self, alert_crisis_type: str = "BANKING_INSTABILITY") -> list[dict]:
        """Generate sector exposure scorecard based on active alert."""
        # Sector → (exposure_score, primary_signal, precedent, flag)
        scorecards = {
            "BANKING_INSTABILITY": [
                {"sector": "Financials", "exposure": 92, "signal": "HY spread +3.2σ", "precedent": "GFC 2008", "flag": "EXPOSED"},
                {"sector": "Real Estate", "exposure": 78, "signal": "Mortgage rates rising", "precedent": "2008 Housing", "flag": "EXPOSED"},
                {"sector": "Energy", "exposure": 55, "signal": "Credit spreads widening", "precedent": "2015 Oil crash", "flag": "MONITOR"},
                {"sector": "Technology", "exposure": 42, "signal": "Growth discount rising", "precedent": "SVB 2023", "flag": "MONITOR"},
                {"sector": "Utilities", "exposure": 28, "signal": "Rate sensitivity moderate", "precedent": "Stable", "flag": "MONITOR"},
                {"sector": "Consumer Staples", "exposure": 18, "signal": "Defensive positioning", "precedent": "Resilient", "flag": "MONITOR"},
            ],
            "MARKET_CRASH": [
                {"sector": "Technology", "exposure": 88, "signal": "VIX +3σ, beta 1.4", "precedent": "Dot-com 2000", "flag": "EXPOSED"},
                {"sector": "Financials", "exposure": 75, "signal": "Vol of vol elevated", "precedent": "Flash Crash 2010", "flag": "EXPOSED"},
                {"sector": "Energy", "exposure": 68, "signal": "Oil demand outlook cut", "precedent": "COVID 2020", "flag": "EXPOSED"},
                {"sector": "Real Estate", "exposure": 52, "signal": "REITs underperforming", "precedent": "Rate shock 2022", "flag": "MONITOR"},
                {"sector": "Consumer Staples", "exposure": 22, "signal": "Low beta shelter", "precedent": "Outperforms", "flag": "MONITOR"},
                {"sector": "Utilities", "exposure": 15, "signal": "Defensive demand", "precedent": "Safe haven", "flag": "MONITOR"},
            ],
            "LIQUIDITY_SHORTAGE": [
                {"sector": "Financials", "exposure": 95, "signal": "SOFR +2.8σ", "precedent": "Repo spike 2019", "flag": "EXPOSED"},
                {"sector": "Real Estate", "exposure": 82, "signal": "Funding cost surge", "precedent": "Lehman 2008", "flag": "EXPOSED"},
                {"sector": "Energy", "exposure": 61, "signal": "Margin calls rising", "precedent": "2022 LDI crisis", "flag": "EXPOSED"},
                {"sector": "Technology", "exposure": 48, "signal": "VC funding freeze risk", "precedent": "SVB 2023", "flag": "MONITOR"},
                {"sector": "Utilities", "exposure": 32, "signal": "Regulated cash flows", "precedent": "Moderate impact", "flag": "MONITOR"},
                {"sector": "Consumer Staples", "exposure": 20, "signal": "Cash-rich balance sheets", "precedent": "Resilient", "flag": "MONITOR"},
            ],
        }
        return scorecards.get(alert_crisis_type, scorecards["BANKING_INSTABILITY"])


# Singleton
cascade_mapper = CascadeMapper()
