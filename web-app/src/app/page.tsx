'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { SiteSelector } from '@/components/site/SiteSelector'
import { DataStats } from '@/components/stats/DataStats'
import { ValidationPanel } from '@/components/validation/ValidationPanel'
import { Navigation } from '@/components/layout/Navigation'
import FileUpload from '@/components/FileUpload'
import ExportControls from '@/components/ExportControls'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import UserMenu from '@/components/auth/UserMenu'
import { api } from '@/lib/api'

// Import MapView dynamically with SSR disabled (Leaflet requires browser APIs)
const MapView = dynamic(
  () => import('@/components/map/MapView').then((mod) => mod.MapView),
  { 
    ssr: false,
    loading: () => <div className="h-full flex items-center justify-center">Loading map...</div>
  }
)

export default function Dashboard() {
  const [selectedSite, setSelectedSite] = useState<string>('KET')
  const [currentView, setCurrentView] = useState<'map' | 'stats' | 'validation' | 'upload'>('map')
  const [networkData, setNetworkData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch network data when site changes
  useEffect(() => {
    if (selectedSite && currentView !== 'upload') {
      fetchNetworkData(selectedSite)
    }
  }, [selectedSite, currentView])

  const fetchNetworkData = async (site: string) => {
    console.log('Fetching network data for site:', site)
    setLoading(true)
    setError(null)
    try {
      const response = await api.getNetwork(site)
      console.log('API response:', response)
      console.log('Network data fetched:', {
        poles: response.data?.poles?.length || 0,
        conductors: response.data?.conductors?.length || 0,
        connections: response.data?.connections?.length || 0
      })
      console.log('Setting networkData to:', response.data)
      setNetworkData(response.data)
    } catch (err) {
      console.error('Failed to fetch network data:', err)
      setError(err instanceof Error ? err.message : 'Failed to load network data')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = (site: string) => {
    setSelectedSite(site)
    setCurrentView('map')
  }

  return (
    <ProtectedRoute requiredPermission="network:view">
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar Navigation */}
        <Navigation currentView={currentView} onViewChange={setCurrentView} />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">1PWR Grid Platform</h1>
              <p className="text-xs text-gray-600">Network Validation & Management</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Export Controls - show when network data is loaded */}
              {networkData && currentView !== 'upload' && (
                <div className="min-w-[200px]">
                  <ExportControls 
                    site={selectedSite}
                    onExportStart={() => console.log('Export started')}
                    onExportComplete={() => console.log('Export complete')}
                  />
                </div>
              )}
              <SiteSelector 
                selectedSite={selectedSite}
                onSiteChange={setSelectedSite}
              />
              <UserMenu />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full relative">
            {currentView === 'upload' && (
              <div className="h-full flex items-center justify-center">
                <FileUpload 
                  onUploadSuccess={handleUploadSuccess}
                  onUploadError={setError}
                />
              </div>
            )}
            {currentView === 'map' && (
              <div className="h-full relative">
                <MapView 
                  site={selectedSite} 
                  networkData={networkData} 
                  loading={loading}
                  onNetworkUpdate={() => fetchNetworkData(selectedSite)}
                />
              </div>
            )}
            {currentView === 'stats' && <DataStats site={selectedSite} networkData={networkData} />}
            {currentView === 'validation' && <ValidationPanel site={selectedSite} networkData={networkData} />}
            {error && (
              <div className="absolute bottom-4 right-4 bg-red-50 text-red-800 p-4 rounded-md">
                {error}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
    </ProtectedRoute>
  )
}
