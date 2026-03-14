const FW = [
  { id:"eu_ai_act",    label:"EU AI Act",   articles:"85 articles",  color:"#3b82f6", bg:"rgba(59,130,246,0.08)"  },
  { id:"gdpr",         label:"GDPR",        articles:"99 articles",  color:"#10b981", bg:"rgba(16,185,129,0.08)"  },
  { id:"nist_ai_rmf",  label:"NIST AI RMF", articles:"4 functions",  color:"#8b5cf6", bg:"rgba(139,92,246,0.08)" },
]

export function FrameworkSelector({ selected, onChange }: {
  selected: string[]
  onChange:  (v: string[]) => void
}) {
  const toggle = (id: string) =>
    onChange(selected.includes(id) ? selected.filter(x=>x!==id) : [...selected, id])

  return (
    <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:8 }}>
      {FW.map(f => {
        const on = selected.includes(f.id)
        return (
          <div key={f.id} onClick={() => toggle(f.id)} style={{
            padding:"12px 14px", borderRadius:10, cursor:"pointer",
            border: on ? `2px solid ${f.color}` : "2px solid var(--border2)",
            background: on ? f.bg : "var(--bg2)",
            transition:"all .15s",
          }}>
            <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:2 }}>
              <div style={{
                width:13, height:13, borderRadius:3, flexShrink:0,
                background: on ? f.color : "var(--border2)",
                display:"flex", alignItems:"center", justifyContent:"center",
              }}>
                {on && <svg width="8" height="8" viewBox="0 0 10 10"><path d="M2 5l2.5 2.5L8 3" stroke="#fff" strokeWidth="1.5" fill="none" strokeLinecap="round"/></svg>}
              </div>
              <span style={{ fontFamily:"var(--display)", fontWeight:700, fontSize:12, color: on ? f.color : "#94a3b8" }}>{f.label}</span>
            </div>
            <div style={{ fontFamily:"var(--mono)", fontSize:10, color:"var(--text3)", paddingLeft:19 }}>{f.articles}</div>
          </div>
        )
      })}
    </div>
  )
}