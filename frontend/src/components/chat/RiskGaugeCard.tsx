/**
 * RiskGaugeCard — mini before/after arc gauges for simulation results.
 */

interface Props {
  label: string;
  before: number;
  after: number;
  delta: number;
}

function gaugeColor(score: number) {
  if (score <= 40) return 'var(--success)';
  if (score <= 65) return 'var(--warning)';
  return 'var(--danger)';
}

export default function RiskGaugeCard({ label, before, after, delta }: Props) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '8px 12px', borderRadius: 'var(--radius-xs)',
      background: 'rgba(255,255,255,.03)',
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', width: 64, flexShrink: 0 }}>{label}</div>

      {/* Before gauge */}
      <div style={{ textAlign: 'center' }}>
        <svg width="36" height="22" viewBox="0 0 36 22">
          <path d="M3 20 A15 15 0 0 1 33 20" fill="none" stroke="var(--border)" strokeWidth="2.5" strokeLinecap="round" />
          <path
            d="M3 20 A15 15 0 0 1 33 20"
            fill="none"
            stroke={gaugeColor(before)}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray={`${(before / 100) * 47} 47`}
          />
        </svg>
        <div style={{ fontSize: 11, fontFamily: 'var(--mono)', color: gaugeColor(before), fontWeight: 700 }}>
          {before.toFixed(1)}
        </div>
      </div>

      {/* Arrow */}
      <div style={{ fontSize: 14, color: 'var(--text-3)' }}>→</div>

      {/* After gauge */}
      <div style={{ textAlign: 'center' }}>
        <svg width="36" height="22" viewBox="0 0 36 22">
          <path d="M3 20 A15 15 0 0 1 33 20" fill="none" stroke="var(--border)" strokeWidth="2.5" strokeLinecap="round" />
          <path
            d="M3 20 A15 15 0 0 1 33 20"
            fill="none"
            stroke={gaugeColor(after)}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray={`${(after / 100) * 47} 47`}
          />
        </svg>
        <div style={{ fontSize: 11, fontFamily: 'var(--mono)', color: gaugeColor(after), fontWeight: 700 }}>
          {after.toFixed(1)}
        </div>
      </div>

      {/* Delta */}
      <div style={{
        fontSize: 11, fontFamily: 'var(--mono)', fontWeight: 700,
        color: delta > 0 ? 'var(--danger)' : delta < 0 ? 'var(--success)' : 'var(--text-3)',
      }}>
        {delta > 0 ? '+' : ''}{delta.toFixed(1)}
      </div>
    </div>
  );
}
