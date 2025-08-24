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
    console.log('=== MapView useEffect triggered ===', { 
      hasNetworkData: !!networkData?.data,
      dataKeys: networkData?.data ? Object.keys(networkData.data) : [] 
    })
    if (networkData?.data) {
      // Transform the data to match frontend expectations
      const transformedData = {
        ...networkData.data,
        poles: networkData.data.poles?.map((pole: any) => ({
          ...pole,
          statusCode: pole.st_code_1,
          constructionStatus: pole.st_code_4
        })) || [],
        connections: networkData.data.connections?.map((conn: any) => ({
          ...conn,
          statusCode: conn.st_code_3
        })) || [],
        conductors: networkData.data.conductors?.map((cond: any) => ({
          ...cond,
          constructionStatus: cond.st_code_4
        })) || []
      }
      console.log('=== MapView transformed data ===', {
        connections: transformedData.connections?.length || 0,
        poles: transformedData.poles?.length || 0,
        conductors: transformedData.conductors?.length || 0
      })
      setTransformedData(transformedData)
    }
  }, [networkData])
  
  
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
        onElementUpdate={onNetworkUpdate ? async () => { onNetworkUpdate() } : undefined}
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
