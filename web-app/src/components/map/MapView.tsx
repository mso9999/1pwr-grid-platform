'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { ClientMapProps } from './ClientMap'
import IssuesList from './IssuesList'

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
  onNetworkUpdate?: () => void;
}

export function MapView({ site, networkData, loading, onNetworkUpdate }: MapViewProps) {
  const [mounted, setMounted] = useState(false)
  const [transformedData, setTransformedData] = useState<any>(null)
  const [showIssues, setShowIssues] = useState(true)
  const [selectedElementFromIssue, setSelectedElementFromIssue] = useState<{type: string, id: string} | null>(null)
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  // Transform backend field names to frontend expected names
  useEffect(() => {
    if (!networkData) {
      setTransformedData(null)
      return
    }

    console.log('Raw network data:', networkData)

    const transformed = {
      poles: networkData.poles?.map((pole: any) => ({
        id: pole.pole_id || pole.id,
        lat: pole.latitude || pole.lat,
        lng: pole.longitude || pole.lng,
        type: pole.pole_type || pole.type,
        status: pole.status,
        pole_class: pole.angle_class || pole.pole_class,
        st_code_1: pole.st_code_1,
        st_code_2: pole.st_code_2,
        ...pole
      })) || [],
      connections: networkData.connections?.map((conn: any) => ({
        id: conn.survey_id || conn.id,
        lat: conn.latitude || conn.lat,
        lng: conn.longitude || conn.lng,
        name: conn.customer_name || conn.name,
        st_code_3: conn.st_code_3,
        ...conn
      })) || [],
      conductors: networkData.conductors?.map((cond: any) => ({
        id: cond.conductor_id || cond.id,
        from: cond.from_pole || cond.from,
        to: cond.to_pole || cond.to,
        type: cond.conductor_type || cond.type,
        st_code_4: cond.st_code_4,
        length: cond.length,
        ...cond
      })) || [],
      transformers: networkData.transformers || [],
      generation: networkData.generation || []
    }

    console.log('Transformed data:', {
      poles: transformed.poles.length,
      connections: transformed.connections.length,
      conductors: transformed.conductors.length
    })

    setTransformedData(transformed)
  }, [networkData])
  
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
    <>
      <ClientMap
        networkData={transformedData ? {...transformedData, site} : null}
        loading={loading}
        onElementUpdate={onNetworkUpdate}
      />
      {showIssues && transformedData && (
        <IssuesList
          networkData={transformedData}
          onClose={() => setShowIssues(false)}
          onSelectElement={(type, id) => {
            setSelectedElementFromIssue({ type, id })
            // TODO: Pass this to ClientMap to highlight the element
          }}
        />
      )}
    </>
  )
}
