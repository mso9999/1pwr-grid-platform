'use client'

import { useEffect, useState, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Zap } from 'lucide-react'
import { LayerControls, LayerVisibility } from './LayerControls'
import { ElementDetailPanel, ElementDetail } from './ElementDetailPanel'
import { SC1_COLORS, SC3_COLORS, SC4_COLORS, getLineType } from '@/utils/statusCodes'

// Fix Leaflet default icon issue
if (typeof window !== 'undefined') {
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  })
}

export interface ClientMapProps {
  networkData?: any
  onElementUpdate?: (element: any) => void
  loading?: boolean
}

export function ClientMap({ networkData, onElementUpdate, loading }: ClientMapProps) {
  console.log('ClientMap received props:', { 
    hasNetworkData: !!networkData,
    dataType: typeof networkData,
    keys: networkData ? Object.keys(networkData) : 'none',
    loading 
  })
  const [map, setMap] = useState<L.Map | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    poles: true,
    connections: true,
    mvLines: true,
    lvLines: true,
    dropLines: true,
    transformers: true,
    generation: true
  })
  const [selectedElement, setSelectedElement] = useState<any>(null)
  const [elementNames, setElementNames] = useState<Map<string, string>>(new Map())

  const layerGroupsRef = useRef<{
    poles?: L.LayerGroup
    connections?: L.LayerGroup
    mvLines?: L.LayerGroup
    lvLines?: L.LayerGroup
    dropLines?: L.LayerGroup
    transformers?: L.LayerGroup
    generation?: L.LayerGroup
  }>({})

  const [elementCounts, setElementCounts] = useState({
    poles: 0,
    connections: 0,
    mvLines: 0,
    lvLines: 0,
    dropLines: 0,
    transformers: 0,
    generation: 0
  })

  // Initialize Leaflet map
  useEffect(() => {
    if (typeof window === 'undefined') return

    let retryCount = 0
    const maxRetries = 10
    
    const initMap = () => {
      const container = document.getElementById('map')
      if (!container) {
        console.log('Map container not found')
        if (retryCount < maxRetries) {
          retryCount++
          setTimeout(initMap, 200)
        }
        return
      }
      
      // Check if map already exists
      if (container.hasAttribute('data-map-initialized')) {
        console.log('Map already initialized')
        return
      }
      
      // Log current styles
      const computedStyle = window.getComputedStyle(container)
      console.log('Container computed styles:', {
        position: computedStyle.position,
        top: computedStyle.top,
        left: computedStyle.left,
        right: computedStyle.right,
        bottom: computedStyle.bottom,
        width: computedStyle.width,
        height: computedStyle.height,
        display: computedStyle.display,
        zIndex: computedStyle.zIndex
      })
      console.log('Container inline styles:', container.style.cssText)
      console.log('Container parent:', container.parentElement)
      
      // Ensure container has dimensions (fixed positioning should provide them)
      if (container.offsetWidth === 0 || container.offsetHeight === 0) {
        console.log(`Container dimensions: ${container.offsetWidth}x${container.offsetHeight}, retry ${retryCount}/${maxRetries}`)
        
        if (retryCount < maxRetries) {
          retryCount++
          setTimeout(initMap, 300)
        }
        return
      }
      
      container.setAttribute('data-map-initialized', 'true')

      console.log('Initializing Leaflet map')
      console.log('Map container:', container)
      console.log('Container dimensions:', container.offsetWidth, 'x', container.offsetHeight)
      
      // Start with a default view, will be updated when data loads
      const newMap = L.map('map', {
        center: [-30.078, 27.859],
        zoom: 13,
        zoomControl: true
      })
      
      const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      })
      
      tileLayer.on('load', () => {
        console.log('Map tiles loaded successfully')
      })
      
      tileLayer.on('tileerror', (error) => {
        console.error('Tile load error:', error)
      })
      
      tileLayer.addTo(newMap)
      console.log('Tile layer added to map')
      
      // Force map to recalculate its size
      setTimeout(() => {
        console.log('Invalidating map size')
        newMap.invalidateSize()
        const size = newMap.getSize()
        console.log('Map size after invalidate:', size.x, 'x', size.y)
      }, 100)

      // Initialize layer groups
      layerGroupsRef.current = {
        poles: L.layerGroup().addTo(newMap),
        connections: L.layerGroup().addTo(newMap),
        mvLines: L.layerGroup().addTo(newMap),
        lvLines: L.layerGroup().addTo(newMap),
        dropLines: L.layerGroup().addTo(newMap),
        transformers: L.layerGroup().addTo(newMap),
        generation: L.layerGroup().addTo(newMap)
      }

      // Add resize observer with proper cleanup
      const resizeObserver = new ResizeObserver(() => {
        if (newMap && newMap.getContainer()) {
          console.log('Container resized, invalidating map size')
          try {
            newMap.invalidateSize()
          } catch (e) {
            console.warn('Error invalidating map size:', e)
          }
        }
      })
      resizeObserver.observe(container)
      
      // Mark container as having resize observer
      container.setAttribute('data-resize-observer', 'true')
      
      // Store reference for cleanup
      mapRef.current = newMap
      resizeObserverRef.current = resizeObserver
      
      setMap(newMap)
    }
    
    // Start initialization
    const timer = setTimeout(initMap, 100)

    return () => {
      clearTimeout(timer)
    }
  }, [])  // Empty dependency array - only run once

  // Clean up map on unmount
  useEffect(() => {
    return () => {
      console.log('Cleaning up map on unmount')
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
      setMap(null)
    }
  }, [])

  // Update layer visibility
  useEffect(() => {
    if (!map || !layerGroupsRef.current) return

    Object.entries(layerVisibility).forEach(([key, visible]) => {
      const layerGroup = layerGroupsRef.current[key as keyof typeof layerGroupsRef.current]
      if (layerGroup) {
        if (visible) {
          map.addLayer(layerGroup)
        } else {
          map.removeLayer(layerGroup)
        }
      }
    })
  }, [layerVisibility, map])

  // Render network data
  useEffect(() => {
    console.log('Network data effect - map:', !!map, 'networkData:', networkData)
    if (!map || !networkData) {
      console.log('Cannot render: map=', !!map, 'networkData=', !!networkData, 'data keys:', networkData ? Object.keys(networkData) : 'none')
      return
    }

    const data = networkData
    console.log('Rendering network data on map:', {
      poles: data.poles?.length || 0,
      connections: data.connections?.length || 0,
      conductors: data.conductors?.length || 0,
      transformers: data.transformers?.length || 0
    })
    
    // Calculate bounds from data
    const bounds = L.latLngBounds([])
    let hasValidCoords = false

    // Clear existing layers
    Object.values(layerGroupsRef.current).forEach(group => {
      if (group) group.clearLayers()
    })

    const names = new Set<string>()
    const counts = {
      poles: 0,
      connections: 0,
      mvLines: 0,
      lvLines: 0,
      dropLines: 0,
      transformers: 0,
      generation: 0
    }

    // Add connections
    if (data.connections && layerGroupsRef.current.connections) {
      data.connections.forEach((connection: any) => {
        if (connection.lat && connection.lng) {
          bounds.extend([connection.lat, connection.lng])
          hasValidCoords = true
          const color = SC3_COLORS[connection.st_code_3 || 0] || '#808080'
          const marker = L.circleMarker([connection.lat, connection.lng], {
            radius: 6,
            fillColor: color,
            color: '#333',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
          })
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'connection',
              id: connection.id,
              name: connection.name,
              data: connection
            })
          })
          
          marker.bindPopup(`Connection: ${connection.name || connection.id}`)
          if (layerGroupsRef.current.connections) {
            marker.addTo(layerGroupsRef.current.connections)
          }
          
          names.add(connection.name || connection.id)
          counts.connections++
        }
      })
    }

    // Add poles
    if (data.poles && layerGroupsRef.current.poles) {
      data.poles.forEach((pole: any) => {
        if (pole.lat && pole.lng) {
          bounds.extend([pole.lat, pole.lng])
          hasValidCoords = true
          const color = SC1_COLORS[pole.st_code_1 || 0] || '#808080'
          const marker = L.circleMarker([pole.lat, pole.lng], {
            radius: 8,
            fillColor: color,
            color: '#000',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
          })
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'pole',
              id: pole.id,
              name: pole.name,
              data: pole
            })
          })
          
          marker.bindPopup(`Pole: ${pole.name || pole.id}`)
          if (layerGroupsRef.current.poles) {
            marker.addTo(layerGroupsRef.current.poles)
          }
          
          names.add(pole.name || pole.id)
          counts.poles++
        }
      })
    }

    // Add conductors
    if (data.conductors) {
      // Create node lookup maps
      const nodeMap = new Map<string, [number, number]>()
      
      data.poles?.forEach((pole: any) => {
        if (pole.lat && pole.lng) {
          nodeMap.set(pole.id, [pole.lat, pole.lng])
        }
      })
      
      data.connections?.forEach((conn: any) => {
        if (conn.lat && conn.lng) {
          nodeMap.set(conn.id, [conn.lat, conn.lng])
        }
      })

      data.conductors.forEach((conductor: any) => {
        const fromCoords = nodeMap.get(conductor.from)
        const toCoords = nodeMap.get(conductor.to)
        
        if (fromCoords && toCoords) {
          const lineType = getLineType(
            conductor,
            data.poles || [],
            data.connections || []
          )
          
          let layerGroup: L.LayerGroup | undefined
          let color = '#808080'
          
          switch (lineType) {
            case 'mv':
              layerGroup = layerGroupsRef.current.mvLines
              color = '#FF0000'
              counts.mvLines++
              break
            case 'lv':
              layerGroup = layerGroupsRef.current.lvLines
              color = '#0000FF'
              counts.lvLines++
              break
            case 'drop':
              layerGroup = layerGroupsRef.current.dropLines
              color = '#00FF00'
              counts.dropLines++
              break
          }
          
          if (layerGroup) {
            const polyline = L.polyline([fromCoords, toCoords], {
              color: SC4_COLORS[conductor.st_code_4 || 0] || color,
              weight: 2,
              opacity: 0.8
            })
            
            polyline.on('click', () => {
              setSelectedElement({
                type: 'conductor',
                id: conductor.id,
                name: conductor.name,
                data: { ...conductor, line_type: lineType }
              })
            })
            
            polyline.bindPopup(`${lineType.toUpperCase()} Line: ${conductor.id}`)
            polyline.addTo(layerGroup)
            
            names.add(conductor.name || conductor.id)
          }
        }
      })
    }

    // Add transformers
    if (data.transformers && layerGroupsRef.current.transformers) {
      data.transformers.forEach((transformer: any) => {
        if (transformer.lat && transformer.lng) {
          const marker = L.marker([transformer.lat, transformer.lng])
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'transformer',
              id: transformer.id,
              name: transformer.name,
              data: transformer
            })
          })
          
          marker.bindPopup(`Transformer: ${transformer.name || transformer.id}`)
          if (layerGroupsRef.current.transformers) {
            marker.addTo(layerGroupsRef.current.transformers)
          }
          
          names.add(transformer.name || transformer.id)
          counts.transformers++
        }
      })
    }

    setElementNames(names)
    setElementCounts(counts)

    // Fit map to data bounds
    if (hasValidCoords && bounds.isValid()) {
      console.log('Fitting map to bounds:', bounds)
      map.fitBounds(bounds, { padding: [50, 50] })
      // Force map to refresh
      setTimeout(() => {
        map.invalidateSize()
        console.log('Map size invalidated after data load')
      }, 200)
    }
  }, [networkData, map])

  const handleElementUpdate = async (id: string, updates: any) => {
    if (onElementUpdate) {
      return await onElementUpdate(id, updates)
    }
    
    // Local update only
    if (networkData) {
      // Update poles
      if (networkData.poles) {
        const pole = networkData.poles.find((p: any) => p.id === id)
        if (pole) {
          pole.name = updates.name
        }
      }
      
      // Update connections
      if (networkData.connections) {
        const connection = networkData.connections.find((c: any) => c.id === id)
        if (connection) {
          connection.name = updates.name
        }
      }
      
      // Update conductors
      if (networkData.conductors) {
        const conductor = networkData.conductors.find((c: any) => c.id === id)
        if (conductor) {
          conductor.name = updates.name
        }
      }
    }
    
    return true
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Zap className="h-12 w-12 text-primary mx-auto mb-4 animate-pulse" />
          <p className="text-lg font-medium">Loading network data...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div 
        id="map" 
        style={{ 
          position: 'fixed', 
          top: '64px',
          left: '256px', 
          right: '0', 
          bottom: '0', 
          width: 'calc(100vw - 256px)',
          height: 'calc(100vh - 64px)',
          zIndex: 10,
          backgroundColor: '#f3f4f6'
        }} 
      />
      
      <LayerControls
        visibility={layerVisibility}
        onVisibilityChange={setLayerVisibility}
        counts={elementCounts}
      />
      
      <ElementDetailPanel
        element={selectedElement}
        onClose={() => setSelectedElement(null)}
        onUpdate={handleElementUpdate}
        existingNames={elementNames}
      />
    </>
  )
}
