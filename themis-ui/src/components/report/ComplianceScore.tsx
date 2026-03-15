import { scoreColor } from "../../lib/utils"

export function ComplianceScore({ score, size = 80 }: { score: number; size?: number }) {
  const r = (size - 12) / 2
  const circ = 2 * Math.PI * r
  const pct = score / 100
  const color = scoreColor(score)

  return (
    <div style={{ position:"relative", width:size, height:size }}>
      <svg width={size} height={size} style={{ transform:"rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--border2)" strokeWidth={6} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={`${circ * pct} ${circ}`}
          strokeLinecap="round"
          style={{ transition:"stroke-dasharray .8s ease" }}
        />
      </svg>
      <div style={{
        position:"absolute", inset:0, display:"flex", flexDirection:"column",
        alignItems:"center", justifyContent:"center"
      }}>
        <span style={{ fontFamily:"var(--display)", fontWeight:800, fontSize:size*.22, color, lineHeight:1 }}>
          {score.toFixed(0)}
        </span>
        <span style={{ fontFamily:"var(--mono)", fontSize:size*.1, color:"var(--text3)", letterSpacing:.5 }}>
          /100
        </span>
      </div>
    </div>
  )
}
