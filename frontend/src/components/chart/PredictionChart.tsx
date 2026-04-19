import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType, CrosshairMode, IChartApi, ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { MOCK_ASSETS, type Candle } from '../../lib/mockData';
import { Layers, Activity, Eye, EyeOff } from 'lucide-react';

const ASSETS = ['GOLD', 'GBPUSD', 'EURUSD', 'SPX'];
const TIMEFRAMES = ['15m', '1H', '4H', '1D'];

// --- Utility to detect basic mock candlestick patterns ---
function detectPatterns(candles: Candle[]): { time: Time, position: 'aboveBar' | 'belowBar', color: string, shape: 'arrowDown' | 'arrowUp', text: string, id: string }[] {
  const markers: any[] = [];
  
  for (let i = 2; i < candles.length; i++) {
    const curr = candles[i];
    const prev = candles[i-1];
    
    const currBody = Math.abs(curr.close - curr.open);
    const prevBody = Math.abs(prev.close - prev.open);
    const isCurrUp = curr.close > curr.open;
    const isPrevUp = prev.close > prev.open;

    const time = (new Date(curr.time).getTime() / 1000) as Time;

    // Bullish Engulfing
    if (!isPrevUp && isCurrUp && curr.close > prev.open && curr.open < prev.close && currBody > prevBody * 1.5) {
      markers.push({ time, position: 'belowBar', color: '#22c55e', shape: 'arrowUp', text: 'Bullish Engulfing', id: `bull-${i}` });
      continue;
    }
    
    // Bearish Engulfing
    if (isPrevUp && !isCurrUp && curr.close < prev.open && curr.open > prev.close && currBody > prevBody * 1.5) {
      markers.push({ time, position: 'aboveBar', color: '#ef4444', shape: 'arrowDown', text: 'Bearish Engulfing', id: `bear-${i}` });
      continue;
    }
    
    // Morning Star (mock simple detection)
    const prev2 = candles[i-2];
    const isPrev2Up = prev2.close > prev2.open;
    if (!isPrev2Up && !isPrevUp && isCurrUp && currBody > prevBody * 2 && curr.close > (prev2.open + prev2.close)/2) {
      markers.push({ time, position: 'belowBar', color: '#22c55e', shape: 'arrowUp', text: 'Morning Star', id: `mstar-${i}` });
    }
  }
  
  return markers;
}

// Generate mock correlation asset data based on primary asset
function generateCorrelationData(candles: Candle[], type: 'AUDUSD' | 'DXY' | 'BONDS') {
  return candles.map((c, i) => {
    let multiplier = type === 'AUDUSD' ? 1.05 : type === 'DXY' ? -0.8 : -0.5;
    const baseVal = type === 'AUDUSD' ? 0.65 : type === 'DXY' ? 104 : 4.2;
    
    // Create some synchronized walk
    const normalizedMove = (c.close - candles[0].close) / candles[0].close;
    const val = baseVal * (1 + (normalizedMove * multiplier)) + (Math.random() - 0.5) * 0.002 * baseVal;
    
    return {
      time: (new Date(c.time).getTime() / 1000) as Time,
      value: val
    };
  });
}

const PredictionChart = React.memo(function PredictionChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const overlaySeriesMap = useRef<Record<string, ISeriesApi<"Line">>>({});
  
  const [asset, setAsset] = useState<string>('GOLD');
  const [tf, setTf] = useState<string>('1H');
  const [showPatterns, setShowPatterns] = useState(true);
  const [overlays, setOverlays] = useState<string[]>(['AUDUSD']);
  
  // Crosshair / Tooltip state
  const [tooltipState, setTooltipState] = useState<{
    visible: boolean; x: number; y: number; time?: string; open?: number; high?: number; low?: number; close?: number; pattern?: string; overlayVals?: Record<string, number>
  }>({ visible: false, x: 0, y: 0 });

  const data = MOCK_ASSETS[asset] || MOCK_ASSETS['GBPUSD'];
  
  // Format candles for lightweight charts
  const chartCandles = useMemo(() => {
    return data.candles.map(c => ({
      time: (new Date(c.time).getTime() / 1000) as Time,
      open: c.open, high: c.high, low: c.low, close: c.close
    })).sort((a,b) => (a.time as number) - (b.time as number));
  }, [data]);
  
  const patterns = useMemo(() => detectPatterns(data.candles), [data]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
      timeScale: { borderColor: 'rgba(255,255,255,0.1)', timeVisible: true, fixLeftEdge: true, fixRightEdge: true },
    });
    chartRef.current = chart;

    // Main Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444', 
      borderVisible: false, wickUpColor: '#22c55e', wickDownColor: '#ef4444'
    });
    candleSeriesRef.current = candleSeries as any;
    candleSeries.setData(chartCandles);
    
    if (showPatterns) {
      candleSeries.setMarkers(patterns as any);
    }

    // Set up overlays
    const availableOverlays = [
      { name: 'AUDUSD', color: '#3b82f6' },
      { name: 'DXY', color: '#f59e0b' },
      { name: 'BONDS', color: '#a855f7' }
    ];

    overlays.forEach(overlay => {
      const config = availableOverlays.find(o => o.name === overlay);
      if (!config) return;
      
      const lineSeries = chart.addLineSeries({
        color: config.color,
        lineWidth: 2,
        priceScaleId: 'percentage_overlay', // Use single detached scale for percentages
        title: overlay
      });
      
      chart.priceScale('percentage_overlay').applyOptions({
        mode: 2, // Percentage scale mode
        scaleMargins: { top: 0.1, bottom: 0.1 },
        visible: true,
        borderColor: 'rgba(255,255,255,0.1)',
        textColor: config.color,
      });

      const corrData = generateCorrelationData(data.candles, overlay as any).sort((a,b) => (a.time as number) - (b.time as number));
      lineSeries.setData(corrData);
      overlaySeriesMap.current[overlay] = lineSeries as any;
    });

    // Tooltip logic via crosshair subscriber
    chart.subscribeCrosshairMove(param => {
      if (!param.time || param.point === undefined || param.point.x < 0 || param.point.y < 0) {
        setTooltipState(s => ({ ...s, visible: false }));
        return;
      }
      
      const priceData = param.seriesData.get(candleSeries) as any;
      if (!priceData) return;

      const marker = patterns.find(p => p.time === param.time);
      
      const overlayVals: Record<string, number> = {};
      Object.entries(overlaySeriesMap.current).forEach(([name, series]) => {
         const valData = param.seriesData.get(series as any) as any;
         if (valData) overlayVals[name] = valData.value;
      });

      setTooltipState({
        visible: true,
        x: param.point.x,
        y: param.point.y,
        time: new Date((param.time as number) * 1000).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }),
        open: priceData.open, high: priceData.high, low: priceData.low, close: priceData.close,
        pattern: marker?.text,
        overlayVals
      });
    });

    // Real-time ticking simulation
    let lastPrice = chartCandles[chartCandles.length - 1].close;
    let high = chartCandles[chartCandles.length - 1].high;
    let low = chartCandles[chartCandles.length - 1].low;
    let time = chartCandles[chartCandles.length - 1].time;

    const interval = setInterval(() => {
      const volatility = asset === 'GOLD' ? 0.3 : 0.0001;
      const change = (Math.random() - 0.48) * volatility;
      lastPrice = lastPrice + change;
      high = Math.max(high, lastPrice);
      low = Math.min(low, lastPrice);

      try {
        candleSeries.update({
          time,
          open: chartCandles[chartCandles.length - 1].open,
          high,
          low,
          close: lastPrice,
        });

        // Also update overlays
        overlays.forEach(overlay => {
           const sMap = overlaySeriesMap.current[overlay];
           if (sMap) {
             let multiplier = overlay === 'AUDUSD' ? 1.05 : overlay === 'DXY' ? -0.8 : -0.5;
             const baseVal = overlay === 'AUDUSD' ? 0.65 : overlay === 'DXY' ? 104 : 4.2;
             const normalizedMove = (lastPrice - chartCandles[0].close) / chartCandles[0].close;
             const val = baseVal * (1 + (normalizedMove * multiplier)) + (Math.random() - 0.5) * 0.002 * baseVal;
             
             sMap.update({
                time,
                value: val
             });
           }
        });
      } catch (e) {}
    }, 500);

    chart.timeScale().fitContent();

    // Responsive resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
      chart.remove();
      overlaySeriesMap.current = {};
    };
  }, [chartCandles, overlays, showPatterns, patterns, data.candles]);

  const toggleOverlay = (name: string) => {
    setOverlays(prev => prev.includes(name) ? prev.filter(o => o !== name) : [...prev, name]);
  };

  return (
    <div className="card chart-card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
      
      {/* Chart Top Toolbar */}
      <div style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.01)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: 16, color: '#fff' }}>{asset}</span>
            <span style={{ padding: '2px 8px', borderRadius: 4, background: 'rgba(255,255,255,0.1)', fontSize: 11, fontWeight: 600, color: 'var(--text-2)' }}>CFD</span>
          </div>
          <div className="asset-selector" style={{ background: 'rgba(0,0,0,0.2)', padding: 4, borderRadius: 6 }}>
            {ASSETS.map(a => (
              <button key={a} className={`asset-btn${asset === a ? ' active' : ''}`} style={{ border: 'none' }} onClick={() => setAsset(a)}>{a}</button>
            ))}
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="chart-tabs" style={{ background: 'rgba(0,0,0,0.2)', padding: 4, borderRadius: 6 }}>
            {TIMEFRAMES.map(t => (
              <button key={t} className={`chart-tab${tf === t ? ' active' : ''}`} onClick={() => setTf(t)}>{t}</button>
            ))}
          </div>
          
          <div style={{ height: 24, width: 1, background: 'var(--border)' }} />
          
          <button 
            onClick={() => setShowPatterns(!showPatterns)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'transparent', border: 'none', color: showPatterns ? 'var(--accent)' : 'var(--text-3)', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
          >
            <Activity size={14} />
            Patterns {showPatterns ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Chart Legend / Overlay toggles */}
      <div style={{ padding: '8px 20px', borderBottom: '1px solid rgba(255,255,255,0.02)', display: 'flex', alignItems: 'center', gap: 16, fontSize: 11, background: 'rgba(0,0,0,0.1)' }}>
        <span style={{ color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4 }}><Layers size={12}/> Overlays:</span>
        <button onClick={() => toggleOverlay('AUDUSD')} style={{ background: 'none', border: '1px solid', borderColor: overlays.includes('AUDUSD') ? '#3b82f6' : 'var(--border)', color: overlays.includes('AUDUSD') ? '#3b82f6' : 'var(--text-3)', borderRadius: 100, padding: '2px 10px', fontSize: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
          {overlays.includes('AUDUSD') ? <Eye size={10}/> : <EyeOff size={10}/>} AUDUSD
        </button>
        <button onClick={() => toggleOverlay('DXY')} style={{ background: 'none', border: '1px solid', borderColor: overlays.includes('DXY') ? '#f59e0b' : 'var(--border)', color: overlays.includes('DXY') ? '#f59e0b' : 'var(--text-3)', borderRadius: 100, padding: '2px 10px', fontSize: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
          {overlays.includes('DXY') ? <Eye size={10}/> : <EyeOff size={10}/>} DXY Index
        </button>
        <button onClick={() => toggleOverlay('BONDS')} style={{ background: 'none', border: '1px solid', borderColor: overlays.includes('BONDS') ? '#a855f7' : 'var(--border)', color: overlays.includes('BONDS') ? '#a855f7' : 'var(--text-3)', borderRadius: 100, padding: '2px 10px', fontSize: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
          {overlays.includes('BONDS') ? <Eye size={10}/> : <EyeOff size={10}/>} Bonds (US10Y)
        </button>
      </div>

      {/* Chart Container */}
      <div style={{ position: 'relative', flex: 1, minHeight: 400 }}>
        <div ref={chartContainerRef} style={{ width: '100%', height: '100%', position: 'absolute', inset: 0 }} />
        
        {/* Floating Tooltip */}
        {tooltipState.visible && tooltipState.open && (
           <div style={{ 
             position: 'absolute', 
             left: Math.min(tooltipState.x + 15, chartContainerRef.current?.clientWidth! - 200), // keep on screen
             top: Math.max(10, tooltipState.y - 15), 
             zIndex: 20, 
             background: 'rgba(15, 23, 41, 0.95)', 
             border: '1px solid #1e293b', 
             borderRadius: 8, 
             padding: '8px 12px', 
             pointerEvents: 'none',
             boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
             backdropFilter: 'blur(4px)',
             minWidth: 160
           }}>
             <div style={{ fontSize: 10, color: 'var(--text-3)', marginBottom: 4 }}>{tooltipState.time}</div>
             <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', fontSize: 11, fontFamily: 'var(--mono)', marginBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 8 }}>
                <div style={{ color: 'var(--text-2)' }}>O: <span style={{ color: '#fff' }}>{tooltipState.open}</span></div>
                <div style={{ color: 'var(--text-2)' }}>H: <span style={{ color: '#fff' }}>{tooltipState.high}</span></div>
                <div style={{ color: 'var(--text-2)' }}>L: <span style={{ color: '#fff' }}>{tooltipState.low}</span></div>
                <div style={{ color: 'var(--text-2)' }}>C: <span style={{ color: '#fff' }}>{tooltipState.close}</span></div>
             </div>
             
             {tooltipState.overlayVals && Object.entries(tooltipState.overlayVals).map(([k, v]) => (
               <div key={k} style={{ fontSize: 10, display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontFamily: 'var(--mono)', gap: '16px' }}>
                  <span style={{ color: k==='AUDUSD'?'#3b82f6':k==='DXY'?'#f59e0b':'#a855f7' }}>{k}</span>
                  <span style={{ color: '#fff' }}>{v.toFixed(4)}</span>
               </div>
             ))}

             {tooltipState.pattern && (
               <div style={{ marginTop: 8, background: tooltipState.pattern.includes('Bull') ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: '1px solid', borderColor: tooltipState.pattern.includes('Bull') ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)', padding: 6, borderRadius: 4, color: tooltipState.pattern.includes('Bull') ? '#22c55e' : '#ef4444', fontSize: 10, fontWeight: 700, textAlign: 'center' }}>
                 ⚡ {tooltipState.pattern}
               </div>
             )}
           </div>
        )}
      </div>
    </div>
  );
});

export default PredictionChart;
