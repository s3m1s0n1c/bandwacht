import { useCallback, useEffect, useRef, useState } from 'react'

interface UseWebSocketOptions {
  url: string
  enabled?: boolean
  onMessage?: (data: any) => void
  reconnectInterval?: number
}

export function useWebSocket({ url, enabled = true, onMessage, reconnectInterval = 3000 }: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!enabled) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = url.startsWith('ws') ? url : `${protocol}//${window.location.host}${url}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (enabled) {
          reconnectTimer.current = setTimeout(connect, reconnectInterval)
        }
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          onMessageRef.current?.(data)
        } catch {
          // ignore
        }
      }
    } catch {
      if (enabled) {
        reconnectTimer.current = setTimeout(connect, reconnectInterval)
      }
    }
  }, [url, enabled, reconnectInterval])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { connected }
}
