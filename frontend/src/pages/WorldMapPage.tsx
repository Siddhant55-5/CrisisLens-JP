/**
 * WorldMapPage — Leaflet dark map with country risk choropleth.
 */
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import { useEffect, useState } from 'react';
import { COUNTRY_RISKS } from '../lib/mockData';
import 'leaflet/dist/leaflet.css';
import type { Layer, PathOptions } from 'leaflet';

const TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR = '&copy; <a href="https://carto.com">CARTO</a>';

function riskColor(score: number): string {
  if (score <= 30) return '#22c55e';
  if (score <= 50) return '#84cc16';
  if (score <= 65) return '#eab308';
  if (score <= 80) return '#f97316';
  return '#ef4444';
}

// Simplified GeoJSON for major countries (bounding rectangles as proxies)
// In production, use full world GeoJSON — this gives demo coverage
function createSimpleGeoJSON() {
  const features = Object.entries(COUNTRY_RISKS).map(([iso, data]) => {
    const coords = COUNTRY_COORDS[iso];
    if (!coords) return null;
    return {
      type: 'Feature' as const,
      properties: { iso, ...data },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [coords],
      },
    };
  }).filter(Boolean);

  return { type: 'FeatureCollection' as const, features };
}

// Simplified country boundary coordinates (rough polygons)
const COUNTRY_COORDS: Record<string, number[][]> = {
  USA: [[-125,24],[-125,50],[-66,50],[-66,24],[-125,24]],
  GBR: [[-8,50],[-8,59],[2,59],[2,50],[-8,50]],
  DEU: [[6,47],[6,55],[15,55],[15,47],[6,47]],
  FRA: [[-5,42],[-5,51],[8,51],[8,42],[-5,42]],
  JPN: [[129,31],[129,45],[146,45],[146,31],[129,31]],
  CHN: [[73,18],[73,54],[135,54],[135,18],[73,18]],
  IND: [[68,8],[68,37],[97,37],[97,8],[68,8]],
  BRA: [[-74,-33],[-74,6],[-35,6],[-35,-33],[-74,-33]],
  AUS: [[113,-44],[113,-10],[154,-10],[154,-44],[113,-44]],
  CAN: [[-141,42],[-141,70],[-52,70],[-52,42],[-141,42]],
  ITA: [[6,36],[6,47],[18,47],[18,36],[6,36]],
  ESP: [[-9,36],[-9,44],[3,44],[3,36],[-9,36]],
  KOR: [[126,33],[126,39],[130,39],[130,33],[126,33]],
  MEX: [[-118,14],[-118,33],[-86,33],[-86,14],[-118,14]],
  RUS: [[27,41],[27,72],[180,72],[180,41],[27,41]],
  TUR: [[26,36],[26,42],[45,42],[45,36],[26,36]],
  ZAF: [[16,-35],[16,-22],[33,-22],[33,-35],[16,-35]],
  ARG: [[-73,-55],[-73,-22],[-53,-22],[-53,-55],[-73,-55]],
  SGP: [[103.6,1.15],[103.6,1.47],[104.1,1.47],[104.1,1.15],[103.6,1.15]],
  CHE: [[6,45.8],[6,47.8],[10.5,47.8],[10.5,45.8],[6,45.8]],
};

export default function WorldMapPage() {
  const [geoData, setGeoData] = useState<any>(null);

  useEffect(() => {
    setGeoData(createSimpleGeoJSON());
  }, []);

  const style = (feature: any): PathOptions => {
    const iso = feature?.properties?.iso;
    const data = iso ? COUNTRY_RISKS[iso] : null;
    const avgScore = data ? (data.banking + data.market + data.liquidity) / 3 : 50;
    return {
      fillColor: riskColor(avgScore),
      fillOpacity: 0.35,
      color: riskColor(avgScore),
      weight: 1,
      opacity: 0.6,
    };
  };

  const onEachFeature = (feature: any, layer: Layer) => {
    const p = feature.properties;
    if (!p) return;

    const avgScore = ((p.banking + p.market + p.liquidity) / 3).toFixed(0);

    const popup = `
      <div class="map-popup">
        <h3>${p.flag} ${p.name}</h3>
        <div class="score-bars">
          <div class="score-bar-row">
            <span class="score-bar-label">Banking</span>
            <div class="score-bar-track"><div class="score-bar-fill" style="width:${p.banking}%;background:${riskColor(p.banking)}"></div></div>
            <span style="font-size:11px;font-family:var(--mono);color:var(--text-2);width:24px;text-align:right">${p.banking}</span>
          </div>
          <div class="score-bar-row">
            <span class="score-bar-label">Market</span>
            <div class="score-bar-track"><div class="score-bar-fill" style="width:${p.market}%;background:${riskColor(p.market)}"></div></div>
            <span style="font-size:11px;font-family:var(--mono);color:var(--text-2);width:24px;text-align:right">${p.market}</span>
          </div>
          <div class="score-bar-row">
            <span class="score-bar-label">Liquidity</span>
            <div class="score-bar-track"><div class="score-bar-fill" style="width:${p.liquidity}%;background:${riskColor(p.liquidity)}"></div></div>
            <span style="font-size:11px;font-family:var(--mono);color:var(--text-2);width:24px;text-align:right">${p.liquidity}</span>
          </div>
        </div>
        <div class="stress-signal">⚡ ${p.topSignal}</div>
      </div>
    `;

    (layer as any).bindPopup(popup, { className: 'dark-popup', maxWidth: 260 });

    (layer as any).on({
      mouseover: (e: any) => {
        e.target.setStyle({ fillOpacity: 0.6, weight: 2 });
      },
      mouseout: (e: any) => {
        e.target.setStyle({ fillOpacity: 0.35, weight: 1 });
      },
    });
  };

  return (
    <div style={{ position: 'relative' }}>
      <div className="map-container">
        <MapContainer
          center={[25, 10]}
          zoom={2}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
          attributionControl={false}
        >
          <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
          {geoData && (
            <GeoJSON data={geoData} style={style} onEachFeature={onEachFeature} />
          )}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="map-legend">
        <div className="map-legend-title">Risk Score</div>
        <div className="map-legend-scale">
          <div style={{ flex: 1, background: '#22c55e' }} />
          <div style={{ flex: 1, background: '#84cc16' }} />
          <div style={{ flex: 1, background: '#eab308' }} />
          <div style={{ flex: 1, background: '#f97316' }} />
          <div style={{ flex: 1, background: '#ef4444' }} />
        </div>
        <div className="map-legend-labels">
          <span>0</span>
          <span>25</span>
          <span>50</span>
          <span>75</span>
          <span>100</span>
        </div>
      </div>
    </div>
  );
}
