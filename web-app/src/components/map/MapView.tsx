'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { ClientMapProps } from './ClientMap'

// Dynamically import ClientMap to avoid SSR issues
const ClientMap = dynamic<ClientMapProps>(
  () => import('./ClientMap').then(mod => mod.ClientMap),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }
)

interface MapViewProps {
  site: string;
  networkData?: any;
  loading?: boolean;
}

export function MapView({ site, networkData, loading }: MapViewProps) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  console.log('MapView props:', { 
    site, 
    hasNetworkData: !!networkData, 
    dataKeys: networkData ? Object.keys(networkData) : 'none',
    loading 
  })
  
  if (!mounted) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }
  
  return (
    <ClientMap
      networkData={networkData}
      loading={loading}
    />
  )
}
