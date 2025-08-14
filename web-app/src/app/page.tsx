'use client'

import { useState } from 'react'
import { MapView } from '@/components/map/MapView'
import { SiteSelector } from '@/components/site/SiteSelector'
import { DataStats } from '@/components/stats/DataStats'
import { ValidationPanel } from '@/components/validation/ValidationPanel'
import { Navigation } from '@/components/layout/Navigation'

export default function Dashboard() {
  const [selectedSite, setSelectedSite] = useState<string>('KET')
  const [currentView, setCurrentView] = useState<'map' | 'stats' | 'validation'>('map')

  return (
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
            <SiteSelector 
              selectedSite={selectedSite}
              onSiteChange={setSelectedSite}
            />
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full">
            {currentView === 'map' && <MapView site={selectedSite} />}
            {currentView === 'stats' && <DataStats site={selectedSite} />}
            {currentView === 'validation' && <ValidationPanel site={selectedSite} />}
          </div>
        </main>
      </div>
    </div>
  )
}
