/**
 * AlertsPage — filterable alert inbox with SHAP expansion.
 */
import { useState, useMemo } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useRiskStore } from '../store/useRiskStore';
import AlertCard from '../components/alerts/AlertCard';
import type { Alert, AlertSeverity } from '../lib/types';

const FILTERS: (AlertSeverity | 'ALL')[] = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export default function AlertsPage() {
  const [filter, setFilter] = useState<string>('ALL');
  const alerts: Alert[] = useRiskStore((s) => s.alerts);

  const filtered = useMemo(() => {
    if (filter === 'ALL') return alerts;
    return alerts.filter(a => a.severity === filter);
  }, [alerts, filter]);

  return (
    <>
      <div className="alerts-header">
        <h2 className="alerts-title">
          Alert Inbox
          <span className="count-badge">{alerts.length}</span>
        </h2>
      </div>

      <div className="filter-tabs">
        {FILTERS.map(f => (
          <button
            key={f}
            className={`filter-tab${filter === f ? ' active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <AnimatePresence mode="popLayout">
        {filtered.map(alert => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </AnimatePresence>

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-3)' }}>
          No {filter.toLowerCase()} alerts found
        </div>
      )}
    </>
  );
}
