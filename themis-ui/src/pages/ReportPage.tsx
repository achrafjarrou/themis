import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Navbar } from "../components/layout/Navbar"
import { EvidenceChainCard } from "../components/report/EvidenceChainCard"
import { ContradictionCard } from "../components/report/ContradictionCard"
import { ComplianceScore } from "../components/report/ComplianceScore"
import { RiskBadge } from "../components/ui/Badge"
import { Skeleton } from "../components/ui/Skeleton"
import { Button } from "../components/ui/Button"
import { api } from "../lib/api"
import { scoreColor, scoreLabel } from "../lib/utils"
import type { ComplianceReport } from "../types"

export default function ReportPage() {
  const { sid } = useParams<{ sid:string }>()
  const nav = useNavigate()
  const [r,       setR]       = useState<ComplianceReport|null>(null)
  const [loading, setLoading] = useState(true)
  const [tab,     setTab]     = useState<"gaps"|"contradictions">("gaps")

  useEffect(() => {
    if (!sid) return
    let tries = 0
    const poll = async () => {
      try {
        const data = await api.report(sid)
        setR(data); setLoading(false)
      } catch(e: any) {
        if (e.message?.includes("202") && tries++ < 30) setTimeout(poll, 6000)
        else setLoading(false)
      }
    }
    poll()
  }, [sid])

  if (loading) return (
    <div style={{ minHeight:"100vh", background:"var(--bg)" }}>
      <Navbar sid={sid} />
      <div style={{ maxWidth:760, margin:"0 auto", padding:"80px 24px" }}>
        <Skeleton h={48} w="60%" r={8} />
        <div style={{ marginTop:24, display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8 }}>
          {[...Array(4)].map((_,i) => <Skeleton key={i} h={80} r={10} />)}
        </div>
        <div style={{ marginTop:24, display:"flex", flexDirection:"column", gap:10 }}>
          {[...Array(5)].map((_,i) => <Skeleton key={i} h={64} r={10} />)}
        </div>
      </div>
    </div>
  )

  if (!r) return (
    <div style={{ minHeight:"100vh", background:"var(--bg)", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div style={{ textAlign:"center" }}>
        <p style={{ fontFamily:"var(--display)", fontSize:24, color:"#e2e8f0", marginBottom:16 }}>Report not found</p>
        <Button variant="ghost" onClick={() => nav("/")}>← New Analysis</Button>
      </div>
    </div>
  )

  const critical = r.gaps.filter(g => g.severity >= 4)
  const missing  = r.gaps.filter(g => g.status === "missing")

  return (
    <div style={{ minHeight:"100vh", background:"var(--bg)", fontFamily:"var(--sans)" }}>
      <Navbar sid={sid} />

      <div style={{ maxWidth:800, margin:"0 auto", padding:"52px 24px 80px" }}>

        {/* Header */}
        <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:24, marginBottom:36, paddingBottom:28, borderBottom:"1px solid var(--border2)" }}>
          <div>
            <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:2, textTransform:"uppercase", marginBottom:10 }}>
              THEMIS Compliance Report · {sid}
            </div>
            <h1 style={{ fontFamily:"var(--display)", fontWeight:800, fontSize:"clamp(28px,4vw,40px)", letterSpacing:"-1.5px", color:"#fff", lineHeight:.95, marginBottom:10 }}>
              {r.system_name}
            </h1>
            <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
              <RiskBadge level={r.risk_classification.risk_level} />
              {r.frameworks_analyzed.map(f => (
                <span key={f} style={{ fontFamily:"var(--mono)", fontSize:9, padding:"2px 8px", borderRadius:4, background:"var(--bg3)", color:"var(--text3)", border:"1px solid var(--border)" }}>
                  {f.replace(/_/g," ").toUpperCase()}
                </span>
              ))}
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text4)", marginTop:8 }}>
              {new Date(r.generated_at).toLocaleString("en-GB", { dateStyle:"long", timeStyle:"short" })}
            </div>
          </div>

          <div style={{ textAlign:"center", flexShrink:0 }}>
            <ComplianceScore score={r.compliance_score} size={96} />
            <div style={{ fontFamily:"var(--mono)", fontSize:9, color: scoreColor(r.compliance_score), letterSpacing:1.5, marginTop:6 }}>
              {scoreLabel(r.compliance_score)}
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:1, background:"var(--border)", borderRadius:14, overflow:"hidden", marginBottom:28 }}>
          {[
            { label:"Total Gaps",    value: r.gaps.length,             color:"#f59e0b" },
            { label:"Critical",      value: critical.length,           color:"#ef4444" },
            { label:"Missing",       value: missing.length,            color:"#ef4444" },
            { label:"Confidence",    value:`${(r.overall_confidence*100).toFixed(0)}%`, color:"#10b981" },
          ].map((s,i) => (
            <div key={i} style={{ background:"var(--bg2)", padding:"18px 14px", textAlign:"center" }}>
              <div style={{ fontFamily:"var(--display)", fontWeight:800, fontSize:24, color:s.color, marginBottom:4 }}>{s.value}</div>
              <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:1.5, textTransform:"uppercase" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Integrity banner */}
        <div style={{
          display:"flex", alignItems:"center", gap:10, padding:"12px 16px", borderRadius:10, marginBottom:28,
          background: r.evidence_integrity_ok ? "rgba(16,185,129,0.07)" : "rgba(239,68,68,0.07)",
          border:`1px solid ${r.evidence_integrity_ok ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`,
        }}>
          <span style={{ fontSize:16 }}>{r.evidence_integrity_ok ? "🔐" : "⚠"}</span>
          <span style={{ fontFamily:"var(--mono)", fontSize:11, color: r.evidence_integrity_ok ? "#34d399" : "#f87171" }}>
            EvidenceChain™ integrity {r.evidence_integrity_ok ? "verified — all SHA-256 hashes valid ✓" : "FAILED — chain may be tampered"}
          </span>
        </div>

        {/* Reasoning */}
        {r.risk_classification.reasoning && (
          <div style={{ background:"var(--bg2)", border:"1px solid var(--border2)", borderRadius:12, padding:"16px 18px", marginBottom:28 }}>
            <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)", letterSpacing:2, textTransform:"uppercase", marginBottom:8 }}>Risk Reasoning</div>
            <p style={{ fontSize:13, color:"var(--text2)", lineHeight:1.6 }}>{r.risk_classification.reasoning}</p>
          </div>
        )}

        {/* Tabs */}
        <div style={{ display:"flex", gap:2, marginBottom:20, background:"var(--bg2)", padding:3, borderRadius:10, width:"fit-content" }}>
          {(["gaps","contradictions"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding:"8px 20px", borderRadius:8, border:"none", cursor:"pointer",
              fontFamily:"var(--display)", fontWeight:700, fontSize:12, letterSpacing:.5,
              background: tab===t ? "linear-gradient(135deg,#2563eb,#7c3aed)" : "none",
              color: tab===t ? "#fff" : "var(--text3)",
              transition:"all .2s",
            }}>
              {t === "gaps" ? `Compliance Gaps (${r.gaps.length})` : `Contradictions (${r.contradictions.length})`}
            </button>
          ))}
        </div>

        {/* Gaps */}
        {tab === "gaps" && (
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {r.gaps.length === 0 ? (
              <div style={{ textAlign:"center", padding:40, color:"var(--text3)", fontFamily:"var(--mono)", fontSize:12 }}>
                ✓ No compliance gaps detected
              </div>
            ) : r.gaps.map(g => <EvidenceChainCard key={g.gap_id} gap={g} />)}
          </div>
        )}

        {/* Contradictions */}
        {tab === "contradictions" && (
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {r.contradictions.length === 0 ? (
              <div style={{ textAlign:"center", padding:40, color:"var(--text3)", fontFamily:"var(--mono)", fontSize:12 }}>
                ✓ No internal contradictions detected
              </div>
            ) : r.contradictions.map(c => <ContradictionCard key={c.contradiction_id} c={c} />)}
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop:40, paddingTop:20, borderTop:"1px solid var(--border)", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <span style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text4)" }}>
            Generated by THEMIS v1.0.0 · EvidenceChain™ integrity: {r.evidence_integrity_ok ? "verified" : "FAILED"}
          </span>
          <Button variant="ghost" onClick={() => nav("/")} style={{ padding:"8px 16px", fontSize:12 }}>
            ← New Analysis
          </Button>
        </div>
      </div>
    </div>
  )
}