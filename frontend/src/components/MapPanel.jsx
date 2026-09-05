import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet'

const BEIJING = [39.925, 116.395]

function lineCoordinates(geometry) {
  return geometry?.coordinates?.map(([longitude, latitude]) => [latitude, longitude]) ?? []
}

export default function MapPanel({ trajectories = [], hotspots = [], selectedHotspot, onHotspotSelect }) {
  return (
    <div className="map-wrap">
      <MapContainer center={BEIJING} zoom={10} scrollWheelZoom className="map-canvas">
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {trajectories.slice(0, 40).map((trajectory) => (
          <Polyline
            key={trajectory.trajectory_id}
            positions={lineCoordinates(trajectory.geometry)}
            pathOptions={{ color: '#35d2b2', weight: 2, opacity: 0.54 }}
          />
        ))}
        {hotspots.map((hotspot) => {
          const active = selectedHotspot?.hotspot_id === hotspot.hotspot_id
          const radius = Math.min(20, Math.max(7, Math.sqrt(hotspot.visit_count) / 2.4))
          return (
            <CircleMarker
              key={hotspot.hotspot_id}
              center={[hotspot.center.latitude, hotspot.center.longitude]}
              radius={active ? radius + 5 : radius}
              eventHandlers={{ click: () => onHotspotSelect?.(hotspot) }}
              pathOptions={{
                color: active ? '#ffb36a' : '#45e0c2',
                fillColor: active ? '#ffb36a' : '#45e0c2',
                fillOpacity: active ? 0.8 : 0.56,
                weight: active ? 3 : 1,
              }}
            >
              <Tooltip direction="top" offset={[0, -8]}>
                {hotspot.hotspot_id} · {hotspot.visit_count.toLocaleString()} visits
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="map-legend">
        <span><i className="legend-dot trajectory" />轨迹线</span>
        <span><i className="legend-dot hotspot" />热点中心</span>
        <span className="map-coordinates">39.925°N · 116.395°E</span>
      </div>
    </div>
  )
}

