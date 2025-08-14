'use client'

import { useEffect, useRef, useState } from 'react'
import { Layers, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import dynamic from 'next/dynamic'

// Dynamically import Leaflet components to avoid SSR issues
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
)
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
)
const Rectangle = dynamic(
  () => import('react-leaflet').then((mod) => mod.Rectangle),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)
const Polyline = dynamic(
  () => import('react-leaflet').then((mod) => mod.Polyline),
  { ssr: false }
)
const ZoomControl = dynamic(
  () => import('react-leaflet').then((mod) => mod.ZoomControl),
  { ssr: false }
)

interface MapViewProps {
  site: string;
  networkData?: any;
  loading?: boolean;
}

interface NetworkData {
  poles: Array<{ id: string; lat: number; lng: number; type: 'MV' | 'LV'; validated: boolean; status: string }>
  connections: Array<{ id: string; lat: number; lng: number; status: string }>
  conductors: Array<{ id: string; from: string; to: string; type: 'backbone' | 'distribution' }>
  transformers: Array<{ id: string; lat: number; lng: number; capacity: number }>
}

export function MapView({ site }: MapViewProps) {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLayer, setSelectedLayer] = useState<'all' | 'poles' | 'conductors' | 'transformers'>('all')
  const mapRef = useRef<any>(null)

  // Status color mapping (consistent with uGridPLAN)
  const statusColors: { [key: string]: string } = {
    'as_designed': '#4CAF50',  // Green
    'as_built': '#2196F3',      // Blue
    'planned': '#FFC107',       // Amber
    'pending': '#FF9800',       // Orange
    'error': '#F44336',         // Red
    'default': '#9E9E9E'        // Grey
  }

  // Site center coordinates (example for KET)
  const siteCoordinates: Record<string, [number, number]> = {
    KET: [-29.8587, 28.7912],
    MAK: [-29.7521, 28.6234],
    LEB: [-29.9123, 28.8567],
    // Add more sites as needed
  }

  useEffect(() => {
    // Initialize Leaflet icon configuration
    if (typeof window !== 'undefined') {
      import('@/lib/leaflet-config')
    }
    
    // Simulate loading network data (will be replaced with API call)
    setLoading(true)
    setTimeout(() => {
      // Generate sample data based on site
      const center = siteCoordinates[site] || [-29.8587, 28.7912]
      
      // Generate sample poles
      const poles = Array.from({ length: 50 }, (_, i) => ({
        id: `${site}_POLE_${i + 1}`,
        lat: center[0] + (Math.random() - 0.5) * 0.02,
        lng: center[1] + (Math.random() - 0.5) * 0.02,
        type: i % 10 === 0 ? 'MV' as const : 'LV' as const,
        validated: Math.random() > 0.1,
        status: ['as_designed', 'as_built', 'planned', 'pending'][Math.floor(Math.random() * 4)]
      }))

      // Generate connections (customer connection points)
      const connections = Array.from({ length: 30 }, (_, i) => ({
        id: `${site}_CON_${i + 1}`,
        lat: center[0] + (Math.random() - 0.5) * 0.018,
        lng: center[1] + (Math.random() - 0.5) * 0.018,
        status: ['as_designed', 'as_built', 'planned', 'pending'][Math.floor(Math.random() * 4)]
      }))

      // Generate conductors connecting poles
      const conductors = poles.slice(0, -1).map((pole, i) => ({
        id: `${site}_COND_${i + 1}`,
        from: pole.id,
        to: poles[i + 1].id,
        type: pole.type === 'MV' ? 'backbone' as const : 'distribution' as const
      }))

      // Generate transformers at key locations
      const transformers = poles
        .filter(p => p.type === 'MV')
        .slice(0, 3)
        .map((pole, i) => ({
          id: `${site}_TX_${i + 1}`,
          lat: pole.lat,
          lng: pole.lng,
          capacity: 500
        }))

      setNetworkData({ poles, connections, conductors, transformers })
      setLoading(false)
    }, 500)
  }, [site])

  if (loading) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading network data...</p>
        </div>
      </div>
    )
  }

  const center = siteCoordinates[site] || [-29.8587, 28.7912]

  return (
    <div className="h-full w-full relative">
      {/* Map Controls */}
      <div className="absolute top-4 right-4 z-[1000] space-y-2">
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-1">
          <button
            onClick={() => setSelectedLayer('all')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              selectedLayer === 'all' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedLayer('poles')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              selectedLayer === 'poles' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Poles
          </button>
          <button
            onClick={() => setSelectedLayer('conductors')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              selectedLayer === 'conductors' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Lines
          </button>
          <button
            onClick={() => setSelectedLayer('transformers')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              selectedLayer === 'transformers' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Transformers
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg border border-gray-200 p-3">
        <h4 className="font-medium text-sm text-gray-900 mb-2">Legend</h4>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-xs text-gray-600">MV Pole</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-xs text-gray-600">LV Pole</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-xs text-gray-600">Transformer</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-0.5 bg-red-500"></div>
            <span className="text-xs text-gray-600">Backbone</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-0.5 bg-blue-500"></div>
            <span className="text-xs text-gray-600">Distribution</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <MapContainer
        ref={mapRef}
        center={center}
        zoom={14}
        style={{ height: '100%', width: '100%' }}
        minZoom={10}
        maxZoom={20}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        <ZoomControl position="bottomright" />

        {/* Render conductors with accurate positioning */}
        {networkData?.conductors?.map((conductor: any, idx: number) => {
          const fromPole = networkData.poles.find((p: any) => p.id === conductor.from)
          const toPole = networkData.poles.find((p: any) => p.id === conductor.to)
          
          if (!fromPole || !toPole) return null
          
          return (
            <Polyline
              key={`conductor-${idx}`}
              positions={[
                [fromPole.lat, fromPole.lng],
                [toPole.lat, toPole.lng]
              ]}
              color={conductor.type === 'backbone' ? '#FF5722' : '#2196F3'}
              weight={conductor.type === 'backbone' ? 3 : 2}
              opacity={0.8}
              smoothFactor={1}
            />
          )
        })}

        {/* Render poles as circles */}
        {networkData && (selectedLayer === 'all' || selectedLayer === 'poles') && 
          networkData.poles.map((pole) => (
            <CircleMarker
              key={pole.id}
              center={[pole.lat, pole.lng]}
              radius={8}
              fillColor={statusColors[pole.status] || statusColors.default}
              fillOpacity={0.8}
              color="#333"
              weight={1}
            >
              <Popup>
                <div className="p-2 text-sm">
                  <p className="font-medium">{pole.id}</p>
                  <p className="text-gray-600">Type: {pole.type}</p>
                  <p className="text-gray-600">
                    Status: <span style={{ color: statusColors[pole.status] }}>{pole.status}</span>
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          ))
        }
        
        {/* Render connections as squares */}
        {networkData && (selectedLayer === 'all') && 
          networkData.connections.map((conn) => (
            <Rectangle
              key={conn.id}
              bounds={[
                [conn.lat - 0.0001, conn.lng - 0.0001],
                [conn.lat + 0.0001, conn.lng + 0.0001]
              ]}
              fillColor={statusColors[conn.status] || statusColors.default}
              fillOpacity={0.8}
              color="#333"
              weight={1}
            >
              <Popup>
                <div className="p-2 text-sm">
                  <p className="font-medium">{conn.id}</p>
                  <p className="text-gray-600">Type: Connection</p>
                  <p className="text-gray-600">
                    Status: <span style={{ color: statusColors[conn.status] }}>{conn.status}</span>
                  </p>
                </div>
              </Popup>
            </Rectangle>
          ))
        }
        
        {/* Render transformers */}
        {networkData && (selectedLayer === 'all' || selectedLayer === 'transformers') && 
          networkData.transformers.map((transformer) => (
            <Marker
              key={transformer.id}
              position={[transformer.lat, transformer.lng]}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-medium">{transformer.id}</p>
                  <p className="text-gray-600">Capacity: {transformer.capacity} kVA</p>
                </div>
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  )
}
