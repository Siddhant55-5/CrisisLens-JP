/**
 * Mock OHLC + event data for the PredictionChart.
 * Generates realistic candle data for GBP/USD, EUR/USD, SPX, GOLD.
 */

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface EventPin {
  index: number;
  label: string;
  detail: string;
  shapSummary: { feature: string; value: string; direction: 'up' | 'down' }[];
}

function generateCandles(basePrice: number, volatility: number, count: number, trend: number): Candle[] {
  const candles: Candle[] = [];
  let price = basePrice;
  const now = Date.now();
  for (let i = 0; i < count; i++) {
    const drift = trend * (1 + Math.random() * 0.5);
    const move = (Math.random() - 0.48 + drift) * volatility;
    const open = price;
    const close = price + move;
    const wickUp = Math.random() * volatility * 0.6;
    const wickDown = Math.random() * volatility * 0.6;
    const high = Math.max(open, close) + wickUp;
    const low = Math.min(open, close) - wickDown;
    const volume = Math.floor(50000 + Math.random() * 150000);
    const time = new Date(now - (count - i) * 3600000).toISOString();
    candles.push({ time, open: +open.toFixed(5), high: +high.toFixed(5), low: +low.toFixed(5), close: +close.toFixed(5), volume });
    price = close;
  }
  return candles;
}

export const MOCK_ASSETS: Record<string, { candles: Candle[]; keyLevels: number[]; direction: 'bullish' | 'bearish'; unit: string }> = {
  GBPUSD: {
    candles: generateCandles(1.2650, 0.0025, 48, -0.001),
    keyLevels: [1.2700, 1.2600, 1.2550],
    direction: 'bearish',
    unit: '',
  },
  EURUSD: {
    candles: generateCandles(1.0820, 0.0020, 48, 0.0005),
    keyLevels: [1.0850, 1.0800, 1.0750],
    direction: 'bullish',
    unit: '',
  },
  SPX: {
    candles: generateCandles(5180, 18, 48, -2),
    keyLevels: [5200, 5150, 5100],
    direction: 'bearish',
    unit: '',
  },
  GOLD: {
    candles: generateCandles(2340, 8, 48, 1.5),
    keyLevels: [2360, 2330, 2300],
    direction: 'bullish',
    unit: '',
  },
};

export const MOCK_EVENTS: EventPin[] = [
  {
    index: 35,
    label: 'Liquidity stress: +14pts',
    detail: 'Interbank lending rates spiked 14bps above 20-day average',
    shapSummary: [
      { feature: 'SOFR z-score', value: '+2.8σ', direction: 'up' },
      { feature: 'HY spread', value: '+3.1σ', direction: 'up' },
      { feature: 'VIX level', value: '+1.4σ', direction: 'up' },
    ],
  },
  {
    index: 41,
    label: 'VIX spike detected',
    detail: 'VIX crossed 25 threshold — equity vol regime shift',
    shapSummary: [
      { feature: 'VIX z-score', value: '+3.2σ', direction: 'up' },
      { feature: 'Put/Call ratio', value: '1.15', direction: 'up' },
      { feature: 'SPX drawdown', value: '-2.3%', direction: 'down' },
    ],
  },
];

export const MOCK_CROSS_IMPACT = [
  { name: 'EUR/USD', type: 'FX' as const, direction: 'down' as const, confidence: 82 },
  { name: 'Nikkei 225', type: 'Equity' as const, direction: 'down' as const, confidence: 74 },
  { name: 'Gold', type: 'Commodity' as const, direction: 'up' as const, confidence: 88 },
  { name: 'US Treasuries', type: 'Bond' as const, direction: 'up' as const, confidence: 91 },
  { name: 'GBP/JPY', type: 'FX' as const, direction: 'down' as const, confidence: 67 },
];

export const MOCK_INSTRUMENTS = [
  { ticker: 'DXY', direction: 'up' as const },
  { ticker: 'USDJPY', direction: 'up' as const },
  { ticker: 'VIX', direction: 'up' as const },
  { ticker: 'TLT', direction: 'down' as const },
];

export const MOCK_ALERTS = [
  {
    id: 1,
    crisis_type: 'BANKING_INSTABILITY',
    score: 84,
    ci_lower: 79,
    ci_upper: 89,
    severity: 'HIGH' as const,
    triggered_at: new Date(Date.now() - 300000).toISOString(),
    recommended_actions: ['Review counterparty exposure', 'Tighten stop-loss thresholds', 'Increase cash reserves'],
    top_shap: [
      { feature_name: 'hy_spread_z5d', shap_value: 0.32, direction: 'up' as const, rank: 1 },
      { feature_name: 'sofr_z5d', shap_value: 0.24, direction: 'up' as const, rank: 2 },
      { feature_name: 'ted_spread_z', shap_value: 0.18, direction: 'up' as const, rank: 3 },
      { feature_name: 't10y2y_z5d', shap_value: -0.12, direction: 'down' as const, rank: 4 },
      { feature_name: 'vix_z5d', shap_value: 0.09, direction: 'up' as const, rank: 5 },
    ],
    historical_analog: { event_name: 'EU Debt Crisis 2011', date: '2011-07-01', similarity_score: 0.87, outcome_summary: 'Sovereign spreads widened 200+ bps, ECB intervention required.' },
  },
  {
    id: 2,
    crisis_type: 'MARKET_CRASH',
    score: 71,
    ci_lower: 65,
    ci_upper: 77,
    severity: 'HIGH' as const,
    triggered_at: new Date(Date.now() - 900000).toISOString(),
    recommended_actions: ['Consider reducing equity exposure', 'Monitor VIX closely'],
    top_shap: [
      { feature_name: 'vix_z5d', shap_value: 0.41, direction: 'up' as const, rank: 1 },
      { feature_name: 'spx_pct5d', shap_value: 0.28, direction: 'up' as const, rank: 2 },
      { feature_name: 'put_call_ratio', shap_value: 0.15, direction: 'up' as const, rank: 3 },
      { feature_name: 'gold_pct5d', shap_value: -0.08, direction: 'down' as const, rank: 4 },
      { feature_name: 'dxy_z5d', shap_value: 0.06, direction: 'up' as const, rank: 5 },
    ],
    historical_analog: { event_name: 'COVID-19 Crash 2020', date: '2020-03-16', similarity_score: 0.72, outcome_summary: 'Fastest 30% drawdown in history. Fed cut rates to zero.' },
  },
  {
    id: 3,
    crisis_type: 'LIQUIDITY_SHORTAGE',
    score: 58,
    ci_lower: 51,
    ci_upper: 65,
    severity: 'MEDIUM' as const,
    triggered_at: new Date(Date.now() - 1800000).toISOString(),
    recommended_actions: ['Monitor interbank lending spreads', 'Prepare liquidity contingency'],
    top_shap: [
      { feature_name: 'libor_ois_z', shap_value: 0.35, direction: 'up' as const, rank: 1 },
      { feature_name: 'fra_ois_z', shap_value: 0.22, direction: 'up' as const, rank: 2 },
      { feature_name: 'sofr_z5d', shap_value: 0.14, direction: 'up' as const, rank: 3 },
      { feature_name: 'pmi_us', shap_value: -0.10, direction: 'down' as const, rank: 4 },
      { feature_name: 'baltic_dry_pct20d', shap_value: -0.07, direction: 'down' as const, rank: 5 },
    ],
    historical_analog: { event_name: 'SVB Banking Crisis 2023', date: '2023-03-10', similarity_score: 0.65, outcome_summary: 'Regional bank stress, FDIC intervention, contagion fears.' },
  },
  {
    id: 4,
    crisis_type: 'BANKING_INSTABILITY',
    score: 42,
    ci_lower: 36,
    ci_upper: 48,
    severity: 'LOW' as const,
    triggered_at: new Date(Date.now() - 7200000).toISOString(),
    recommended_actions: ['Monitor signal trends over next 24 hours'],
    top_shap: [
      { feature_name: 'interbank_stress', shap_value: 0.18, direction: 'up' as const, rank: 1 },
      { feature_name: 'dff_z5d', shap_value: 0.11, direction: 'up' as const, rank: 2 },
      { feature_name: 'cpi_yoy', shap_value: -0.09, direction: 'down' as const, rank: 3 },
      { feature_name: 'pmi_eu', shap_value: -0.06, direction: 'down' as const, rank: 4 },
      { feature_name: 'copper_gold_ratio', shap_value: -0.04, direction: 'down' as const, rank: 5 },
    ],
    historical_analog: null,
  },
];

export const MOCK_SCORES = [
  { crisis_type: 'BANKING_INSTABILITY', score: 72.4, ci_lower: 66.1, ci_upper: 78.7, scored_at: new Date().toISOString() },
  { crisis_type: 'MARKET_CRASH', score: 58.1, ci_lower: 51.3, ci_upper: 64.9, scored_at: new Date().toISOString() },
  { crisis_type: 'LIQUIDITY_SHORTAGE', score: 45.6, ci_lower: 39.2, ci_upper: 52.0, scored_at: new Date().toISOString() },
];

/* Country risk data for world map choropleth */
export const COUNTRY_RISKS: Record<string, { name: string; flag: string; banking: number; market: number; liquidity: number; topSignal: string }> = {
  USA: { name: 'United States', flag: '🇺🇸', banking: 68, market: 55, liquidity: 42, topSignal: 'SOFR rate elevated +2.1σ' },
  GBR: { name: 'United Kingdom', flag: '🇬🇧', banking: 72, market: 61, liquidity: 48, topSignal: 'Gilt yields inverted -45bps' },
  DEU: { name: 'Germany', flag: '🇩🇪', banking: 58, market: 52, liquidity: 38, topSignal: 'DAX vol above 20-day mean' },
  FRA: { name: 'France', flag: '🇫🇷', banking: 61, market: 54, liquidity: 41, topSignal: 'OAT-Bund spread widening' },
  JPN: { name: 'Japan', flag: '🇯🇵', banking: 45, market: 62, liquidity: 55, topSignal: 'JPY carry unwind risk rising' },
  CHN: { name: 'China', flag: '🇨🇳', banking: 78, market: 71, liquidity: 65, topSignal: 'Property sector stress elevated' },
  IND: { name: 'India', flag: '🇮🇳', banking: 35, market: 38, liquidity: 28, topSignal: 'Stable — no anomalies detected' },
  BRA: { name: 'Brazil', flag: '🇧🇷', banking: 52, market: 58, liquidity: 44, topSignal: 'BRL under pressure, -1.8σ' },
  AUS: { name: 'Australia', flag: '🇦🇺', banking: 42, market: 45, liquidity: 35, topSignal: 'Housing market cooling' },
  CAN: { name: 'Canada', flag: '🇨🇦', banking: 48, market: 44, liquidity: 36, topSignal: 'BoC rate sensitivity elevated' },
  ITA: { name: 'Italy', flag: '🇮🇹', banking: 65, market: 57, liquidity: 50, topSignal: 'BTP spread +120bps' },
  ESP: { name: 'Spain', flag: '🇪🇸', banking: 55, market: 48, liquidity: 40, topSignal: 'Tourism sector normalization' },
  KOR: { name: 'South Korea', flag: '🇰🇷', banking: 40, market: 50, liquidity: 38, topSignal: 'Chip export orders declining' },
  MEX: { name: 'Mexico', flag: '🇲🇽', banking: 44, market: 46, liquidity: 39, topSignal: 'Peso stable, nearshoring flows' },
  RUS: { name: 'Russia', flag: '🇷🇺', banking: 85, market: 80, liquidity: 78, topSignal: 'Sanctions pressure persistent' },
  TUR: { name: 'Turkey', flag: '🇹🇷', banking: 75, market: 72, liquidity: 68, topSignal: 'Lira depreciation accelerating' },
  ZAF: { name: 'South Africa', flag: '🇿🇦', banking: 58, market: 55, liquidity: 48, topSignal: 'Load shedding impacting growth' },
  ARG: { name: 'Argentina', flag: '🇦🇷', banking: 82, market: 78, liquidity: 75, topSignal: 'Peso crisis, inflation >100%' },
  SGP: { name: 'Singapore', flag: '🇸🇬', banking: 28, market: 32, liquidity: 22, topSignal: 'Safe haven flows elevated' },
  CHE: { name: 'Switzerland', flag: '🇨🇭', banking: 32, market: 30, liquidity: 25, topSignal: 'CHF strength — safe haven bid' },
};
