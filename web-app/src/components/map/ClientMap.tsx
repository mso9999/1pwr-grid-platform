'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Button } from '@/components/ui/button';
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet'
import { LayerControls } from './LayerControls'
import { ElementDetailPanel } from './ElementDetailPanel'
import { MapEditToolbar } from './MapEditToolbar'
import { ElementEditDialog } from './ElementEditDialog'
import { SearchPanel } from './SearchPanel'
import { GenerationSiteEditor } from './GenerationSiteEditor'
import { toast } from 'sonner'
import { 
  SC1_COLORS, 
  SC1_DESCRIPTIONS,
  SC3_COLORS, 
  SC3_DESCRIPTIONS,
  SC4_COLORS, 
  SC4_DESCRIPTIONS,
  getLineType 
} from '@/utils/statusCodes'
import { Crosshair, Search, Layers, Eye, EyeOff, Zap, Activity } from 'lucide-react';

type EditMode = 'select' | 'add-pole' | 'add-connection' | 'add-conductor' | 'split-conductor' | 'delete';

interface ElementDetail {
  type: 'pole' | 'connection' | 'conductor' | 'transformer' | 'generation';
  id: string;
  data: any;
}

interface LayerVisibility {
  poles: boolean;
  connections: boolean;
  mvLines: boolean;
  lvLines: boolean;
  dropLines: boolean;
  transformers: boolean;
  generation: boolean;
}

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
  onElementUpdate?: () => void
  loading?: boolean
}

export function ClientMap({ networkData, onElementUpdate, loading }: ClientMapProps) {
  console.log('ClientMap received props:', { 
    hasNetworkData: !!networkData,
    keys: networkData ? Object.keys(networkData) : 'none',
    loading 
  })
  const [map, setMap] = useState<L.Map | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)
  const [selectedElement, setSelectedElement] = useState<ElementDetail | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingElement, setEditingElement] = useState<ElementDetail | null>(null)
  const [showVoltageOverlay, setShowVoltageOverlay] = useState(false)
  const [editMode, setEditMode] = useState<EditMode>('select')
  const [pendingPoleLocation, setPendingPoleLocation] = useState<{lat: number, lng: number} | null>(null)
  const [pendingConnectionLocation, setPendingConnectionLocation] = useState<{lat: number, lng: number} | null>(null)
  const [showSearchPanel, setShowSearchPanel] = useState(false)
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    poles: true,
    connections: true,
    mvLines: true,
    lvLines: true,
    dropLines: true,
    transformers: true,
    generation: true
  })
  const [elementCounts, setElementCounts] = useState({
    poles: 0,
    connections: 0,
    conductors: 0,
    mvLines: 0,
    lvLines: 0,
    dropLines: 0,
    transformers: 0,
    generation: 0
  })
  const [elementNames, setElementNames] = useState<Set<string>>(new Set())
  const [voltageOverlayEnabled, setVoltageOverlayEnabled] = useState(false)

  const layerGroupsRef = useRef<{
    poles?: L.LayerGroup
    connections?: L.LayerGroup
    conductors?: L.LayerGroup
    mvLines?: L.LayerGroup
    lvLines?: L.LayerGroup
    dropLines?: L.LayerGroup
    transformers?: L.LayerGroup
    generation?: L.LayerGroup
  }>({})

  const site = networkData?.site || 'UGRIDPLAN'

  // Handle map clicks for editing
  const handleMapClick = useCallback((e: L.LeafletMouseEvent) => {
    if (editMode === 'add-pole') {
      setPendingPoleLocation({
        lat: e.latlng.lat,
        lng: e.latlng.lng
      });
    } else if (editMode === 'add-connection') {
      setPendingConnectionLocation({
        lat: e.latlng.lat,
        lng: e.latlng.lng
      });
    }
  }, [editMode]);

  // Handle pole creation completion
  const handlePoleCreated = useCallback(() => {
    setPendingPoleLocation(null);
    setEditMode('select');
  }, []);

  // Handle connection creation completion
  const handleConnectionCreated = useCallback(() => {
    setPendingConnectionLocation(null);
    setEditMode('select');
  }, []);

  const handleElementUpdate = useCallback(async (id: string, updates: any): Promise<boolean> => {
    // Update the local element data
    if (networkData) {
      // Update poles
      if (networkData.poles) {
        const pole = networkData.poles.find((p: any) => p.id === id)
        if (pole) {
          Object.assign(pole, updates)
        }
      }
      
      // Update connections
      if (networkData.connections) {
        const connection = networkData.connections.find((c: any) => c.id === id)
        if (connection) {
          Object.assign(connection, updates)
        }
      }
      
      // Update conductors
      if (networkData.conductors) {
        const conductor = networkData.conductors.find((c: any) => c.id === id)
        if (conductor) {
          Object.assign(conductor, updates)
        }
      }
    }
    
    // Refresh the map
    if (onElementUpdate) {
      onElementUpdate()
    }
    
    return true
  }, [networkData, onElementUpdate])

  const handleEditElement = useCallback((element: any) => {
    setEditingElement(element)
    setEditDialogOpen(true)
  }, [])

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

      // Create custom panes for proper layer ordering
      newMap.createPane('connectionsPane')
      newMap.createPane('lvPolesPane')
      newMap.createPane('mvPolesPane')
      newMap.createPane('linesPane')
      
      // Set z-index for each pane (higher = on top)
      newMap.getPane('connectionsPane')!.style.zIndex = '400'  // Bottom
      newMap.getPane('lvPolesPane')!.style.zIndex = '500'       // LV poles
      newMap.getPane('mvPolesPane')!.style.zIndex = '550'       // MV poles (above LV)
      newMap.getPane('linesPane')!.style.zIndex = '600'        // Top
      
      // Initialize layer groups
      layerGroupsRef.current = {
        connections: L.layerGroup().addTo(newMap),
        transformers: L.layerGroup().addTo(newMap),   
        poles: L.layerGroup().addTo(newMap),
        generation: L.layerGroup().addTo(newMap),
        dropLines: L.layerGroup().addTo(newMap),
        lvLines: L.layerGroup().addTo(newMap),
        mvLines: L.layerGroup().addTo(newMap)
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
      
      // Add click handler for editing
      newMap.on('click', handleMapClick)
      
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

  // Show pending location markers
  useEffect(() => {
    if (!map) return

    // Clear any existing pending markers
    const pendingMarkersLayer = L.layerGroup().addTo(map)
    
    // Add pending pole marker
    if (pendingPoleLocation) {
      const pendingIcon = L.divIcon({
        html: `<div style="
          width: 20px; 
          height: 20px; 
          background: rgba(59, 130, 246, 0.5); 
          border: 2px solid #3b82f6; 
          border-radius: 50%;
          animation: pulse 1.5s infinite;
        "></div>`,
        className: 'pending-marker',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })
      
      L.marker([pendingPoleLocation.lat, pendingPoleLocation.lng], { icon: pendingIcon })
        .addTo(pendingMarkersLayer)
    }
    
    // Add pending connection marker
    if (pendingConnectionLocation) {
      const pendingIcon = L.divIcon({
        html: `<div style="
          width: 16px; 
          height: 16px; 
          background: rgba(168, 85, 247, 0.5); 
          border: 2px solid #a855f7; 
          border-radius: 50%;
          animation: pulse 1.5s infinite;
        "></div>`,
        className: 'pending-marker',
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      })
      
      L.marker([pendingConnectionLocation.lat, pendingConnectionLocation.lng], { icon: pendingIcon })
        .addTo(pendingMarkersLayer)
    }
    
    return () => {
      pendingMarkersLayer.clearLayers()
      pendingMarkersLayer.remove()
    }
  }, [map, pendingPoleLocation, pendingConnectionLocation])

  // Clean up map on unmount
  useEffect(() => {
    return () => {
      console.log('Cleaning up map on unmount')
      if (mapRef.current) {
        try {
          mapRef.current.remove()
          mapRef.current = null
        } catch (e) {
          console.warn('Error removing map:', e)
        }
      }
      if (resizeObserverRef.current && typeof window !== 'undefined') {
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }
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

  // Helper function to calculate size based on zoom
  const getZoomScale = (zoom: number) => {
    // Scale factor: smaller at low zoom, larger at high zoom
    const minZoom = 10
    const maxZoom = 18
    const minScale = 0.5
    const maxScale = 2.0
    
    if (zoom <= minZoom) return minScale
    if (zoom >= maxZoom) return maxScale
    
    const zoomRange = maxZoom - minZoom
    const scaleRange = maxScale - minScale
    const zoomProgress = (zoom - minZoom) / zoomRange
    
    return minScale + (scaleRange * zoomProgress)
  }

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

    if (!map || !data || !layerGroupsRef.current) return

    console.log('Updating network data on map', { 
      map: !!map, 
      data: !!data,
      layerGroups: !!layerGroupsRef.current
    })

    // Clear existing layers
    Object.values(layerGroupsRef.current).forEach(group => {
      if (group) group.clearLayers()
    })

    const bounds = L.latLngBounds([])
    let hasValidCoords = false
    const names = new Set<string>()

    // Store references to markers for zoom updates
    const connectionMarkers: Array<{marker: L.Marker, baseSize: number}> = []
    const poleMarkers: L.CircleMarker[] = []

    const counts = {
      poles: 0,
      connections: 0,
      conductors: data.conductors?.length || 0,
      mvLines: 0,
      lvLines: 0,
      dropLines: 0,
      transformers: data.transformers?.length || 0,
      generation: data.generation?.length || 0
    }

    // Add connections
    if (data.connections && layerGroupsRef.current.connections) {
      const currentZoom = map.getZoom()
      const scale = getZoomScale(currentZoom)
      
      data.connections.forEach((connection: any) => {
        if (connection.lat && connection.lng) {
          bounds.extend([connection.lat, connection.lng])
          hasValidCoords = true
          const color = SC3_COLORS[connection.st_code_3 || 0] || '#808080'
          // Create square icon for connections
          const squareSize = Math.round(12 * scale) // Base size 12px, scaled
          const squareIcon = L.divIcon({
            html: `<div style="background-color: ${color}; width: ${squareSize}px; height: ${squareSize}px;"></div>`,
            className: 'connection-square-marker',
            iconSize: [squareSize, squareSize],
            iconAnchor: [squareSize/2, squareSize/2]
          })
          
          const marker = L.marker([connection.lat, connection.lng], { 
            icon: squareIcon,
            pane: 'connectionsPane',
            alt: JSON.stringify(connection) // Store connection data for zoom updates
          })
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'connection',
              id: connection.id,
              data: connection
            })
          })
          
          marker.bindPopup(`
            <div>
              <strong>Connection: ${connection.name || connection.id}</strong><br/>
              Status: ${connection.st_code_3 || 0} - ${SC3_DESCRIPTIONS[connection.st_code_3 || 0]}<br/>
              Coords: ${connection.lat.toFixed(6)}, ${connection.lng.toFixed(6)}
            </div>
          `)
          if (layerGroupsRef.current.connections) {
            marker.addTo(layerGroupsRef.current.connections)
            connectionMarkers.push({marker, baseSize: 12})
          }
          
          names.add(connection.name || connection.id)
          counts.connections++
        }
      })
    }

    // Add poles
    if (data.poles && layerGroupsRef.current.poles) {
      const currentZoom = map.getZoom()
      const scale = getZoomScale(currentZoom)
      
      data.poles.forEach((pole: any) => {
        if (pole.lat && pole.lng) {
          bounds.extend([pole.lat, pole.lng])
          hasValidCoords = true
          const color = SC1_COLORS[pole.st_code_1 || 0] || '#808080'
          // MV poles have "_M" in their ID and keep borders
          const isMVPole = pole.id && pole.id.includes('_M')
          const marker = L.circleMarker([pole.lat, pole.lng], {
            radius: 8 * scale,  // Base size 8, scaled by zoom
            fillColor: color,
            color: isMVPole ? '#000' : color,  // MV poles get black border, LV poles borderless
            weight: isMVPole ? 2 : 0,
            opacity: 1,
            fillOpacity: 0.9,
            pane: isMVPole ? 'mvPolesPane' : 'lvPolesPane'  // MV poles render above LV poles
          })
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'pole',
              id: pole.id,
              data: pole
            })
          })
          
          marker.bindPopup(`
            <div>
              <strong>Pole: ${pole.name || pole.id}</strong><br/>
              Class: ${pole.pole_class || 'Unknown'}<br/>
              Type: ${pole.pole_type || 'Unknown'}<br/>
              Status: ${pole.st_code_1 || 0} - ${SC1_DESCRIPTIONS[pole.st_code_1 || 0]}<br/>
              Coords: ${pole.lat.toFixed(6)}, ${pole.lng.toFixed(6)}
            </div>
          `)
          if (layerGroupsRef.current.poles) {
            marker.addTo(layerGroupsRef.current.poles)
            poleMarkers.push(marker)
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
              color = '#0000FF'  // Blue for MV
              counts.mvLines++
              break
            case 'lv':
              layerGroup = layerGroupsRef.current.lvLines
              color = '#00FF00'  // Green for LV
              counts.lvLines++
              break
            case 'drop':
              layerGroup = layerGroupsRef.current.dropLines
              color = '#FFA500'  // Orange for Drop
              counts.dropLines++
              break
          }
          
          if (layerGroup) {
            const polyline = L.polyline([fromCoords, toCoords], {
              color: conductor.st_code_4 && conductor.st_code_4 > 0 ? SC4_COLORS[conductor.st_code_4] : color,
              weight: 2,
              pane: 'linesPane',
              opacity: 0.8
            })
            
            polyline.on('click', () => {
              if (editMode === 'split-conductor') {
                // Show split dialog for this conductor
                setSelectedElement({
                  type: 'conductor',
                  id: conductor.id,
                  data: { ...conductor, line_type: lineType }
                })
                // The MapEditToolbar will handle showing the split dialog
              } else {
                setSelectedElement({
                  type: 'conductor',
                  id: conductor.id,
                  data: { ...conductor, line_type: lineType }
                })
              }
            })
            
            polyline.bindPopup(`
              <div>
                <strong>${lineType.toUpperCase()} Line: ${conductor.id}</strong><br/>
                From: ${conductor.from}<br/>
                To: ${conductor.to}<br/>
                Length: ${conductor.length ? conductor.length.toFixed(2) + 'm' : 'Unknown'}<br/>
                Status: ${conductor.st_code_4 || 0} - ${SC4_DESCRIPTIONS[conductor.st_code_4 || 0]}
              </div>
            `)
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

    // Add generation sites (substations)
    if (data.generation && layerGroupsRef.current.generation) {
      console.log('Processing generation sites:', data.generation)
      data.generation.forEach((gen: any) => {
        if (gen.lat && gen.lng) {
          console.log('Adding generation marker at:', gen.lat, gen.lng, gen)
          // Create a distinctive icon for generation/substation
          const genIcon = L.divIcon({
            className: 'generation-icon',
            html: `<div style="
              width: 24px;
              height: 24px;
              background: linear-gradient(135deg, #f59e0b, #dc2626);
              border: 3px solid white;
              border-radius: 50%;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
              display: flex;
              align-items: center;
              justify-content: center;
            "><svg style="width: 14px; height: 14px; fill: white;" viewBox="0 0 24 24">
              <path d="M11 2v9.4l-6.4-6.4-1.4 1.4L11 14.2V22h2v-7.8l7.8-7.8L19.4 5 13 11.4V2z"/>
            </svg></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            popupAnchor: [0, -12]
          })
          
          const marker = L.marker([gen.lat, gen.lng], { icon: genIcon })
          
          marker.on('click', () => {
            setSelectedElement({
              type: 'generation',
              id: gen.id,
              data: gen
            })
          })
          
          marker.bindPopup(`
            <div>
              <strong>${gen.name || 'Generation Site'}</strong><br/>
              Type: ${gen.type || 'Substation'}<br/>
              Pole: ${gen.pole_id}<br/>
              Capacity: ${gen.capacity || 'Unknown'}
            </div>
          `)
          
          if (layerGroupsRef.current.generation) {
            marker.addTo(layerGroupsRef.current.generation)
          }
          
          names.add(gen.name || gen.id)
          counts.generation++
        }
      })
    }

    setElementNames(names)
    setElementCounts(counts)
    
    // Enforce fixed positioning after network data update
    const mapContainer = document.getElementById('map-container')
    if (mapContainer) {
      mapContainer.style.position = 'fixed'
      mapContainer.style.top = '64px'
      mapContainer.style.left = '256px'
      mapContainer.style.right = '0'
      mapContainer.style.bottom = '0'
      mapContainer.style.zIndex = '1'
    }

    // Add zoom event listener to update marker sizes
    const onZoomEnd = () => {
      const currentZoom = map.getZoom()
      const scale = getZoomScale(currentZoom)
      
      // Update connection marker sizes (recreate icons)
      connectionMarkers.forEach(({marker, baseSize}) => {
        const squareSize = Math.round(baseSize * scale)
        const connection = marker.options.alt ? JSON.parse(marker.options.alt) : null
        const color = SC3_COLORS[connection?.st_code_3 || 0] || '#808080'
        const newIcon = L.divIcon({
          html: `<div style="background-color: ${color}; width: ${squareSize}px; height: ${squareSize}px;"></div>`,
          className: 'connection-square-marker',
          iconSize: [squareSize, squareSize],
          iconAnchor: [squareSize/2, squareSize/2]
        })
        marker.setIcon(newIcon)
      })
      
      // Update pole marker sizes
      poleMarkers.forEach(marker => {
        marker.setRadius(8 * scale)
      })
    }

    map.on('zoomend', onZoomEnd)

    // Cleanup
    return () => {
      map.off('zoomend', onZoomEnd)
    }
  }, [map, networkData, layerGroupsRef])

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
        className="map-container"
      />
      <MapEditToolbar 
        site={site}
        editMode={editMode}
        onEditModeChange={setEditMode}
        selectedElement={selectedElement}
        pendingPoleLocation={pendingPoleLocation}
        pendingConnectionLocation={pendingConnectionLocation}
        onPoleCreated={handlePoleCreated}
        onConnectionCreated={handleConnectionCreated}
        onElementUpdate={() => {
          // Trigger the network data refresh
          if (onElementUpdate) {
            onElementUpdate();
          }
        }}
      />
      <LayerControls
        visibility={layerVisibility}
        onVisibilityChange={setLayerVisibility}
        counts={elementCounts}
      />
      {/* Map Control Buttons */}
      <div className="absolute top-20 right-4 z-50 space-y-2">
        {/* Search Button */}
        <button
          onClick={() => setShowSearchPanel(!showSearchPanel)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg shadow-md transition-all w-full ${
            showSearchPanel 
              ? 'bg-blue-100 text-blue-700 border-2 border-blue-300' 
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <Search className="h-4 w-4" />
          <span>Search</span>
        </button>
        
        {/* Voltage Drop Toggle Button */}
        <button
          onClick={() => setVoltageOverlayEnabled(!voltageOverlayEnabled)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg shadow-md transition-all w-full ${
            voltageOverlayEnabled 
              ? 'bg-yellow-100 text-yellow-700 border-2 border-yellow-300' 
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <Activity className="h-4 w-4" />
          <span>Voltage Drop</span>
        </button>
        
        {/* Generation Site Editor */}
        {networkData && (
          <GenerationSiteEditor
            site={site}
            currentPoleId={networkData.generation?.[0]?.pole_id}
            poles={networkData.poles || []}
            onUpdate={async () => {
              // Trigger element update callback to refresh data
              if (onElementUpdate) {
                onElementUpdate();
              }
            }}
          />
        )}
      </div>
      
      {/* Search Panel */}
      {showSearchPanel && networkData && (
        <SearchPanel
          poles={networkData.poles || []}
          connections={networkData.connections || []}
          conductors={networkData.conductors || []}
          onElementSelect={(element) => {
            setSelectedElement(element);
            setShowSearchPanel(false);
          }}
          onClose={() => setShowSearchPanel(false)}
        />
      )}
      
      <ElementDetailPanel
        element={selectedElement}
        onClose={() => setSelectedElement(null)}
        onUpdate={handleElementUpdate}
        onEdit={handleEditElement}
        existingNames={elementNames}
      />
      
      <ElementEditDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        element={editingElement}
        site={site}
        onElementUpdated={() => {
          setEditDialogOpen(false)
          setEditingElement(null)
          if (onElementUpdate) {
            onElementUpdate()
          }
        }}
      />
    </>
  )
}
