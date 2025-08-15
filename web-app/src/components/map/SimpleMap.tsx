'use client'

import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

export function SimpleMap() {
  console.log('SimpleMap rendering')
  
  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      <h1 style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 1000, background: 'white', padding: '10px' }}>
        Test Map
      </h1>
      <MapContainer
        center={[-30.07, 27.85]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
      </MapContainer>
    </div>
  )
}
