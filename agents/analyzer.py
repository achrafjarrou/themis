from __future__ import annotations
from core.llm import _raw, client as _client
import asyncio, uuid
from pydantic  import BaseModel, Field
from loguru    import logger
from core.models           import ComplianceGap, Framework, GapStatus, SeverityLevel, RiskLevel
from agents.evidence_chain import build_evidence_chain
from core.llm              import client, MODEL, LLM_TIMEOUT, MAX_RETRIES, OLLAMA_OPTIONS
from core.utils            import normalise_article_ref

MAX_ARTICLE_TEXT = 800   # chars
MAX_SYSTEM_TEXT  = 600   # chars
SEMAPHORE_LIMIT  = 2     # appels LLM parallèles max (RAM limitée)


class ArticleAnalysis(BaseModel):
    obligation:           str       = Field(description="The specific compliance obligation")
    severity:             int       = Field(ge=1, le=4, description="1=low 2=medium 3=high 4=critical")
    remediation_steps:    list[str] = Field(min_length=2, max_length=4)
    deadline_risk:        str | None = Field(default=None)
    cross_framework_refs: list[str] = Field(default_factory=list)


ANALYZE_SYSTEM = """You are an EU AI Act compliance auditor.
Given a regulation article and AI system documentation, extract:
- The specific compliance obligation
- Severity (1=low, 4=critical)
- 2-4 concrete remediation steps
- Cross-framework references (GDPR/NIST if applicable)

EXAMPLE OUTPUT:
{"obligation":"Provide transparency disclosure to users about AI system capabilities","severity":3,"remediation_steps":["Create user-facing transparency notice","Publish model card with system capabilities","Add disclosure banner to UI"],"deadline_risk":"EU AI Act enforcement Aug 2026","cross_framework_refs":["GDPR Article 13"]}

Respond ONLY with valid JSON."""


async def _analyze_single(
    article:     dict,
    system_text: str,
    system_name: str,
    risk_level:  RiskLevel,
    sem:         asyncio.Semaphore,
) -> ComplianceGap | None:
    async with sem:
        article_ref   = normalise_article_ref(article.get("article_num", "Unknown"))
        article_title = article.get("article_title", "")
        framework_str = article.get("framework", "eu_ai_act")

        try:
            import json as _json
            _resp = await asyncio.wait_for(
                _raw.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": ANALYZE_SYSTEM},
                        {"role": "user",   "content":
                            f"Article: {article_ref} — {article_title}\n"
                            f"Article text: {article.get('text','')[:MAX_ARTICLE_TEXT]}\n\n"
                            f"System: {system_name} (risk: {risk_level.value if hasattr(risk_level,'value') else str(risk_level)})\n"
                            f"Documentation: {system_text[:MAX_SYSTEM_TEXT]}"},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=600,
                ),
                timeout=LLM_TIMEOUT,
            )
            _data = _json.loads(_resp.choices[0].message.content)
            # Normaliser remediation_steps — min 2 items, strings uniquement
            steps = _data.get("remediation_steps", [])
            if isinstance(steps, str):
                steps = [steps]
            steps = [str(s) if not isinstance(s, str) else s for s in steps]
            if len(steps) < 2:
                steps = (steps + ["Review and update documentation", "Consult legal compliance team"])[:4]
            _data["remediation_steps"] = steps
            # Normaliser cross_framework_refs — liste de strings
            refs = _data.get("cross_framework_refs", [])
            if isinstance(refs, str):
                refs = [refs]
            _data["cross_framework_refs"] = [
                r.get("ref_type","") + " " + r.get("ref_article", r.get("ref",""))
                if isinstance(r, dict) else str(r)
                for r in refs
            ]
            # Garantir obligation et severity
            if not _data.get("obligation"):
                _data["obligation"] = f"Comply with {article_ref} requirements"
            if not _data.get("severity"):
                _data["severity"] = 2
            # Normaliser tous les champs qui peuvent etre None ou non-iterables
            steps = _data.get("remediation_steps") or []
            if isinstance(steps, str): steps = [steps]
            steps = [str(s) for s in steps if s]
            if len(steps) < 2:
                steps = (steps + ["Review and update documentation", "Consult legal compliance team"])[:4]
            _data["remediation_steps"] = steps
            refs = _data.get("cross_framework_refs") or []
            if isinstance(refs, str): refs = [refs]
            _data["cross_framework_refs"] = [
                r.get("ref_type","") + " " + r.get("ref_article", r.get("ref",""))
                if isinstance(r, dict) else str(r)
                for r in refs if r
            ]
            if not _data.get("deadline_risk"):
                _data["deadline_risk"] = None
            analysis = ArticleAnalysis(**_data)
        except asyncio.TimeoutError:
            logger.warning(f"[Analyzer] Timeout for {article_ref} — skipped")
            return None
        except Exception as e:
            logger.warning(f"[Analyzer] Failed for {article_ref}: {e} — skipped")
            return None

        chain = await build_evidence_chain(
            article_ref=article_ref,
            article_title=article_title,
            obligation_text=analysis.obligation,
            system_text=system_text,
            system_name=system_name,
        )

        fw_map = {
            "eu_ai_act":   Framework.EU_AI_ACT,
            "gdpr":        Framework.GDPR,
            "nist_ai_rmf": Framework.NIST_AI_RMF,
        }

        return ComplianceGap(
            gap_id=str(uuid.uuid4())[:8],
            framework=fw_map.get(framework_str, Framework.EU_AI_ACT),
            article_num=article_ref,
            article_title=article_title,
            obligation=analysis.obligation,
            gap_description=analysis.obligation,
            status=chain.final_status,
            severity=int(analysis.severity),
            evidence_chain=chain,
            remediation_steps=analysis.remediation_steps,
            deadline_risk=analysis.deadline_risk,
            cross_framework_refs=analysis.cross_framework_refs,
        )


async def analyze_all_articles(
    system_text: str,
    articles:    list[dict],
    risk_level:  RiskLevel,
    system_name: str = "Unknown",
) -> tuple[list[ComplianceGap], float]:
    """
    Analyze all retrieved articles against the system documentation.
    Semaphore(2) — max 2 LLM calls in parallel pour limiter la RAM.
    Returns (gaps, overall_confidence).
    """
    if not articles:
        logger.warning("[Analyzer] No articles to analyze — returning empty gaps")
        return [], 0.0

    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    tasks = [
        _analyze_single(art, system_text, system_name, risk_level, sem)
        for art in articles
    ]
    results = await asyncio.gather(*tasks)
    gaps = [g for g in results if g is not None]

    if not gaps:
        logger.warning("[Analyzer] All articles failed analysis — returning empty gaps")
        return [], 0.0

    confidence = round(
        sum(g.evidence_chain.avg_confidence for g in gaps) / len(gaps), 3
    )
    logger.info(f"[Analyzer] {len(gaps)}/{len(articles)} gaps built — conf={confidence:.2f}")
    return gaps, confidence