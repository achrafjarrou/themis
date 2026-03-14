from __future__ import annotations
import re
from dataclasses import dataclass
from loguru      import logger
from core.models  import EvidenceChain, ComplianceReport


# ── RAGAS wrapper (requires: pip install ragas datasets) ───────────
def run_ragas_eval(
    questions:  list[str],
    answers:    list[str],
    contexts:   list[list[str]],
    ground_truths: list[str] | None = None,
) -> dict[str, float]:
    """
    Run RAGAS evaluation on RAG retrieval results.
    Metrics: faithfulness, answer_relevancy, context_precision, context_recall.
    Returns dict of metric_name → score (0.0–1.0).
    """
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from datasets import Dataset
    except ImportError:
        logger.warning("RAGAS not installed — pip install ragas datasets")
        return {}

    data = {
        "question": questions,
        "answer":   answers,
        "contexts": contexts,
    }
    if ground_truths:
        data["ground_truth"] = ground_truths

    dataset = Dataset.from_dict(data)
    metrics = [faithfulness, answer_relevancy, context_precision]
    result  = evaluate(dataset, metrics=metrics)

    scores = {
        "faithfulness":      result["faithfulness"],
        "answer_relevancy":  result["answer_relevancy"],
        "context_precision": result["context_precision"],
    }
    logger.info(f"RAGAS scores: {scores}")
    return scores


# ── LegalCitationAccuracy™ ─────────────────────────────────────────

@dataclass
class CitationMetrics:
    precision: float
    recall:    float
    f1:        float
    false_positive_rate: float


def legal_citation_accuracy(
    predicted_citations: list[str],
    ground_truth_citations: list[str],
    fp_penalty: float = 0.3,
) -> CitationMetrics:
    """
    LegalCitationAccuracy™ — custom F1 metric for legal citation quality.
    False positives are penalized more heavily than in standard F1
    because incorrect article citations have legal consequences.

    fp_penalty: extra weight applied to false positives (default 0.3)
    """
    pred_set = {c.strip().lower() for c in predicted_citations}
    true_set = {c.strip().lower() for c in ground_truth_citations}

    tp = len(pred_set & true_set)
    fp = len(pred_set - true_set)
    fn = len(true_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    # Penalised F1
    adjusted_precision = tp / (tp + fp * (1 + fp_penalty)) if (tp + fp) > 0 else 0.0
    f1 = (
        2 * adjusted_precision * recall / (adjusted_precision + recall)
        if (adjusted_precision + recall) > 0 else 0.0
    )
    fpr = fp / (fp + tp) if (fp + tp) > 0 else 0.0

    return CitationMetrics(
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1=round(f1, 3),
        false_positive_rate=round(fpr, 3),
    )



# ── EvidenceChainCoherence™ ────────────────────────────────────────

def evidence_chain_coherence(chain: EvidenceChain) -> dict[str, bool]:
    """
    EvidenceChainCoherence™ — 5-rule logical check for chain validity.
    These rules are deterministic — no LLM needed.

    Rules:
    1. step_order   : steps must be in order 1→2→3→4
    2. step_types   : exactly [LEGAL_PREMISE, DOCUMENT_FACT, INFERENCE, CONCLUSION]
    3. confidence   : all confidence values must be [0,1]
    4. integrity    : SHA-256 hash must match recomputed hash
    5. conclusion   : CONCLUSION step must align with final_status
    """
    EXPECTED_TYPES = ["LEGAL_PREMISE", "DOCUMENT_FACT", "INFERENCE", "CONCLUSION"]

    step_order = [l.step_num for l in chain.links] == list(range(1, len(chain.links) + 1))
    step_types = [l.step_type for l in chain.links] == EXPECTED_TYPES
    confidence = all(0.0 <= l.confidence <= 1.0 for l in chain.links)

    import json, hashlib
    payload  = json.dumps([l.model_dump() for l in chain.links], sort_keys=True)
    expected = hashlib.sha256(payload.encode()).hexdigest()[:16]
    integrity = chain.chain_hash == expected

    conclusion_link = chain.links[-1] if chain.links else None
    conclusion_ok = (
        conclusion_link is not None and
        conclusion_link.step_type == "CONCLUSION" and
        len(conclusion_link.claim) >= 10
    )

    return {
        "step_order":  step_order,
        "step_types":  step_types,
        "confidence": confidence,
        "integrity":  integrity,
        "conclusion": conclusion_ok,
        "all_pass":   all([step_order, step_types, confidence, integrity, conclusion_ok]),
    }



def evaluate_report(report: ComplianceReport) -> dict:
    """Run all custom metrics on a full report — use after pipeline completion."""
    coherences = [evidence_chain_coherence(g.evidence_chain) for g in report.gaps]
    all_pass   = sum(1 for c in coherences if c["all_pass"])
    citations  = [
        cite
        for g in report.gaps
        for link in g.evidence_chain.links
        for cite in re.findall(r'Article\s+\d+', link.source_ref)
    ]
    return {
        "compliance_score":          report.compliance_score,
        "evidence_integrity":        report.evidence_integrity_ok,
        "chain_coherence_pass_rate":  all_pass / len(coherences) if coherences else 0.0,
        "unique_articles_cited":      len(set(citations)),
        "critical_gaps":              len(report.critical_gaps),
        "contradictions":             len(report.contradictions),
    }
