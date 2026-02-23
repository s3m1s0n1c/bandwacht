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
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage
  const enabledRef = useRef(enabled)
  enabledRef.current = enabled

  const connect = useCallback(() => {
    if (!enabledRef.current) return

    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = url.startsWith('ws') ? url : `${protocol}//${window.location.host}${url}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        if (enabledRef.current) {
          reconnectTimer.current = setTimeout(connect, reconnectInterval)
        }
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          onMessageRef.current?.(data)
        } catch (_) {
          // ignore
        }
      }
    } catch (_) {
      if (enabledRef.current) {
        reconnectTimer.current = setTimeout(connect, reconnectInterval)
      }
    }
  }, [url, reconnectInterval])

  useEffect(() => {
    clearTimeout(reconnectTimer.current)
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
      wsRef.current = null
    }
    if (enabled) {
      connect()
    } else {
      setConnected(false)
    }
    return () => {
      clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [enabled, connect])

  return { connected }
}
