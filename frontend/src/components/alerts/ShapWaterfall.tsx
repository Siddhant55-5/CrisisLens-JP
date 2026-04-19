/**
 * ShapWaterfall — horizontal bar chart of SHAP feature contributions.
 */
import type { ShapContribution } from '../../lib/types';

interface Props {
  contributions: ShapContribution[];
}

export default function ShapWaterfall({ contributions }: Props) {
  if (!contributions || contributions.length === 0) return null;
  const maxAbs = Math.max(...contributions.map(c => Math.abs(c.shap_value)), 0.01);

  return (
    <div className="shap-waterfall">
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '.05em' }}>
        SHAP Feature Contributions
      </div>
      {contributions.map((c, i) => {
        const pct = (Math.abs(c.shap_value) / maxAbs) * 45;
        const isPositive = c.shap_value > 0;
        return (
          <div className="shap-bar-row" key={i}>
            <span className="shap-feature">{c.feature_name.replace(/_/g, ' ')}</span>
            <div className="shap-bar-wrap">
              <div className="shap-center-line" />
              <div
                className={`shap-bar ${isPositive ? 'positive' : 'negative'}`}
                style={{
                  width: `${pct}%`,
                  position: 'absolute',
                  ...(isPositive
                    ? { left: '50%' }
                    : { right: '50%' }),
                }}
              />
            </div>
            <span className="shap-val" style={{ color: isPositive ? 'var(--danger)' : 'var(--teal)' }}>
              {isPositive ? '+' : ''}{c.shap_value.toFixed(3)}
            </span>
          </div>
        );
      })}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8, fontSize: 10, color: 'var(--text-3)' }}>
        <span>← Reduces risk (teal)</span>
        <span>Increases risk (red) →</span>
      </div>
    </div>
  );
}
