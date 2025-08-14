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
const Polyline = dynamic(
  () => import('react-leaflet').then((mod) => mod.Polyline),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)

interface MapViewProps {
  site: string
}

interface NetworkData {
  poles: Array<{ id: string; lat: number; lng: number; type: 'MV' | 'LV'; validated: boolean }>
  conductors: Array<{ id: string; from: [number, number]; to: [number, number]; type: 'backbone' | 'distribution' }>
  transformers: Array<{ id: string; lat: number; lng: number; capacity: number }>
}

export function MapView({ site }: MapViewProps) {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLayer, setSelectedLayer] = useState<'all' | 'poles' | 'conductors' | 'transformers'>('all')
  const mapRef = useRef<any>(null)

  // Site center coordinates (example for KET)
  const siteCoordinates: Record<string, [number, number]> = {
    KET: [-29.8587, 28.7912],
    MAK: [-29.7521, 28.6234],
    LEB: [-29.9123, 28.8567],
    // Add more sites as needed
  }

  useEffect(() => {
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
        validated: Math.random() > 0.1
      }))

      // Generate conductors connecting poles
      const conductors = poles.slice(0, -1).map((pole, i) => ({
        id: `${site}_COND_${i + 1}`,
        from: [pole.lat, pole.lng] as [number, number],
        to: [poles[i + 1].lat, poles[i + 1].lng] as [number, number],
        type: pole.type === 'MV' ? 'backbone' as const : 'distribution' as const
      }))

      // Generate transformers
      const transformers = Array.from({ length: 3 }, (_, i) => ({
        id: `TX_${site}_${i + 1}`,
        lat: center[0] + (Math.random() - 0.5) * 0.015,
        lng: center[1] + (Math.random() - 0.5) * 0.015,
        capacity: [100, 200, 315][i % 3]
      }))

      setNetworkData({ poles, conductors, transformers })
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
    <div className="relative w-full h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
        center={center}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* Render conductors/lines */}
        {networkData && (selectedLayer === 'all' || selectedLayer === 'conductors') && 
          networkData.conductors.map((conductor) => (
            <Polyline
              key={conductor.id}
              positions={[conductor.from, conductor.to]}
              color={conductor.type === 'backbone' ? '#ef4444' : '#3b82f6'}
              weight={conductor.type === 'backbone' ? 3 : 2}
              opacity={0.8}
            />
          ))
        }

        {/* Render poles */}
        {networkData && (selectedLayer === 'all' || selectedLayer === 'poles') && 
          networkData.poles.map((pole) => {
            const icon = new (window as any).L.DivIcon({
              className: 'custom-marker',
              html: `<div style="
                width: 12px;
                height: 12px;
                background-color: ${pole.type === 'MV' ? '#ef4444' : '#3b82f6'};
                border: 2px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              "></div>`,
              iconSize: [12, 12],
              iconAnchor: [6, 6]
            })

            return (
              <Marker
                key={pole.id}
                position={[pole.lat, pole.lng]}
                icon={icon}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-medium">{pole.id}</p>
                    <p className="text-gray-600">Type: {pole.type}</p>
                    <p className="text-gray-600">
                      Status: {pole.validated ? 
                        <span className="text-green-600">Validated</span> : 
                        <span className="text-orange-600">Pending</span>
                      }
                    </p>
                  </div>
                </Popup>
              </Marker>
            )
          })}

        {/* Render transformers */}
        {networkData && (selectedLayer === 'all' || selectedLayer === 'transformers') && 
          networkData.transformers.map((transformer) => {
            const icon = new (window as any).L.DivIcon({
              className: 'custom-marker',
              html: `<div style="
                width: 16px;
                height: 16px;
                background-color: #8b5cf6;
                border: 2px solid white;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              "></div>`,
              iconSize: [16, 16],
              iconAnchor: [8, 8]
            })

            return (
              <Marker
                key={transformer.id}
                position={[transformer.lat, transformer.lng]}
                icon={icon}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-medium">{transformer.id}</p>
                    <p className="text-gray-600">Capacity: {transformer.capacity} kVA</p>
                  </div>
                </Popup>
              </Marker>
            )
          })}
      </MapContainer>
    </div>
  )
}
