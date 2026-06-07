import 'leaflet/dist/leaflet.css'
import { useMemo } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet'
import type { ProbeResult } from '../hooks/useProbeResults'
import { useRoute } from '../hooks/useRoute'
import { type HopMessage, useWebSocket } from '../hooks/useWebSocket'

const INITIAL_CENTER: [number, number] = [20, 0]
const INITIAL_ZOOM = 2
const WS_URL = `ws://${window.location.host}/live`

interface Props {
  selectedTargetId: string | null
  selectedProbe: ProbeResult | null
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

export default function MapView({ selectedTargetId, selectedProbe, refreshSignal }: Props) {
  const hops = useWebSocket(WS_URL)
  const fallbackRoute = useRoute(selectedTargetId, refreshSignal)

  const probeGroups = useMemo(() => groupByProbe(hops), [hops])

  const selectedRoute = useMemo<[number, number][]>(() => {
    if (!selectedProbe) return []
    return selectedProbe.hops
      .filter((h) => h.latitude !== null && h.longitude !== null)
      .sort((a, b) => a.ttl - b.ttl)
      .map((h) => [h.latitude!, h.longitude!])
  }, [selectedProbe])

  const activeRoute = selectedRoute.length > 0 ? selectedRoute : fallbackRoute

  // Deduplicate consecutive identical coordinates (Docker NAT causes all hops to share one IP)
  const dedupedRoute = useMemo<[number, number][]>(() => {
    const seen = new Set<string>()
    return activeRoute.filter(([lat, lon]) => {
      const key = `${lat},${lon}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }, [activeRoute])

  const routeColor = selectedRoute.length > 0 ? '#a855f7' : '#f59e0b'
  const noLocationData = selectedTargetId !== null && dedupedRoute.length === 0 && hops.length === 0

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
    {noLocationData && (
      <div style={{
        position: 'absolute',
        top: 12,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        background: '#1f2937',
        border: '1px solid #4b5563',
        borderRadius: 8,
        padding: '6px 14px',
        fontSize: '0.8rem',
        color: '#9ca3af',
        pointerEvents: 'none',
        whiteSpace: 'nowrap',
      }}>
        No location data — IP not found in GeoIP database
      </div>
    )}
    <MapContainer
      center={INITIAL_CENTER}
      zoom={INITIAL_ZOOM}
      style={{ height: '100vh', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {dedupedRoute.length > 1 && (
        <Polyline
          positions={dedupedRoute}
          pathOptions={{ color: routeColor, weight: 3, dashArray: '6 4' }}
        />
      )}

      {dedupedRoute.map(([lat, lon], i) => (
        <CircleMarker
          key={`route-${lat}-${lon}-${i}`}
          center={[lat, lon]}
          radius={8}
          pathOptions={{ color: routeColor, fillColor: routeColor, fillOpacity: 0.85 }}
        />
      ))}

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
    </div>
  )
}