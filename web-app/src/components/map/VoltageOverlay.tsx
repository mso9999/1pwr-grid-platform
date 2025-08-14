'use client';

import React, { useEffect, useState } from 'react';
import { Polyline, Tooltip } from 'react-leaflet';
import { api } from '@/lib/api';

interface VoltageOverlayProps {
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

  // Calculate voltage when enabled
  useEffect(() => {
    if (enabled && site && conductors.length > 0) {
      calculateVoltage();
    }
  }, [enabled, site]);

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
  const getVoltageColor = (fromNode: string, toNode: string): string => {
    if (!voltageData?.voltages) return '#999999'; // Grey if no data

    const fromVoltage = voltageData.voltages[fromNode] || sourceVoltage;
    const toVoltage = voltageData.voltages[toNode] || sourceVoltage;
    
    // Calculate average voltage drop percentage
    const avgVoltage = (fromVoltage + toVoltage) / 2;
    const dropPercent = ((sourceVoltage - avgVoltage) / sourceVoltage) * 100;

    // Color gradient based on voltage drop
    if (dropPercent <= 2) return '#00ff00'; // Green - Excellent
    if (dropPercent <= 4) return '#90ee90'; // Light Green - Good
    if (dropPercent <= 6) return '#ffff00'; // Yellow - Acceptable
    if (dropPercent <= 7) return '#ffa500'; // Orange - Warning
    if (dropPercent <= 8) return '#ff6600'; // Dark Orange - Critical
    return '#ff0000'; // Red - Violation
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
  const findPoleCoords = (poleId: string) => {
    const pole = poles.find(p => p.id === poleId);
    return pole ? [pole.lat, pole.lng] as [number, number] : null;
  };

  if (!enabled || loading) return null;

  return (
    <>
      {/* Render voltage-colored conductors */}
      {conductors.map(conductor => {
        const fromCoords = findPoleCoords(conductor.from);
        const toCoords = findPoleCoords(conductor.to);
        
        if (!fromCoords || !toCoords) return null;

        const color = getVoltageColor(conductor.from, conductor.to);
        const weight = getLineWeight(conductor.from, conductor.to);

        // Get voltage values for tooltip
        const fromVoltage = voltageData?.voltages?.[conductor.from] || sourceVoltage;
        const toVoltage = voltageData?.voltages?.[conductor.to] || sourceVoltage;
        const avgVoltage = (fromVoltage + toVoltage) / 2;
        const dropPercent = ((sourceVoltage - avgVoltage) / sourceVoltage) * 100;

        return (
          <Polyline
            key={`voltage-${conductor.id}`}
            positions={[fromCoords, toCoords]}
            color={color}
            weight={weight}
            opacity={0.8}
          >
            <Tooltip sticky>
              <div className="text-xs">
                <p className="font-semibold">{conductor.id}</p>
                <p>From: {conductor.from} ({fromVoltage.toFixed(0)}V)</p>
                <p>To: {conductor.to} ({toVoltage.toFixed(0)}V)</p>
                <p className={dropPercent > voltageThreshold ? 'text-red-600 font-bold' : ''}>
                  Drop: {dropPercent.toFixed(2)}%
                </p>
              </div>
            </Tooltip>
          </Polyline>
        );
      })}

      {/* Display error if any */}
      {error && (
        <div className="absolute top-4 right-4 bg-red-50 text-red-800 p-3 rounded-md text-sm">
          Voltage calculation error: {error}
        </div>
      )}

      {/* Voltage legend */}
      {voltageData && (
        <div className="absolute bottom-20 right-4 bg-white p-3 rounded-lg shadow-md">
          <h4 className="text-xs font-semibold mb-2">Voltage Drop</h4>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-green-500"></div>
              <span className="text-xs">0-2% Excellent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-green-300"></div>
              <span className="text-xs">2-4% Good</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-yellow-400"></div>
              <span className="text-xs">4-6% Acceptable</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-orange-500"></div>
              <span className="text-xs">6-7% Warning</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-orange-600"></div>
              <span className="text-xs">7-8% Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-2 bg-red-500"></div>
              <span className="text-xs">&gt;8% Violation</span>
            </div>
          </div>
          {voltageData.max_drop && (
            <div className="mt-2 pt-2 border-t text-xs">
              <p>Max Drop: <span className="font-semibold">{voltageData.max_drop.toFixed(2)}%</span></p>
              <p>Violations: <span className="font-semibold">{voltageData.violations?.length || 0}</span></p>
            </div>
          )}
        </div>
      )}
    </>
  );
}
