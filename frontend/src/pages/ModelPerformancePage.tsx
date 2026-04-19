import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity } from 'lucide-react';

const mockReport = {
  banking: { precision: 0.88, recall: 0.92, f1: 0.90, avg_lead_time_hours: 72.5 },
  market: { precision: 0.85, recall: 0.89, f1: 0.87, avg_lead_time_hours: 48.0 },
  liquidity: { precision: 0.91, recall: 0.86, f1: 0.88, avg_lead_time_hours: 120.0 },
  notable_misses: [
    { event: "Flash Crash 2010", reason: "Microstructure event, undetectable via macro daily signals" },
    { event: "Repo Spike 2019", reason: "Insufficient granular liquidity data at the time" }
  ],
  notable_catches: [
    { event: "Lehman Collapse 2008", lead_time_hours: 336 },
    { event: "COVID Dash for Cash 2020", lead_time_hours: 96 },
    { event: "Silicon Valley Bank 2023", lead_time_hours: 48 }
  ]
};

const leadTimeData = [
  { bin: '< 24h', count: 12 },
  { bin: '24-48h', count: 28 },
  { bin: '48-72h', count: 45 },
  { bin: '72h-1w', count: 18 },
  { bin: '> 1w', count: 5 }
];

export default function ModelPerformancePage() {
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    // In production, we would fetch from /v1/backtest/report
    // Simulate network delay
    const t = setTimeout(() => {
      setReport(mockReport);
    }, 600);
    return () => clearTimeout(t);
  }, []);

  if (!report) {
    return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-3)' }}>Loading validation report...</div>;
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', paddingBottom: 40 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <Activity size={24} style={{ color: 'var(--accent)' }} />
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Model Performance & Backtesting</h2>
      </div>
      <p style={{ color: 'var(--text-2)', marginBottom: 24, fontSize: 13 }}>
        Historical validation against crisis events from 2000–2025. Model trained on data up to Dec 2023.
      </p>

      {/* F1 Score Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Banking Instability', stats: report.banking },
          { label: 'Market Crash', stats: report.market },
          { label: 'Liquidity Shortage', stats: report.liquidity }
        ].map((item, i) => (
          <div key={i} className="card" style={{ textAlign: 'center', padding: '24px 16px' }}>
            <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {item.label} F1 Score
            </div>
            <div style={{ fontSize: 36, fontWeight: 800, fontFamily: 'var(--mono)', color: 'var(--success)' }}>
              {(item.stats.f1 * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 8 }}>
              Avg lead time: <strong style={{color:'var(--text-1)'}}>{item.stats.avg_lead_time_hours}h</strong>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 24 }}>
        {/* Lead Time Histogram */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Lead Time Distribution</span>
          </div>
          <div style={{ height: 350, marginTop: 16 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={leadTimeData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="bin" 
                  tick={{fill:'var(--text-3)', fontSize: 11}} 
                  axisLine={false} 
                  tickLine={false} 
                  label={{ value: 'Time Before Crisis (Days)', position: 'insideBottom', offset: -15, fill: 'var(--text-2)', fontSize: 13 }}
                />
                <YAxis 
                  tick={{fill:'var(--text-3)', fontSize: 11}} 
                  axisLine={false} 
                  tickLine={false} 
                  label={{ value: 'Prediction Accuracy (%)', angle: -90, position: 'insideLeft', fill: 'var(--text-2)', fontSize: 13, dy: 70 }}
                />
                <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.02)'}} contentStyle={{background: '#0d1520', border: '1px solid #1e2e42'}} />
                <Bar dataKey="count" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
