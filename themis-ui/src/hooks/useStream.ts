import { useEffect, useState, useRef } from "react"
import type { StreamEvent, SessionStatus } from "../types"

export function useStream(sid: string | undefined) {
  const [event, setEvent] = useState<StreamEvent | null>(null)
  const [done,  setDone]  = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!sid) return
    const es = new EventSource(`http://localhost:8000/sessions/${sid}/stream`)
    esRef.current = es
    es.onmessage = (e) => {
      try {
        const d: StreamEvent = JSON.parse(e.data)
        setEvent(d)
        if (d.status === "completed" || d.status === "error") {
          setDone(true)
          es.close()
        }
      } catch {}
    }
    es.onerror = () => {
      setEvent(prev => prev
        ? { ...prev, status: "error" as SessionStatus }
        : { session_id: sid, status: "error", progress_pct: 0, hitl_required: false }
      )
      setDone(true)
      es.close()
    }
    return () => es.close()
  }, [sid])

  return { event, done }
}