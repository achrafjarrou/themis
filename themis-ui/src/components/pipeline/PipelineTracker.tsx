import { NodeCard } from "./NodeCard"

const NODES = [
  { key:"classify",              icon:"⚡", label:"Risk Classification",     sub:"Determining EU AI Act risk tier — Article 6 + Annex III" },
  { key:"detect_contradictions", icon:"🔍", label:"ContradictionDetector™",  sub:"Scanning documentation for internal contradictions" },
  { key:"map_obligations",       icon:"🗺", label:"HyDE + Rerank RAG",       sub:"Mapping obligations via HyDE + cross-encoder rerank" },
  { key:"analyze_gaps",          icon:"⛓", label:"EvidenceChain™ Analysis", sub:"Building SHA-256 cryptographic proofs per gap (parallel)" },
  { key:"hitl",                  icon:"👤", label:"Human Review (HITL)",     sub:"LangGraph interrupt() — awaiting decision if confidence < 0.7" },
  { key:"report",                icon:"📋", label:"Report Generation",       sub:"Assembling final compliance dossier" },
]

export function PipelineTracker({ activeNode, elapsed, completed }: {
  activeNode: string
  elapsed:    number
  completed:  boolean
}) {
  const activeIdx = NODES.findIndex(n => n.key === activeNode)
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:3 }}>
      {NODES.map((n, i) => (
        <NodeCard
          key={n.key}
          icon={n.icon}
          label={n.label}
          sub={n.sub}
          elapsed={elapsed}
          status={
            completed         ? "done"    :
            i < activeIdx     ? "done"    :
            i === activeIdx   ? "active"  : "pending"
          }
        />
      ))}
    </div>
  )
}