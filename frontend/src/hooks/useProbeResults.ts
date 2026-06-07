import { useEffect, useState } from 'react'

export interface ProbeResult {
  id: string
  target_id: string
  started_at: string
  finished_at: string | null
  rtt_ms: number | null
  packet_loss: number | null
}

export function useProbeResults(target: string | null, refreshSignal: number): ProbeResult[] {
  const [results, setResults] = useState<ProbeResult[]>([])

  useEffect(() => {
    if (!target) {
      setResults([])
      return
    }

    const url = `/api/results?target=${encodeURIComponent(target)}&limit=50`
    fetch(url)
      .then((r) => r.json())
      .then((data: { items: ProbeResult[] }) => setResults(data.items))
      .catch(() => setResults([]))
  }, [target, refreshSignal])

  return results
}