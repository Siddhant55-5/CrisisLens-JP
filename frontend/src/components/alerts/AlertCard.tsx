/**
 * AlertCard — simplified alert view per user request.
 */
import { motion } from 'framer-motion';
import type { Alert } from '../../lib/types';

interface Props {
  alert: Alert;
}

function scoreColor(s: number) {
  if (s <= 40) return 'var(--success)';
  if (s <= 65) return 'var(--warning)';
  return 'var(--danger)';
}

function formatTime(ts: string) {
  const d = new Date(ts);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString();
}

function crisisLabel(ct: string) {
  return ct.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export default function AlertCard({ alert }: Props) {
  const sev = alert.severity.toLowerCase();

  // Use recommended_actions as the primary human reason, or map from the crisis type to a simple realistic sentence.
  let reasonText = alert.recommended_actions?.[0] || 'Unusual condition flagged by the system.';
  
  if (!alert.recommended_actions?.length) {
    if (alert.crisis_type === 'BANKING_INSTABILITY') {
      reasonText = 'Recent banking sector stress and rising loan defaults';
    } else if (alert.crisis_type === 'MARKET_CRASH') {
      reasonText = 'Stock market volatility is increasing due to investor panic';
    } else if (alert.crisis_type === 'LIQUIDITY_SHORTAGE') {
      reasonText = 'Cash flow in financial system is tightening';
    }
  }

  return (
    <motion.div
      className={`alert-card ${sev}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      layout
    >
      <div className="alert-card-top" style={{ marginBottom: 12 }}>
        <span className={`severity-pill ${sev}`}>{alert.severity}</span>
        <span className="crisis-badge" style={{ fontWeight: 600, fontSize: 13, color: '#fff' }}>
          {crisisLabel(alert.crisis_type)}
        </span>
        <span className="alert-time" style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-3)' }}>
          {formatTime(alert.triggered_at)}
        </span>
      </div>

      <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 6, marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Risk Percentage</span>
          <span style={{ fontSize: 16, fontWeight: 700, fontFamily: 'var(--mono)', color: scoreColor(alert.score) }}>
            {alert.score.toFixed(1)}%
          </span>
        </div>
      </div>

      <div style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text-1)' }}>
        <strong>Reason:</strong> {reasonText}
      </div>
    </motion.div>
  );
}
