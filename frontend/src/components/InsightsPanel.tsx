/**
 * Correlation Insights — context specific to the correlation charts.
 */
export default function InsightsPanel() {
  return (
    <div className="card insights-panel" style={{ display: 'flex', flexDirection: 'column', gap: 16, backgroundColor: 'transparent', border: 'none', padding: 0 }}>
      {/* Correlation Insights Header */}
      <h2 style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Correlation Insights</h2>
      
      <div style={{ padding: 16, border: '1px solid rgba(239, 68, 68, 0.2)', backgroundColor: 'rgba(239, 68, 68, 0.05)', borderRadius: 8, borderLeft: '4px solid #ef4444' }}>
        <h3 style={{ color: '#ef4444', fontSize: 13, fontWeight: 700, marginBottom: 8, letterSpacing: '0.05em' }}>SELL SIGNAL DETECTED</h3>
        <p style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.5 }}>
          Gold is falling with strong negative momentum. Since Gold and AUD/USD are highly correlated (0.85), AUD/USD is also projected to fall. Consider short positions.
        </p>
      </div>
      <div style={{ padding: 16, border: '1px solid rgba(20, 184, 166, 0.2)', backgroundColor: 'rgba(20, 184, 166, 0.05)', borderRadius: 8, borderLeft: '4px solid #14b8a6' }}>
        <h3 style={{ color: '#14b8a6', fontSize: 13, fontWeight: 700, marginBottom: 8, letterSpacing: '0.05em' }}>BUY SIGNAL (HEDGING)</h3>
        <p style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.5 }}>
          Due to the Iranian-US war fears, oil prices are spiking. USD/CAD presents a buying opportunity due to inverse correlation with crude oil prices.
        </p>
      </div>
    </div>
  );
}
