import { useState, useEffect, useRef } from 'react'
import { MONKEY_WS_URL } from '@/api/client'

export type ModelStatus = 'idle' | 'loading' | 'inferring'

export interface AllowedApp {
  app_name: string
  version: number
}

export interface ActiveRequest {
  session_id: number
  question_preview: string
  started_at: string
}

export interface InstanceStatus {
  instance_id: string
  healthy: boolean
  model_status: ModelStatus
  current_model: string | null
  queue_size: number
  active_request: ActiveRequest | null
  allowed_apps: AllowedApp[]
}

export function useMonkeyStatus() {
  const [instances, setInstances] = useState<InstanceStatus[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let cancelled = false
    const wsUrl = `${MONKEY_WS_URL}/ws/status`

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (!cancelled) setConnected(true)
      }

      ws.onmessage = (event) => {
        if (cancelled) return
        try {
          const data: InstanceStatus[] = JSON.parse(event.data)
          setInstances(data)
        } catch {
          // ignore parse error
        }
      }

      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        setTimeout(connect, 5000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [])

  return { instances, connected }
}
