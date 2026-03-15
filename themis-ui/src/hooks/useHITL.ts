import { useEffect, useRef, useState } from "react"

const HF_BASE = "wss://achrafjarrou-themis.hf.space"

export function useHITL(sid: string | undefined, active: boolean) {
  const wsRef  = useRef<WebSocket | null>(null)
  const [data, setData]  = useState<any>(null)
  const [sent, setSent]  = useState(false)

  useEffect(() => {
    if (!sid || !active) return
    const ws = new WebSocket(HF_BASE + "/sessions/" + sid + "/hitl")
    wsRef.current = ws
    ws.onmessage = (e) => {
      const d = JSON.parse(e.data)
      if (d.type === "review_required") setData(d.data)
    }
    return () => ws.close()
  }, [sid, active])

  const approve = (approved: boolean, notes = "") => {
    wsRef.current?.send(JSON.stringify({ approved, notes }))
    setSent(true)
  }

  return { hitlData: data, approve, sent }
}
