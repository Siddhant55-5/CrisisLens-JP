/**
 * ContagionSankey — D3 force-directed graph showing cross-asset contagion flows.
 *
 * Uses a custom Sankey-like layout with animated stress paths.
 * Nodes = asset classes, links = impact channels.
 */
import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { MOCK_CASCADE_GRAPH } from '../../lib/crossMarketData';

interface Props {
  graphData?: typeof MOCK_CASCADE_GRAPH;
  activeSource?: string;
}

const NODE_POSITIONS: Record<string, [number, number]> = {
  CURRENCY:  [0.1, 0.3],
  COMMODITY: [0.1, 0.7],
  EQUITY:    [0.5, 0.15],
  BOND:      [0.5, 0.85],
  SOVEREIGN: [0.9, 0.5],
};

export default function ContagionSankey({ graphData, activeSource }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);

  const data = graphData || MOCK_CASCADE_GRAPH;

  useEffect(() => {
    if (!svgRef.current || !wrapRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const rect = wrapRef.current.getBoundingClientRect();
    const W = rect.width;
    const H = 340;
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g');

    // Defs for animated dash
    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient').attr('id', 'stress-gradient');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#6366f1').attr('stop-opacity', 0.8);
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ef4444').attr('stop-opacity', 0.8);

    // Draw links
    data.links.forEach((link, i) => {
      const srcPos = NODE_POSITIONS[link.source];
      const tgtPos = NODE_POSITIONS[link.target];
      if (!srcPos || !tgtPos) return;

      const x1 = srcPos[0] * W;
      const y1 = srcPos[1] * H;
      const x2 = tgtPos[0] * W;
      const y2 = tgtPos[1] * H;

      const isHighlighted = selectedNode
        ? (link.source === selectedNode || link.target === selectedNode)
        : link.active;

      const midX = (x1 + x2) / 2;
      const midY = (y1 + y2) / 2 + (i % 2 === 0 ? -15 : 15);

      const path = g.append('path')
        .attr('d', `M${x1},${y1} Q${midX},${midY} ${x2},${y2}`)
        .attr('fill', 'none')
        .attr('stroke', isHighlighted
          ? (link.impact_strength === 'High' ? '#ef4444' : link.impact_strength === 'Medium' ? '#f59e0b' : '#64748b')
          : 'rgba(255,255,255,.06)'
        )
        .attr('stroke-width', isHighlighted ? link.value * 0.4 + 1 : 1)
        .attr('opacity', isHighlighted ? 0.8 : 0.3)
        .style('cursor', 'pointer');

      // Animated dash for active stress paths
      if (isHighlighted && link.active) {
        path
          .attr('stroke-dasharray', '8,4')
          .style('animation', `dash-flow ${3 - (link.confidence || 0.5)}s linear infinite`);
      }

      // Link hover
      path.on('mouseover', function(event) {
        d3.select(this).attr('stroke-width', link.value * 0.6 + 2).attr('opacity', 1);
        const [mx, my] = d3.pointer(event, wrapRef.current);
        setTooltip({
          x: mx,
          y: my,
          content: `${link.source} → ${link.target}\n${link.description}\nStrength: ${link.impact_strength} | Lag: ${link.avg_lag_days}d | Conf: ${(link.confidence * 100).toFixed(0)}%`,
        });
      });
      path.on('mouseout', function() {
        d3.select(this)
          .attr('stroke-width', isHighlighted ? link.value * 0.4 + 1 : 1)
          .attr('opacity', isHighlighted ? 0.8 : 0.3);
        setTooltip(null);
      });

      // Confidence label on link
      if (isHighlighted) {
        g.append('text')
          .attr('x', midX).attr('y', midY - 6)
          .attr('text-anchor', 'middle')
          .attr('fill', 'var(--text-3)').attr('font-size', 9).attr('font-family', 'var(--mono)')
          .text(`${(link.confidence * 100).toFixed(0)}%`);
      }
    });

    // Draw nodes
    data.nodes.forEach((node) => {
      const pos = NODE_POSITIONS[node.id];
      if (!pos) return;
      const x = pos[0] * W;
      const y = pos[1] * H;
      const r = 28;
      const isSelected = selectedNode === node.id;

      // Glow for active nodes
      if (node.active || isSelected) {
        g.append('circle')
          .attr('cx', x).attr('cy', y).attr('r', r + 6)
          .attr('fill', 'none')
          .attr('stroke', node.color).attr('stroke-width', 2)
          .attr('opacity', 0.3)
          .style('filter', 'blur(4px)');
      }

      // Node circle
      g.append('circle')
        .attr('cx', x).attr('cy', y).attr('r', r)
        .attr('fill', isSelected ? node.color : `${node.color}22`)
        .attr('stroke', node.color)
        .attr('stroke-width', isSelected ? 3 : 1.5)
        .style('cursor', 'pointer')
        .on('click', () => {
          setSelectedNode(selectedNode === node.id ? null : node.id);
        });

      // Node label
      g.append('text')
        .attr('x', x).attr('y', y + 4)
        .attr('text-anchor', 'middle')
        .attr('fill', isSelected ? '#fff' : node.color)
        .attr('font-size', 10).attr('font-weight', 700)
        .attr('font-family', 'var(--font)')
        .style('pointer-events', 'none')
        .text(node.id.slice(0, 5));
    });

  }, [data, selectedNode]);

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">
        <span className="card-title">Contagion Flow Map</span>
        {selectedNode && (
          <button
            className="chart-tab active"
            onClick={() => setSelectedNode(null)}
            style={{ fontSize: 10 }}
          >
            Clear: {selectedNode}
          </button>
        )}
      </div>
      <div ref={wrapRef} style={{ width: '100%', height: 340 }}>
        <svg ref={svgRef} style={{ width: '100%', height: '100%' }}>
          <style>{`
            @keyframes dash-flow {
              to { stroke-dashoffset: -24; }
            }
          `}</style>
        </svg>
      </div>
      {tooltip && (
        <div style={{
          position: 'absolute', left: tooltip.x + 12, top: tooltip.y + 12,
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xs)', padding: '8px 12px',
          fontSize: 11, color: 'var(--text-2)', whiteSpace: 'pre-line',
          pointerEvents: 'none', zIndex: 10, maxWidth: 260,
        }}>
          {tooltip.content}
        </div>
      )}
    </div>
  );
}
