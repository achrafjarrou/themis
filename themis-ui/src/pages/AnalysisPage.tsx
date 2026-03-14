import { useEffect, useState, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Navbar } from "../components/layout/Navbar"
import { PipelineTracker } from "../components/pipeline/PipelineTracker"
import { Button } from "../components/ui/Button"
import { useStream } from "../hooks/useStream"
import { useHITL } from "../hooks/useHITL"
import { api } from "../lib/api"
import { fmt, scoreColor } from "../lib/utils"

export default function AnalysisPage() {
  const { sid } = useParams<{ sid:string }>()
  const nav = useNavigate()
  const { event } = useStream(sid)
  const [elapsed, setElapsed] = useState(0)
  const [report,  setReport]  = useState<any>(null)
  const timerRef = useRef<ReturnType<typeof setInterval>|null>(null)

  const status   = event?.status ?? "running"
  const node     = event?.current_node ?? "classify"
  const pct      = event?.progress_pct ?? 5
  const isRunning  = status === "running" || status === "pending"
  const isComplete = status === "completed"
  const isFailed   = status === "error"
  const isHITL     = status === "hitl_required"

  const { hitlData, approve, sent } = useHITL(sid, isHITL)

  // Timer
  useEffect(() => {
    if (isRunning || isHITL) {
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [isRunning, isHITL])

  // Fetch report on completion
  useEffect(() => {
    if (!isComplete || !sid) return
    api.report(sid).then(setReport).catch(() => {})
  }, [isComplete, sid])

  return (
    <div style={{ minHeight:"100vh", background:"var(--bg)", fontFamily:"var(--sans)" }}>
      <Navbar sid={sid} />

      <div style={{ maxWidth:720, margin:"0 auto", padding:"56px 24px 80px" }}>

        {/* Session ID */}
        <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text4)", letterSpacing:2, marginBottom:28 }}>
          SESSION {sid}
        </div>

        {/* Hero */}
        <div style={{ marginBottom:40 }}>
          <h1 style={{
            fontFamily:"var(--display)", fontWeight:800,
            fontSize:"clamp(36px,6vw,52px)", lineHeight:.9, letterSpacing:"-2px", color:"#fff", marginBottom:10,
          }}>
            Analysis<br />
            <span style={{
              background: isComplete
                ? "linear-gradient(135deg,#10b981,#06b6d4)"
                : isFailed
                ? "linear-gradient(135deg,#ef4444,#f59e0b)"
                : isHITL
                ? "linear-gradient(135deg,#f59e0b,#f97316)"
                : "linear-gradient(135deg,#60a5fa,#a78bfa)",
              WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
              fontStyle:"italic",
            }}>
              {isComplete ? "Complete" : isFailed ? "Failed" : isHITL ? "Paused" : "Running"}
            </span>
          </h1>
          {(isRunning || isHITL) && (
            <div style={{ fontFamily:"var(--mono)", fontSize:12, color:"var(--text3)", display:"flex", alignItems:"center", gap:12 }}>
              <div style={{ flex:1, height:2, background:"var(--border2)", borderRadius:2, overflow:"hidden" }}>
                <div style={{ height:"100%", width:`${pct}%`, background:"linear-gradient(90deg,#3b82f6,#8b5cf6)", borderRadius:2, transition:"width .5s ease" }} />
              </div>
              <span>{pct}% · {fmt(elapsed)}</span>
            </div>
          )}
        </div>

        {/* Error */}
        {isFailed && (
          <div style={{ background:"rgba(239,68,68,0.07)", border:"1px solid rgba(239,68,68,0.2)", borderRadius:14, padding:"18px 22px", marginBottom:24 }}>
            <div style={{ fontFamily:"var(--display)", fontWeight:700, color:"#f87171", marginBottom:6 }}>⚠ Pipeline Error</div>
            <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"#7f1d1d", marginBottom:14 }}>
              {event?.current_msg ?? "Unknown error — check uvicorn logs"}
            </div>
            <Button variant="ghost" onClick={() => nav("/")}>← Try Again</Button>
          </div>
        )}

        {/* HITL */}
        {isHITL && hitlData && !sent && (
          <div style={{ background:"rgba(245,158,11,0.07)", border:"1px solid rgba(245,158,11,0.2)", borderRadius:14, padding:"20px 24px", marginBottom:24 }}>
            <div style={{ fontFamily:"var(--display)", fontWeight:700, color:"#fbbf24", marginBottom:8, fontSize:15 }}>
              👤 Human Review Required
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)", marginBottom:16 }}>
              Confidence: {(hitlData.confidence * 100).toFixed(0)}% · {hitlData.reason}
            </div>
            <div style={{ display:"flex", gap:10 }}>
              <Button variant="success" onClick={() => approve(true)}>✓ Approve & Continue</Button>
              <Button variant="danger"  onClick={() => approve(false)}>✗ Reject</Button>
            </div>
          </div>
        )}

        {/* Pipeline steps */}
        <PipelineTracker activeNode={node} elapsed={elapsed} completed={isComplete} />

        {/* Completed metrics */}
        {isComplete && report && (
          <div style={{ marginTop:36 }}>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10, marginBottom:24 }}>
              {[
                { label:"Compliance Score", value:`${report.compliance_score?.toFixed(1)}%`, color: scoreColor(report.compliance_score) },
                { label:"Gaps Identified",  value: String(report.gaps?.length ?? 0),         color:"#f59e0b" },
                { label:"Contradictions",   value: String(report.contradictions?.length ?? 0), color:"#a78bfa" },
              ].map((m,i) => (
                <div key={i} style={{ background:"var(--bg2)", border:"1px solid var(--border2)", borderRadius:12, padding:"18px 16px", textAlign:"center" }}>
                  <div style={{ fontFamily:"var(--display)", fontWeight:800, fontSize:26, color:m.color, marginBottom:4 }}>{m.value}</div>
                  <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:1.5, textTransform:"uppercase" }}>{m.label}</div>
                </div>
              ))}
            </div>

            <Button variant="success" onClick={() => nav(`/report/${sid}`)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              View Full Compliance Report
            </Button>
          </div>
        )}

        {(isRunning || isHITL) && (
          <p style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text4)", marginTop:28 }}>
            ~2–8 min · Groq LPU · llama-3.1-8b-instant · {fmt(elapsed)} elapsed
          </p>
        )}
      </div>
    </div>
  )
}