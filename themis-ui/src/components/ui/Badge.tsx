import type { GapStatus, RiskLevel } from "../../types"

const STATUS: Record<GapStatus, { bg: string; color: string; label: string }> = {
  compliant:      { bg:"rgba(16,185,129,0.12)",  color:"#10b981", label:"COMPLIANT"    },
  partial:        { bg:"rgba(245,158,11,0.12)",  color:"#f59e0b", label:"PARTIAL"      },
  missing:        { bg:"rgba(239,68,68,0.12)",   color:"#ef4444", label:"MISSING"      },
  not_applicable: { bg:"rgba(100,116,139,0.12)", color:"#64748b", label:"N/A"          },
}
const RISK: Record<RiskLevel, { color: string }> = {
  unacceptable: { color:"#ef4444" },
  high:         { color:"#f97316" },
  limited:      { color:"#f59e0b" },
  minimal:      { color:"#10b981" },
  gpai:         { color:"#8b5cf6" },
  unknown:      { color:"#64748b" },
}

export function StatusBadge({ status }: { status: GapStatus }) {
  const s = STATUS[status] ?? STATUS.missing
  return (
    <span style={{
      fontFamily:"var(--mono)", fontSize:9, fontWeight:600, letterSpacing:1.5,
      padding:"3px 8px", borderRadius:4,
      background: s.bg, color: s.color,
      border: `1px solid ${s.color}30`,
    }}>{s.label}</span>
  )
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  const r = RISK[level] ?? RISK.unknown
  return (
    <span style={{
      fontFamily:"var(--mono)", fontSize:9, fontWeight:600, letterSpacing:1.5,
      padding:"3px 10px", borderRadius:4,
      background: r.color + "18", color: r.color,
      border: `1px solid ${r.color}30`,
      textTransform:"uppercase"
    }}>{level.replace("_"," ")}</span>
  )
}