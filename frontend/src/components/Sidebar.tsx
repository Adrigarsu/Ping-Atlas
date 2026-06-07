import { useState } from 'react'
import { useProbeResults } from '../hooks/useProbeResults'
import LatencyChart from './LatencyChart'

interface Props {
  refreshSignal: number
}

export default function Sidebar({ refreshSignal }: Props) {
  const [input, setInput] = useState('')
  const [target, setTarget] = useState<string | null>(null)

  const results = useProbeResults(target, refreshSignal)

  return (
    <aside style={{
      width: 320,
      background: '#111827',
      color: '#f9fafb',
      display: 'flex',
      flexDirection: 'column',
      padding: '1rem',
      gap: '0.75rem',
      overflowY: 'auto',
    }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Latency over time</h2>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && setTarget(input.trim() || null)}
          placeholder="hostname or IP…"
          style={{
            flex: 1,
            background: '#1f2937',
            border: '1px solid #374151',
            borderRadius: 6,
            color: '#f9fafb',
            padding: '0.4rem 0.6rem',
            fontSize: '0.875rem',
          }}
        />
        <button
          onClick={() => setTarget(input.trim() || null)}
          style={{
            background: '#6366f1',
            border: 'none',
            borderRadius: 6,
            color: '#fff',
            padding: '0.4rem 0.75rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Go
        </button>
      </div>

      {target && (
        <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
          Showing: <strong style={{ color: '#f9fafb' }}>{target}</strong>
        </p>
      )}

      <LatencyChart results={results} />
    </aside>
  )
}