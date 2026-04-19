/**
 * RiskMonitorPage — detailed risk score monitoring (placeholder for Sprint 3).
 */
import { useRiskStore } from '../store/useRiskStore';
import { MOCK_SCORES } from '../lib/mockData';

function scoreColor(s: number) {
  if (s <= 40) return 'var(--success)';
  if (s <= 65) return 'var(--warning)';
  return 'var(--danger)';
}

export default function RiskMonitorPage() {
  const storeScores = useRiskStore((s) => s.scores);
  const scores = storeScores.length > 0 ? storeScores : MOCK_SCORES;

  return (
    <>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Risk Monitor</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
        {scores.map((s) => {
          const pct = s.score;
          const ciWidth = s.ci_upper - s.ci_lower;
          return (
            <div className="card" key={s.crisis_type} style={{ padding: 28 }}>
              <div className="card-title" style={{ marginBottom: 20 }}>
                {s.crisis_type.replace(/_/g, ' ')}
              </div>

              {/* Large gauge */}
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <svg width="140" height="80" viewBox="0 0 140 80">
                  <path d="M10 70 A60 60 0 0 1 130 70" fill="none" stroke="var(--border)" strokeWidth="8" strokeLinecap="round" />
                  <path
                    d="M10 70 A60 60 0 0 1 130 70"
                    fill="none"
                    stroke={scoreColor(pct)}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(pct / 100) * 188} 188`}
                  />
                </svg>
                <div style={{ fontSize: 42, fontWeight: 900, fontFamily: 'var(--mono)', color: scoreColor(pct), marginTop: -8 }}>
                  {s.score.toFixed(1)}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
                  [{s.ci_lower.toFixed(1)} – {s.ci_upper.toFixed(1)}]
                </div>
              </div>

              {/* Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-2)' }}>
                  <span>CI Width</span>
                  <span style={{ fontFamily: 'var(--mono)' }}>{ciWidth.toFixed(1)} pts</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-2)' }}>
                  <span>Status</span>
                  <span style={{
                    fontWeight: 700, fontSize: 11,
                    color: pct > 80 ? 'var(--danger)' : pct > 65 ? 'var(--warning)' : pct > 40 ? 'var(--warning)' : 'var(--success)',
                  }}>
                    {pct > 80 ? 'CRITICAL' : pct > 65 ? 'HIGH' : pct > 40 ? 'MEDIUM' : 'LOW'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-2)' }}>
                  <span>Last Updated</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-3)' }}>
                    {new Date(s.scored_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginTop: 16, height: 6, borderRadius: 3, background: 'var(--border)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 3,
                  width: `${pct}%`,
                  background: scoreColor(pct),
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
