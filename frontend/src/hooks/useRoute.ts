import { useEffect, useState } from 'react'

export function useRoute(targetId: string | null, refreshSignal: number): [number, number][] {
  const [route, setRoute] = useState<[number, number][]>([])

  useEffect(() => {
    if (!targetId) {
      setRoute([])
      return
    }
    fetch(`/api/routes/${targetId}`)
      .then((r) => r.json())
      .then((data: { hops: [number, number][] }) => setRoute(data.hops))
      .catch(() => setRoute([]))
  }, [targetId, refreshSignal])

  return route
}