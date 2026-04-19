/**
 * OpportunityPanel — green-accented watchlist showing defensive/beneficiary assets.
 *
 * Shows top 6 opportunity cards with ticker, direction signal,
 * confidence bar, win rate, window, and plain-English basis.
 */
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Eye, ExternalLink } from 'lucide-react';

// Mock watchlist (matches backend asset_engine output)
const MOCK_WATCHLIST = [
  {
    ticker: 'TLT',
    name: 'iShares 20+ Year Treasury Bond ETF',
    asset_type: 'ETF',
    expected_direction: 'LONG',
    confidence: 0.86,
    historical_win_rate_pct: 81,
    suggested_window_days: 5,
    basis: 'Flight-to-quality during banking stress historically benefits long-duration Treasuries.',
  },
  {
    ticker: 'BIL',
    name: 'SPDR Bloomberg 1-3 Month T-Bill ETF',
    asset_type: 'ETF',
    expected_direction: 'LONG',
    confidence: 0.90,
    historical_win_rate_pct: 92,
    suggested_window_days: 20,
    basis: 'Ultra-short Treasuries as cash equivalent during funding stress. Near-zero duration risk.',
  },
  {
    ticker: 'VIXY',
    name: 'ProShares VIX Short-Term Futures',
    asset_type: 'ETF',
    expected_direction: 'LONG',
    confidence: 0.88,
    historical_win_rate_pct: 82,
    suggested_window_days: 5,
    basis: 'VIX spikes during market crashes. Captured 50-120% gains during COVID selloff.',
  },
  {
    ticker: 'XLU',
    name: 'Utilities Select Sector SPDR',
    asset_type: 'ETF',
    expected_direction: 'LONG',
    confidence: 0.82,
    historical_win_rate_pct: 78,
    suggested_window_days: 10,
    basis: 'Regulated cash flows and dividend stability attract defensive capital in stress.',
  },
  {
    ticker: 'GLD',
    name: 'SPDR Gold Shares',
    asset_type: 'ETF',
    expected_direction: 'LONG',
    confidence: 0.80,
    historical_win_rate_pct: 76,
    suggested_window_days: 15,
    basis: 'Gold acts as store of value during banking crises. Post-Lehman rallied 25% in 6 months.',
  },
  {
    ticker: 'SH',
    name: 'ProShares Short S&P500',
    asset_type: 'ETF',
    expected_direction: 'SHORT',
    confidence: 0.85,
    historical_win_rate_pct: 79,
    suggested_window_days: 5,
    basis: 'Inverse S&P 500 ETF — direct hedge against broad equity drawdown.',
  },
];

interface WatchItem {
  ticker: string;
  addedAt: string;
}

export default function OpportunityPanel() {
  const [watchlist, setWatchlist] = useState<WatchItem[]>(() => {
    try {
      const saved = localStorage.getItem('cl_watchlist');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('cl_watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  const toggleWatch = (ticker: string) => {
    setWatchlist(prev => {
      const exists = prev.find(w => w.ticker === ticker);
      if (exists) {
        return prev.filter(w => w.ticker !== ticker);
      }
      return [...prev, { ticker, addedAt: new Date().toISOString() }];
    });
  };

  const isWatched = (ticker: string) => watchlist.some(w => w.ticker === ticker);

  return (
    <div className="card opp-panel">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="card-title" style={{ color: 'var(--success)' }}>Opportunity Intelligence</span>
          <span className="live-badge">
            <span className="dot" />
            LIVE
          </span>
        </div>
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-3)', marginBottom: 14, fontStyle: 'italic' }}>
        Intelligence signals — not investment advice
      </div>

      <div className="opp-list">
        {MOCK_WATCHLIST.map((item) => (
          <div key={item.ticker} className="opp-card">
            <div className="opp-card-top">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="opp-ticker">{item.ticker}</span>
                <span className="opp-type-badge">{item.asset_type}</span>
              </div>
              <div className={`opp-direction ${item.expected_direction === 'LONG' ? 'long' : 'short'}`}>
                {item.expected_direction === 'LONG'
                  ? <><TrendingUp size={12} /> LONG SIGNAL</>
                  : <><TrendingDown size={12} /> SHORT SIGNAL</>
                }
              </div>
            </div>

            <div className="opp-name">{item.name}</div>

            {/* Confidence bar */}
            <div className="opp-metric-row">
              <span className="opp-metric-label">Confidence</span>
              <div className="opp-conf-bar">
                <div
                  className="opp-conf-fill"
                  style={{ width: `${item.confidence * 100}%` }}
                />
              </div>
              <span className="opp-metric-val">{(item.confidence * 100).toFixed(0)}%</span>
            </div>

            <div className="opp-meta">
              <span>Win rate: {item.historical_win_rate_pct}% in analogous events</span>
              <span>Window: {item.suggested_window_days}d</span>
            </div>

            <div className="opp-basis">{item.basis}</div>

            <button
              className={`opp-monitor-btn ${isWatched(item.ticker) ? 'active' : ''}`}
              onClick={() => toggleWatch(item.ticker)}
            >
              <Eye size={12} />
              {isWatched(item.ticker) ? 'Watching' : 'Monitor'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
