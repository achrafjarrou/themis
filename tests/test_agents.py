import pytest, json, hashlib
from core.models  import (
    EvidenceLink, EvidenceChain, Contradiction, ComplianceGap,
    RiskClassification, ComplianceReport, RiskLevel, GapStatus, SeverityLevel, Framework,
)
from core.state   import initial_state
from graph.routing import route_after_analysis


# ── EvidenceChain integrity ──────────────────────────────────────────
class TestEvidenceChain:

    def _make_chain(self, status=GapStatus.MISSING) -> EvidenceChain:
        links = [
            EvidenceLink(step_num=1, step_type="LEGAL_PREMISE",  source_ref="Article 13", claim="Transparency required",         confidence=0.95),
            EvidenceLink(step_num=2, step_type="DOCUMENT_FACT",  source_ref="System Doc §3", claim="No transparency section found", confidence=0.80),
            EvidenceLink(step_num=3, step_type="INFERENCE",      source_ref="Analysis",     claim="Requirement not addressed",    confidence=0.85),
            EvidenceLink(step_num=4, step_type="CONCLUSION",     source_ref="THEMIS",       claim="Non-compliant",               confidence=0.88),
        ]
        return EvidenceChain(chain_id="test01", article_ref="Article 13",
            obligation_text="Transparency obligation", links=links, final_status=status)


    def test_hash_computed_on_init(self):
        chain = self._make_chain()
        assert chain.chain_hash != ""
        assert len(chain.chain_hash) == 16

    def test_hash_is_deterministic(self):
        chain1 = self._make_chain()
        chain2 = self._make_chain()
        assert chain1.chain_hash == chain2.chain_hash

    def test_avg_confidence_correct(self):
        chain = self._make_chain()
        expected = round((0.95 + 0.80 + 0.85 + 0.88) / 4, 3)
        assert chain.avg_confidence == expected


    def test_frozen_links(self):
        chain = self._make_chain()
        with pytest.raises(Exception):
            chain.links[0].claim = "tampered"   # frozen model


# ── ComplianceReport integrity ──────────────────────────────────────
class TestComplianceReport:

    def _make_gap(self, status: GapStatus, severity: SeverityLevel) -> ComplianceGap:
        tc = TestEvidenceChain()
        chain = tc._make_chain(status)
        return ComplianceGap(
            gap_id="g01", framework=Framework.EU_AI_ACT,
            article_num="Article 13", article_title="Transparency",
            obligation="Provide transparency", status=status, severity=severity,
            evidence_chain=chain, remediation_steps=["Add transparency docs", "Publish model card"],
        )

    def test_score_all_compliant(self):
        gap    = self._make_gap(GapStatus.COMPLIANT, SeverityLevel.LOW)
        report = ComplianceReport(
            session_id="test", system_name="TestAI",
            risk_classification=RiskClassification(
                risk_level=RiskLevel.HIGH, reasoning="High risk because Annex III" * 3,
                applicable_annexes=["Annex III"], applicable_articles=["Article 6"],
                confidence=0.9),
            gaps=[gap], contradictions=[], frameworks_analyzed=[Framework.EU_AI_ACT],
            overall_confidence=0.85, markdown_report="# Report",
        )
        assert report.compliance_score == 100.0

    def test_score_all_missing(self):
        gap    = self._make_gap(GapStatus.MISSING, SeverityLevel.CRITICAL)
        report = ComplianceReport(
            session_id="test", system_name="TestAI",
            risk_classification=RiskClassification(
                risk_level=RiskLevel.HIGH, reasoning="High risk for testing purposes only",
                applicable_annexes=[], applicable_articles=[], confidence=0.8),
            gaps=[gap], contradictions=[], frameworks_analyzed=[Framework.EU_AI_ACT],
            overall_confidence=0.5, markdown_report="# Report",
        )
        assert report.compliance_score == 0.0

    def test_evidence_integrity_ok(self):
        gap    = self._make_gap(GapStatus.MISSING, SeverityLevel.HIGH)
        report = ComplianceReport(
            session_id="test", system_name="TestAI",
            risk_classification=RiskClassification(
                risk_level=RiskLevel.MINIMAL, reasoning="Low risk for testing",
                applicable_annexes=[], applicable_articles=[], confidence=0.7),
            gaps=[gap], contradictions=[], frameworks_analyzed=[Framework.EU_AI_ACT],
            overall_confidence=0.7, markdown_report="# Report",
        )
        assert report.evidence_integrity_ok is True

    def test_critical_gaps_filter(self):
        g1 = self._make_gap(GapStatus.MISSING, SeverityLevel.CRITICAL)
        g2 = self._make_gap(GapStatus.MISSING, SeverityLevel.LOW)
        rc = RiskClassification(risk_level=RiskLevel.HIGH, reasoning="High risk test scenario here",
            applicable_annexes=[], applicable_articles=[], confidence=0.8)
        report = ComplianceReport(session_id="t", system_name="T", risk_classification=rc,
            gaps=[g1, g2], contradictions=[], frameworks_analyzed=[Framework.EU_AI_ACT],
            overall_confidence=0.6, markdown_report="")
        assert len(report.critical_gaps) == 1


# ── Routing logic ───────────────────────────────────────────────────
class TestRouting:

    def _state(self, confidence: float, retry: int, critical_missing: int):
        tc  = TestEvidenceChain()
        def make_gap(sev):
            return ComplianceGap(
                gap_id="x", framework=Framework.EU_AI_ACT,
                article_num="Article 1", article_title="T", obligation="O",
                status=GapStatus.MISSING, severity=sev,
                evidence_chain=tc._make_chain(GapStatus.MISSING),
                remediation_steps=["Fix it", "Document it"],
            )
        gaps = [make_gap(SeverityLevel.CRITICAL) for _ in range(critical_missing)]
        s = initial_state(session_id="t", system_name="T",
                          system_text="test", frameworks=[Framework.EU_AI_ACT])
        s["overall_confidence"] = confidence
        s["retry_count"]        = retry
        s["gaps"]               = gaps
        return s

    def test_route_retry_low_conf(self):
        assert route_after_analysis(self._state(0.25, 0, 0)) == "retry"

    def test_route_no_retry_after_max(self):
        assert route_after_analysis(self._state(0.25, 2, 0)) != "retry"

    def test_route_hitl_very_low_conf(self):
        assert route_after_analysis(self._state(0.15, 2, 0)) == "hitl"

    def test_route_hitl_too_many_critical(self):
        assert route_after_analysis(self._state(0.50, 0, 4)) == "hitl"

    def test_route_report_good_conf(self):
        assert route_after_analysis(self._state(0.75, 0, 0)) == "report"
