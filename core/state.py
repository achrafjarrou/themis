from __future__ import annotations
from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages
from core.models import (
    RiskClassification, ComplianceGap, Contradiction,
    ComplianceReport, Framework,
)


class ThemisState(TypedDict):
    # ── Identity ────────────────────────────────────────────────────
    session_id:   str
    system_name:  str

    # ── Input document ──────────────────────────────────────────────
    system_text:  str                      # full extracted PDF text
    pdf_path:     Optional[str]

    # ── Analysis config ─────────────────────────────────────────────
    frameworks:   list[Framework]

    # ── Pipeline outputs ────────────────────────────────────────────

    risk_classification: Optional[RiskClassification]
    contradictions:      list[Contradiction]
    retrieved_articles:  list[dict]        # from HyDE+RRF+reranker
    gaps:                list[ComplianceGap]


    # ── Control flow ────────────────────────────────────────────────
    retry_count:         int
    overall_confidence:  float
    hitl_response:       Optional[dict]    # from WebSocket HITL

    # ── Final output ────────────────────────────────────────────────
    report:              Optional[ComplianceReport]

    # ── LangGraph messages (for tracing) ────────────────────────────
    messages: Annotated[list, add_messages]


def initial_state(
    *,
    session_id:  str,
    system_name: str,
    system_text: str,
    frameworks:  list[Framework],
    pdf_path:    Optional[str] = None,
) -> ThemisState:
    """Factory — always use this, never construct ThemisState manually."""
    return ThemisState(
        session_id=session_id,
        system_name=system_name,
        system_text=system_text,
        pdf_path=pdf_path,
        frameworks=frameworks,
        risk_classification=None,
        contradictions=[],
        retrieved_articles=[],
        gaps=[],
        retry_count=0,
        overall_confidence=0.0,
        hitl_response=None,
        report=None,
        messages=[],
    )
