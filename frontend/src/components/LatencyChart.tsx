import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ProbeResult } from '../hooks/useProbeResults'

interface Props {
  results: ProbeResult[]
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function LatencyChart({ results }: Props) {
  if (results.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#9ca3af', textAlign: 'center' }}>
        No probes yet for this target.
      </div>
    )
  }

  const data = [...results]
    .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime())
    .map((r) => ({
      time: formatTime(r.started_at),
      rtt: r.rtt_ms !== null ? Math.round(r.rtt_ms * 10) / 10 : null,
    }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} />
        <YAxis unit=" ms" tick={{ fontSize: 11, fill: '#9ca3af' }} width={56} />
        <Tooltip
          contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 6 }}
          labelStyle={{ color: '#f9fafb' }}
          itemStyle={{ color: '#6366f1' }}
        />
        <Line
          type="monotone"
          dataKey="rtt"
          stroke="#6366f1"
          strokeWidth={2}
          dot={{ r: 3 }}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}