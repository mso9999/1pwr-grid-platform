'use client';

import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import { api } from '@/lib/api';

interface VoltageOverlayProps {
  map: L.Map | null;
  site: string;
  conductors: Array<{
    id: string;
    from: string;
    to: string;
    type: string;
  }>;
  poles: Array<{
    id: string;
    lat: number;
    lng: number;
  }>;
  enabled: boolean;
  sourceVoltage?: number;
  voltageThreshold?: number;
}

interface VoltageResult {
  voltages: Record<string, number>;
  violations: Array<{
    node: string;
    voltage: number;
    drop_percent: number;
  }>;
  max_drop: number;
}

export default function VoltageOverlay({
  map,
  site,
  conductors,
  poles,
  enabled,
  sourceVoltage = 11000,
  voltageThreshold = 7.0
}: VoltageOverlayProps) {
  const [voltageData, setVoltageData] = useState<VoltageResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const legendRef = useRef<L.Control | null>(null);

  // Initialize layer group when map is available
  useEffect(() => {
    if (map && !layerGroupRef.current) {
      layerGroupRef.current = L.layerGroup().addTo(map);
    }
    return () => {
      if (layerGroupRef.current && map) {
        map.removeLayer(layerGroupRef.current);
        layerGroupRef.current = null;
      }
      if (legendRef.current && map) {
        map.removeControl(legendRef.current);
        legendRef.current = null;
      }
    };
  }, [map]);

  // Calculate voltage when enabled
  useEffect(() => {
    if (enabled && site && conductors.length > 0 && map) {
      calculateVoltage();
    } else if (!enabled && layerGroupRef.current) {
      layerGroupRef.current.clearLayers();
      if (legendRef.current && map) {
        map.removeControl(legendRef.current);
        legendRef.current = null;
      }
    }
  }, [enabled, site, map]);

  const calculateVoltage = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.calculateVoltage(site, sourceVoltage, voltageThreshold);
      if (result.success && result.results) {
        setVoltageData(result.results);
      } else {
        setError(result.message || 'Voltage calculation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate voltage');
    } finally {
      setLoading(false);
    }
  };

  // Get voltage drop color based on percentage
  const getVoltageColor = (dropPercent: number, threshold: number): string => {
    if (dropPercent <= 3) return '#10b981'; // Green - Excellent
    if (dropPercent <= 5) return '#eab308'; // Yellow - Good
    if (dropPercent <= threshold) return '#f97316'; // Orange - Warning
    return '#ef4444'; // Red - Violation
  };

  // Get line weight based on voltage drop severity
  const getLineWeight = (fromNode: string, toNode: string): number => {
    if (!voltageData?.voltages) return 2;

    const fromVoltage = voltageData.voltages[fromNode] || sourceVoltage;
    const toVoltage = voltageData.voltages[toNode] || sourceVoltage;
    const avgVoltage = (fromVoltage + toVoltage) / 2;
    const dropPercent = ((sourceVoltage - avgVoltage) / sourceVoltage) * 100;

    // Thicker lines for higher voltage drops
    if (dropPercent > voltageThreshold) return 5;
    if (dropPercent > 5) return 4;
    return 3;
  };

  // Helper to find pole coordinates
  // Render conductor lines on the map
  useEffect(() => {
    if (!map || !voltageData || !enabled || !layerGroupRef.current) return;

    // Clear existing layers
    layerGroupRef.current.clearLayers();

    // Remove existing legend if any
    if (legendRef.current) {
      map.removeControl(legendRef.current);
      legendRef.current = null;
    }

    // Add conductor lines
    conductors.forEach(conductor => {
      const fromPole = poles.find(p => p.id === conductor.from);
      const toPole = poles.find(p => p.id === conductor.to);
      
      if (!fromPole || !toPole) return;

      // Get voltage drop for this conductor
      const fromVoltage = voltageData.voltages[conductor.from] || sourceVoltage;
      const toVoltage = voltageData.voltages[conductor.to] || sourceVoltage;
      const voltageDrop = ((sourceVoltage - toVoltage) / sourceVoltage) * 100;

      // Determine color based on voltage drop
      const color = getVoltageColor(voltageDrop, voltageThreshold);

      // Create polyline
      const polyline = L.polyline(
        [[fromPole.lat, fromPole.lng], [toPole.lat, toPole.lng]],
        {
          color,
          weight: 3,
          opacity: 0.8
        }
      );

      // Add popup to polyline
      const popupContent = `
        <div style="font-size: 12px;">
          <div style="font-weight: bold;">${conductor.id}</div>
          <div>Type: ${conductor.type}</div>
          <div>From: ${conductor.from} (${fromVoltage.toFixed(0)}V)</div>
          <div>To: ${conductor.to} (${toVoltage.toFixed(0)}V)</div>
          <div style="font-weight: bold; color: ${voltageDrop > voltageThreshold ? '#dc2626' : '#16a34a'};">
            Drop: ${voltageDrop.toFixed(2)}%
          </div>
        </div>`;
      polyline.bindPopup(popupContent);

      layerGroupRef.current?.addLayer(polyline);
    });

    // Add legend
    const LegendControl = L.Control.extend({
      options: { position: 'bottomright' },
      onAdd: function() {
        const div = L.DomUtil.create('div', 'bg-white p-3 rounded shadow-lg');
        div.innerHTML = `
          <div class="text-sm font-semibold mb-2">Voltage Drop</div>
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <div class="w-4 h-1" style="background: #10b981"></div>
              <span class="text-xs">0-3%</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-1" style="background: #eab308"></div>
              <span class="text-xs">3-5%</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-1" style="background: #f97316"></div>
              <span class="text-xs">5-7%</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-1" style="background: #ef4444"></div>
              <span class="text-xs">>7%</span>
            </div>
          </div>
          ${voltageData.max_drop > 0 ? `
            <div class="mt-2 pt-2 border-t text-xs">
              Max Drop: ${voltageData.max_drop.toFixed(2)}%
            </div>
          ` : ''}
        `;
        return div;
      }
    });
    const legend = new LegendControl();
    legend.addTo(map);
    legendRef.current = legend;
  }, [map, voltageData, enabled, conductors, poles, sourceVoltage, voltageThreshold]);

  // Render loading/error states
  if (!map) return null;

  return (
    <>
      {/* Loading indicator */}
      {loading && (
        <div className="absolute top-4 right-4 bg-white p-2 rounded shadow z-[1000]">
          <div className="text-sm">Calculating voltage...</div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="absolute top-4 right-4 bg-red-50 border border-red-200 p-2 rounded shadow z-[1000]">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}
    </>
  );
}
