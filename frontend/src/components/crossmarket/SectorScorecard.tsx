/**
 * SectorScorecard — ranked table of sector exposure to active crisis.
 */
import { MOCK_SECTOR_SCORECARD } from '../../lib/crossMarketData';

interface SectorRow {
  sector: string;
  exposure: number;
  signal: string;
  precedent: string;
  flag: string;
}

interface Props {
  sectors?: SectorRow[];
  crisisType?: string;
}

function exposureColor(e: number) {
  if (e >= 70) return 'var(--danger)';
  if (e >= 45) return 'var(--warning)';
  return 'var(--teal)';
}

export default function SectorScorecard({ sectors, crisisType }: Props) {
  const data = sectors || MOCK_SECTOR_SCORECARD;
  const crisis = crisisType || 'BANKING_INSTABILITY';

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Sector Exposure Scorecard</span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 12, fontStyle: 'italic' }}>
        Based on active {crisis.replace(/_/g, ' ').toLowerCase()} alert
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-3)', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>Sector</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-3)', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>Exposure</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-3)', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>Primary Signal</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-3)', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>Precedent</th>
              <th style={{ textAlign: 'center', padding: '8px 12px', color: 'var(--text-3)', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>Flag</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-light, rgba(255,255,255,.04))' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-1)' }}>{row.sector}</td>
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 80, height: 6, borderRadius: 3, background: 'var(--border)', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 3,
                        width: `${row.exposure}%`,
                        background: exposureColor(row.exposure),
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: exposureColor(row.exposure), fontWeight: 700 }}>
                      {row.exposure}
                    </span>
                  </div>
                </td>
                <td style={{ padding: '10px 12px', color: 'var(--text-2)', fontFamily: 'var(--mono)', fontSize: 11 }}>{row.signal}</td>
                <td style={{ padding: '10px 12px', color: 'var(--text-3)', fontSize: 11 }}>{row.precedent}</td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <span style={{
                    display: 'inline-block', padding: '3px 10px', borderRadius: 100,
                    fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.05em',
                    background: row.flag === 'EXPOSED' ? 'var(--danger-dim)' : 'var(--warning-dim)',
                    color: row.flag === 'EXPOSED' ? 'var(--danger)' : 'var(--warning)',
                  }}>
                    {row.flag}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
