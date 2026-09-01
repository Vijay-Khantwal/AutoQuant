import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(url, onMessage) {
  const ws = useRef(null)
  const timeoutRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!url) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const fullUrl = `${proto}://${window.location.host}${url}`
    
    ws.current = new WebSocket(fullUrl)
    
    ws.current.onmessage = (e) => {
      try { onMessageRef.current(JSON.parse(e.data)) } catch {}
    }
    
    ws.current.onclose = () => {
      // Auto-reconnect after 3 seconds
      timeoutRef.current = setTimeout(() => {
        connect()
      }, 3000)
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      if (ws.current) {
        ws.current.onclose = null // prevent reconnect loop on unmount
        ws.current.close()
      }
    }
  }, [connect])

  const close = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (ws.current) {
      ws.current.onclose = null
      ws.current.close()
    }
  }, [])
  
  return { close }
}
