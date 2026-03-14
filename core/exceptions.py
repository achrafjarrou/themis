from __future__ import annotations


class ThemisError(Exception):
    """Base error for all THEMIS components."""
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


# ── Ingest layer ────────────────────────────────────────────────────
class ParseError(ThemisError):
    """PDF parsing failed or returned empty content."""

class ChunkError(ThemisError):
    """Chunking produced zero usable chunks."""


# ── RAG layer ───────────────────────────────────────────────────────
class IndexError(ThemisError):
    """Qdrant collection missing or build failed."""

class RetrievalError(ThemisError):
    """HyDE or reranker returned empty results."""


# ── Agent layer ─────────────────────────────────────────────────────
class ClassificationError(ThemisError):
    """Risk classifier returned invalid or empty output."""

class EvidenceChainError(ThemisError):
    """EvidenceChain builder failed — chain integrity cannot be guaranteed."""

class ContradictionError(ThemisError):
    """ContradictionDetector failed during claim extraction or comparison."""


# ── Graph layer ─────────────────────────────────────────────────────
class GraphBuildError(ThemisError):
    """LangGraph builder failed — cannot start pipeline."""

class HITLTimeoutError(ThemisError):
    """Human-in-the-loop reviewer did not respond within the timeout."""


# ── Report layer ────────────────────────────────────────────────────
class ReportError(ThemisError):
    """Report generation failed — missing required fields in state."""

class IntegrityError(ThemisError):
    """EvidenceChain SHA-256 hash mismatch — report has been tampered."""
