import type { Contradiction } from "../../types"
import { Card } from "../ui/Card"

export function ContradictionCard({ c }: { c: Contradiction }) {
  return (
    <Card style={{ padding:"18px 20px", borderLeft:"3px solid #ef4444" }}>
      <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
        <span style={{ fontSize:14 }}>⚠</span>
        <span style={{ fontFamily:"var(--mono)", fontSize:9, letterSpacing:2, color:"#f87171", textTransform:"uppercase" }}>
          ContradictionDetector™ · {c.contradiction_type} · Severity {c.severity}/4
        </span>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12 }}>
        {[{ loc:c.location_a, stmt:c.statement_a }, { loc:c.location_b, stmt:c.statement_b }].map((x,i) => (
          <div key={i} style={{
            padding:"10px 12px", borderRadius:8,
            background:"rgba(239,68,68,0.06)", border:"1px solid rgba(239,68,68,0.15)"
          }}>
            <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"#f87171", marginBottom:4, letterSpacing:.5 }}>{x.loc}</div>
            <div style={{ fontSize:12, color:"var(--text2)", lineHeight:1.5 }}>{x.stmt}</div>
          </div>
        ))}
      </div>

      <div style={{ fontSize:12, color:"var(--text2)", marginBottom:4 }}>
        <strong style={{ color:"var(--text)" }}>Legal risk:</strong> {c.legal_risk}
      </div>
      <div style={{ fontSize:12, color:"var(--text3)" }}>
        <strong style={{ color:"var(--text2)" }}>Resolution:</strong> {c.resolution_hint}
      </div>
    </Card>
  )
}