/* ── TypeScript interfaces mirroring all backend Pydantic models ── */

/* ── Signals ──────────────────────────────────────────────────── */

export type SignalCategory =
  | 'INTERBANK'
  | 'FX'
  | 'EQUITY'
  | 'BOND'
  | 'COMMODITY'
  | 'MACRO';

export type QualityBadge = 'FRESH' | 'STALE' | 'DEGRADED' | 'UNAVAILABLE';

export interface Signal {
  signal_id: string;
  name: string;
  category: SignalCategory;
  description: string | null;
  source: string | null;
  unit: string | null;
  raw_value: number | null;
  z_score: number | null;
  pct_change_1d: number | null;
  freshness_ts: string;
  freshness_score: number;
  completeness_ratio: number;
  anomaly_flag: boolean;
  quality_badge: QualityBadge;
  is_mock: boolean;
  created_at: string;
  updated_at: string;
}

/* ── Risk Scores ─────────────────────────────────────────────── */

export interface RiskScore {
  crisis_type: string;
  score: number;
  ci_lower: number;   // Required — never returned without bounds
  ci_upper: number;    // Required — never returned without bounds
  scored_at: string;
}

export interface RiskScoreHistoryPoint {
  crisis_type: string;
  score: number;
  ci_lower: number;
  ci_upper: number;
  scored_at: string;
}

/* ── Alerts ──────────────────────────────────────────────────── */

export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Alert {
  id: number;
  crisis_type: string;
  score: number;
  ci_lower: number;
  ci_upper: number;
  severity: AlertSeverity;
  triggered_at: string;
  recommended_actions: string[];
  top_shap?: ShapContribution[];
  historical_analog?: HistoricalAnalog | null;
}

/* ── SHAP Explainability ─────────────────────────────────────── */

export interface ShapContribution {
  feature_name: string;
  shap_value: number;
  direction: 'up' | 'down';
  rank: number;
}

export interface HistoricalAnalog {
  event_name: string;
  date: string;
  similarity_score: number;
  outcome_summary: string;
}

/* ── Simulation ──────────────────────────────────────────────── */

export interface SimulateRequest {
  overrides: Record<string, number>;
}

export interface ScoreDiff {
  crisis_type: string;
  current_score: number;
  simulated_score: number;
  delta: number;
  ci_lower: number;
  ci_upper: number;
}

export interface SimulateResponse {
  scores: RiskScore[];
  diff: ScoreDiff[];
}

/* ── Health ───────────────────────────────────────────────────── */

export interface HealthStatus {
  status: string;
  version: string;
  db_connected: boolean;
  redis_connected: boolean;
  signal_count: number;
}

/* ── WebSocket Messages ──────────────────────────────────────── */

export type ConnectionStatus = 'live' | 'reconnecting' | 'offline';

export interface WSMessage {
  type: 'score_update' | 'alert' | 'signal_update';
  data: RiskScore | Alert | Signal;
}
