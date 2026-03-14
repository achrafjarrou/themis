import { useState } from "react"
import type { ComplianceGap } from "../../types"
import { StatusBadge } from "../ui/Badge"
import { Card } from "../ui/Card"

const STEP_STYLE: Record<string, { icon:string; bg:string; color:string; border:string }> = {
  LEGAL_PREMISE: { icon:"⚖", bg:"rgba(59,130,246,0.07)",  color:"#93c5fd", border:"rgba(59,130,246,0.15)" },
  DOCUMENT_FACT: { icon:"📄", bg:"rgba(100,116,139,0.06)", color:"#94a3b8", border:"rgba(100,116,139,0.15)" },
  INFERENCE:     { icon:"→",  bg:"rgba(245,158,11,0.07)",  color:"#fbbf24", border:"rgba(245,158,11,0.15)" },
  CONCLUSION:    { icon:"✓",  bg:"rgba(16,185,129,0.07)",  color:"#34d399", border:"rgba(16,185,129,0.15)" },
}

export function EvidenceChainCard({ gap }: { gap: ComplianceGap }) {
  const [open, setOpen] = useState(false)
  const ec = gap.evidence_chain

  return (
    <Card style={{ padding:0, overflow:"hidden" }}>
      {/* Header */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width:"100%", padding:"16px 20px",
          display:"flex", alignItems:"center", gap:14,
          background:"none", border:"none", cursor:"pointer", textAlign:"left",
        }}
      >
        {/* Status stripe */}
        <div style={{
          width:3, alignSelf:"stretch", borderRadius:2, flexShrink:0,
          background: gap.status==="compliant" ? "#10b981" : gap.status==="partial" ? "#f59e0b" : "#ef4444"
        }} />

        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
            <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:1, textTransform:"uppercase" }}>
              {gap.framework.replace(/_/g," ")}
            </span>
            <StatusBadge status={gap.status} />
            <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text4)", marginLeft:"auto" }}>
              #{ec.chain_hash}
            </span>
          </div>
          <div style={{ fontFamily:"var(--display)", fontWeight:700, fontSize:15, color:"#e2e8f0" }}>
            {gap.article_num}
            <span style={{ fontWeight:400, fontSize:12, color:"var(--text2)", marginLeft:8 }}>{gap.article_title}</span>
          </div>
        </div>

        {/* Severity + chevron */}
        <div style={{ display:"flex", alignItems:"center", gap:10, flexShrink:0 }}>
          <div style={{ display:"flex", gap:3 }}>
            {[1,2,3,4].map(i => (
              <div key={i} style={{
                width:6, height:6, borderRadius:1,
                background: i <= gap.severity
                  ? (gap.severity >= 4 ? "#ef4444" : gap.severity >= 3 ? "#f97316" : gap.severity >= 2 ? "#f59e0b" : "#10b981")
                  : "var(--border2)"
              }} />
            ))}
          </div>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--text3)" strokeWidth="1.5"
            style={{ transform: open ? "rotate(180deg)" : "none", transition:"transform .2s" }}>
            <path d="M2 4l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {/* Expanded */}
      {open && (
        <div style={{ padding:"0 20px 20px", animation:"fadeUp .25s ease" }}>
          {/* Obligation */}
          <div style={{
            fontFamily:"var(--mono)", fontSize:11, color:"var(--text2)",
            background:"var(--bg3)", border:"1px solid var(--border)", borderRadius:8,
            padding:"10px 14px", marginBottom:14, lineHeight:1.6,
          }}>
            {gap.obligation}
          </div>

          {/* Evidence chain */}
          <div style={{ display:"flex", flexDirection:"column", gap:3, marginBottom:14 }}>
            {ec.links.map(link => {
              const s = STEP_STYLE[link.step_type] ?? STEP_STYLE.INFERENCE
              return (
                <div key={link.step_num} style={{
                  display:"flex", gap:12, padding:"10px 12px",
                  background:s.bg, border:`1px solid ${s.border}`, borderRadius:8,
                }}>
                  <span style={{ fontSize:14, flexShrink:0, marginTop:1 }}>{s.icon}</span>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontFamily:"var(--mono)", fontSize:8, color:s.color, letterSpacing:2, textTransform:"uppercase", marginBottom:3 }}>
                      {link.step_type} · {link.source_ref} · {(link.confidence*100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize:12, color:"#e2e8f0", lineHeight:1.5 }}>{link.claim}</div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Remediation */}
          {gap.remediation_steps.length > 0 && (
            <div>
              <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:2, textTransform:"uppercase", marginBottom:8 }}>
                Remediation Steps
              </div>
              {gap.remediation_steps.map((s, i) => (
                <div key={i} style={{ display:"flex", gap:10, marginBottom:6 }}>
                  <span style={{ fontFamily:"var(--mono)", fontSize:11, color:"#ef4444", fontWeight:700, flexShrink:0 }}>{i+1}.</span>
                  <span style={{ fontSize:12, color:"var(--text2)", lineHeight:1.5 }}>{s}</span>
                </div>
              ))}
            </div>
          )}

          {/* Deadline + Cross refs */}
          {(gap.deadline_risk || gap.cross_framework_refs.length > 0) && (
            <div style={{ display:"flex", gap:8, marginTop:12, flexWrap:"wrap" }}>
              {gap.deadline_risk && (
                <span style={{ fontFamily:"var(--mono)", fontSize:9, padding:"3px 8px", borderRadius:4, background:"rgba(239,68,68,0.1)", color:"#ef4444", border:"1px solid rgba(239,68,68,0.2)" }}>
                  ⏱ {gap.deadline_risk}
                </span>
              )}
              {gap.cross_framework_refs.map((r,i) => (
                <span key={i} style={{ fontFamily:"var(--mono)", fontSize:9, padding:"3px 8px", borderRadius:4, background:"rgba(139,92,246,0.1)", color:"#a78bfa", border:"1px solid rgba(139,92,246,0.2)" }}>
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}