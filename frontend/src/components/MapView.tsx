import 'leaflet/dist/leaflet.css'
import { useMemo } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet'
import { useRoute } from '../hooks/useRoute'
import { type HopMessage, useWebSocket } from '../hooks/useWebSocket'

const INITIAL_CENTER: [number, number] = [20, 0]
const INITIAL_ZOOM = 2
const WS_URL = `ws://${window.location.host}/live`

interface Props {
  selectedTargetId: string | null
  refreshSignal: number
}

function rttColor(rtt: number | null): string {
  if (rtt === null) return '#9ca3af'
  if (rtt < 50) return '#22c55e'
  if (rtt < 150) return '#eab308'
  return '#ef4444'
}

function groupByProbe(hops: HopMessage[]): Map<string, HopMessage[]> {
  const groups = new Map<string, HopMessage[]>()
  for (const hop of hops) {
    const list = groups.get(hop.probe_id) ?? []
    list.push(hop)
    groups.set(hop.probe_id, list)
  }
  return groups
}

export default function MapView({ selectedTargetId, refreshSignal }: Props) {
  const hops = useWebSocket(WS_URL)
  const route = useRoute(selectedTargetId, refreshSignal)

  const probeGroups = useMemo(() => groupByProbe(hops), [hops])

  return (
    <MapContainer
      center={INITIAL_CENTER}
      zoom={INITIAL_ZOOM}
      style={{ height: '100vh', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {route.length > 1 && (
        <Polyline positions={route} pathOptions={{ color: '#f59e0b', weight: 3, dashArray: '6 4' }} />
      )}

      {Array.from(probeGroups.entries()).map(([probeId, probeHops]) => {
        const sorted = [...probeHops].sort((a, b) => a.ttl - b.ttl)
        const positions = sorted.map((h) => [h.lat!, h.lon!] as [number, number])

        return (
          <span key={probeId}>
            <Polyline positions={positions} pathOptions={{ color: '#6366f1', weight: 2 }} />

            {sorted.map((hop) => (
              <CircleMarker
                key={`${hop.probe_id}-${hop.ttl}`}
                center={[hop.lat!, hop.lon!]}
                radius={7}
                pathOptions={{
                  color: rttColor(hop.rtt_ms),
                  fillColor: rttColor(hop.rtt_ms),
                  fillOpacity: 0.85,
                }}
              >
                <Popup>
                  <strong>Hop {hop.ttl}</strong>
                  <br />
                  IP: {hop.ip ?? '—'}
                  <br />
                  RTT: {hop.rtt_ms !== null ? `${hop.rtt_ms} ms` : 'timeout'}
                  <br />
                  {hop.country && <>Country: {hop.country}<br /></>}
                  {hop.city && <>City: {hop.city}<br /></>}
                </Popup>
              </CircleMarker>
            ))}
          </span>
        )
      })}
    </MapContainer>
  )
}
