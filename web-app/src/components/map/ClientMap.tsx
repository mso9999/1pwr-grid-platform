'use client'

import { useEffect, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Zap } from 'lucide-react'

// Fix Leaflet default icon issue
if (typeof window !== 'undefined') {
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  })
}

interface MapViewProps {
  site: string
  networkData?: any
  loading?: boolean
}

export function ClientMap({ site, networkData: propNetworkData, loading: propLoading }: MapViewProps) {
  const [map, setMap] = useState<L.Map | null>(null)
  const [selectedLayer, setSelectedLayer] = useState<'all' | 'poles' | 'conductors' | 'transformers'>('all')
  const [voltageOverlayEnabled, setVoltageOverlayEnabled] = useState(false)

  // Desktop uGridPLAN color specifications from MGD045V03 SOP and desktop code
  const statusCode1Colors: { [key: number]: string } = {
    0: '#FFFFFF', // uGridNET output (white)
    1: '#FFFF00', // Updated planned location (yellow)
    2: '#ccffd2', // Marked with label onsite (light green)
    3: '#FF0000', // Consent withheld (red)
    4: '#95F985', // Consented (green)
    5: '#000000', // Hard Rock (black)
    6: '#38fb14', // Excavated (bright green)
    7: '#26d102', // Pole planted (green)
    8: '#018501', // Poletop dressed (dark green)
    9: '#014803', // Conductor attached (very dark green)
  };

  const statusCode3Colors: { [key: number]: string } = {
    0: '#adadff', // uGridNET Survey (light blue)
    1: '#FFD700', // Updated Location (gold)
    2: '#DAA520', // Connection fee paid (goldenrod)
    3: '#D8BFD8', // Ready board paid (thistle)
    4: '#DDA0DD', // Contract Signed (plum)
    5: '#BA55D3', // DB Tested (medium orchid)
    6: '#9370DB', // Ready Board Installed (medium purple)
    7: '#696969', // Airdac Terminated (dim gray)
    8: '#191970', // Customer training (midnight blue)
    9: '#303030', // Connection commissioned (gray)
  };

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return

    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      console.log('Initializing Leaflet map')
      
      // Ensure container exists and has size
      const container = document.getElementById('map-container')
      if (!container) {
        console.error('Map container not found')
        return
      }
      
      console.log('Container dimensions:', container.offsetWidth, 'x', container.offsetHeight)
      
      // If container has no size, set it explicitly
      if (container.offsetHeight === 0) {
        console.warn('Container has no height, setting to 100vh')
        container.style.height = '100vh'
      }

      try {
        // Create map
        const mapInstance = L.map('map-container').setView([-30.07, 27.85], 14)
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(mapInstance)

        setMap(mapInstance)
        console.log('Map created successfully');
        
        // Store map instance globally for debugging
        (window as any).debugMap = mapInstance
      } catch (error) {
        console.error('Error creating map:', error)
      }
    }, 100)

    // Cleanup
    return () => {
      clearTimeout(timer)
      if (map) {
        map.remove()
      }
    }
  }, [])

  useEffect(() => {
    console.log('Network data effect - map:', !!map, 'data:', !!propNetworkData)
    
    if (!map || !propNetworkData) {
      console.log('Skipping network data - map or data not ready')
      return
    }

    console.log('Adding network data to map', {
      poles: propNetworkData.poles?.length || 0,
      conductors: propNetworkData.conductors?.length || 0,
      connections: propNetworkData.connections?.length || 0
    })

    // Clear existing layers
    map.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer)
      }
    })

    // Add poles and connections with visual differentiation
    if (propNetworkData.poles && (selectedLayer === 'all' || selectedLayer === 'poles')) {
      propNetworkData.poles.forEach((pole: any) => {
        const lat = pole.latitude || pole.gps_lat || pole.lat
        const lng = pole.longitude || pole.gps_lng || pole.lng
        
        if (!lat || !lng) return
        
        // Check if this is a customer connection
        if (pole.pole_type === 'CUSTOMER_CONNECTION' || pole.is_connection) {
          // Customer connections show as squares (per desktop spec)
          const stCode3 = pole.st_code_3 || 0
          const connectionColor = statusCode3Colors[stCode3] || '#adadff'
          
          // Create square marker for customer connections per desktop spec
          // Increased size for better visibility to match desktop
          const squareIcon = L.divIcon({
            html: `<div style="width: 16px; height: 16px; background: ${connectionColor}; border: 1px solid #000;"></div>`,
            className: 'square-marker',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          })
          
          const marker = L.marker([lat, lng], { icon: squareIcon })
            .bindPopup(`
              <b>Customer Connection</b><br/>
              ID: ${pole.pole_id || pole.id}<br/>
              Type: ${pole.pole_type}<br/>
              Status Code 3: ${stCode3}
            `)
          
          map.addLayer(marker)
        } else {
          // Regular poles - use status code 1 colors per desktop spec
          const stCode1 = pole.st_code_1 || 0
          let color = statusCode1Colors[stCode1] || '#FFFFFF'
          
          // Desktop spec: white poles need black outline, others use same color
          let strokeColor = stCode1 === 0 ? '#000000' : color
          let fillOpacity = 1 // Desktop uses full opacity
          let weight = 1 // Desktop uses thin border
          
          // Desktop spec: MV poles are larger than LV poles
          // Increased sizes for better visibility to match desktop
          let radius = 6 // Default LV size (was 2, now 3x larger)
          if (pole.pole_type === 'MV' || pole.subnetwork?.includes('MV')) {
            radius = 10 // MV poles are larger (was 4, now 2.5x larger)
          }
          
          const markerOptions: any = {
            radius: radius,
            fillColor: color,
            color: strokeColor,
            weight: weight,
            opacity: 1,
            fillOpacity: fillOpacity
          }
          
          const marker = L.circleMarker([lat, lng], markerOptions)
            .bindPopup(`
              <b>Pole</b><br/>
              ID: ${pole.pole_id || pole.id}<br/>
              Type: ${pole.pole_type || 'LV'}<br/>
              Class: ${pole.pole_class || pole.angle_class || 'N/A'}<br/>
              Status Code 1: ${stCode1}<br/>
              Status: ${pole.status || 'as_designed'}<br/>
              Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}
            `)
          
          map.addLayer(marker)
        }
      })
    }

    // Add conductors
    if (propNetworkData.conductors && (selectedLayer === 'all' || selectedLayer === 'conductors')) {
      console.log(`Processing ${propNetworkData.conductors.length} conductors`)
      let conductorsRendered = 0
      let conductorsSkipped = 0
      
      propNetworkData.conductors.forEach((conductor: any, idx: number) => {
        // Try multiple field names for compatibility
        const fromRef = conductor.from_pole || conductor.from
        const toRef = conductor.to_pole || conductor.to
        
        if (idx < 3) {
          console.log(`Conductor ${idx}: from="${fromRef}" to="${toRef}"`)
        }
        
        const fromPole = propNetworkData.poles?.find((p: any) => 
          p.pole_id === fromRef || p.id === fromRef
        )
        const toPole = propNetworkData.poles?.find((p: any) => 
          p.pole_id === toRef || p.id === toRef
        )
        
        if (fromPole && toPole) {
          const fromLat = fromPole.latitude || fromPole.gps_lat || fromPole.lat
          const fromLng = fromPole.longitude || fromPole.gps_lng || fromPole.lng
          const toLat = toPole.latitude || toPole.gps_lat || toPole.lat
          const toLng = toPole.longitude || toPole.gps_lng || toPole.lng
          
          if (fromLat && fromLng && toLat && toLng) {
            // Desktop spec: MV lines are thicker and red, LV lines are thinner and black
            let color = '#000000' // Black for LV (desktop default)
            let weight = 1.5 // Thin for LV
            let dashArray = ''
            let opacity = 1
            
            // Check if MV or LV based on conductor type or connected poles
            const isMV = conductor.conductor_type?.includes('MV') || 
                        fromPole.pole_type?.includes('MV') || 
                        toPole.pole_type?.includes('MV') ||
                        fromPole.subnetwork?.includes('MV') ||
                        toPole.subnetwork?.includes('MV')
            
            if (isMV) {
              color = '#FF0000' // Red for MV lines (desktop spec)
              weight = 2.5 // Thicker for MV
            }
            
            // Desktop spec: Use status code 4 for conductor status
            // 0 = uGridNET output (dashed), 3+ = installed (solid)
            const stCode4 = conductor.st_code_4 || 0
            if (stCode4 === 0) {
              dashArray = '5, 5' // Dashed for uninstalled
              opacity = 0.7
            } else if (stCode4 >= 3) {
              dashArray = '' // Solid for installed
              opacity = 1
            } else {
              dashArray = '3, 3' // Light dash for in-progress
              opacity = 0.8
            }
            
            const polyline = L.polyline(
              [[fromLat, fromLng], [toLat, toLng]], 
              { 
                color: color,
                weight: weight,
                opacity: opacity,
                dashArray: dashArray
              }
            )
            
            const conductorId = conductor.conductor_id || conductor.id || 'Unknown'
            const conductorType = conductor.conductor_type || (isMV ? 'MV' : 'LV')
            const length = conductor.length || 'N/A'
            const status = conductor.status || 'as_designed'
            
            polyline.bindPopup(`
              <div style="min-width: 200px;">
                <strong>Conductor: ${conductorId}</strong><br/>
                <hr style="margin: 5px 0;"/>
                <b>Type:</b> ${conductorType}<br/>
                <b>Status:</b> ${status}<br/>
                <b>From:</b> ${fromRef}<br/>
                <b>To:</b> ${toRef}<br/>
                <b>Length:</b> ${length}m
              </div>
            `)
            
            // Add the conductor to the map!
            map.addLayer(polyline)
            
            conductorsRendered++
          } else {
            conductorsSkipped++
            if (idx < 3) {
              console.log(`Skipped conductor ${idx}: missing coordinates`)
            }
          }
        } else {
          conductorsSkipped++
          if (idx < 3) {
            console.log(`Skipped conductor ${idx}: fromPole=${!!fromPole}, toPole=${!!toPole}`)
          }
        }
      })
      console.log(`Conductors rendered: ${conductorsRendered}, skipped: ${conductorsSkipped}`)
    }

    // Add connections
    if (propNetworkData.connections) {
      propNetworkData.connections.forEach((connection: any) => {
        const lat = connection.gps_lat || connection.latitude || connection.lat
        const lng = connection.gps_lng || connection.longitude || connection.lng
        if (lat && lng) {
          L.circleMarker([lat, lng], {
            radius: 3,
            fillColor: '#4CAF50',
            fillOpacity: 0.8,
            color: '#fff',
            weight: 1
          })
          .bindPopup(`<b>${connection.survey_id}</b><br>Status: ${connection.status || 'active'}`)
          .addTo(map)
        }
      })
    }

    // Fit map to bounds if we have data
    if (propNetworkData.poles?.length || propNetworkData.conductors?.length) {
      const bounds: [number, number][] = []
      propNetworkData.poles?.forEach((pole: any) => {
        const lat = pole.latitude || pole.gps_lat || pole.lat
        const lng = pole.longitude || pole.gps_lng || pole.lng
        if (lat && lng) {
          bounds.push([lat, lng])
        }
      })
      if (bounds.length > 0) {
        map.fitBounds(bounds)
      }
    }
  }, [map, propNetworkData, selectedLayer])

  if (propLoading) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading network data...</p>
        </div>
      </div>
    )
  }

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

      {/* Map Container */}
      <div id="map-container" className="absolute inset-0 z-0" />
    </div>
  )
}
