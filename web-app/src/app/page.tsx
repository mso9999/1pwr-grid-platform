'use client'

import { useState } from 'react'
import { MapView } from '@/components/map/MapView'
import { SiteSelector } from '@/components/site/SiteSelector'
import { DataStats } from '@/components/stats/DataStats'
import { ValidationPanel } from '@/components/validation/ValidationPanel'
import { Navigation } from '@/components/layout/Navigation'

export default function Dashboard() {
  const [selectedSite, setSelectedSite] = useState<string>('KET')
  const [activeView, setActiveView] = useState<'map' | 'data' | 'validation'>('map')

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar Navigation */}
      <Navigation activeView={activeView} onViewChange={setActiveView} />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">1PWR Grid Platform</h1>
              <p className="text-sm text-gray-500 mt-1">Network Validation & Management</p>
            </div>
            <SiteSelector 
              selectedSite={selectedSite}
              onSiteChange={setSelectedSite}
            />
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 p-6 overflow-auto">
          {activeView === 'map' && (
            <div className="h-full">
              <MapView site={selectedSite} />
            </div>
          )}
          
          {activeView === 'data' && (
            <div className="space-y-6">
              <DataStats site={selectedSite} />
            </div>
          )}
          
          {activeView === 'validation' && (
            <div className="h-full">
              <ValidationPanel site={selectedSite} />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
