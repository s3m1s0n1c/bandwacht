import { useCallback, useEffect, useState } from 'react'
import { instances as api } from '../api/client'
import type { SdrInstance } from '../types'

export function useInstances() {
  const [data, setData] = useState<SdrInstance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.list()
      setData(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { instances: data, loading, error, refresh }
}
