from __future__ import annotations
from core.llm import _raw, client as _client
import uuid
from pydantic  import BaseModel, Field, field_validator
from loguru    import logger
from core.models     import EvidenceChain, EvidenceLink, GapStatus
from core.exceptions import EvidenceChainError

MODEL   = "llama-3.1-8b-instant"


# ── Instructor schema for structured chain generation ─────────────
class RawLink(BaseModel):
    step_type:  str   = Field(description="LEGAL_PREMISE | DOCUMENT_FACT | INFERENCE | CONCLUSION")
    source_ref: str   = Field(default="", description="e.g. 'Article 13 §2' or 'System Doc §4.2'")
    claim:      str   = Field(description="The specific claim for this reasoning step")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="0.0-1.0")

    @field_validator("source_ref", mode="before")
    @classmethod
    def coerce_source_ref(cls, v):
        # phi3 sometimes emits null for middle steps
        if v is None:
            return ""
        return str(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v):
        if v is None:
            return 0.5
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.5


class RawChain(BaseModel):
    links:        list[RawLink] = Field(min_length=2, max_length=8)
    final_status: str           = Field(default="partial",
                                        description="compliant | partial | missing | not_applicable")

    @field_validator("links", mode="before")
    @classmethod
    def require_links_list(cls, v):
        if not isinstance(v, list):
            raise ValueError("links must be a list")
        return v

    @field_validator("final_status", mode="before")
    @classmethod
    def coerce_status(cls, v):
        if v is None:
            return "partial"
        v = str(v).lower().strip()
        allowed = {"compliant", "partial", "missing", "not_applicable"}
        return v if v in allowed else "partial"


# ── Schema-echo detector ─────────────────────────────────────────
def _is_schema_echo(obj: dict) -> bool:
    """phi3 sometimes returns the JSON schema itself instead of an instance."""
    return "$defs" in obj or "properties" in obj or "title" in obj


CHAIN_SYSTEM = """You are a legal compliance analyst. Build a concise evidence chain.
Respond ONLY with valid JSON — no markdown, no explanation.
Required format:
{
  "final_status": "compliant|partial|missing",
  "links": [
    {"step_type": "LEGAL_PREMISE",  "source_ref": "Article X", "claim": "...", "confidence": 0.9},
    {"step_type": "DOCUMENT_FACT",  "source_ref": "System Doc", "claim": "...", "confidence": 0.8},
    {"step_type": "INFERENCE",      "source_ref": "Analysis",  "claim": "...", "confidence": 0.7},
    {"step_type": "CONCLUSION",     "source_ref": "THEMIS",    "claim": "...", "confidence": 0.85}
  ]
}"""


async def build_evidence_chain(
    article_ref:      str,
    article_title:    str,
    obligation_text:  str,
    system_text:      str,
    system_name:      str,
) -> EvidenceChain:
    """
    Build a 4-step EvidenceChain(TM) for a single compliance obligation.
    Each chain is SHA-256 hashed for integrity verification.
    """
    # Aggressively trim inputs to avoid 10-min timeouts on llama-3.1-8b-instant (4K ctx)
    obligation_short = obligation_text[:300]
    doc_excerpt      = system_text[:600]

    prompt = (
        f"Article: {article_ref} — {article_title}\n"
        f"Obligation (excerpt): {obligation_short}\n\n"
        f"System: {system_name}\n"
        f"Doc excerpt:\n{doc_excerpt}\n\n"
        f"Build the evidence chain JSON now."
    )

    raw: RawChain | None = None

    try:
        import json as _json
        resp = await _raw.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CHAIN_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        data = _json.loads(resp.choices[0].message.content)
        if not _is_schema_echo(data):
            raw = RawChain(**data)
    except Exception as e:
        logger.warning(
            f"EvidenceChain LLM failed for {article_ref}: {e} — using fallback"
        )

    # ── Fallback if LLM failed or returned schema echo ────────────
    if raw is None:
        raw = RawChain(
            links=[
                RawLink(step_type="LEGAL_PREMISE",  source_ref=article_ref,  claim=obligation_short,                     confidence=0.5),
                RawLink(step_type="DOCUMENT_FACT",  source_ref="System Doc", claim="Unable to extract — LLM timeout",    confidence=0.1),
                RawLink(step_type="INFERENCE",      source_ref="Analysis",   claim="Insufficient evidence to infer",     confidence=0.1),
                RawLink(step_type="CONCLUSION",     source_ref="THEMIS",     claim="Manual review required",             confidence=0.1),
            ],
            final_status="partial",
        )

    status_map = {
        "compliant":      GapStatus.COMPLIANT,
        "partial":        GapStatus.PARTIAL,
        "missing":        GapStatus.MISSING,
        "not_applicable": GapStatus.NOT_APPLICABLE,
    }

    links = [
        EvidenceLink(
            step_num=i + 1,
            step_type=l.step_type.upper(),
            source_ref=l.source_ref or article_ref,
            claim=l.claim,
            confidence=l.confidence,
        )
        for i, l in enumerate(raw.links)
    ]

    chain = EvidenceChain(
        chain_id=str(uuid.uuid4())[:8],
        article_ref=article_ref,
        obligation_text=obligation_text,
        links=links,
        final_status=status_map.get(raw.final_status.lower(), GapStatus.PARTIAL),
    )
    logger.debug(
        logger.debug(f"EvidenceChain built: {article_ref} -> {chain.final_status.value if hasattr(chain.final_status,'value') else chain.final_status} hash={chain.chain_hash}")
    )
    return chain


def format_chain_for_report(chain: EvidenceChain) -> str:
    """Human-readable markdown representation of an EvidenceChain."""
    step_icons = {
        "LEGAL_PREMISE": "⚖",
        "DOCUMENT_FACT": "📄",
        "INFERENCE":     "→",
        "CONCLUSION":    "✓",
    }
    lines = [
        f"## EvidenceChain(TM) — {chain.article_ref}",
        f"**Status:** {chain.final_status.value if hasattr(chain.final_status,'value') else chain.final_status} | **Integrity:** \{chain.chain_hash}\
",
    ]
    for link in chain.links:
        icon = step_icons.get(link.step_type, "•")
        lines.append(
            f"{icon} **{link.step_type}** [{link.source_ref}] "
            f"(conf: {link.confidence:.0%})\n   {link.claim}"
        )
    return "\n".join(lines)