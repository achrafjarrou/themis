// THEMIS-UI — src\types\index.ts
// Mirrors core/models.py — keep in sync

export type RiskLevel    = "unacceptable" | "high" | "limited" | "minimal" | "gpai" | "unknown"
export type GapStatus    = "compliant"    | "partial"  | "missing"  | "not_applicable"
export type Framework    = "eu_ai_act"    | "gdpr"     | "nist_ai_rmf"
export type Severity     = 1 | 2 | 3 | 4
export type SessionStatus = "pending" | "running" | "completed" | "error" | "hitl_required"

export interface EvidenceLink {
  step_num:   number
  step_type:  "LEGAL_PREMISE" | "DOCUMENT_FACT" | "INFERENCE" | "CONCLUSION"
  source_ref: string
  claim:      string
  confidence: number
}
export interface EvidenceChain {
  chain_id: string; article_ref: string; obligation_text: string
  links: EvidenceLink[]; final_status: GapStatus
  chain_hash: string; avg_confidence: number
}
export interface Contradiction {
  contradiction_id: string; contradiction_type: string
  statement_a: string; location_a: string
  statement_b: string; location_b: string
  legal_risk: string; severity: Severity; resolution_hint: string
}
export interface ComplianceGap {
  gap_id: string; framework: Framework; article_num: string
  article_title: string; obligation: string
  status: GapStatus; severity: Severity
  evidence_chain: EvidenceChain
  remediation_steps: string[]; deadline_risk?: string
  cross_framework_refs: string[]
}
export interface RiskClassification {
  risk_level: RiskLevel; reasoning: string
  applicable_annexes: string[]; applicable_articles: string[]
  confidence: number; prohibited_practice?: string
}
export interface ComplianceReport {
  session_id: string; system_name: string; generated_at: string
  compliance_score: number; risk_classification: RiskClassification
  gaps: ComplianceGap[]; contradictions: Contradiction[]
  critical_gaps: ComplianceGap[]; frameworks_analyzed: Framework[]
  overall_confidence: number; evidence_integrity_ok: boolean
}
export interface SessionData {
  session_id: string; status: SessionStatus; system_name: string
  current_node?: string; current_msg?: string; progress_pct: number
  created_at: string; error?: string; hitl_required: boolean
}
export interface StreamEvent {
  session_id: string; status: SessionStatus
  current_node?: string; current_msg?: string
  progress_pct: number; hitl_required: boolean
}
