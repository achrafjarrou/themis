import { useNavigate, useLocation } from "react-router-dom"

export function Navbar({ sid }: { sid?: string }) {
  const nav = useNavigate()
  const loc = useLocation()
  const onAnalysis = loc.pathname.startsWith("/analysis")
  const onReport   = loc.pathname.startsWith("/report")

  return (
    <nav style={{
      position:"sticky", top:0, zIndex:100,
      height:56, padding:"0 32px",
      display:"flex", alignItems:"center", justifyContent:"space-between",
      background:"rgba(4,8,15,0.9)", backdropFilter:"blur(24px)",
      borderBottom:"1px solid var(--border2)",
    }}>
      {/* Logo */}
      <div style={{ display:"flex", alignItems:"center", gap:10 }}>
        <div style={{
          width:32, height:32, borderRadius:8,
          background:"linear-gradient(135deg,#3b82f6,#8b5cf6)",
          display:"flex", alignItems:"center", justifyContent:"center",
          fontFamily:"var(--display)", fontWeight:800, fontSize:14, color:"#fff",
        }}>T</div>
        <span style={{ fontFamily:"var(--display)", fontWeight:800, fontSize:16, letterSpacing:3, color:"#fff" }}>THEMIS</span>
        <span style={{
          fontFamily:"var(--mono)", fontSize:9, letterSpacing:2,
          background:"rgba(59,130,246,0.12)", color:"#60a5fa",
          border:"1px solid rgba(59,130,246,0.25)", padding:"2px 8px", borderRadius:4,
        }}>BETA</span>

        {(onAnalysis || onReport) && (
          <button
            onClick={() => nav("/")}
            style={{ marginLeft:12, fontFamily:"var(--mono)", fontSize:11, color:"var(--text3)", background:"none", border:"none", cursor:"pointer", letterSpacing:.5 }}
          >← New Analysis</button>
        )}
      </div>

      {/* Right */}
      <div style={{ display:"flex", alignItems:"center", gap:16 }}>
        {sid && (
          <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", letterSpacing:1 }}>
            {sid}
          </span>
        )}
        <div style={{ display:"flex", alignItems:"center", gap:6 }}>
          <div style={{ width:6, height:6, borderRadius:"50%", background:"#10b981" }} />
          <span style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", letterSpacing:.5 }}>
            EU AI Act · Aug 2026
          </span>
        </div>
      </div>
    </nav>
  )
}