/**
 * CrisisLens API Client — typed Axios instance with response wrappers.
 *
 * Base URL from VITE_API_URL environment variable.
 */

import axios from 'axios';
import type {
  Alert,
  HealthStatus,
  RiskScore,
  RiskScoreHistoryPoint,
  Signal,
  SimulateRequest,
  SimulateResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ── Signal Endpoints ────────────────────────────────────────── */

export async function fetchSignals(): Promise<Signal[]> {
  const { data } = await api.get<Signal[]>('/v1/signals');
  return data;
}

export async function fetchSignalById(signalId: string): Promise<Signal> {
  const { data } = await api.get<Signal>(`/v1/signals/${signalId}`);
  return data;
}

/* ── Risk Score Endpoints ────────────────────────────────────── */

export async function fetchScores(): Promise<RiskScore[]> {
  const { data } = await api.get<RiskScore[]>('/v1/scores');
  return data;
}

export async function fetchScoreHistory(days: number = 90): Promise<RiskScoreHistoryPoint[]> {
  const { data } = await api.get<RiskScoreHistoryPoint[]>('/v1/scores/history', {
    params: { days },
  });
  return data;
}

/* ── Alert Endpoints ─────────────────────────────────────────── */

export async function fetchAlerts(limit: number = 50, offset: number = 0): Promise<Alert[]> {
  const { data } = await api.get<Alert[]>('/v1/alerts', {
    params: { limit, offset },
  });
  return data;
}

export async function fetchAlertById(alertId: number): Promise<Alert> {
  const { data } = await api.get<Alert>(`/v1/alerts/${alertId}`);
  return data;
}

/* ── Simulation Endpoint ─────────────────────────────────────── */

export async function simulateScenario(request: SimulateRequest): Promise<SimulateResponse> {
  const { data } = await api.post<SimulateResponse>('/v1/simulate', request);
  return data;
}

/* ── Health Endpoint ─────────────────────────────────────────── */

export async function fetchHealth(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>('/healthz');
  return data;
}

/* ── Cross-Market Endpoints ──────────────────────────────────── */

export async function fetchCorrelations(window: string = '20D'): Promise<any> {
  const { data } = await api.get('/v1/correlations', { params: { window } });
  return data;
}

export async function fetchRegime(): Promise<any> {
  const { data } = await api.get('/v1/correlations/regime');
  return data;
}

export async function fetchCascadeGraph(source?: string): Promise<any> {
  const { data } = await api.get('/v1/cascade/graph', { params: source ? { source } : {} });
  return data;
}

export async function fetchSectorScorecard(crisisType: string = 'BANKING_INSTABILITY'): Promise<any> {
  const { data } = await api.get('/v1/sector-scorecard', { params: { crisis_type: crisisType } });
  return data;
}

/* ── Opportunity Endpoints ───────────────────────────────────── */

export async function fetchInversePairs(crisisType?: string): Promise<any> {
  const { data } = await api.get('/v1/opportunities/inverse', { params: crisisType ? { crisis_type: crisisType } : {} });
  return data;
}

export async function fetchDefensiveAssets(crisisType: string = 'BANKING_INSTABILITY'): Promise<any> {
  const { data } = await api.get('/v1/opportunities/defensive', { params: { crisis_type: crisisType } });
  return data;
}

export async function fetchWatchlist(crisisType?: string): Promise<any> {
  const { data } = await api.get('/v1/opportunities/watchlist', { params: crisisType ? { crisis_type: crisisType } : {} });
  return data;
}

/* ── Sentiment Endpoints ─────────────────────────────────────── */

export async function fetchSentiment(limit: number = 10): Promise<any> {
  const { data } = await api.get('/v1/sentiment', { params: { limit } });
  return data;
}

export async function fetchSentimentHistory(days: number = 7): Promise<any> {
  const { data } = await api.get('/v1/sentiment/history', { params: { days } });
  return data;
}
