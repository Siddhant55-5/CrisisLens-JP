/**
 * Mock data for cross-market contagion analysis.
 */

/* ── Cascade graph (D3 Sankey-compatible) ─────────────────── */

export const MOCK_CASCADE_GRAPH = {
  nodes: [
    { id: 'CURRENCY', color: '#3b82f6', active: true },
    { id: 'COMMODITY', color: '#f59e0b', active: true },
    { id: 'EQUITY', color: '#6366f1', active: true },
    { id: 'BOND', color: '#14b8a6', active: true },
    { id: 'SOVEREIGN', color: '#ef4444', active: false },
  ],
  links: [
    { source: 'CURRENCY', target: 'EQUITY', impact_strength: 'High', avg_lag_days: 2, confidence: 0.85, value: 8, active: true, description: 'FX stress transmits via trade channels' },
    { source: 'CURRENCY', target: 'COMMODITY', impact_strength: 'High', avg_lag_days: 1, confidence: 0.82, value: 8, active: true, description: 'USD strength depresses commodity prices' },
    { source: 'CURRENCY', target: 'BOND', impact_strength: 'Medium', avg_lag_days: 3, confidence: 0.71, value: 5, active: true, description: 'Capital flows adjust fixed income' },
    { source: 'CURRENCY', target: 'SOVEREIGN', impact_strength: 'Medium', avg_lag_days: 5, confidence: 0.68, value: 5, active: false, description: 'EM sovereign risk rises' },
    { source: 'EQUITY', target: 'BOND', impact_strength: 'High', avg_lag_days: 0, confidence: 0.88, value: 8, active: true, description: 'Flight to quality drives bond rally' },
    { source: 'EQUITY', target: 'COMMODITY', impact_strength: 'Medium', avg_lag_days: 1, confidence: 0.72, value: 5, active: false, description: 'Demand destruction narrative' },
    { source: 'EQUITY', target: 'CURRENCY', impact_strength: 'Medium', avg_lag_days: 1, confidence: 0.69, value: 5, active: false, description: 'Risk-off triggers safe-haven flows' },
    { source: 'BOND', target: 'EQUITY', impact_strength: 'High', avg_lag_days: 1, confidence: 0.81, value: 8, active: true, description: 'Rate shock reprices equity risk' },
    { source: 'BOND', target: 'SOVEREIGN', impact_strength: 'High', avg_lag_days: 2, confidence: 0.87, value: 8, active: false, description: 'Core rates cascade to sovereigns' },
    { source: 'BOND', target: 'CURRENCY', impact_strength: 'Medium', avg_lag_days: 1, confidence: 0.74, value: 5, active: false, description: 'Yield differentials drive carry' },
    { source: 'COMMODITY', target: 'CURRENCY', impact_strength: 'Medium', avg_lag_days: 2, confidence: 0.66, value: 5, active: false, description: 'Commodity exporters FX tracks' },
    { source: 'COMMODITY', target: 'EQUITY', impact_strength: 'Medium', avg_lag_days: 1, confidence: 0.63, value: 5, active: false, description: 'Energy costs squeeze margins' },
    { source: 'COMMODITY', target: 'SOVEREIGN', impact_strength: 'Low', avg_lag_days: 7, confidence: 0.55, value: 2, active: false, description: 'Resource-dependent sovereigns' },
    { source: 'SOVEREIGN', target: 'BOND', impact_strength: 'High', avg_lag_days: 0, confidence: 0.91, value: 8, active: false, description: 'Sovereign stress widens spreads' },
    { source: 'SOVEREIGN', target: 'EQUITY', impact_strength: 'High', avg_lag_days: 1, confidence: 0.84, value: 8, active: false, description: 'Banking exposures propagate' },
    { source: 'SOVEREIGN', target: 'CURRENCY', impact_strength: 'High', avg_lag_days: 0, confidence: 0.89, value: 8, active: false, description: 'Sovereign risk depresses FX' },
  ],
};

/* ── Correlation matrix (12 signals × 12 signals) ─────────── */

export const CORR_SIGNALS = [
  'SOFR', 'DFF', 'DGS2', 'DGS10', 'T10Y2Y', 'HY_Spread',
  'VIX', 'SPX', 'DXY', 'EURUSD', 'GBPUSD', 'GOLD',
];

// Realistic correlation matrix (upper triangle filled, mirrored)
const RAW_CORR: Record<string, Record<string, number>> = {
  SOFR:      { DFF: 0.97, DGS2: 0.68, DGS10: 0.42, T10Y2Y: -0.31, HY_Spread: 0.44, VIX: 0.28, SPX: -0.22, DXY: 0.35, EURUSD: -0.31, GBPUSD: -0.25, GOLD: -0.18 },
  DFF:       { DGS2: 0.71, DGS10: 0.45, T10Y2Y: -0.28, HY_Spread: 0.41, VIX: 0.25, SPX: -0.19, DXY: 0.33, EURUSD: -0.29, GBPUSD: -0.22, GOLD: -0.15 },
  DGS2:      { DGS10: 0.91, T10Y2Y: -0.42, HY_Spread: 0.35, VIX: 0.18, SPX: -0.15, DXY: 0.28, EURUSD: -0.24, GBPUSD: -0.20, GOLD: -0.22 },
  DGS10:     { T10Y2Y: 0.65, HY_Spread: 0.28, VIX: 0.12, SPX: -0.08, DXY: 0.21, EURUSD: -0.18, GBPUSD: -0.14, GOLD: -0.25 },
  T10Y2Y:    { HY_Spread: -0.15, VIX: -0.22, SPX: 0.31, DXY: -0.08, EURUSD: 0.06, GBPUSD: 0.09, GOLD: 0.05 },
  HY_Spread: { VIX: 0.71, SPX: -0.58, DXY: 0.22, EURUSD: -0.19, GBPUSD: -0.24, GOLD: 0.15 },
  VIX:       { SPX: -0.82, DXY: 0.18, EURUSD: -0.14, GBPUSD: -0.21, GOLD: 0.35 },
  SPX:       { DXY: -0.12, EURUSD: 0.09, GBPUSD: 0.15, GOLD: -0.28 },
  DXY:       { EURUSD: -0.88, GBPUSD: -0.75, GOLD: -0.45 },
  EURUSD:    { GBPUSD: 0.72, GOLD: 0.38 },
  GBPUSD:    { GOLD: 0.31 },
  GOLD:      {},
};

export function getCorrelationValue(sigA: string, sigB: string): number {
  if (sigA === sigB) return 1.0;
  return RAW_CORR[sigA]?.[sigB] ?? RAW_CORR[sigB]?.[sigA] ?? 0.0;
}

/* ── Regime info ──────────────────────────────────────────── */

export const MOCK_REGIME = {
  current_regime: 'elevated',
  avg_correlation: 0.52,
  last_shift: {
    detected_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    from_regime: 'normal',
    to_regime: 'elevated',
    avg_correlation: 0.52,
    most_correlated_pairs: [
      { signal_a: 'SOFR', signal_b: 'DFF', value: 0.97 },
      { signal_a: 'DGS2', signal_b: 'DGS10', value: 0.91 },
      { signal_a: 'DXY', signal_b: 'EURUSD', value: -0.88 },
      { signal_a: 'VIX', signal_b: 'SPX', value: -0.82 },
      { signal_a: 'DXY', signal_b: 'GBPUSD', value: -0.75 },
    ],
    historical_precedent: 'Elevated correlations resemble the 2011 European Debt Crisis, where contagion spread across sovereign, banking, and equity markets.',
  },
};

/* ── Sector scorecard ─────────────────────────────────────── */

export const MOCK_SECTOR_SCORECARD = [
  { sector: 'Financials', exposure: 92, signal: 'HY spread +3.2σ', precedent: 'GFC 2008', flag: 'EXPOSED' },
  { sector: 'Real Estate', exposure: 78, signal: 'Mortgage rates rising', precedent: '2008 Housing', flag: 'EXPOSED' },
  { sector: 'Energy', exposure: 55, signal: 'Credit spreads widening', precedent: '2015 Oil crash', flag: 'MONITOR' },
  { sector: 'Technology', exposure: 42, signal: 'Growth discount rising', precedent: 'SVB 2023', flag: 'MONITOR' },
  { sector: 'Utilities', exposure: 28, signal: 'Rate sensitivity moderate', precedent: 'Stable', flag: 'MONITOR' },
  { sector: 'Consumer Staples', exposure: 18, signal: 'Defensive positioning', precedent: 'Resilient', flag: 'MONITOR' },
];
