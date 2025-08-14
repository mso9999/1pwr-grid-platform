'use client';

import React, { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface FileUploadProps {
  onUploadSuccess?: (site: string) => void;
  onUploadError?: (error: string) => void;
}

export default function FileUpload({ onUploadSuccess, onUploadError }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      // Determine file type
      const fileName = file.name.toLowerCase();
      let response;

      if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
        response = await api.uploadExcel(file);
      } else if (fileName.endsWith('.pkl') || fileName.endsWith('.pickle')) {
        response = await api.uploadPickle(file);
      } else {
        throw new Error('Unsupported file type. Please upload Excel (.xlsx/.xls) or Pickle (.pkl) files.');
      }

      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded ${file.name}. Site: ${response.site}, 
          Poles: ${response.stats?.poles || 0}, 
          Conductors: ${response.stats?.conductors || 0}`
      });

      if (onUploadSuccess) {
        onUploadSuccess(response.site);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadStatus({
        type: 'error',
        message: errorMessage
      });

      if (onUploadError) {
        onUploadError(errorMessage);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="sr-only"
          accept=".xlsx,.xls,.pkl,.pickle"
          onChange={handleChange}
          disabled={uploading}
        />
        
        <label
          htmlFor="file-upload"
          className="cursor-pointer"
        >
          <div className="flex flex-col items-center justify-center">
            {uploading ? (
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            ) : (
              <Upload className="h-12 w-12 text-gray-400" />
            )}
            
            <p className="mt-4 text-lg font-medium text-gray-900">
              {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </p>
            
            <p className="mt-2 text-sm text-gray-600">
              Supports Excel (.xlsx, .xls) and Pickle (.pkl) files from uGridPLAN
            </p>
            
            <div className="mt-4 flex items-center space-x-2 text-xs text-gray-500">
              <FileSpreadsheet className="h-4 w-4" />
              <span>Maximum file size: 100MB</span>
            </div>
          </div>
        </label>
      </div>

      {/* Status Messages */}
      {uploadStatus.type && (
        <div
          className={`mt-4 p-4 rounded-md flex items-start space-x-2 ${
            uploadStatus.type === 'success'
              ? 'bg-green-50 text-green-800'
              : 'bg-red-50 text-red-800'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          )}
          <span className="text-sm">{uploadStatus.message}</span>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Import Instructions:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Upload Excel exports from uGridPLAN containing network data</li>
          <li>• Pickle files from legacy uGridPLAN installations are also supported</li>
          <li>• Site name will be extracted from the filename</li>
          <li>• Data will be validated and cleaned automatically</li>
        </ul>
      </div>
    </div>
  );
}
