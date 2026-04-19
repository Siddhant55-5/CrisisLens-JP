/**
 * CrossMarketPage — contagion analysis dashboard with Sankey, heatmap, and scorecard.
 */
import { MOCK_REGIME } from '../lib/crossMarketData';
import ContagionSankey from '../components/crossmarket/ContagionSankey';
import CorrelationHeatmap from '../components/crossmarket/CorrelationHeatmap';
import SectorScorecard from '../components/crossmarket/SectorScorecard';

function regimePill(regime: string) {
  switch (regime) {
    case 'stress':
      return { label: 'Stress Regime', cls: 'critical' };
    case 'elevated':
      return { label: 'Elevated Regime', cls: 'warning' };
    default:
      return { label: 'Normal Regime', cls: 'safe' };
  }
}

export default function CrossMarketPage() {
  const regime = MOCK_REGIME;
  const pill = regimePill(regime.current_regime);

  return (
    <>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Cross-Market Contagion Analysis</h2>
          <p style={{ fontSize: 12, color: 'var(--text-3)' }}>
            Correlation-driven regime detection + cascade impact mapping
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className={`market-pill ${pill.cls}`} style={{ animation: regime.current_regime === 'stress' ? 'pulse-danger 1.5s infinite' : 'none' }}>
            {pill.label}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
            Avg ρ: {regime.avg_correlation.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Regime shift alert */}
      {regime.last_shift && (
        <div className="card" style={{ marginBottom: 20, padding: 16, borderLeft: '4px solid var(--warning)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span className="severity-pill medium">REGIME SHIFT</span>
            <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
              {new Date(regime.last_shift.detected_at).toLocaleString()}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 6 }}>
            Regime changed from <strong>{regime.last_shift.from_regime}</strong> → <strong style={{ color: 'var(--warning)' }}>{regime.last_shift.to_regime}</strong>
            {' '}(avg correlation: {regime.last_shift.avg_correlation.toFixed(3)})
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', fontStyle: 'italic' }}>
            📜 {regime.last_shift.historical_precedent}
          </div>
          <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {regime.last_shift.most_correlated_pairs.map((p: any, i: number) => (
              <span key={i} style={{
                display: 'inline-block', padding: '3px 8px', borderRadius: 'var(--radius-xs)',
                background: 'var(--bg-input)', fontSize: 10, color: 'var(--text-2)', fontFamily: 'var(--mono)',
              }}>
                {p.signal_a}↔{p.signal_b}: {p.value.toFixed(2)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sankey + Heatmap grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <ContagionSankey />
        <CorrelationHeatmap />
      </div>

      {/* Sector Scorecard */}
      <SectorScorecard />
    </>
  );
}
