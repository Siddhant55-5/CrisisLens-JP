/**
 * HomePage — full CrisisLens dashboard combining all widgets:
 *  • Gauge + stat cards (Global Risk, Banking, Market, Liquidity)
 *  • Sentiment badge
 *  • Risk Score Time Series chart (Recharts)
 *  • Alert Panel with live alerts
 *  • Top Contributing Factors (SHAP bar chart)
 *  • PredictionChart (candlestick)
 *  • Correlation Insights
 *  • Per-category score cards
 *  • Opportunity Intelligence panel
 */
import { useState, useEffect, useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine,
  BarChart, Bar, Cell,
} from 'recharts';
import { useRiskStore } from '../store/useRiskStore';
import { MOCK_SCORES, MOCK_ALERTS } from '../lib/mockData';
import PredictionChart from '../components/chart/PredictionChart';
import InsightsPanel from '../components/InsightsPanel';
import OpportunityPanel from '../components/OpportunityPanel';
import ComplianceModal from '../components/ComplianceModal';

/* ── Helpers ──────────────────────────────────────────────────── */

function scoreColor(s: number) {
  if (s <= 40) return 'green';
  if (s <= 65) return 'amber';
  return 'red';
}
function scoreColorCSS(s: number) {
  if (s <= 40) return 'var(--success)';
  if (s <= 65) return 'var(--warning)';
  return 'var(--danger)';
}

function severityLabel(s: number) {
  if (s > 80) return 'CRITICAL';
  if (s > 65) return 'HIGH';
  if (s > 40) return 'MEDIUM';
  return 'LOW';
}

/* Skeleton shimmer placeholder */
function Skeleton({ width, height }: { width?: string; height?: string }) {
  return (
    <div className="skeleton" style={{ width: width || '100%', height: height || '16px' }} />
  );
}

/* Sentiment badge for header */
function SentimentBadge() {
  const sentimentScore = -0.32;
  const cls = sentimentScore <= -0.2 ? 'stress' : sentimentScore >= 0.2 ? 'relief' : 'neutral';
  const label = sentimentScore <= -0.2 ? 'STRESSED' : sentimentScore >= 0.2 ? 'RELIEVED' : 'NEUTRAL';
  return (
    <span className={`sentiment-badge ${cls}`}>
      Sentiment: {label}
    </span>
  );
}

/* ── Generate time-series history ─────────────────────────────── */
function generateTimeSeriesData(currentScore: number, points: number = 60) {
  const data = [];
  const now = Date.now();
  let val = currentScore - 15 + Math.random() * 10;

  for (let i = 0; i < points; i++) {
    const drift = (Math.random() - 0.45) * 3;
    val = Math.max(10, Math.min(95, val + drift));
    // Gradually trend toward currentScore
    val += (currentScore - val) * 0.03;
    const time = new Date(now - (points - i) * 60000);
    data.push({
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      score: +val.toFixed(1),
    });
  }
  return data;
}

/* ── Top SHAP Contributing Factors ────────────────────────────── */
const INITIAL_FACTORS = [
  { feature: 'HY Spread (Credit)', value: 0.346, direction: 'up' as const },
  { feature: 'LIBOR-OIS Spread', value: 0.335, direction: 'up' as const },
  { feature: 'S&P 500 Returns', value: 0.250, direction: 'up' as const },
  { feature: 'SOFR Rate', value: 0.222, direction: 'up' as const },
  { feature: 'FRA-OIS Spread', value: 0.180, direction: 'up' as const },
];

/* ═══════════════════════════════════════════════════════════════ */

export default function HomePage() {
  const storeScores = useRiskStore((s) => s.scores);
  const storeAlerts = useRiskStore((s) => s.alerts);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Local state for live risk scores to simulate real-time variation
  const [liveScores, setLiveScores] = useState(MOCK_SCORES);
  
  // Starting composite score
  const initialGlobalScore = MOCK_SCORES.reduce((a, s) => a + s.score, 0) / MOCK_SCORES.length;
  const [timeSeriesData, setTimeSeriesData] = useState(() => generateTimeSeriesData(initialGlobalScore));
  const [topFactors, setTopFactors] = useState(INITIAL_FACTORS);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(t);
  }, []);

  // Simulate real-time risk value changes
  useEffect(() => {
    const interval = setInterval(() => {
      let maxNewScore = 0;
      let relatedCrisis = '';
      let newGlobalScore = 0;

      setLiveScores(prev => {
        const nextScores = prev.map(s => {
          const drift = (Math.random() - 0.4) * 4;
          const newScore = Math.max(0, Math.min(100, s.score + drift));

          if (newScore > maxNewScore && newScore >= 65) {
            maxNewScore = newScore;
            relatedCrisis = s.crisis_type;
          }

          return {
            ...s,
            score: newScore,
            ci_lower: Math.max(0, newScore - (s.ci_upper - s.ci_lower) / 2),
            ci_upper: Math.min(100, newScore + (s.ci_upper - s.ci_lower) / 2),
          };
        });
        
        newGlobalScore = nextScores.reduce((a, s) => a + s.score, 0) / nextScores.length;

        // Dynamically add an alert if risk exceeds threshold
        if (maxNewScore >= 65 && relatedCrisis) {
          const existingAlerts = useRiskStore.getState().alerts;
          if (!existingAlerts.find(a => a.crisis_type === relatedCrisis && a.score >= 65)) {
            let reason = "Unusual condition flagged by the system.";
            if (relatedCrisis === "BANKING_INSTABILITY") reason = "Recent banking sector stress and rising loan defaults";
            if (relatedCrisis === "MARKET_CRASH") reason = "Stock market volatility is increasing due to investor panic";
            if (relatedCrisis === "LIQUIDITY_SHORTAGE") reason = "Cash flow in financial system is tightening";

            useRiskStore.getState().addAlert({
              id: Date.now(),
              crisis_type: relatedCrisis,
              score: maxNewScore,
              ci_lower: maxNewScore - 4,
              ci_upper: maxNewScore + 4,
              severity: maxNewScore > 80 ? 'CRITICAL' : 'HIGH',
              triggered_at: new Date().toISOString(),
              recommended_actions: [reason]
            });
          }
        }

        return nextScores;
      });
      
      // Update the continuous time series
      setTimeSeriesData(prev => {
        const next = [...prev.slice(1)];
        const now = new Date();
        next.push({
          time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          score: +newGlobalScore.toFixed(1)
        });
        return next;
      });
      
      // Slightly fluctuate the SHAP factors
      setTopFactors(prev => prev.map(f => {
        const drift = (Math.random() - 0.4) * 0.05;
        const val = Math.max(0.1, Math.min(0.8, f.value + drift));
        return { ...f, value: val };
      }));

      setLastUpdated(new Date());
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Seed alerts from MOCK_ALERTS on first mount
  useEffect(() => {
    const existing = useRiskStore.getState().alerts;
    if (existing.length === 0) {
      MOCK_ALERTS.forEach(a => useRiskStore.getState().addAlert(a as any));
    }
  }, []);

  const alerts = storeAlerts.length > 0 ? storeAlerts : [];
  const scores = storeScores.length > 0 ? storeScores : liveScores;

  const globalScore = scores.length > 0
    ? +(scores.reduce((a, s) => a + s.score, 0) / scores.length).toFixed(1)
    : 0;
  const ciLow = scores.length > 0 ? +(scores.reduce((a, s) => a + s.ci_lower, 0) / scores.length).toFixed(1) : 0;
  const ciHigh = scores.length > 0 ? +(scores.reduce((a, s) => a + s.ci_upper, 0) / scores.length).toFixed(1) : 0;

  const alertCount = alerts.length;

  const avgCIWidth = scores.length > 0
    ? scores.reduce((a, s) => a + (s.ci_upper - s.ci_lower), 0) / scores.length
    : 12;
  const modelConf = Math.max(0, Math.min(100, 100 - avgCIWidth * 2.5)).toFixed(0);

  // Keyboard: Esc closes chat panel
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        const toggle = document.querySelector('.chat-toggle-btn') as HTMLElement;
        const panel = document.querySelector('.chat-panel');
        if (panel && toggle) toggle.click();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <>
      <ComplianceModal />

      {/* ── Header: Last updated + Sentiment ─────────────────── */}
      <div className="home-header-bar">
        <div className="last-updated">
          <span className="last-updated-dot" />
          Last updated: {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>
        <SentimentBadge />
      </div>

      {/* ── Stats Row: Gauge + Category Score Cards ───────────── */}
      <div className="stats-row">
        {loading ? (
          <>
            {[1, 2, 3, 4].map(i => (
              <div className="card stat-card" key={i}>
                <Skeleton width="60%" height="12px" />
                <div style={{ marginTop: 12 }}><Skeleton width="40%" height="28px" /></div>
                <div style={{ marginTop: 8 }}><Skeleton width="50%" height="10px" /></div>
              </div>
            ))}
          </>
        ) : (
          <>
            {/* Gauge Card */}
            <div className="card stat-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <div className="gauge-container">
                <svg width="120" height="70" viewBox="0 0 120 70">
                  <path d="M10 65 A50 50 0 0 1 110 65" fill="none" stroke="var(--border)" strokeWidth="8" strokeLinecap="round" />
                  <path
                    d="M10 65 A50 50 0 0 1 110 65"
                    fill="none"
                    stroke={scoreColorCSS(globalScore)}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(globalScore / 100) * 157} 157`}
                  />
                </svg>
                <div className="gauge-score-text" style={{ color: scoreColorCSS(globalScore), marginTop: -8 }}>
                  {globalScore.toFixed(1)}
                </div>
                <div className="gauge-ci-text">CI [{ciLow} – {ciHigh}]</div>
                <div style={{
                  marginTop: 6,
                  padding: '2px 10px',
                  borderRadius: 100,
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  background: globalScore > 65 ? 'var(--danger-dim)' : globalScore > 40 ? 'var(--warning-dim)' : 'var(--success-dim)',
                  color: scoreColorCSS(globalScore),
                  letterSpacing: '.05em'
                }}>
                  🚨 {severityLabel(globalScore)}
                </div>
              </div>
            </div>

            {/* Per-crisis score cards */}
            {scores.map((s) => (
              <div className="card stat-card" key={s.crisis_type}>
                <div className="stat-label">{s.crisis_type.replace(/_/g, ' ')}</div>
                <div className={`stat-value ${scoreColor(s.score)}`}>{s.score.toFixed(1)}</div>
                <div className="stat-sub">[{s.ci_lower.toFixed(1)} – {s.ci_upper.toFixed(1)}]</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: s.score > 65 ? 'var(--danger)' : s.score > 40 ? 'var(--warning)' : 'var(--success)',
                  }}>
                    {s.score > 65 ? '⚠ Stress' : s.score > 40 ? '⚠ Elevated' : '✅ Stable'}
                  </span>
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* ── Risk Score Time Series + Alert Panel ─────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16, marginBottom: 24 }}>
        {/* Time Series Chart */}
        <div className="card" style={{ padding: '20px 20px 12px', position: 'relative' }}>
          <div className="card-header" style={{ marginBottom: 8 }}>
            <span className="card-title">📈 Risk Score Time Series</span>
            <div style={{ display: 'flex', gap: 12, fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text-3)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--danger)' }} /> Risk Score
              </span>
              <span>--- HIGH (50)</span>
              <span style={{ color: 'var(--warning)' }}>--- MED (20)</span>
            </div>
          </div>
          {loading ? (
            <Skeleton width="100%" height="200px" />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={timeSeriesData} margin={{ top: 12, right: 40, left: 0, bottom: 4 }}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--danger)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--danger)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: 'var(--text-3)', fontSize: 10 }} axisLine={false} tickLine={false} interval={9} />
                <YAxis domain={[0, 100]} orientation="right" hide />
                <RechartsTooltip
                  contentStyle={{ background: '#0d1520', border: '1px solid #1e2e42', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: 'var(--text-3)' }}
                  isAnimationActive={false}
                />
                <ReferenceLine y={50} stroke="var(--danger)" strokeDasharray="6 3" strokeOpacity={0.5} label={{ value: 'HIGH (50)', position: 'insideBottomRight', fill: 'var(--danger)', fontSize: 10 }} />
                <ReferenceLine y={20} stroke="var(--warning)" strokeDasharray="6 3" strokeOpacity={0.4} label={{ value: 'MED (20)', position: 'insideBottomRight', fill: 'var(--warning)', fontSize: 10 }} />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="var(--danger)"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  isAnimationActive={false}
                  activeDot={{ r: 4, fill: 'var(--danger)' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
          {/* Current score label right-aligned over graph */}
          {!loading && (
            <div style={{ position: 'absolute', right: 28, top: 12 + (184 * (1 - globalScore / 100)) - 10, background: 'var(--bg)', padding: '2px 0px', fontSize: 12, fontWeight: 800, fontFamily: 'var(--mono)', color: '#fff' }}>
              {globalScore.toFixed(1)}
            </div>
          )}
        </div>
      </div>

      {/* ── Alert Panel + Top Contributing Factors ────────────── */}
      <div className="asset-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: 16, marginBottom: 24 }}>
        {/* Alert Panel */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">🔔 Alert Panel</span>
          </div>
          {loading ? (
            <Skeleton width="100%" height="200px" />
          ) : alerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-3)', fontSize: 13 }}>
              No active alerts
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 350, overflowY: 'auto' }}>
              {alerts.slice(0, 5).map((alert) => {
                const sev = (alert.severity || severityLabel(alert.score)).toLowerCase();
                const reason = alert.recommended_actions?.[0] || 'System-detected anomaly';
                return (
                  <div key={alert.id} style={{
                    padding: '14px 16px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: `4px solid ${sev === 'critical' ? 'var(--danger)' : sev === 'high' ? '#f97316' : sev === 'medium' ? 'var(--warning)' : 'var(--teal)'}`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span className={`severity-pill ${sev}`}>{alert.severity || severityLabel(alert.score)}</span>
                      <span style={{ fontWeight: 700, fontSize: 13, color: '#fff', textTransform: 'uppercase' }}>
                        {alert.crisis_type.replace(/_/g, ' ')}
                      </span>
                      <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
                        {new Date(alert.triggered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>
                      {alert.score > 65 ? 'Critical' : 'Moderate'} Risk: {reason}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
                      Score: <span style={{ fontWeight: 700, fontFamily: 'var(--mono)', color: scoreColorCSS(alert.score) }}>{alert.score.toFixed(1)}</span>
                    </div>
                    {alert.recommended_actions && alert.recommended_actions.length > 1 && (
                      <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 6, fontStyle: 'italic' }}>
                        💡 {alert.recommended_actions.slice(0, 3).join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Top Contributing Factors (SHAP) */}
        <div className="card">
          <div className="card-header" style={{ marginBottom: 24 }}>
            <span className="card-title" style={{ textTransform: 'uppercase', letterSpacing: '1px' }}>📊 TOP CONTRIBUTING FACTORS</span>
          </div>
          {loading ? (
            <Skeleton width="100%" height="200px" />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {topFactors.map((f, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 10, color: f.direction === 'up' ? 'var(--danger)' : 'var(--success)' }}>
                    ▲
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-2)', flex: 1 }}>{f.feature}</span>
                  <div style={{ width: 120, height: 8, background: '#1e293b', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${(f.value / 0.8) * 100}%`,
                      background: f.direction === 'up' ? 'var(--danger)' : 'var(--success)',
                      borderRadius: 4,
                      transition: 'width 0.5s linear',
                    }} />
                  </div>
                  <span style={{ fontSize: 12, fontFamily: 'var(--mono)', color: f.direction === 'up' ? 'var(--danger)' : 'var(--success)', width: 60, textAlign: 'right' }}>
                    +{f.value.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── PredictionChart + Insights ────────────────────────── */}
      <div className="chart-section asset-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: 16, marginBottom: 24 }}>
        {loading ? (
          <div className="card chart-card">
            <Skeleton width="100%" height="340px" />
          </div>
        ) : (
          <PredictionChart />
        )}
        <InsightsPanel />
      </div>

      {/* ── Per-Category Cards + Opportunity Panel ────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginBottom: 24 }}>
        {/* Per-Category Scores */}
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {loading ? (
              [1, 2, 3].map(i => (
                <div className="card" key={i} style={{ textAlign: 'center', padding: 24 }}>
                  <Skeleton width="60%" height="12px" />
                  <div style={{ marginTop: 16 }}><Skeleton width="40%" height="36px" /></div>
                  <div style={{ marginTop: 12 }}><Skeleton width="100%" height="4px" /></div>
                </div>
              ))
            ) : (
              scores.map((s) => (
                <div className="card" key={s.crisis_type} style={{ textAlign: 'center' }}>
                  <div className="card-title" style={{ marginBottom: 8 }}>
                    {s.crisis_type.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: 36, fontWeight: 900, fontFamily: 'var(--mono)', color: s.score > 65 ? 'var(--danger)' : s.score > 40 ? 'var(--warning)' : 'var(--success)' }}>
                    {s.score.toFixed(1)}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--mono)', marginTop: 4 }}>
                    [{s.ci_lower.toFixed(1)} – {s.ci_upper.toFixed(1)}]
                  </div>
                  <div style={{ marginTop: 12, height: 4, borderRadius: 2, background: 'var(--border)', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', borderRadius: 2,
                      width: `${s.score}%`,
                      background: s.score > 65 ? 'var(--danger)' : s.score > 40 ? 'var(--warning)' : 'var(--success)',
                      transition: 'width 0.5s ease'
                    }} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Opportunity Watchlist */}
        <OpportunityPanel />
      </div>
    </>
  );
}
