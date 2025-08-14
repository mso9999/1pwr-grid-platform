'use client';

import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileText, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface ExportControlsProps {
  site: string;
  onExportStart?: () => void;
  onExportComplete?: () => void;
}

export default function ExportControls({ 
  site, 
  onExportStart, 
  onExportComplete 
}: ExportControlsProps) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportType, setExportType] = useState<'network' | 'field'>('network');

  const handleNetworkExport = async () => {
    setExporting(true);
    setError(null);
    onExportStart?.();

    try {
      // Build export URL with parameters
      const params = new URLSearchParams({
        site: site,
        include_voltage: 'true',
        include_validation: 'true'
      });
      
      const response = await fetch(`http://localhost:8000/api/export/network-report?${params}`, {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get filename from response headers or use default
      const contentDisposition = response.headers.get('content-disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/['"]/g, '')
        : `network_report_${site}_${new Date().toISOString().split('T')[0]}.xlsx`;

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      onExportComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const handleFieldExport = async () => {
    setExporting(true);
    setError(null);
    onExportStart?.();

    try {
      // Example field report data - in production, this would come from UI inputs
      const fieldData = {
        site: site,
        work_completed: [
          {
            id: 'WC001',
            description: 'Installed MV poles KET-001 to KET-010',
            component_type: 'MV Pole',
            date_completed: new Date().toISOString().split('T')[0],
            team: 'Team A'
          }
        ],
        pending_work: [
          {
            id: 'PW001',
            description: 'Install LV distribution from transformer T01',
            component_type: 'LV Network',
            priority: 'High',
            assigned_team: 'Team B'
          }
        ],
        issues: [
          {
            id: 'IS001',
            description: 'Rocky terrain at pole location KET-015',
            severity: 'Medium',
            component: 'MV Pole',
            date_reported: new Date().toISOString().split('T')[0]
          }
        ]
      };

      const response = await fetch('http://localhost:8000/api/export/field-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        body: JSON.stringify(fieldData)
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get filename from response headers or use default
      const contentDisposition = response.headers.get('content-disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/['"]/g, '')
        : `field_report_${site}_${new Date().toISOString().split('T')[0]}.xlsx`;

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      onExportComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Export Reports</h3>
        <FileSpreadsheet className="w-5 h-5 text-gray-400" />
      </div>

      {/* Export Type Selection */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setExportType('network')}
          className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            exportType === 'network'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100'
          }`}
        >
          Network Report
        </button>
        <button
          onClick={() => setExportType('field')}
          className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            exportType === 'field'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100'
          }`}
        >
          Field Report
        </button>
      </div>

      {/* Export Details */}
      <div className="mb-4 p-3 bg-gray-50 rounded-md">
        {exportType === 'network' ? (
          <div className="text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-1">Network Report includes:</p>
            <ul className="space-y-1 ml-4">
              <li>• Complete pole and conductor inventory</li>
              <li>• Voltage drop calculations and violations</li>
              <li>• Network validation results</li>
              <li>• Status distribution and statistics</li>
              <li>• Charts and visualizations</li>
            </ul>
          </div>
        ) : (
          <div className="text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-1">Field Report includes:</p>
            <ul className="space-y-1 ml-4">
              <li>• Completed work items</li>
              <li>• Pending work assignments</li>
              <li>• Field issues and observations</li>
              <li>• Team assignments and priorities</li>
              <li>• Status tracking</li>
            </ul>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Export Button */}
      <button
        onClick={exportType === 'network' ? handleNetworkExport : handleFieldExport}
        disabled={exporting || !site}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
          exporting || !site
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {exporting ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            Generating Report...
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            Export {exportType === 'network' ? 'Network' : 'Field'} Report
          </>
        )}
      </button>

      {/* Site Info */}
      <div className="mt-3 text-xs text-gray-500 text-center">
        Site: <span className="font-medium">{site || 'No site selected'}</span>
      </div>
    </div>
  );
}
