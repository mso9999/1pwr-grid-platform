'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'
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
  onElementUpdate?: () => Promise<void>
  loading?: boolean
  onElementDelete?: () => Promise<void>
}

export function ClientMap({ networkData, onElementUpdate, loading, onElementDelete }: ClientMapProps) {
  // Use ref to persist map instance across re-renders and StrictMode remounts
  const mapInstanceRef = useRef<L.Map | null>(null)
  const [map, setMapState] = useState<L.Map | null>(() => {
    // Check for existing map on initial state
    if (typeof window !== 'undefined' && (window as any).__leafletMapInstance) {
      return (window as any).__leafletMapInstance
    }
    return null
  })
  
  // Wrapper to track state changes and persist map instance globally
  const setMap = useCallback((newMap: L.Map | null) => {
    mapInstanceRef.current = newMap
    // Store globally to survive StrictMode remounts
    if (typeof window !== 'undefined') {
      (window as any).__leafletMapInstance = newMap
    }
    setMapState(newMap)
  }, [])
  const mapRef = useRef<HTMLDivElement | null>(null)
  const resizeObserverRef = useRef<ResizeObserver | null>(null)
  const retryCountRef = useRef<number>(0)
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

  // Add new pole to map without reloading
  const handleNewPole = useCallback((pole: any) => {
    if (!map || !layerGroupsRef.current.poles) return
    
    // Determine if MV or LV pole
    const isMV = pole.pole_class === 'MV' || (pole.pole_id && pole.pole_id.includes('_M'))
    const color = SC1_COLORS[pole.st_code_1 || 0] || '#808080'
    
    const circleMarker = L.circleMarker([pole.latitude, pole.longitude], {
      radius: 6,
      fillColor: color,
      color: isMV ? '#000000' : 'transparent',
      weight: isMV ? 1 : 0,
      opacity: 1,
      fillOpacity: 0.5,
      pane: isMV ? 'mvPolesPane' : 'lvPolesPane'
    })
    
    circleMarker.on('click', () => {
      setSelectedElement({
        type: 'pole',
        id: pole.pole_id,
        data: pole
      })
    })
    
    circleMarker.bindPopup(`
      <div>
        <strong>Pole: ${pole.pole_id}</strong><br/>
        Type: ${pole.pole_class || 'Unknown'}<br/>
        Status: ${pole.st_code_1 || 0} - ${SC1_DESCRIPTIONS[pole.st_code_1 || 0]}
      </div>
    `)
    
    // Add to appropriate layer group
    if (isMV && layerGroupsRef.current.mvPoles) {
      layerGroupsRef.current.mvPoles.addLayer(circleMarker)
    } else if (layerGroupsRef.current.lvPoles) {
      layerGroupsRef.current.lvPoles.addLayer(circleMarker)
    }
  }, [map, setSelectedElement, SC1_COLORS, SC1_DESCRIPTIONS])

  // Add new connection to map without reloading
  const handleNewConnection = useCallback((connection: any) => {
    if (!map || !layerGroupsRef.current.connections) return
    // Add test marker directly to map for debugging
    if (connection.lat && connection.lng && map) {
      const testMarker = L.circleMarker([connection.lat, connection.lng], {
        radius: 8,
        fillColor: '#ff0000',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      })
      testMarker.addTo(map)
    }
    
    const color = connection.st_code_3 === 'Energized' ? '#4ade80' : '#94a3b8'
    
    const marker = L.circleMarker([connection.latitude, connection.longitude], {
      radius: 6,
      fillColor: color,
      color: 'transparent',
      weight: 0,
      opacity: 1,
      fillOpacity: 0.5,
      pane: 'connectionsPane'
    })
    
    marker.bindPopup(`
      <div>
        <strong>Connection: ${connection.connection_id}</strong><br/>
        Status: ${connection.st_code_3 || 'Unknown'}<br/>
        Lat: ${connection.latitude.toFixed(6)}<br/>
        Lng: ${connection.longitude.toFixed(6)}
      </div>
    `)
    
    marker.on('click', () => {
      setSelectedElement({
        type: 'connection',
        id: connection.connection_id,
        data: connection
      })
    })
    
    layerGroupsRef.current.connections.addLayer(marker)
  }, [map, setSelectedElement])

  const updateNetworkData = useCallback(async (data: any) => {
    console.log('=== updateNetworkData called ===', {
      hasMap: !!map,
      hasData: !!data
    });
    console.log('Network data received:', {
      connections: data.connections?.length || 0,
      poles: data.poles?.length || 0,
      conductors: data.conductors?.length || 0
    });
    
    // Create unique render ID for this call
    const renderID = Date.now() + Math.random();
    (window as any).currentRenderID = renderID;
    
    // Cancel any pending retry timeouts
    if ((window as any).pendingRetryTimeout) {
      clearTimeout((window as any).pendingRetryTimeout);
      (window as any).pendingRetryTimeout = null;
    }

    try {
      // Check if this render has been superseded
      if ((window as any).currentRenderID !== renderID) {
        console.log('Render superseded, exiting');
        return;
      }
      
      // Clear existing layers first
      console.log('Clearing existing layers');
      if (layerGroupsRef.current.connections) layerGroupsRef.current.connections.clearLayers()
      if (layerGroupsRef.current.transformers) layerGroupsRef.current.transformers.clearLayers()
      if (layerGroupsRef.current.mvPoles) layerGroupsRef.current.mvPoles.clearLayers()
      if (layerGroupsRef.current.lvPoles) layerGroupsRef.current.lvPoles.clearLayers()
      if (layerGroupsRef.current.mvLines) layerGroupsRef.current.mvLines.clearLayers()
      if (layerGroupsRef.current.lvLines) layerGroupsRef.current.lvLines.clearLayers()
      if (layerGroupsRef.current.dropLines) layerGroupsRef.current.dropLines.clearLayers()
      if (layerGroupsRef.current.others) layerGroupsRef.current.others.clearLayers()

      // Ensure layer groups exist and are added to map
      if (map) {
        if (!layerGroupsRef.current.connections || !map.hasLayer(layerGroupsRef.current.connections)) {
          layerGroupsRef.current.connections = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.poles || !map.hasLayer(layerGroupsRef.current.poles)) {
          layerGroupsRef.current.poles = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.mvPoles || !map.hasLayer(layerGroupsRef.current.mvPoles)) {
          layerGroupsRef.current.mvPoles = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.lvPoles || !map.hasLayer(layerGroupsRef.current.lvPoles)) {
          layerGroupsRef.current.lvPoles = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.mvLines || !map.hasLayer(layerGroupsRef.current.mvLines)) {
          layerGroupsRef.current.mvLines = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.lvLines || !map.hasLayer(layerGroupsRef.current.lvLines)) {
          layerGroupsRef.current.lvLines = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.dropLines || !map.hasLayer(layerGroupsRef.current.dropLines)) {
          layerGroupsRef.current.dropLines = L.layerGroup().addTo(map);
        }
        if (!layerGroupsRef.current.transformers || !map.hasLayer(layerGroupsRef.current.transformers)) {
          layerGroupsRef.current.transformers = L.layerGroup().addTo(map);
        }
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
      const frameTimeLimit = 16 // Target 16ms per frame for 60fps
      
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

    // Initialize tracking variables
    const connectionMarkers: L.Marker[] = []
    const poleMarkers: any[] = [] // Using any[] since we're mixing L.CircleMarker types
    const conductorLines: L.Polyline[] = []
    const bounds = L.latLngBounds([])
    let hasValidCoords = false
    const names = new Set<string>()
    const counts = {
      connections: 0,
      poles: 0,
      conductors: 0,
      mvLines: 0,
      lvLines: 0,
      dropLines: 0
    }

    // Helper function to determine line type
    const getLineType = (conductor: any, poles: any[], connections: any[]): 'mv' | 'lv' | 'drop' => {
      const isFromConnection = connections.some((conn: any) => conn.id === conductor.from)
      const isToConnection = connections.some((conn: any) => conn.id === conductor.to)
      
      // If either end connects to a connection (customer), it's a drop line
      if (isFromConnection || isToConnection) {
        return 'drop'
      }
      
      // Check if both ends are poles
      const fromPole = poles.find((p: any) => p.id === conductor.from)
      const toPole = poles.find((p: any) => p.id === conductor.to)
      
      // If both are MV poles, it's MV line
      if (fromPole?.type === 'MV' && toPole?.type === 'MV') {
        return 'mv'
      }
      
      // Default to LV for pole-to-pole connections that aren't MV
      return 'lv'
    }

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

    // Render connections
    if (data.connections?.length > 0) {
      console.log('Starting to render connections...');
      
      // Ensure map is ready before adding markers
      if (!map || !map.getContainer()) {
        console.log('Map or container not ready');
        return;
      }
      
      const containerHeight = map.getContainer().offsetHeight;
      const containerWidth = map.getContainer().offsetWidth;
      
      if (containerHeight === 0 || containerWidth === 0) {
        console.log('Map container has no size:', { width: containerWidth, height: containerHeight });
        
        // Try to force the map to update its size
        map.invalidateSize();
        
        // Use a unique key for retry tracking based on data signature
        const dataKey = `${data.connections?.length}-${data.poles?.length}-${data.conductors?.length}`;
        
        if (!retryCountRef.current) {
          retryCountRef.current = 0;
        }
        
        // Reset retry count if this is different data
        if ((window as any).lastDataKey !== dataKey) {
          retryCountRef.current = 0;
          (window as any).lastDataKey = dataKey;
        }
        
        retryCountRef.current++;
        
        if (retryCountRef.current < 15) { // Increased retry limit
          console.log(`Retrying updateNetworkData, attempt ${retryCountRef.current}`);
          // Store timeout reference to cancel if needed
          (window as any).pendingRetryTimeout = setTimeout(() => {
            (window as any).pendingRetryTimeout = null;
            updateNetworkData(data)
          }, 1000) // Increased delay to give map more time to initialize
        } else {
          console.log('Max retries reached, forcing render anyway');
          // Continue with rendering even if container has no size
          // The map will update when it gets proper size
        }
        
        if (retryCountRef.current < 15) {
          return;
        }
      }
      
      // Reset retry count on successful render
      retryCountRef.current = 0
      console.log('Map ready, starting batch render of connections');
      
      // Check if this render has been superseded before starting batch
      if ((window as any).currentRenderID !== renderID) {
        console.log('Render superseded before batch, exiting');
        return;
      }
      
      await renderBatch(
        data.connections,
        (connection: any) => {
          // Check if render was superseded during batch
          if ((window as any).currentRenderID !== renderID) {
            return;
          }
          
          if (connection.lat && connection.lng) {
            const color = connection.st_code_3 === 'Energized' ? '#4ade80' : '#94a3b8'
            
            // Create square marker for connections (per specifications)
            const iconHtml = `<div style="
              width: 12px;
              height: 12px;
              background-color: ${color};
              opacity: 0.5;
              border: none;
              transform: translate(-50%, -50%);
            "></div>`
            
            const marker = L.marker(
              [connection.lat, connection.lng],
              {
                icon: L.divIcon({
                  html: iconHtml,
                  className: 'connection-marker',
                  iconSize: [12, 12],
                  iconAnchor: [6, 6]
                }),
                pane: 'markerPane'
              }
            )
            
            // Add popup to marker
            marker.bindPopup(`Connection<br>Status: ${connection.st_code_3 || 'Unknown'}<br>Lat: ${connection.lat}<br>Lng: ${connection.lng}`)
            
            // Add marker to layer group instead of directly to map
            if (layerGroupsRef.current.connections) {
              layerGroupsRef.current.connections.addLayer(marker)
            } else {
              marker.addTo(map)
            }
            connectionMarkers.push(marker)
            
            bounds.extend([connection.lat, connection.lng])
            hasValidCoords = true
            names.add(connection.name || connection.id || 'Connection')
            counts.connections++
          }
        },
        20
      )
      
    }

    // Final debug check
    if (layerGroupsRef.current.connections && map) {
      const layerCount = layerGroupsRef.current.connections.getLayers().length
      
      // Try to manually ensure visibility
      if (!map.hasLayer(layerGroupsRef.current.connections)) {
        layerGroupsRef.current.connections.addTo(map)
      }
      
      // Force a delayed update to ensure map is ready
      setTimeout(() => {
        if (layerGroupsRef.current.connections && map) {
          const layers = layerGroupsRef.current.connections.getLayers()
          
          // Force map refresh
          map.invalidateSize()
          
          // If we have connections, ensure we're zoomed to see them
          if (data.connections.length > 0 && bounds.isValid() && map) {
            map.fitBounds(bounds, { padding: [50, 50] })
          }
        }
      }, 100) // Reduced delay for faster map update
    }
    
    // Force map to redraw after a short delay
    setTimeout(() => {
      if (map) {
        map.invalidateSize()
      }
    }, 50) // Reduced delay for faster redraw

    // Process poles in batches
    if (data.poles && layerGroupsRef.current.poles) {
      await renderBatch(
        data.poles,
        (pole: any) => {
          if (pole.lat && pole.lng) {
            const color = SC1_COLORS[pole.st_code_1 || 0] || '#808080'
            
            // Determine pane and border based on pole type (MV or LV)
            const isMV = pole.type === 'MV' || (pole.id && pole.id.includes('_M'))
            const polePane = isMV ? 'mvPolesPane' : 'lvPolesPane'
            
            const circleMarker = L.circleMarker([pole.lat, pole.lng], {
              radius: 6,  // Increased from 3 to 6 for better visibility
              fillColor: color,
              color: isMV ? '#000000' : 'transparent',  // Black border for MV, no border for LV
              weight: isMV ? 1 : 0,  // 1px weight for MV, 0 for LV
              opacity: 1,
              fillOpacity: 0.5,  // 50% transparent fill
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
            
            // Add to poleMarkers array (type mismatch is intentional)
            poleMarkers.push(circleMarker as any)
            bounds.extend([pole.lat, pole.lng])
            hasValidCoords = true
            names.add(pole.name || pole.id)
            counts.poles++
          }
        },
        20 // Batch size for poles - optimized for performance
      );
    }

    // Process conductors in batches
    const conductorBatches = {
      mv: [] as L.Polyline[],
      lv: [] as L.Polyline[],
      drop: [] as L.Polyline[]
    }
    
    // Debug: Count droplines before processing
    const dropLineCount = data.conductors?.filter((c: any) => {
      const isFromConnection = data.connections?.some((conn: any) => conn.id === c.from)
      const isToConnection = data.connections?.some((conn: any) => conn.id === c.to)
      return isFromConnection || isToConnection
    }).length || 0
    
    if (data.conductors && (layerGroupsRef.current.mvLines || layerGroupsRef.current.lvLines || layerGroupsRef.current.dropLines)) {
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
                color: color,  // Use line type color (MV=blue, LV=green, Drop=orange) per specifications
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

    // Add markers directly to layer groups (no clustering)
    if (layerGroupsRef.current.poles && poleMarkers.length > 0) {
      poleMarkers.forEach((marker: any) => marker.addTo(layerGroupsRef.current.poles!))  
    }
    
    if (layerGroupsRef.current.connections && connectionMarkers.length > 0) {
      connectionMarkers.forEach((marker: any) => marker.addTo(layerGroupsRef.current.connections!))
    }
    
    // Add conductor batches to their respective layer groups
    if (conductorBatches.mv.length > 0 && layerGroupsRef.current.mvLines) {
      conductorBatches.mv.forEach(line => line.addTo(layerGroupsRef.current.mvLines!))
    }
      
    if (conductorBatches.lv.length > 0 && layerGroupsRef.current.lvLines) {
      conductorBatches.lv.forEach(line => line.addTo(layerGroupsRef.current.lvLines!))
    }
      
    if (conductorBatches.drop.length > 0 && layerGroupsRef.current.dropLines) {
      conductorBatches.drop.forEach(line => line.addTo(layerGroupsRef.current.dropLines!))
    }
    
    // Center map on data bounds if we have valid coordinates
    if (hasValidCoords && map) {
      console.log('Fitting bounds, hasValidCoords:', hasValidCoords, 'bounds:', bounds.toBBoxString());
      setTimeout(() => {
        try {
          map.fitBounds(bounds, { padding: [50, 50] });
          console.log('Map fitBounds called successfully');
          
          // Also ensure layer groups are visible
          Object.entries(layerGroupsRef.current).forEach(([key, layer]) => {
            if (layer && 'getLayers' in layer && typeof layer.getLayers === 'function' && map) {
              const layerCount = layer.getLayers().length;
              if (layerCount > 0 && !map.hasLayer(layer)) {
                console.log(`Adding ${key} layer with ${layerCount} items`);
                layer.addTo(map);
              }
            }
          });
        } catch (error) {
          console.error('Error fitting bounds:', error);
        }
      }, 500)
    } else {
      console.log('No valid coordinates to fit bounds');
    }
  } catch (error) {
      console.error('Error in updateNetworkData:', error);
    } finally {
      // Clear progress after a delay
      setTimeout(() => {
        setRenderProgress(null);
      }, 500);
    }
  }, [map, setSelectedElement, setRenderProgress, editMode, SC1_COLORS, SC3_COLORS, SC4_COLORS])

  // Update map when networkData prop changes
  useEffect(() => {
    console.log('=== ClientMap networkData useEffect ===', {
      hasNetworkData: !!networkData,
      hasMap: !!map
    });
    if (networkData && map) {
      updateNetworkData(networkData);
    }
  }, [networkData, map]); // Remove updateNetworkData from deps to avoid infinite loop

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
            setMap(globalMap)
            mapInstanceRef.current = globalMap
            return
          }
          // Move map to new container if needed
          if (existingContainer.parentNode) {
            container.appendChild(existingContainer)
            globalMap.invalidateSize()
            setMap(globalMap)
            mapInstanceRef.current = globalMap
            return
          }
        }
      } catch (e) {
        // Map instance is invalid, will create new one
      }
    }
    
    // Check if already initialized
    if (container.hasAttribute('data-map-initialized')) {
      return
    }
    
    mapRef.current = container
    
    // Get the parent wrapper to check dimensions
    const wrapper = container.parentElement
    if (!wrapper) {
      return
    }
    
    // Ensure wrapper has dimensions
    if (wrapper.offsetWidth === 0 || wrapper.offsetHeight === 0) {
      setTimeout(() => setMapContainer(container), 100)
      return
    }
    
    
    container.setAttribute('data-map-initialized', 'true')

    
    // Start with a default view, will be updated when data loads
    const newMap = L.map(container, {
      center: [-30.078, 27.859],
      zoom: 13,
      zoomControl: true,
      preferCanvas: true,  // Use canvas renderer for better containment
      renderer: L.canvas({ padding: 0 })  // No padding outside container
    })
    
    // Add tile layer
    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: ' OpenStreetMap contributors'
    }).addTo(newMap)
    
    // Log when tiles load
    tileLayer.on('load', () => {
    })
    
    tileLayer.on('tileerror', (error: any) => {
    })
    
    
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
        console.log('Map size after requestAnimationFrame:', size1);
      }
    })
    
    // Multiple attempts to ensure map has proper size
    const ensureMapSize = () => {
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
        }
        
        newMap.invalidateSize({ pan: false })
        const size = newMap.getSize()
        console.log('Map size after invalidateSize:', size);
        
        // If map still has no height, try again
        if (size.y === 0) {
          setTimeout(ensureMapSize, 100);
        }
      }
    };
    
    setTimeout(ensureMapSize, 200)

    // Create custom panes for proper layer ordering
    newMap.createPane('connectionsPane')
    newMap.createPane('lvPolesPane')
    newMap.createPane('mvPolesPane')
    newMap.createPane('dropLinesPane')
    newMap.createPane('lvLinesPane')
    newMap.createPane('mvLinesPane')
    
    // Set z-index for each pane according to specifications (from bottom to top)
    newMap.getPane('connectionsPane')!.style.zIndex = '600'   // Connections (bottom)
    newMap.getPane('lvPolesPane')!.style.zIndex = '700'       // LV poles
    newMap.getPane('mvPolesPane')!.style.zIndex = '750'       // MV poles
    newMap.getPane('dropLinesPane')!.style.zIndex = '800'     // Drop lines
    newMap.getPane('lvLinesPane')!.style.zIndex = '850'       // LV lines
    newMap.getPane('mvLinesPane')!.style.zIndex = '900'       // MV lines (top)
    
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
        try {
          newMap.invalidateSize()
        } catch (e) {
        }
      }
    })
    resizeObserver.observe(container)
    
    // Mark container as having resize observer
    container.setAttribute('data-resize-observer', 'true')
    
    // Add click handler for editing
    newMap.on('click', handleMapClick)
    
    // Store reference for cleanup
    setMap(newMap)
    resizeObserverRef.current = resizeObserver
    
    // Store in window for debugging and persistence
    if (typeof window !== 'undefined') {
      (window as any).__leafletMapInstance = newMap
    }
  }, [handleMapClick, setMap])

  // Skip cleanup in development to avoid destroying map on hot reload/StrictMode
  useEffect(() => {
    return () => {
      // In development, React StrictMode causes double mounting
      // Skip cleanup to preserve map instance
      if (process.env.NODE_ENV === 'development') {
        return
      }
      
      // Only clean up in production
      const mapInstance = typeof window !== 'undefined' ? (window as any).__leafletMap : null
      if (mapInstance) {
        if ((mapInstance as any)._wrapperObserver) {
          (mapInstance as any)._wrapperObserver.disconnect()
        }
        try {
          mapInstance.remove()
        } catch (e) {
        }
      }
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
      }
    }
  }, [])

  // Handle layer visibility changes
  React.useEffect(() => {
    if (!map || !layerGroupsRef.current) return

    // Toggle layer visibility based on state
    Object.entries(layerVisibility).forEach(([layer, visible]) => {
      const layerGroup = layerGroupsRef.current[layer as keyof typeof layerGroupsRef.current]
      if (layerGroup) {
        if (visible) {
          if (!map.hasLayer(layerGroup)) {
            layerGroup.addTo(map)
          }
        } else {
          if (map.hasLayer(layerGroup)) {
            map.removeLayer(layerGroup)
          }
        }
      }
    })
  }, [map, layerVisibility])

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
      // Use contain: layout instead of strict to allow rendering but prevent size changes
      boundary.style.setProperty('contain', 'layout', 'important')
      // Remove any problematic properties
      boundary.style.removeProperty('inset')
      boundary.style.removeProperty('margin')
      boundary.style.removeProperty('padding')
      boundary.style.removeProperty('transform')
      boundary.style.removeProperty('clip-path')  // Remove clip-path to allow SVG rendering
    }

    const enforceWrapperStyles = () => {
      wrapper.style.setProperty('position', 'relative', 'important')
      wrapper.style.setProperty('width', '100%', 'important')
      wrapper.style.setProperty('height', '100%', 'important')
      wrapper.style.setProperty('overflow', 'visible', 'important')  // Allow overflow for markers
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
  }, [map])

  // Network data effect - just call updateNetworkData
  useEffect(() => {
    if (!map || !networkData) {
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
        onNewPole={handleNewPole}
        onNewConnection={handleNewConnection}
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
