import { useState } from 'react'
import type { Alert } from '../hooks/useAlerts'
import type { ProbeResult } from '../hooks/useProbeResults'

interface Props {
  probes: ProbeResult[]
  alerts: Alert[]
  selectedProbeId: string | null
  onSelect: (probe: ProbeResult) => void
}

function rttColor(rtt: number | null): string {
  if (rtt === null) return '#4b5563'
  if (rtt < 50) return '#22c55e'
  if (rtt < 150) return '#eab308'
  return '#ef4444'
}

function formatTs(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

export default function ProbeTimeline({ probes, alerts, selectedProbeId, onSelect }: Props) {
  const [hoveredAlertId, setHoveredAlertId] = useState<string | null>(null)

  if (probes.length === 0) return null

  const alertByProbe = new Map(alerts.map((a) => [a.probe_id, a]))
  const sorted = [...probes].sort(
    (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <h3 style={{ fontSize: '0.875rem', fontWeight: 500, margin: 0 }}>Timeline</h3>
      <div
        style={{
          overflowX: 'auto',
          paddingBottom: 4,
          display: 'flex',
          alignItems: 'flex-end',
          gap: 3,
          minHeight: 56,
        }}
      >
        {sorted.map((probe) => {
          const alert = alertByProbe.get(probe.id)
          const isSelected = probe.id === selectedProbeId
          const color = rttColor(probe.rtt_ms)
          const label = probe.rtt_ms !== null ? `${probe.rtt_ms.toFixed(0)} ms` : 'n/a'
          const tooltip = `${formatTs(probe.started_at)}\nRTT: ${label}${alert ? `\n⚠ Alert: +${alert.delta_ms.toFixed(1)} ms above avg` : ''}`

          return (
            <div key={probe.id} style={{ position: 'relative', flexShrink: 0 }}>
              {alert && (
                <div
                  onMouseEnter={() => setHoveredAlertId(probe.id)}
                  onMouseLeave={() => setHoveredAlertId(null)}
                  style={{
                    position: 'absolute',
                    top: -8,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#ef4444',
                    cursor: 'default',
                    zIndex: 10,
                  }}
                >
                  {hoveredAlertId === probe.id && (
                    <div
                      style={{
                        position: 'absolute',
                        bottom: 12,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: '#1f2937',
                        border: '1px solid #ef4444',
                        borderRadius: 4,
                        padding: '4px 8px',
                        fontSize: '0.7rem',
                        color: '#f9fafb',
                        whiteSpace: 'nowrap',
                        pointerEvents: 'none',
                        zIndex: 20,
                      }}
                    >
                      ⚠ +{alert.delta_ms.toFixed(1)} ms above avg ({alert.rolling_avg_ms.toFixed(1)} ms)
                    </div>
                  )}
                </div>
              )}
              <div
                title={tooltip}
                onClick={() => onSelect(probe)}
                style={{
                  width: 10,
                  height: 40,
                  background: color,
                  borderRadius: 2,
                  cursor: 'pointer',
                  outline: isSelected ? '2px solid #fff' : 'none',
                  outlineOffset: 1,
                  opacity: isSelected ? 1 : 0.75,
                  transition: 'opacity 0.1s',
                }}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}