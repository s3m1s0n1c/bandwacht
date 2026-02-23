import { useCallback, useEffect, useState } from 'react'
import { events as api } from '../api/client'
import type { DetectionEvent, PaginatedResponse } from '../types'

export function useEvents(params?: {
  page?: number
  page_size?: number
  instance_id?: number
  label?: string
}) {
  const [data, setData] = useState<PaginatedResponse<DetectionEvent>>({
    items: [], total: 0, page: 1, page_size: 50, pages: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await api.list(params)
      setData(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => { refresh() }, [refresh])

  return { ...data, loading, error, refresh }
}
