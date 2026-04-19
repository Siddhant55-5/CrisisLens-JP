/**
 * CorrelationHeatmap — D3 grid heatmap of signal-pair correlations.
 */
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { CORR_SIGNALS, getCorrelationValue } from '../../lib/crossMarketData';

const WINDOWS = ['5D', '20D', '60D', '252D'];

const CorrelationHeatmap = React.memo(function CorrelationHeatmap() {
  const svgRef = useRef<SVGSVGElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [window, setWindow] = useState('20D');
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);

  useEffect(() => {
    if (!svgRef.current || !wrapRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const rect = wrapRef.current.getBoundingClientRect();
    const W = Math.min(rect.width, 680);
    const n = CORR_SIGNALS.length;
    const margin = { top: 60, right: 16, bottom: 16, left: 70 };
    const iW = W - margin.left - margin.right;
    const iH = iW; // Square
    const H = iH + margin.top + margin.bottom;
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const cellSize = iW / n;

    // Color scale: green → amber → red for abs correlation
    const colorScale = d3.scaleLinear<string>()
      .domain([0, 0.3, 0.6, 1.0])
      .range(['#0f1729', '#14532d', '#854d0e', '#991b1b'])
      .clamp(true);

    // Draw cells
    CORR_SIGNALS.forEach((sigA, i) => {
      CORR_SIGNALS.forEach((sigB, j) => {
        const val = getCorrelationValue(sigA, sigB);
        const absVal = Math.abs(val);

        const cell = g.append('rect')
          .attr('x', j * cellSize)
          .attr('y', i * cellSize)
          .attr('width', cellSize - 1)
          .attr('height', cellSize - 1)
          .attr('fill', i === j ? 'rgba(99,102,241,.3)' : colorScale(absVal))
          .attr('rx', 2)
          .style('cursor', 'pointer')
          .attr('stroke', 'transparent')
          .attr('stroke-width', 1);

        cell.on('mouseover', function(event) {
          d3.select(this).attr('stroke', 'var(--accent)').attr('stroke-width', 2);
          const [mx, my] = d3.pointer(event, wrapRef.current);
          setTooltip({
            x: mx,
            y: my,
            content: `${sigA} ↔ ${sigB}: ${val.toFixed(3)} (${window} rolling)`,
          });
        });
        cell.on('mouseout', function() {
          d3.select(this).attr('stroke', 'transparent').attr('stroke-width', 1);
          setTooltip(null);
        });

        // Show value in cell if large enough
        if (cellSize > 30 && i !== j) {
          g.append('text')
            .attr('x', j * cellSize + cellSize / 2)
            .attr('y', i * cellSize + cellSize / 2 + 3)
            .attr('text-anchor', 'middle')
            .attr('fill', absVal > 0.6 ? '#fca5a5' : absVal > 0.3 ? '#fbbf24' : 'var(--text-3)')
            .attr('font-size', Math.min(9, cellSize * 0.3))
            .attr('font-family', 'var(--mono)')
            .text(val.toFixed(2));
        }
      });
    });

    // X axis labels (top)
    CORR_SIGNALS.forEach((sig, i) => {
      g.append('text')
        .attr('x', i * cellSize + cellSize / 2)
        .attr('y', -6)
        .attr('text-anchor', 'end')
        .attr('transform', `rotate(-45 ${i * cellSize + cellSize / 2} -6)`)
        .attr('fill', 'var(--text-3)')
        .attr('font-size', 9)
        .attr('font-family', 'var(--mono)')
        .text(sig);
    });

    // Y axis labels (left)
    CORR_SIGNALS.forEach((sig, i) => {
      g.append('text')
        .attr('x', -6)
        .attr('y', i * cellSize + cellSize / 2 + 3)
        .attr('text-anchor', 'end')
        .attr('fill', 'var(--text-3)')
        .attr('font-size', 9)
        .attr('font-family', 'var(--mono)')
        .text(sig);
    });

  }, [window]);

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">
        <span className="card-title">Correlation Matrix</span>
        <div className="chart-tabs">
          {WINDOWS.map(w => (
            <button
              key={w}
              className={`chart-tab${window === w ? ' active' : ''}`}
              onClick={() => setWindow(w)}
            >
              {w}
            </button>
          ))}
        </div>
      </div>
      <div ref={wrapRef} style={{ width: '100%', overflow: 'auto' }}>
        <svg ref={svgRef} style={{ width: '100%' }} />
      </div>
      {tooltip && (
        <div style={{
          position: 'absolute', left: tooltip.x + 12, top: tooltip.y + 12,
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xs)', padding: '6px 10px',
          fontSize: 11, color: 'var(--text-2)', whiteSpace: 'nowrap',
          pointerEvents: 'none', zIndex: 10,
        }}>
          {tooltip.content}
        </div>
      )}
    </div>
  );
});

export default CorrelationHeatmap;
