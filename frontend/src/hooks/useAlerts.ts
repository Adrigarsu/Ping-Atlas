import { useEffect, useState } from 'react'

export interface Alert {
  id: string
  target_id: string
  probe_id: string
  triggered_at: string
  rtt_ms: number
  rolling_avg_ms: number
  delta_ms: number
  resolved: boolean
}

export function useAlerts(targetId: string | null, refreshSignal: number): Alert[] {
  const [alerts, setAlerts] = useState<Alert[]>([])

  useEffect(() => {
    if (!targetId) {
      setAlerts([])
      return
    }
    fetch(`/api/alerts?target_id=${encodeURIComponent(targetId)}`)
      .then((r) => r.json())
      .then((data: Alert[]) => setAlerts(data))
      .catch(() => setAlerts([]))
  }, [targetId, refreshSignal])

  return alerts
}