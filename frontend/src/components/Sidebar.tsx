import { useState } from 'react'
import type { ProbeResult } from '../hooks/useProbeResults'
import { useProbeResults } from '../hooks/useProbeResults'
import type { Target } from '../hooks/useTargets'
import { useTargets } from '../hooks/useTargets'
import LatencyChart from './LatencyChart'

interface Props {
  refreshSignal: number
  onTargetChange: (target: Target | null) => void
}

function ProbeStats({ results }: { results: ProbeResult[] }) {
  const last = results[0]
  if (!last) return null

  const rtts = results.map((r) => r.rtt_ms).filter((v): v is number => v !== null)
  const min = rtts.length ? Math.min(...rtts).toFixed(1) : '—'
  const avg = rtts.length ? (rtts.reduce((a, b) => a + b, 0) / rtts.length).toFixed(1) : '—'
  const max = rtts.length ? Math.max(...rtts).toFixed(1) : '—'
  const ts = new Date(last.started_at).toLocaleString()

  return (
    <div style={{ fontSize: '0.8rem', color: '#9ca3af', display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div><span style={{ color: '#6b7280' }}>Last probe:</span> {ts}</div>
      <div style={{ display: 'flex', gap: 12 }}>
        <span><span style={{ color: '#22c55e' }}>min</span> {min} ms</span>
        <span><span style={{ color: '#6366f1' }}>avg</span> {avg} ms</span>
        <span><span style={{ color: '#ef4444' }}>max</span> {max} ms</span>
      </div>
    </div>
  )
}

export default function Sidebar({ refreshSignal, onTargetChange }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [probing, setProbing] = useState(false)

  const targets = useTargets(refreshSignal)
  const selected = targets.find((t) => t.id === selectedId) ?? null
  const results = useProbeResults(selected?.host ?? null, refreshSignal)

  function handleSelect(t: Target) {
    setSelectedId(t.id)
    onTargetChange(t)
  }

  async function handleProbe() {
    if (!selected) return
    setProbing(true)
    try {
      await fetch('/api/probe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: selected.host }) })
    } finally {
      setProbing(false)
    }
  }

  return (
    <aside style={{
      width: 'clamp(260px, 25vw, 340px)',
      background: '#111827',
      color: '#f9fafb',
      display: 'flex',
      flexDirection: 'column',
      padding: '1rem',
      gap: '0.75rem',
      overflowY: 'auto',
      flexShrink: 0,
    }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Targets</h2>

      {targets.length === 0 ? (
        <p style={{ fontSize: '0.8rem', color: '#6b7280' }}>No targets yet. Run a probe first.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {targets.map((t) => (
            <li key={t.id}>
              <button
                onClick={() => handleSelect(t)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  background: t.id === selectedId ? '#1e3a5f' : '#1f2937',
                  border: `1px solid ${t.id === selectedId ? '#6366f1' : '#374151'}`,
                  borderRadius: 6,
                  color: '#f9fafb',
                  padding: '0.4rem 0.75rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                {t.label ?? t.host}
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <>
          <button
            onClick={handleProbe}
            disabled={probing}
            style={{
              background: probing ? '#374151' : '#6366f1',
              border: 'none',
              borderRadius: 6,
              color: '#fff',
              padding: '0.5rem',
              cursor: probing ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500,
            }}
          >
            {probing ? 'Probing…' : `Probe ${selected.host}`}
          </button>

          <ProbeStats results={results} />

          <h3 style={{ fontSize: '0.875rem', fontWeight: 500, margin: 0 }}>Latency over time</h3>
          <LatencyChart results={results} />
        </>
      )}
    </aside>
  )
}