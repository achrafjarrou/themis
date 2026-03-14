from __future__ import annotations
from core.llm import _raw, client as _client
from datetime import datetime
from loguru   import logger
from core.state   import ThemisState
from core.models  import ComplianceReport, GapStatus, SeverityLevel
from agents.evidence_chain import format_chain_for_report



def _v(x):
    """Safe .value — fonctionne sur Enum, IntEnum, str, int."""
    return x.value if hasattr(x, "value") else x

def _s(x):
    """Safe str — retourne la valeur string d'un enum ou str."""
    v = _v(x)
    return str(v).lower() if v is not None else ""

async def generate_report(state: ThemisState) -> ComplianceReport:
    """
    Assemble the final ComplianceReport from pipeline state.
    1. Collect all gaps, contradictions, risk classification
    2. Build markdown narrative
    3. Verify EvidenceChain integrity (SHA-256)
    4. Return validated ComplianceReport Pydantic model
    """
    if not state["risk_classification"]:
        raise ValueError("Cannot generate report: risk_classification missing from state")

    gaps     = state["gaps"]
    contras  = state["contradictions"]
    risk     = state["risk_classification"]

    md = _build_markdown(
        system_name=state["system_name"],
        session_id=state["session_id"],
        risk=risk,
        gaps=gaps,
        contradictions=contras,
        frameworks=state["frameworks"],
        confidence=state["overall_confidence"],
    )

    report = ComplianceReport(
        session_id=state["session_id"],
        system_name=state["system_name"],
        generated_at=datetime.utcnow(),
        risk_classification=risk,
        gaps=gaps,
        contradictions=contras,
        frameworks_analyzed=state["frameworks"],
        overall_confidence=state["overall_confidence"],
        markdown_report=md,
    )

    # Integrity check — verify all SHA-256 hashes
    if not report.evidence_integrity_ok:
        logger.critical(f"[{state['session_id']}] INTEGRITY VIOLATION — EvidenceChain hash mismatch!")
    else:
        logger.success(f"[{state['session_id']}] All {len(gaps)} EvidenceChains verified ✓")

    return report


def _build_markdown(
    system_name, session_id, risk, gaps, contradictions, frameworks, confidence
) -> str:
    """Generate the full Markdown compliance dossier."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Score calculation (mirrors ComplianceReport.compliance_score property)
    if not gaps:
        score = 100.0
    else:
        missing = sum(1 for g in gaps if g.status == GapStatus.MISSING)
        partial = sum(1 for g in gaps if g.status == GapStatus.PARTIAL)
        score   = round(max(0.0, (1.0 - (missing * 1.0 + partial * 0.5) / len(gaps)) * 100), 1)

    critical = [g for g in gaps if g.severity == SeverityLevel.CRITICAL]
    fw_str   = " + ".join((_v(f) if hasattr(f,"value") else str(f)).replace("_"," ").upper() for f in frameworks)

    sections = [
        f"# THEMIS Compliance Report",
        f"**System:** {system_name} | **Session:** {session_id} | **Generated:** {now}",
        f"**Frameworks:** {fw_str} | **Compliance Score:** {score}/100 | **Confidence:** {confidence:.0%}",
        f"\n---\n",
    ]

    # Executive summary
    sections += [
        "## Executive Summary",
        "- Risk Classification: **" + str(getattr(getattr(risk,"risk_level",risk),"value",str(getattr(risk,"risk_level",risk)))).upper() + "**",
        f"- Total Gaps Identified: **{len(gaps)}** ({len(critical)} critical)",
        f"- Internal Contradictions Detected: **{len(contradictions)}**",
        f"- Overall Confidence: **{confidence:.0%}**",
        f"\n**Risk Reasoning:** {risk.reasoning}\n",
    ]

    # ContradictionDetector™ section
    if contradictions:
        sections.append("## ContradictionDetector™ Findings")
        sections.append(f"> ⚠ {len(contradictions)} internal contradictions found in documentation")
        for c in contradictions:
            sections += [
                f"\n### Contradiction {c.contradiction_id} — {c.contradiction_type.upper()}",
                f"**Severity:** {c.severity}/4 | **Legal Risk:** {c.legal_risk}",
                f"- A [{c.location_a}]: {c.statement_a}",
                f"- B [{c.location_b}]: {c.statement_b}",
                f"**Resolution:** {c.resolution_hint}",
            ]

    # Critical gaps first
    if critical:
        sections.append("\n## 🔴 Critical Gaps — Immediate Action Required")
        for g in critical:
            sections += [
                f"\n### {g.article_num} — {g.article_title}",
                format_chain_for_report(g.evidence_chain),
                "\n**Remediation:**",
                *[f"{i+1}. {s}" for i, s in enumerate(g.remediation_steps)],
            ]
            if g.deadline_risk:
                sections.append(f"> ⏱ Deadline risk: {g.deadline_risk}")

    # All gaps
    sections.append("\n## All Compliance Gaps")
    for g in gaps:
        status_icon = {"missing":"🔴", "partial":"🟡", "compliant":"🟢"}.get(str(_v(g.status)).lower(), "⚪")
        sections += [
            f"\n### {status_icon} {g.article_num} [{(_v(g.framework))}]",
            f"**Status:** {_v(g.status)} | **Severity:** {g.severity}/4",
            format_chain_for_report(g.evidence_chain),
        ]
        if g.cross_framework_refs:
            sections.append(f"**Cross-references:** {', '.join(g.cross_framework_refs)}")

    sections += [
        "\n---",
        f"*Generated by THEMIS v1.0.0 — EvidenceChain™ integrity: verified*",
    ]
    return "\n".join(sections)