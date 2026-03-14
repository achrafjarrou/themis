from __future__ import annotations
from core.llm import _raw, client as _client
import asyncio, uuid
from itertools import combinations
from pydantic  import BaseModel, Field
from loguru    import logger
from core.models     import Contradiction, SeverityLevel
from core.exceptions import ContradictionError
from core.llm        import client, MODEL, LLM_TIMEOUT, MAX_RETRIES, OLLAMA_OPTIONS

MAX_CONTEXT = 900  # chars


class Claim(BaseModel):
    text:     str
    location: str
    topic:    str

class ClaimList(BaseModel):
    claims: list[Claim] = Field(max_length=15)

class ContradictionCheck(BaseModel):
    is_contradiction:   bool
    contradiction_type: str = Field(description="factual | scope | data | process | none")
    legal_risk:         str
    severity:           int = Field(ge=1, le=4)
    resolution_hint:    str


EXTRACT_SYSTEM = """Extract compliance claims from AI system documentation.
Focus on: data handling, human oversight, transparency, accuracy, scope, user rights.
OUTPUT EXAMPLE:
{"claims":[{"text":"System retains data 5 years","location":"Section 4.1","topic":"data_retention"},{"text":"No human oversight implemented","location":"Section 2.3","topic":"human_oversight"}]}
Respond ONLY with valid JSON."""

CHECK_SYSTEM = """Detect if two documentation claims legally contradict each other.
Types: factual|scope|data|process  Severity: 1=low 2=medium 3=high 4=critical
EXAMPLE:
A: "Data retained 30 days" vs B: "User data never stored"
-> {"is_contradiction":true,"contradiction_type":"factual","legal_risk":"GDPR Art.5(1)(e) violated","severity":3,"resolution_hint":"Align data retention policy"}
Respond ONLY with valid JSON."""


async def extract_claims(system_text: str) -> list[Claim]:
    try:
        result: ClaimList = await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                response_model=ClaimList,
                messages=[
                    {"role": "system", "content": EXTRACT_SYSTEM},
                    {"role": "user",   "content": f"Documentation:\n{system_text[:MAX_CONTEXT]}"},
                ],
                max_retries=MAX_RETRIES,
                extra_body=OLLAMA_OPTIONS,
            ),
            timeout=LLM_TIMEOUT,
        )
        logger.debug(f"[Contradiction] Extracted {len(result.claims)} claims")
        return result.claims
    except asyncio.TimeoutError:
        logger.warning(f"[Contradiction] Extraction timeout ({LLM_TIMEOUT}s)")
        return []
    except Exception as e:
        logger.warning(f"[Contradiction] Extraction failed: {e}")
        return []


async def _check_pair(a: Claim, b: Claim) -> ContradictionCheck | None:
    if a.topic != b.topic:
        return None
    try:
        return await asyncio.wait_for(
            client.chat.completions.create(
                model=MODEL,
                response_model=ContradictionCheck,
                messages=[
                    {"role": "system", "content": CHECK_SYSTEM},
                    {"role": "user",   "content":
                        f"Claim A [{a.location}]: {a.text}\n"
                        f"Claim B [{b.location}]: {b.text}\n"
                        f"Contradiction?"},
                ],
                max_retries=MAX_RETRIES,
                extra_body=OLLAMA_OPTIONS,
            ),
            timeout=LLM_TIMEOUT,
        )
    except Exception:
        return None


async def detect_contradictions(system_text: str) -> list[Contradiction]:
    claims = await extract_claims(system_text)
    if len(claims) < 2:
        return []

    topic_groups: dict[str, list[Claim]] = {}
    for c in claims:
        topic_groups.setdefault(c.topic, []).append(c)

    tasks, pairs = [], []
    for group in topic_groups.values():
        for a, b in combinations(group, 2):
            tasks.append(_check_pair(a, b))
            pairs.append((a, b))

    results = await asyncio.gather(*tasks)
    contradictions: list[Contradiction] = []
    for (a, b), check in zip(pairs, results):
        if check is None or not check.is_contradiction:
            continue
        contradictions.append(Contradiction(
            contradiction_id=str(uuid.uuid4())[:8],
            contradiction_type=check.contradiction_type,
            statement_a=a.text,  location_a=a.location,
            statement_b=b.text,  location_b=b.location,
            legal_risk=check.legal_risk,
            severity=SeverityLevel(check.severity),
            resolution_hint=check.resolution_hint,
        ))

    logger.info(
        f"[Contradiction] {len(tasks)} pairs checked -> "
        f"{len(contradictions)} contradictions"
    )
    return contradictions