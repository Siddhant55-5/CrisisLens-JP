import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

export default function DataGapBanner() {
  const [gaps, setGaps] = useState<any[]>([]);

  useEffect(() => {
    // Mocking the data gap from the Sprint 7 prompt
    const mockGap = {
      id: 'gap-1',
      signal_name: 'SOFR feed',
      last_seen: new Date(Date.now() - 3600000 * 1.5).toLocaleTimeString(), // 1.5 hours ago
      impact: 'Liquidity score confidence is reduced'
    };
    
    // Set mock gap after 3 seconds for demonstration
    const t = setTimeout(() => {
      setGaps([mockGap]);
    }, 3000);

    return () => clearTimeout(t);
  }, []);

  if (gaps.length === 0) return null;

  return (
    <>
      {gaps.map((gap, i) => (
        <div key={gap.id || i} style={{
          width: '100%',
          backgroundColor: '#1a0e00',
          color: 'var(--warning)',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
          fontSize: '13px',
          fontWeight: 500,
          zIndex: 40
        }}>
          <AlertCircle size={16} />
          <span>
            Data gap detected: {gap.signal_name} unavailable — {gap.impact}. 
            <span style={{opacity: 0.8, marginLeft: 8}}>Last data: {gap.last_seen}</span>
          </span>
        </div>
      ))}
    </>
  );
}
