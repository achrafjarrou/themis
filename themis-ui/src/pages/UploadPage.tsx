import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Navbar } from "../components/layout/Navbar"
import { DropZone } from "../components/upload/DropZone"
import { FrameworkSelector } from "../components/upload/FrameworkSelector"
import { Button } from "../components/ui/Button"
import { api } from "../lib/api"

const TRUST = [
  { icon:"🔒", label:"Air-gapped",      sub:"No external storage — runs locally" },
  { icon:"⛓",  label:"EvidenceChain™",  sub:"SHA-256 tamper-proof audit trail"   },
  { icon:"⚡",  label:"Groq LPU",        sub:"~2 min · 900 tokens/sec"            },
]

export default function UploadPage() {
  const nav = useNavigate()
  const [file,    setFile]    = useState<File|null>(null)
  const [name,    setName]    = useState("")
  const [fw,      setFw]      = useState(["eu_ai_act","gdpr","nist_ai_rmf"])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")

  const submit = async () => {
    if (!file)    { setError("Please upload a PDF document"); return }
    if (!name.trim()) { setError("Please enter the system name"); return }
    if (!fw.length)   { setError("Select at least one framework"); return }
    setError(""); setLoading(true)
    try {
      const form = new FormData()
      form.append("file", file)
      form.append("system_name", name.trim())
      form.append("frameworks", fw.join(","))
      const r = await api.analyze(form)
      nav(`/analysis/${r.session_id}`)
    } catch (e: any) {
      setError(e.message ?? "Failed to start analysis")
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight:"100vh", background:"var(--bg)", fontFamily:"var(--sans)" }} className="grid-bg">
      <Navbar />

      <div style={{ maxWidth:560, margin:"0 auto", padding:"60px 24px 80px" }}>

        {/* Hero */}
        <div style={{ textAlign:"center", marginBottom:40 }}>
          <div style={{
            display:"inline-flex", alignItems:"center", gap:6, marginBottom:16,
            fontFamily:"var(--mono)", fontSize:10, letterSpacing:2,
            color:"#60a5fa", background:"rgba(59,130,246,0.1)",
            border:"1px solid rgba(59,130,246,0.2)", padding:"4px 12px", borderRadius:20,
          }}>
            <span style={{ width:5, height:5, borderRadius:"50%", background:"#60a5fa", display:"inline-block" }} />
            EU AI Act enforcement · August 2026
          </div>

          <h1 style={{
            fontFamily:"var(--display)", fontWeight:800,
            fontSize:"clamp(32px,5vw,48px)", lineHeight:.95, letterSpacing:"-2px",
            color:"#fff", marginBottom:16,
          }}>
            AI COMPLIANCE<br />
            <span style={{
              background:"linear-gradient(135deg,#3b82f6,#8b5cf6)",
              WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
            }}>INTELLIGENCE</span>
          </h1>

          <p style={{ fontSize:14, color:"var(--text2)", lineHeight:1.7, maxWidth:400, margin:"0 auto" }}>
            Upload your AI system documentation. THEMIS detects compliance gaps, builds cryptographic{" "}
            <strong style={{ color:"#e2e8f0" }}>EvidenceChains™</strong>{" "}
            and flags internal contradictions — in under 2 minutes.
          </p>
        </div>

        {/* Card */}
        <div style={{
          background:"var(--bg2)", border:"1px solid var(--border2)",
          borderRadius:20, padding:28,
          boxShadow:"0 0 60px rgba(59,130,246,0.05)",
        }}>
          {/* Drop zone */}
          <div style={{ marginBottom:20 }}>
            <DropZone file={file} onFile={setFile} />
          </div>

          {/* System name */}
          <div style={{ marginBottom:20 }}>
            <label style={{ display:"block", fontFamily:"var(--mono)", fontSize:9, letterSpacing:2, color:"var(--text3)", textTransform:"uppercase", marginBottom:8 }}>
              System Name
            </label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. CreditScore AI v2.1"
              style={{
                width:"100%", padding:"12px 14px",
                background:"var(--bg3)", border:"1px solid var(--border2)",
                borderRadius:10, fontSize:14, color:"#e2e8f0",
                fontFamily:"var(--sans)", outline:"none",
                boxSizing:"border-box", transition:"border .2s",
              }}
              onFocus={e => (e.target.style.borderColor = "#3b82f6")}
              onBlur={e  => (e.target.style.borderColor = "var(--border2)")}
            />
          </div>

          {/* Frameworks */}
          <div style={{ marginBottom:24 }}>
            <label style={{ display:"block", fontFamily:"var(--mono)", fontSize:9, letterSpacing:2, color:"var(--text3)", textTransform:"uppercase", marginBottom:10 }}>
              Regulatory Frameworks
            </label>
            <FrameworkSelector selected={fw} onChange={setFw} />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.25)",
              borderRadius:8, padding:"10px 14px", color:"#f87171",
              fontFamily:"var(--mono)", fontSize:11, marginBottom:16,
            }}>⚠ {error}</div>
          )}

          {/* Submit */}
          <Button variant="primary" fullWidth disabled={loading} onClick={submit}>
            {loading ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation:"spin 1s linear infinite" }}>
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
                </svg>
                Launching audit...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                Start Compliance Audit
              </>
            )}
          </Button>

          <p style={{ textAlign:"center", fontFamily:"var(--mono)", fontSize:10, color:"var(--text4)", marginTop:10 }}>
            ~2 min · Groq LPU · Zero data leaves your network
          </p>
        </div>

        {/* Trust badges */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8, marginTop:16 }}>
          {TRUST.map((b,i) => (
            <div key={i} style={{
              padding:"14px 12px", textAlign:"center",
              background:"var(--bg2)", border:"1px solid var(--border)",
              borderRadius:12,
            }}>
              <div style={{ fontSize:20, marginBottom:5 }}>{b.icon}</div>
              <div style={{ fontFamily:"var(--display)", fontWeight:700, fontSize:11, color:"#e2e8f0", marginBottom:2 }}>{b.label}</div>
              <div style={{ fontFamily:"var(--mono)", fontSize:9, color:"var(--text3)" }}>{b.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}