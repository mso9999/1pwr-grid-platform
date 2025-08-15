'use client'

import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, CircleMarker, Popup, ZoomControl } from 'react-leaflet'
import { Zap } from 'lucide-react'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix Leaflet icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

interface MapViewProps {
  site: string
  networkData?: any
  loading?: boolean
}

export function MapView({ site, networkData: propNetworkData, loading: propLoading }: MapViewProps) {
  console.log('MapViewFixed component mounting', { site, propNetworkData, propLoading })
  
  const [networkData, setNetworkData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLayer, setSelectedLayer] = useState<'all' | 'poles' | 'conductors' | 'transformers'>('all')
  const [voltageOverlayEnabled, setVoltageOverlayEnabled] = useState(false)

  // Calculate map center from actual data
  const calculateCenter = (data: any): [number, number] => {
    if (!data || !data.poles || data.poles.length === 0) {
      return [-30.07, 27.85] // Default KET coordinates
    }
    
    let totalLat = 0
    let totalLng = 0
    let count = 0
    
    data.poles.forEach((pole: any) => {
      if (pole.lat && pole.lng) {
        totalLat += pole.lat
        totalLng += pole.lng
        count++
      }
    })
    
    if (count === 0) return [-30.07, 27.85]
    
    return [totalLat / count, totalLng / count]
  }

  useEffect(() => {
    // Use network data from props if available
    if (propNetworkData && propNetworkData.data) {
      const data = propNetworkData.data
      console.log('MapView received data:', {
        poles: data.poles?.length || 0,
        connections: data.connections?.length || 0,
        conductors: data.conductors?.length || 0,
        samplePole: data.poles?.[0]
      })
      
      // Transform backend data to match frontend format
      const transformedData = {
        poles: data.poles?.map((pole: any) => ({
          id: pole.pole_id || pole.id,
          lat: pole.latitude || pole.gps_lat || pole.lat,
          lng: pole.longitude || pole.gps_lng || pole.lng,
          type: pole.pole_type || 'LV',
          validated: pole.validated || false,
          status: pole.status || 'as_designed'
        })) || [],
        connections: data.connections?.map((conn: any) => ({
          id: conn.survey_id || conn.id,
          lat: conn.gps_lat || conn.latitude || conn.lat,
          lng: conn.gps_lng || conn.longitude || conn.lng,
          status: conn.status || 'active'
        })) || [],
        conductors: data.conductors?.map((cond: any) => ({
          id: cond.conductor_id || cond.id,
          from: cond.from_pole || cond.from,
          to: cond.to_pole || cond.to,
          type: cond.conductor_type || 'distribution'
        })) || [],
        transformers: data.transformers || []
      }
      
      setNetworkData(transformedData)
      setLoading(false)
    } else {
      setLoading(propLoading || false)
    }
  }, [propNetworkData, propLoading])

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

  const center: [number, number] = networkData ? calculateCenter(networkData) : [-30.07, 27.85]

  return (
    <div className="h-full w-full relative">
      {/* Map Controls */}
      <div className="absolute top-4 right-4 z-[1000] space-y-2">
        {/* Voltage Overlay Toggle */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-2">
          <button
            onClick={() => setVoltageOverlayEnabled(!voltageOverlayEnabled)}
            className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition-colors w-full ${
              voltageOverlayEnabled ? 'bg-yellow-100 text-yellow-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Zap className="w-4 h-4" />
            {voltageOverlayEnabled ? 'Voltage ON' : 'Voltage OFF'}
          </button>
        </div>
        
        {/* Layer Controls */}
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

      {/* Map Container with explicit height */}
      <div className="absolute inset-0 z-0">
        <MapContainer
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

          {/* Render conductors */}
          {(selectedLayer === 'all' || selectedLayer === 'conductors') && 
            networkData?.conductors?.map((conductor: any, idx: number) => {
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
                />
              )
            })}

          {/* Render poles */}
          {(selectedLayer === 'all' || selectedLayer === 'poles') && 
            networkData?.poles?.map((pole: any, idx: number) => (
              <CircleMarker
                key={`pole-${idx}`}
                center={[pole.lat, pole.lng]}
                radius={pole.type === 'MV' ? 6 : 4}
                fillColor={pole.type === 'MV' ? '#FF5722' : '#2196F3'}
                fillOpacity={0.8}
                color="#fff"
                weight={2}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-semibold">{pole.id}</p>
                    <p>Type: {pole.type}</p>
                    <p>Status: {pole.status}</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

          {/* Render connections */}
          {networkData?.connections?.map((connection: any, idx: number) => (
            <CircleMarker
              key={`connection-${idx}`}
              center={[connection.lat, connection.lng]}
              radius={3}
              fillColor="#4CAF50"
              fillOpacity={0.8}
              color="#fff"
              weight={1}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-semibold">{connection.id}</p>
                  <p>Status: {connection.status}</p>
                </div>
              </Popup>
            </CircleMarker>
          ))}

          {/* Render transformers */}
          {(selectedLayer === 'all' || selectedLayer === 'transformers') && 
            networkData?.transformers?.map((transformer: any, idx: number) => (
              <Marker
                key={`transformer-${idx}`}
                position={[transformer.lat, transformer.lng]}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-semibold">Transformer {transformer.id}</p>
                    <p>Capacity: {transformer.capacity} kVA</p>
                  </div>
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </div>
    </div>
  )
}
