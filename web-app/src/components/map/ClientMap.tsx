'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster';
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
  SC5_COLORS, 
  SC5_DESCRIPTIONS,
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
  // Use ref to persist map instance across re-renders and StrictMode remounts
  const mapInstanceRef = useRef<L.Map | null>(null)
  const [map, setMapState] = useState<L.Map | null>(() => {
    // Check for existing map on initial state
    if (typeof window !== 'undefined' && (window as any).__leafletMapInstance) {
      console.log('Found existing map instance on mount')
      return (window as any).__leafletMapInstance
    }
    return null
  })
  
  // Wrapper to track state changes and persist map instance globally
  const setMap = useCallback((newMap: L.Map | null) => {
    console.log('setMap called with:', newMap ? 'Leaflet Map instance' : 'null')
    mapInstanceRef.current = newMap
    // Store globally to survive StrictMode remounts
    if (typeof window !== 'undefined') {
      (window as any).__leafletMapInstance = newMap
    }
    setMapState(newMap)
  }, [])
  const mapRef = useRef<HTMLDivElement | null>(null)
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
  const [renderProgress, setRenderProgress] = useState<{current: number, total: number} | null>(null)

  const layerGroupsRef = useRef<{
    poles?: L.LayerGroup
    mvPoles?: L.LayerGroup
    lvPoles?: L.LayerGroup
    connections?: L.LayerGroup
    conductors?: L.LayerGroup
    mvLines?: L.LayerGroup
    lvLines?: L.LayerGroup
    dropLines?: L.LayerGroup
    transformers?: L.LayerGroup
    poleCluster?: L.MarkerClusterGroup
    connectionCluster?: L.MarkerClusterGroup
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

  const updateNetworkData = useCallback(async (data: any) => {
    if (!map || !data || !layerGroupsRef.current) return

    console.log('Updating network data on map', { 
      map: !!map, 
      data: !!data,
      layerGroups: !!layerGroupsRef.current
    })

    // Clear existing layers
    Object.values(layerGroupsRef.current).forEach(group => {
      if (group) {
        if ('clearLayers' in group) {
          group.clearLayers()
        }
      }
    })

    const bounds = L.latLngBounds([])
    let hasValidCoords = false
    const names = new Set<string>()

    // Store references to markers for zoom updates
    const connectionMarkers: Array<{marker: L.Marker, baseSize: number}> = []
    const poleMarkers: L.CircleMarker[] = []
    
    // Defer cluster initialization to avoid blocking
    const initClusters = () => {
      if (!layerGroupsRef.current.poleCluster && map) {
        layerGroupsRef.current.poleCluster = (L as any).markerClusterGroup({
          maxClusterRadius: 80,
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          disableClusteringAtZoom: 18,
          chunkedLoading: true,
          chunkInterval: 200,
          chunkDelay: 50,
          iconCreateFunction: function(cluster: any) {
            const count = cluster.getChildCount()
            let size = 'small'
            let bgColor = '#b91c1c'
            
            if (count > 100) {
              size = 'large'
              bgColor = '#7c2d12'
            } else if (count > 50) {
              size = 'medium' 
              bgColor = '#991b1b'
            }
            
            return L.divIcon({
              html: `<div style="background-color: ${bgColor};"><span>${count}</span></div>`,
              className: `marker-cluster marker-cluster-${size}`,
              iconSize: L.point(40, 40)
            })
          }
        })
        if (layerGroupsRef.current.poleCluster) {
          map.addLayer(layerGroupsRef.current.poleCluster)
        }
      }
      
      if (!layerGroupsRef.current.connectionCluster && map) {
        layerGroupsRef.current.connectionCluster = (L as any).markerClusterGroup({
          maxClusterRadius: 60,
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          disableClusteringAtZoom: 18,
          chunkedLoading: true,
          chunkInterval: 200,
          chunkDelay: 50,
          iconCreateFunction: function(cluster: any) {
            const count = cluster.getChildCount()
            let size = 'small'
            let bgColor = '#1e40af'
            
            if (count > 100) {
              size = 'large'
              bgColor = '#1e3a8a'
            } else if (count > 50) {
              size = 'medium'
              bgColor = '#1e40af'
            }
            
            return L.divIcon({
              html: `<div style="background-color: ${bgColor};"><span>${count}</span></div>`,
              className: `marker-cluster marker-cluster-${size}`,
              iconSize: L.point(40, 40)
            })
          }
        })
        if (layerGroupsRef.current.connectionCluster) {
          map.addLayer(layerGroupsRef.current.connectionCluster)
        }
      }
    }
    
    // Initialize clusters after a short delay
    setTimeout(initClusters, 100)

    const counts = {
      poles: 0,
      connections: 0,
      conductors: 0,
      mvLines: 0,
      lvLines: 0,
      dropLines: 0,
      transformers: 0,
      generation: 0
    }
    
    // Calculate total items to render
    const totalItems = (data.poles?.length || 0) + 
                      (data.connections?.length || 0) + 
                      (data.conductors?.length || 0)
    let renderedItems = 0
    
    // Show progress indicator
    setRenderProgress({ current: 0, total: totalItems })

    const renderBatch = async (
      items: any[],
      renderFn: (item: any) => void,
      batchSize: number
    ) => {
      const frameTimeLimit = 8 // Target 8ms per frame for smooth UI
      
      for (let i = 0; i < items.length; i += batchSize) {
        const frameStartTime = performance.now();
        const batch = items.slice(i, Math.min(i + batchSize, items.length));
        
        // Process batch
        for (const item of batch) {
          renderFn(item);
          renderedItems++;
          
          // Update progress every 25 items to reduce setState overhead
          if (renderedItems % 25 === 0 || renderedItems === totalItems) {
            setRenderProgress({ current: renderedItems, total: totalItems })
          }
          
          // Check if we're exceeding frame time limit
          if (performance.now() - frameStartTime > frameTimeLimit) {
            // Immediately yield if we exceed time limit
            await new Promise(resolve => {
              setTimeout(resolve, 0);
            });
            // Start new frame timing
            break;
          }
        }
        
        // Always yield between batches to keep UI responsive
        await new Promise(resolve => {
          requestAnimationFrame(() => setTimeout(resolve, 0));
        });
      }
    };

    // Build node map for connections and conductors
    const nodeMap = new Map<string, [number, number]>()
    
    if (data.poles) {
      data.poles.forEach((pole: any) => {
        if (pole.lat && pole.lng) {
          nodeMap.set(pole.id, [pole.lat, pole.lng])
        }
      })
    }
    
    if (data.connections) {
      data.connections.forEach((conn: any) => {
        if (conn.lat && conn.lng) {
          nodeMap.set(conn.id, [conn.lat, conn.lng])
        }
      })
    }

    // Process connections in batches
    if (data.connections && layerGroupsRef.current.connections) {
      await renderBatch(
        data.connections,
        (connection: any) => {
          if (connection.lat && connection.lng) {
            const baseSize = 8
            const color = SC3_COLORS[connection.st_code_3 || 0] || '#808080'
            const squareIcon = L.divIcon({
              html: `<div style="background-color: ${color}; opacity: 0.5; width: ${baseSize}px; height: ${baseSize}px;"></div>`,
              className: 'connection-square-marker',
              iconSize: [baseSize, baseSize],
              iconAnchor: [baseSize/2, baseSize/2]
            })
            
            const marker = L.marker([connection.lat, connection.lng], {
              icon: squareIcon,
              pane: 'connectionsPane',
              alt: JSON.stringify(connection)
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
                Status: ${connection.st_code_3 || 0} - ${SC3_DESCRIPTIONS[connection.st_code_3 || 0]}
              </div>
            `)
            
            connectionMarkers.push({marker, baseSize})
            bounds.extend([connection.lat, connection.lng])
            hasValidCoords = true
            names.add(connection.name || connection.id)
            counts.connections++
          }
        },
        5 // Batch size for connections
      );
    }

    // Process poles in batches
    if (data.poles && layerGroupsRef.current.poles) {
      await renderBatch(
        data.poles,
        (pole: any) => {
          if (pole.lat && pole.lng) {
            const color = SC1_COLORS[pole.st_code_1 || 0] || '#808080'
            
            // Determine pane based on pole type (MV or LV)
            const polePane = pole.type === 'MV' ? 'mvPolesPane' : 'lvPolesPane'
            
            const circleMarker = L.circleMarker([pole.lat, pole.lng], {
              radius: 3,
              fillColor: color,
              color: '#000',
              weight: 1,
              opacity: 1,
              fillOpacity: 0.5,
              pane: polePane
            })
            
            circleMarker.on('click', () => {
              setSelectedElement({
                type: 'pole',
                id: pole.id,
                data: pole
              })
            })
            
            circleMarker.bindPopup(`
              <div>
                <strong>Pole: ${pole.name || pole.id}</strong><br/>
                Height: ${pole.height || 'Unknown'}m<br/>
                Type: ${pole.type || 'Unknown'}<br/>
                Status: ${pole.st_code_1 || 0} - ${SC1_DESCRIPTIONS[pole.st_code_1 || 0]}
              </div>
            `)
            
            // Add to appropriate layer group based on voltage level
            if (pole.type === 'MV' && layerGroupsRef.current.mvPoles) {
              layerGroupsRef.current.mvPoles.addLayer(circleMarker)
            } else if (layerGroupsRef.current.lvPoles) {
              layerGroupsRef.current.lvPoles.addLayer(circleMarker)
            }
            
            poleMarkers.push(circleMarker)
            bounds.extend([pole.lat, pole.lng])
            hasValidCoords = true
            names.add(pole.name || pole.id)
            counts.poles++
          }
        },
        10 // Batch size for poles
      );
    }

    // Process conductors in batches
    const conductorBatches: { [key: string]: L.Polyline[] } = {
      mv: [],
      lv: [],
      drop: []
    }
    
    if (data.conductors) {
      await renderBatch(
        data.conductors,
        (conductor: any) => {
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
            let pane = 'dropLinesPane'  // Default to drop lines pane
            
            switch (lineType) {
              case 'mv':
                layerGroup = layerGroupsRef.current.mvLines
                color = '#0000FF'  // Blue for MV
                pane = 'mvLinesPane'
                counts.mvLines++
                break
              case 'lv':
                layerGroup = layerGroupsRef.current.lvLines
                color = '#00FF00'  // Green for LV
                pane = 'lvLinesPane'
                counts.lvLines++
                break
              case 'drop':
                layerGroup = layerGroupsRef.current.dropLines
                color = '#FFA500'  // Orange for Drop
                pane = 'dropLinesPane'
                counts.dropLines++
                break
            }
            
            if (layerGroup) {
              const polyline = L.polyline([fromCoords, toCoords], {
                color: conductor.st_code_4 && conductor.st_code_4 > 0 ? SC4_COLORS[conductor.st_code_4] : color,
                weight: 2,
                pane: pane,
                opacity: 1,  // No transparency for lines
                dashArray: conductor.st_code_4 >= 3 ? undefined : '5, 10'  // Solid for installed (SC4>=3), dashed for planned/in-progress
              })
              
              polyline.on('click', () => {
                setSelectedElement({
                  type: 'conductor',
                  id: conductor.id,
                  data: { ...conductor, line_type: lineType }
                })
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
              conductorBatches[lineType].push(polyline)
              names.add(conductor.name || conductor.id)
              counts.conductors++
            }
          }
        },
        10 // Smaller batch size for conductors to prevent blocking
      );
    }

    // Add markers to cluster groups after all are created
    setTimeout(() => {
      if (layerGroupsRef.current.poleCluster && poleMarkers.length > 0) {
        layerGroupsRef.current.poleCluster.addLayers(poleMarkers)
      } else if (layerGroupsRef.current.poles && poleMarkers.length > 0) {
        poleMarkers.forEach(marker => marker.addTo(layerGroupsRef.current.poles!))
      }
      
      if (layerGroupsRef.current.connectionCluster && connectionMarkers.length > 0) {
        layerGroupsRef.current.connectionCluster.addLayers(connectionMarkers.map(item => item.marker))
      } else if (layerGroupsRef.current.connections && connectionMarkers.length > 0) {
        connectionMarkers.forEach(({marker}) => marker.addTo(layerGroupsRef.current.connections!))
      }
      
      const addConductorBatch = (type: string, layerGroup: L.LayerGroup | undefined) => {
        if (!layerGroup) return
        const batch = conductorBatches[type]
        if (batch.length === 0) return
        
        const batchSize = 50
        let index = 0
        
        const addBatch = () => {
          const end = Math.min(index + batchSize, batch.length)
          for (let i = index; i < end; i++) {
            batch[i].addTo(layerGroup)
          }
          index = end
          
          if (index < batch.length) {
            requestAnimationFrame(addBatch)
          }
        }
        
        requestAnimationFrame(addBatch)
      }
      
      addConductorBatch('mv', layerGroupsRef.current.mvLines)
      addConductorBatch('lv', layerGroupsRef.current.lvLines)
      addConductorBatch('drop', layerGroupsRef.current.dropLines)
    }, 100)

    // Clear progress after rendering
    setTimeout(() => {
      setRenderProgress(null)
    }, 500)

    // Center map on data bounds if we have valid coordinates
    if (hasValidCoords) {
      setTimeout(() => {
        map.fitBounds(bounds, { padding: [50, 50] })
      }, 200)
    }
  }, [map, setSelectedElement, setRenderProgress, editMode]);

  // Initialize map using callback ref
  const setMapContainer = useCallback((container: HTMLDivElement | null) => {
    if (!container) {
      return
    }
    
    // Check for globally persisted map instance (survives StrictMode)
    const globalMap = typeof window !== 'undefined' ? (window as any).__leafletMapInstance : null
    if (globalMap) {
      try {
        const existingContainer = globalMap.getContainer()
        // Check if map is still valid and attached to DOM
        if (existingContainer && document.body.contains(existingContainer)) {
          if (existingContainer === container) {
            console.log('Map already initialized for this container')
            setMap(globalMap)
            mapInstanceRef.current = globalMap
            return
          }
          // Move map to new container if needed
          if (existingContainer.parentNode) {
            console.log('Moving existing map to new container')
            container.appendChild(existingContainer)
            globalMap.invalidateSize()
            setMap(globalMap)
            mapInstanceRef.current = globalMap
            return
          }
        }
      } catch (e) {
        console.log('Existing map instance is invalid, creating new one')
        // Map instance is invalid, will create new one
      }
    }
    
    // Check if already initialized
    if (container.hasAttribute('data-map-initialized')) {
      console.log('Map container already initialized, skipping')
      return
    }
    
    mapRef.current = container
    
    // Get the parent wrapper to check dimensions
    const wrapper = container.parentElement
    if (!wrapper) {
      console.error('Map container has no parent wrapper!')
      return
    }
    
    // Ensure wrapper has dimensions
    if (wrapper.offsetWidth === 0 || wrapper.offsetHeight === 0) {
      console.log(`Wrapper dimensions: ${wrapper.offsetWidth}x${wrapper.offsetHeight}, retrying...`)
      setTimeout(() => setMapContainer(container), 100)
      return
    }
    
    console.log('Initializing map with container:', container)
    console.log('Container parent (wrapper):', wrapper)
    console.log('Wrapper dimensions:', wrapper.offsetWidth, 'x', wrapper.offsetHeight)
    
    container.setAttribute('data-map-initialized', 'true')

    console.log('Initializing Leaflet map')
    
    // Start with a default view, will be updated when data loads
    const newMap = L.map(container, {
      center: [-30.078, 27.859],
      zoom: 13,
      zoomControl: true,
      preferCanvas: true,  // Use canvas renderer for better containment
      renderer: L.canvas({ padding: 0 })  // No padding outside container
    })
    
    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: ' OpenStreetMap contributors',
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
    
    // Ensure the parent boundary container cannot be modified
    const boundary = document.getElementById('map-boundary')
    if (boundary) {
      // Force the boundary to stay at left: 400px
      boundary.style.setProperty('position', 'fixed', 'important')
      boundary.style.setProperty('left', '400px', 'important')
      boundary.style.setProperty('top', '64px', 'important')
      boundary.style.setProperty('width', 'calc(100vw - 400px)', 'important')
      boundary.style.setProperty('height', 'calc(100vh - 64px)', 'important')
      boundary.style.setProperty('z-index', '5', 'important')
      boundary.style.setProperty('overflow', 'hidden', 'important')
      boundary.style.setProperty('clip-path', 'inset(0)', 'important')
      boundary.style.setProperty('contain', 'strict', 'important')
      // Remove any problematic properties
      boundary.style.removeProperty('inset')
      boundary.style.removeProperty('margin-left')
      boundary.style.removeProperty('padding-left')
    }
    
    // Fix the initial size issue by invalidating immediately and after delay
    requestAnimationFrame(() => {
      if (newMap) {
        newMap.invalidateSize({ pan: false })
        const size1 = newMap.getSize()
        console.log('Map size after first invalidate:', size1.x, 'x', size1.y)
      }
    })
    
    setTimeout(() => {
      if (newMap && newMap.getContainer()) {
        const mapContainer = newMap.getContainer()
        
        // Re-enforce boundary positioning
        const boundary = document.getElementById('map-boundary')
        if (boundary) {
          boundary.style.setProperty('left', '400px', 'important')
        }
        
        if (mapContainer) {
          // Remove any inline positioning styles that Leaflet might have added
          mapContainer.style.position = 'absolute'
          mapContainer.style.inset = ''
          mapContainer.style.top = '0'
          mapContainer.style.left = '0'
          mapContainer.style.right = '0'
          mapContainer.style.bottom = '0'
          mapContainer.style.width = '100%'
          mapContainer.style.height = '100%'
          console.log('Reset map container positioning to absolute')
        }
        
        console.log('Invalidating map size after initialization')
        newMap.invalidateSize({ pan: false })
        const size = newMap.getSize()
        console.log('Map size after invalidate:', size.x, 'x', size.y)
      }
    }, 200)

    // Create custom panes for proper layer ordering
    newMap.createPane('connectionsPane')
    newMap.createPane('lvPolesPane')
    newMap.createPane('mvPolesPane')
    newMap.createPane('dropLinesPane')
    newMap.createPane('lvLinesPane')
    newMap.createPane('mvLinesPane')
    
    // Set z-index for each pane (higher = on top)
    newMap.getPane('connectionsPane')!.style.zIndex = '400'  // Bottom
    newMap.getPane('lvPolesPane')!.style.zIndex = '500'       // LV poles
    newMap.getPane('mvPolesPane')!.style.zIndex = '550'       // MV poles (above LV)
    newMap.getPane('dropLinesPane')!.style.zIndex = '600'     // Drop lines
    newMap.getPane('lvLinesPane')!.style.zIndex = '650'       // LV lines (above drop)
    newMap.getPane('mvLinesPane')!.style.zIndex = '700'       // MV lines (top)
    
    // Initialize layer groups
    layerGroupsRef.current = {
      connections: L.layerGroup().addTo(newMap),
      transformers: L.layerGroup().addTo(newMap),   
      poles: L.layerGroup().addTo(newMap),  // Keep for backward compatibility
      mvPoles: L.layerGroup().addTo(newMap),  // MV poles layer group
      lvPoles: L.layerGroup().addTo(newMap),  // LV poles layer group
      mvLines: L.layerGroup().addTo(newMap),
      lvLines: L.layerGroup().addTo(newMap),
      dropLines: L.layerGroup().addTo(newMap)
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
    console.log('Setting map state with newMap instance')
    setMap(newMap)
    resizeObserverRef.current = resizeObserver
    
    // Store in window for debugging and persistence
    if (typeof window !== 'undefined') {
      (window as any).__leafletMapInstance = newMap
      console.log('Map stored in window.__leafletMapInstance for debugging and persistence')
    }
  }, [handleMapClick, setMap])

  // Skip cleanup in development to avoid destroying map on hot reload/StrictMode
  useEffect(() => {
    return () => {
      // In development, React StrictMode causes double mounting
      // Skip cleanup to preserve map instance
      if (process.env.NODE_ENV === 'development') {
        console.log('Skipping map cleanup in development')
        return
      }
      
      // Only clean up in production
      const mapInstance = typeof window !== 'undefined' ? (window as any).__leafletMap : null
      if (mapInstance) {
        console.log('Cleaning up map on unmount')
        if ((mapInstance as any)._wrapperObserver) {
          (mapInstance as any)._wrapperObserver.disconnect()
        }
        try {
          mapInstance.remove()
        } catch (e) {
          console.warn('Error removing map:', e)
        }
      }
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
      }
    }
  }, [])

  // Create a MutationObserver to watch for style changes on wrapper and boundary
  React.useEffect(() => {
    if (!map) return

    const wrapper = document.getElementById('map-wrapper')
    const boundary = document.getElementById('map-boundary')
    if (!wrapper || !boundary) return

    const enforceBoundaryStyles = () => {
      // Force boundary to stay at left: 400px
      boundary.style.setProperty('position', 'fixed', 'important')
      boundary.style.setProperty('left', '400px', 'important')
      boundary.style.setProperty('top', '64px', 'important')
      boundary.style.setProperty('right', 'auto', 'important')
      boundary.style.setProperty('width', 'calc(100vw - 400px)', 'important')
      boundary.style.setProperty('height', 'calc(100vh - 64px)', 'important')
      boundary.style.setProperty('z-index', '5', 'important')
      boundary.style.setProperty('overflow', 'hidden', 'important')
      boundary.style.setProperty('clip-path', 'inset(0)', 'important')
      boundary.style.setProperty('contain', 'strict', 'important')
      // Remove any problematic properties
      boundary.style.removeProperty('inset')
      boundary.style.removeProperty('margin')
      boundary.style.removeProperty('padding')
      boundary.style.removeProperty('transform')
    }

    const enforceWrapperStyles = () => {
      wrapper.style.setProperty('position', 'relative', 'important')
      wrapper.style.setProperty('width', '100%', 'important')
      wrapper.style.setProperty('height', '100%', 'important')
      wrapper.style.setProperty('overflow', 'hidden', 'important')
      wrapper.style.setProperty('background-color', '#f3f4f6', 'important')
    }

    // Create observer to watch for style changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          if (mutation.target === boundary) {
            enforceBoundaryStyles()
          } else if (mutation.target === wrapper) {
            enforceWrapperStyles()
          }
        }
      })
    })

    // Start observing both elements
    observer.observe(wrapper, {
      attributes: true,
      attributeFilter: ['style']
    })
    observer.observe(boundary, {
      attributes: true,
      attributeFilter: ['style']
    })

    // Enforce initially and repeatedly
    enforceBoundaryStyles()
    enforceWrapperStyles()
    
    // Enforce periodically to counter any overrides
    const interval = setInterval(() => {
      enforceBoundaryStyles()
      enforceWrapperStyles()
    }, 500)

    // Store observer reference for cleanup
    ;(map as any)._boundaryObserver = observer
    ;(map as any)._boundaryInterval = interval

    // Cleanup
    return () => {
      observer.disconnect()
      clearInterval(interval)
    }
  }, [map])

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

  // Map initialization is handled by the main useEffect above

  // Clean up map on unmount - removed duplicate cleanup that was destroying the map

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

  // Render  // Log map state changes
  useEffect(() => {
    console.log('Map state changed to:', map ? 'Map instance exists' : 'null')
  }, [map])

  // Network data effect - just call updateNetworkData
  useEffect(() => {
    console.log('Network data effect - map:', !!map, 'networkData:', !!networkData)
    if (!map || !networkData) {
      console.log(`Cannot render: map= ${!!map} networkData= ${!!networkData} data keys: ${networkData ? Object.keys(networkData) : 'none'}`)
      return
    }

    // Call the async updateNetworkData function
    updateNetworkData(networkData)
  }, [map, networkData, updateNetworkData])

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
      {/* Loading indicator */}
      {renderProgress && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 9999,
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '10px' }}>
            Loading network data...
          </div>
          <div style={{
            width: '200px',
            height: '4px',
            background: '#e5e7eb',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${(renderProgress.current / renderProgress.total) * 100}%`,
              height: '100%',
              background: '#3b82f6',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: '#6b7280' }}>
            {renderProgress.current} / {renderProgress.total} elements
          </div>
        </div>
      )}
      
      {/* Simple map container */}
      <div 
        id="map" 
        ref={setMapContainer}
        className="map-container"
        style={{
          width: '100%',
          height: '100%'
        }} />
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
