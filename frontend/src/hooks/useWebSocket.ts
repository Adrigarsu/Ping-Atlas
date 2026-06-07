import { useEffect, useRef, useState } from 'react'

export interface HopMessage {
  probe_id: string
  ttl: number
  ip: string | null
  rtt_ms: number | null
  lat: number | null
  lon: number | null
  country: string | null
  city: string | null
}

export function useWebSocket(url: string): HopMessage[] {
  const [hops, setHops] = useState<HopMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (event: MessageEvent<string>) => {
      const hop = JSON.parse(event.data) as HopMessage
      if (hop.lat !== null && hop.lon !== null) {
        setHops((prev) => [...prev, hop])
      }
    }

    ws.onerror = () => ws.close()

    return () => ws.close()
  }, [url])

  return hops
}