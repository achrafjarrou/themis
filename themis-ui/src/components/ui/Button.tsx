import type { ReactNode, CSSProperties } from "react"

type Variant = "primary" | "success" | "ghost" | "danger"

const V: Record<Variant, CSSProperties> = {
  primary: { background:"linear-gradient(135deg,#2563eb,#7c3aed)", boxShadow:"0 4px 20px rgba(37,99,235,0.35)" },
  success: { background:"linear-gradient(135deg,#059669,#0891b2)", boxShadow:"0 4px 20px rgba(5,150,105,0.3)"  },
  ghost:   { background:"rgba(255,255,255,0.04)", border:"1px solid var(--border2)" },
  danger:  { background:"rgba(239,68,68,0.15)",   border:"1px solid rgba(239,68,68,0.3)", color:"#ef4444" },
}

export function Button({ children, variant="primary", onClick, disabled, style, fullWidth }: {
  children: ReactNode
  variant?: Variant
  onClick?: () => void
  disabled?: boolean
  style?: CSSProperties
  fullWidth?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display:"flex", alignItems:"center", justifyContent:"center", gap:8,
        padding:"14px 28px", borderRadius:12,
        fontFamily:"var(--display)", fontWeight:700, fontSize:14, letterSpacing:.5,
        color:"#fff", border:"none", cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? .5 : 1,
        transition:"all .2s",
        width: fullWidth ? "100%" : undefined,
        ...V[variant],
        ...style,
      }}
    >
      {children}
    </button>
  )
}