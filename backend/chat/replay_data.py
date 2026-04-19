"""Crisis replay data — historical crisis sequences for time-travel analysis.

Pre-loaded with 3 crises:
  - 2008 Lehman: Sep 2007 → Mar 2008 (26 weekly frames)
  - SVB 2023: Jan → Mar 2023 (8 weekly frames)
  - EU Debt 2011: Jan → Dec 2011 (12 monthly frames)
"""

from __future__ import annotations

REPLAYS: dict[str, dict] = {
    "2008_lehman": {
        "id": "2008_lehman",
        "name": "2008 Lehman Brothers Collapse",
        "description": "The cascade from subprime mortgages to global systemic crisis",
        "period": "Sep 2007 – Mar 2009",
        "frames": [
            {"date": "2007-09-07", "signals": {"SOFR": 5.25, "VIX": 18.2, "SPX": 1453, "DXY": 80.1, "HY_spread": 3.8, "T10Y2Y": 0.15}, "scores": {"banking": 28, "market": 22, "liquidity": 18}},
            {"date": "2007-10-05", "signals": {"SOFR": 5.25, "VIX": 16.5, "SPX": 1557, "DXY": 78.2, "HY_spread": 3.6, "T10Y2Y": 0.08}, "scores": {"banking": 25, "market": 18, "liquidity": 20}},
            {"date": "2007-11-02", "signals": {"SOFR": 4.75, "VIX": 21.8, "SPX": 1509, "DXY": 76.5, "HY_spread": 4.2, "T10Y2Y": -0.05}, "scores": {"banking": 35, "market": 30, "liquidity": 28}},
            {"date": "2007-12-07", "signals": {"SOFR": 4.50, "VIX": 22.5, "SPX": 1481, "DXY": 76.8, "HY_spread": 4.8, "T10Y2Y": -0.15}, "scores": {"banking": 42, "market": 35, "liquidity": 34}},
            {"date": "2008-01-04", "signals": {"SOFR": 4.25, "VIX": 23.2, "SPX": 1411, "DXY": 76.1, "HY_spread": 5.5, "T10Y2Y": -0.28}, "scores": {"banking": 48, "market": 42, "liquidity": 40}},
            {"date": "2008-02-01", "signals": {"SOFR": 3.50, "VIX": 26.1, "SPX": 1355, "DXY": 75.8, "HY_spread": 6.2, "T10Y2Y": -0.40}, "scores": {"banking": 55, "market": 48, "liquidity": 45}},
            {"date": "2008-03-07", "signals": {"SOFR": 3.00, "VIX": 28.5, "SPX": 1304, "DXY": 73.5, "HY_spread": 6.8, "T10Y2Y": -0.55}, "scores": {"banking": 62, "market": 55, "liquidity": 52}},
            {"date": "2008-03-14", "signals": {"SOFR": 3.00, "VIX": 32.2, "SPX": 1288, "DXY": 72.1, "HY_spread": 7.8, "T10Y2Y": -0.68}, "scores": {"banking": 72, "market": 65, "liquidity": 62}},
            {"date": "2008-03-17", "signals": {"SOFR": 2.25, "VIX": 35.1, "SPX": 1256, "DXY": 71.5, "HY_spread": 8.5, "T10Y2Y": -0.82}, "scores": {"banking": 78, "market": 72, "liquidity": 68}},
            {"date": "2008-04-04", "signals": {"SOFR": 2.25, "VIX": 24.5, "SPX": 1370, "DXY": 72.8, "HY_spread": 7.2, "T10Y2Y": -0.60}, "scores": {"banking": 65, "market": 58, "liquidity": 55}},
            {"date": "2008-05-02", "signals": {"SOFR": 2.00, "VIX": 19.8, "SPX": 1413, "DXY": 73.1, "HY_spread": 6.8, "T10Y2Y": -0.45}, "scores": {"banking": 58, "market": 50, "liquidity": 48}},
            {"date": "2008-06-06", "signals": {"SOFR": 2.00, "VIX": 22.1, "SPX": 1360, "DXY": 72.5, "HY_spread": 7.0, "T10Y2Y": -0.48}, "scores": {"banking": 60, "market": 55, "liquidity": 52}},
            {"date": "2008-07-03", "signals": {"SOFR": 2.00, "VIX": 24.8, "SPX": 1262, "DXY": 72.0, "HY_spread": 7.5, "T10Y2Y": -0.55}, "scores": {"banking": 65, "market": 60, "liquidity": 58}},
            {"date": "2008-08-01", "signals": {"SOFR": 2.00, "VIX": 22.5, "SPX": 1267, "DXY": 73.8, "HY_spread": 7.2, "T10Y2Y": -0.50}, "scores": {"banking": 62, "market": 58, "liquidity": 55}},
            {"date": "2008-09-05", "signals": {"SOFR": 2.00, "VIX": 25.5, "SPX": 1242, "DXY": 79.5, "HY_spread": 8.0, "T10Y2Y": -0.62}, "scores": {"banking": 68, "market": 65, "liquidity": 60}},
            {"date": "2008-09-12", "signals": {"SOFR": 2.00, "VIX": 28.2, "SPX": 1252, "DXY": 80.2, "HY_spread": 8.8, "T10Y2Y": -0.72}, "scores": {"banking": 75, "market": 70, "liquidity": 68}},
            {"date": "2008-09-15", "signals": {"SOFR": 2.00, "VIX": 36.2, "SPX": 1192, "DXY": 80.8, "HY_spread": 11.5, "T10Y2Y": -0.92}, "scores": {"banking": 92, "market": 88, "liquidity": 85}},
            {"date": "2008-09-19", "signals": {"SOFR": 2.00, "VIX": 33.5, "SPX": 1255, "DXY": 78.2, "HY_spread": 10.2, "T10Y2Y": -0.80}, "scores": {"banking": 85, "market": 80, "liquidity": 78}},
            {"date": "2008-09-29", "signals": {"SOFR": 2.00, "VIX": 46.7, "SPX": 1106, "DXY": 80.5, "HY_spread": 13.5, "T10Y2Y": -1.05}, "scores": {"banking": 95, "market": 92, "liquidity": 90}},
            {"date": "2008-10-10", "signals": {"SOFR": 1.50, "VIX": 69.9, "SPX": 899, "DXY": 82.1, "HY_spread": 18.2, "T10Y2Y": -1.50}, "scores": {"banking": 98, "market": 97, "liquidity": 95}},
            {"date": "2008-10-27", "signals": {"SOFR": 1.00, "VIX": 80.1, "SPX": 848, "DXY": 86.5, "HY_spread": 21.5, "T10Y2Y": -1.85}, "scores": {"banking": 99, "market": 98, "liquidity": 97}},
            {"date": "2008-11-20", "signals": {"SOFR": 1.00, "VIX": 80.9, "SPX": 752, "DXY": 88.0, "HY_spread": 22.0, "T10Y2Y": -2.10}, "scores": {"banking": 99, "market": 98, "liquidity": 98}},
            {"date": "2008-12-05", "signals": {"SOFR": 0.50, "VIX": 62.5, "SPX": 876, "DXY": 86.2, "HY_spread": 19.5, "T10Y2Y": -1.60}, "scores": {"banking": 92, "market": 90, "liquidity": 88}},
            {"date": "2009-01-09", "signals": {"SOFR": 0.25, "VIX": 45.2, "SPX": 890, "DXY": 85.8, "HY_spread": 17.8, "T10Y2Y": -1.20}, "scores": {"banking": 88, "market": 85, "liquidity": 82}},
            {"date": "2009-02-06", "signals": {"SOFR": 0.25, "VIX": 42.1, "SPX": 868, "DXY": 86.9, "HY_spread": 16.5, "T10Y2Y": -1.00}, "scores": {"banking": 85, "market": 82, "liquidity": 78}},
            {"date": "2009-03-06", "signals": {"SOFR": 0.25, "VIX": 49.7, "SPX": 683, "DXY": 89.0, "HY_spread": 19.8, "T10Y2Y": -0.80}, "scores": {"banking": 90, "market": 92, "liquidity": 85}},
        ],
    },
    "svb_2023": {
        "id": "svb_2023",
        "name": "SVB Banking Crisis 2023",
        "description": "Silicon Valley Bank collapse and regional banking contagion",
        "period": "Jan – Mar 2023",
        "frames": [
            {"date": "2023-01-13", "signals": {"SOFR": 4.30, "VIX": 18.7, "SPX": 3999, "DXY": 102.2, "HY_spread": 4.2, "KBW_bank_idx": 105.2}, "scores": {"banking": 25, "market": 20, "liquidity": 30}},
            {"date": "2023-01-27", "signals": {"SOFR": 4.55, "VIX": 19.2, "SPX": 4070, "DXY": 101.5, "HY_spread": 4.1, "KBW_bank_idx": 108.5}, "scores": {"banking": 22, "market": 18, "liquidity": 32}},
            {"date": "2023-02-10", "signals": {"SOFR": 4.55, "VIX": 20.5, "SPX": 4090, "DXY": 103.8, "HY_spread": 4.5, "KBW_bank_idx": 104.1}, "scores": {"banking": 30, "market": 22, "liquidity": 35}},
            {"date": "2023-02-24", "signals": {"SOFR": 4.55, "VIX": 21.8, "SPX": 3970, "DXY": 105.1, "HY_spread": 4.8, "KBW_bank_idx": 99.8}, "scores": {"banking": 38, "market": 28, "liquidity": 42}},
            {"date": "2023-03-03", "signals": {"SOFR": 4.55, "VIX": 20.5, "SPX": 4045, "DXY": 104.5, "HY_spread": 4.6, "KBW_bank_idx": 100.5}, "scores": {"banking": 35, "market": 25, "liquidity": 40}},
            {"date": "2023-03-09", "signals": {"SOFR": 4.57, "VIX": 24.8, "SPX": 3861, "DXY": 105.5, "HY_spread": 5.2, "KBW_bank_idx": 85.2}, "scores": {"banking": 72, "market": 55, "liquidity": 65}},
            {"date": "2023-03-13", "signals": {"SOFR": 4.59, "VIX": 28.5, "SPX": 3855, "DXY": 103.8, "HY_spread": 5.8, "KBW_bank_idx": 72.5}, "scores": {"banking": 88, "market": 68, "liquidity": 78}},
            {"date": "2023-03-17", "signals": {"SOFR": 4.55, "VIX": 25.5, "SPX": 3917, "DXY": 103.2, "HY_spread": 5.5, "KBW_bank_idx": 78.1}, "scores": {"banking": 80, "market": 60, "liquidity": 72}},
        ],
    },
    "eu_debt_2011": {
        "id": "eu_debt_2011",
        "name": "European Sovereign Debt Crisis 2011",
        "description": "Greek debt contagion spreading to Italy, Spain, and the Eurozone banking sector",
        "period": "Jan – Dec 2011",
        "frames": [
            {"date": "2011-01-14", "signals": {"EURUSD": 1.335, "VIX": 16.5, "italian_10y": 4.72, "greek_10y": 11.5, "SPX": 1293, "HY_spread": 4.5}, "scores": {"banking": 32, "market": 22, "liquidity": 25}},
            {"date": "2011-02-11", "signals": {"EURUSD": 1.355, "VIX": 16.2, "italian_10y": 4.68, "greek_10y": 11.8, "SPX": 1329, "HY_spread": 4.3}, "scores": {"banking": 30, "market": 20, "liquidity": 22}},
            {"date": "2011-03-11", "signals": {"EURUSD": 1.382, "VIX": 20.5, "italian_10y": 4.85, "greek_10y": 12.5, "SPX": 1304, "HY_spread": 4.5}, "scores": {"banking": 35, "market": 28, "liquidity": 28}},
            {"date": "2011-04-08", "signals": {"EURUSD": 1.448, "VIX": 15.2, "italian_10y": 4.62, "greek_10y": 13.8, "SPX": 1328, "HY_spread": 4.2}, "scores": {"banking": 38, "market": 22, "liquidity": 25}},
            {"date": "2011-05-13", "signals": {"EURUSD": 1.414, "VIX": 17.1, "italian_10y": 4.78, "greek_10y": 16.5, "SPX": 1337, "HY_spread": 4.5}, "scores": {"banking": 42, "market": 28, "liquidity": 30}},
            {"date": "2011-06-10", "signals": {"EURUSD": 1.435, "VIX": 18.5, "italian_10y": 4.92, "greek_10y": 17.2, "SPX": 1270, "HY_spread": 4.8}, "scores": {"banking": 48, "market": 35, "liquidity": 35}},
            {"date": "2011-07-15", "signals": {"EURUSD": 1.415, "VIX": 22.8, "italian_10y": 5.75, "greek_10y": 18.5, "SPX": 1316, "HY_spread": 5.2}, "scores": {"banking": 58, "market": 45, "liquidity": 42}},
            {"date": "2011-08-05", "signals": {"EURUSD": 1.428, "VIX": 32.0, "italian_10y": 6.18, "greek_10y": 20.2, "SPX": 1199, "HY_spread": 6.0}, "scores": {"banking": 72, "market": 65, "liquidity": 55}},
            {"date": "2011-09-09", "signals": {"EURUSD": 1.365, "VIX": 38.5, "italian_10y": 5.55, "greek_10y": 22.5, "SPX": 1154, "HY_spread": 6.5}, "scores": {"banking": 78, "market": 72, "liquidity": 62}},
            {"date": "2011-10-07", "signals": {"EURUSD": 1.338, "VIX": 36.2, "italian_10y": 5.68, "greek_10y": 24.0, "SPX": 1155, "HY_spread": 6.8}, "scores": {"banking": 80, "market": 74, "liquidity": 65}},
            {"date": "2011-11-09", "signals": {"EURUSD": 1.355, "VIX": 34.5, "italian_10y": 7.48, "greek_10y": 28.5, "SPX": 1261, "HY_spread": 6.2}, "scores": {"banking": 85, "market": 70, "liquidity": 72}},
            {"date": "2011-12-09", "signals": {"EURUSD": 1.335, "VIX": 28.1, "italian_10y": 6.35, "greek_10y": 32.0, "SPX": 1255, "HY_spread": 5.8}, "scores": {"banking": 75, "market": 62, "liquidity": 60}},
        ],
    },
}


def list_replays() -> list[dict]:
    """List available crisis replays (without frame data)."""
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "period": r["period"],
            "frame_count": len(r["frames"]),
        }
        for r in REPLAYS.values()
    ]


def get_replay_frames(replay_id: str) -> list[dict] | None:
    """Get all frames for a replay, or None if not found."""
    replay = REPLAYS.get(replay_id)
    return replay["frames"] if replay else None
