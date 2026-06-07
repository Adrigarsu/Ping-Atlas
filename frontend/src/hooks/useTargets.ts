import { useEffect, useState } from 'react'

export interface Target {
  id: string
  host: string
  label: string | null
  created_at: string
}

export function useTargets(refreshSignal: number): Target[] {
  const [targets, setTargets] = useState<Target[]>([])

  useEffect(() => {
    fetch('/api/targets')
      .then((r) => r.json())
      .then((data: Target[]) => setTargets(data))
      .catch(() => setTargets([]))
  }, [refreshSignal])

  return targets
}