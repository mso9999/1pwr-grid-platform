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

  const renderContent = () => {
    switch (currentView) {
      case 'upload':
        return (
          <div className="h-full flex items-center justify-center">
            <FileUpload 
              onUploadSuccess={handleUploadSuccess}
              onUploadError={setError}
            />
          </div>
        )
      case 'map':
        return (
          <div className="h-full relative">
            <MapView 
              site={selectedSite} 
              networkData={networkData} 
              loading={loading}
              onNetworkUpdate={() => fetchNetworkData(selectedSite)}
            />
          </div>
        )
      case 'stats':
        return <DataStats site={selectedSite} networkData={networkData} />
      case 'validation':
        return <ValidationPanel site={selectedSite} networkData={networkData} />
      default:
        return null
    }
  }

  return (
    <ProtectedRoute>
      <div className="grid-layout">
        {/* Sidebar Navigation */}
        <div className="sidebar-zone">
          <Navigation currentView={currentView} onViewChange={setCurrentView} />
        </div>
        
        {/* Main Content */}
        <div className="content-zone">
          {/* Header */}
          <header className="header-bar">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">1PWR Grid Platform</h1>
                <p className="text-sm text-gray-500">
                  {currentView === 'map' && 'Network Visualization'}
                  {currentView === 'stats' && 'Data Statistics'}
                  {currentView === 'validation' && 'Network Validation'}
                  {currentView === 'upload' && 'Upload Network Data'}
                </p>
              </div>
              <div className="flex items-center space-x-4">
                {/* Site Selector */}
                <SiteSelector
                  selectedSite={selectedSite}
                  onSiteChange={setSelectedSite}
                />
                <UserMenu />
              </div>
            </div>
          </header>

          {/* Content Area */}
          <main className="main-content">
            {renderContent()}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
