from __future__ import annotations
from core.llm import _raw, client as _client
import asyncio
from loguru  import logger
from core.models     import RiskClassification, RiskLevel
from core.exceptions import ClassificationError
from core.llm        import client, MODEL, LLM_TIMEOUT, MAX_RETRIES, OLLAMA_OPTIONS

MAX_CONTEXT = 1200  # chars — réduit pour tenir dans num_ctx=768

SYSTEM_PROMPT = """You are an EU AI Act compliance expert.
Classify the AI system according to EU AI Act risk levels.

RISK LEVELS:
- unacceptable : prohibited (Article 5) — social scoring, real-time biometric surveillance
- high         : Annex III — credit scoring, CV screening, biometrics, critical infra, law enforcement
- limited      : Article 50 — chatbots, emotion recognition, deepfakes (transparency only)
- minimal      : no specific obligations — spam filters, AI in video games
- gpai         : Title VIII Article 51+ — general-purpose AI models
- unknown      : insufficient information

EXAMPLE 1:
System: "AutoHireAI — ranks job applicants automatically."
-> {"risk_level":"high","reasoning":"CV screening for employment is Annex III point 4(a). Article 6 applies.","applicable_annexes":["Annex III"],"applicable_articles":["Article 6","Article 9","Article 13"],"confidence":0.93}

EXAMPLE 2:
System: "ChatSupport — customer service chatbot."
-> {"risk_level":"limited","reasoning":"Chatbot triggers Article 50(1) transparency obligation only.","applicable_annexes":[],"applicable_articles":["Article 50"],"confidence":0.88}

RULES:
- Respond ONLY with valid JSON — no preamble, no markdown.
- applicable_articles format: exactly "Article N" (e.g. "Article 6").
- confidence: 0.0 to 1.0."""


async def classify_system_risk(
    system_text: str,
    system_name: str,
) -> RiskClassification:
    prompt = (
        f"System name: {system_name}\n\n"
        f"Documentation excerpt:\n{system_text[:MAX_CONTEXT]}\n\n"
        f"Classify this AI system. Cite the exact article or annex."
    )
    try:
        result: RiskClassification = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                response_model=RiskClassification,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_retries=MAX_RETRIES,
                extra_body=OLLAMA_OPTIONS,
            ),
            timeout=LLM_TIMEOUT,
        )
        logger.info(
            f"[Classifier] '{system_name}' -> {result.risk_level.value} "
            f"(conf={result.confidence:.2f})"
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"[Classifier] Timeout ({LLM_TIMEOUT}s) — fallback UNKNOWN")
    except Exception as e:
        logger.error(f"[Classifier] Failed for '{system_name}': {e}")

    return RiskClassification(
        risk_level=RiskLevel.UNKNOWN,
        reasoning="Classification timed out or failed — manual review required.",
        applicable_annexes=[],
        applicable_articles=[],
        confidence=0.0,
    )