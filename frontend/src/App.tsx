import { useEffect, useRef, useState } from 'react'
import MapView from './components/MapView'
import Sidebar from './components/Sidebar'
import type { HopMessage } from './hooks/useWebSocket'

const WS_URL = `ws://${window.location.host}/live`

export default function App() {
  const [refreshSignal, setRefreshSignal] = useState(0)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)

    ws.onmessage = (e: MessageEvent<string>) => {
      const hop = JSON.parse(e.data) as HopMessage
      if (hop.rtt_ms !== null) {
        if (debounceRef.current) clearTimeout(debounceRef.current)
        debounceRef.current = setTimeout(() => setRefreshSignal((s) => s + 1), 2000)
      }
    }

    ws.onerror = () => ws.close()
    return () => ws.close()
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100%' }}>
      <div style={{ flex: 1, position: 'relative' }}>
        <MapView />
      </div>
      <Sidebar refreshSignal={refreshSignal} />
    </div>
  )
}