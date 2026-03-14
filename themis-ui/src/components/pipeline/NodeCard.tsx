import { fmt } from "../../lib/utils"

type Status = "done" | "active" | "pending"

const STYLES = {
  done:    { row:"rgba(16,185,129,0.05)", border:"rgba(16,185,129,0.15)", ico:"rgba(16,185,129,0.15)", badge:"rgba(16,185,129,0.12)", bcolor:"#10b981" },
  active:  { row:"rgba(59,130,246,0.07)", border:"rgba(59,130,246,0.25)", ico:"rgba(59,130,246,0.15)", badge:"rgba(59,130,246,0.12)", bcolor:"#60a5fa" },
  pending: { row:"rgba(255,255,255,0.01)", border:"#0f172a",              ico:"rgba(255,255,255,0.03)", badge:"rgba(255,255,255,0.04)", bcolor:"#334155" },
}

export function NodeCard({ icon, label, sub, status, elapsed }: {
  icon:    string
  label:   string
  sub:     string
  status:  Status
  elapsed: number
}) {
  const s = STYLES[status]
  return (
    <div style={{
      display:"flex", alignItems:"center", gap:16,
      padding:"14px 18px", borderRadius:12,
      background: s.row, border:`1px solid ${s.border}`,
      transition:"all .35s",
      boxShadow: status==="active" ? "0 0 24px rgba(59,130,246,0.07)" : "none",
    }}>
      {/* Icon */}
      <div style={{
        width:38, height:38, borderRadius:10, flexShrink:0,
        display:"flex", alignItems:"center", justifyContent:"center",
        fontSize:17, background: s.ico,
      }}>{icon}</div>

      {/* Info */}
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ fontFamily:"var(--display)", fontWeight:600, fontSize:13, color:"#e2e8f0", marginBottom:2 }}>{label}</div>
        <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", letterSpacing:.3 }}>{sub}</div>
      </div>

      {/* Badge */}
      <div style={{ display:"flex", alignItems:"center", gap:6, flexShrink:0 }}>
        {status === "active" && (
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={s.bcolor} strokeWidth="2" style={{ animation:"spin 1s linear infinite" }}>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4" />
          </svg>
        )}
        {status === "done" && (
          <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke={s.bcolor} strokeWidth="2">
            <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
        <span style={{
          fontFamily:"var(--mono)", fontSize:9, fontWeight:600, letterSpacing:1.5,
          padding:"3px 8px", borderRadius:4,
          background: s.badge, color: s.bcolor,
          border:`1px solid ${s.bcolor}25`,
        }}>
          {status === "done" ? "DONE" : status === "active" ? `RUNNING ${fmt(elapsed)}` : "PENDING"}
        </span>
      </div>
    </div>
  )
}