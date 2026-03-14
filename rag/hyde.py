# THEMIS — rag\hyde.py

from __future__ import annotations
import asyncio
from typing  import Optional
from loguru  import logger
from rag.store import vector_search

LLM_MODEL  = "phi3:mini"
RRF_K      = 60   # RRF constant — 60 is the standard


async def _llm_complete(prompt: str, max_tokens: int = 200) -> str:
    from core.llm import chat_with_retry
    return await chat_with_retry([{"role":"user","content":prompt}], max_tokens=max_tokens)

async def hyde_retrieve(
    query: str,
    framework: Optional[str] = None,
    top_k: int = 20,
) -> list[dict]:
    """
    HyDE (Hypothetical Document Embeddings) retrieval.
    1. Generate a hypothetical compliance passage that would answer the query
    2. Embed the hypothetical passage instead of the raw query
    3. Search with the hypothetical embedding — much better recall for legal text
    """
    hyde_prompt = (
        f"Write a short passage from an EU AI Act compliance audit report that directly\n"
        f"addresses this compliance question:\n\n{query}\n\n"
        f"The passage should cite specific articles and explain obligations clearly.\n"
        f"Passage:"
    )
    hypothetical = await asyncio.wait_for(_llm_complete(hyde_prompt, max_tokens=200), timeout=90)
    logger.debug(f"HyDE hypothesis generated ({len(hypothetical.split())} words)")
    return await vector_search(hypothetical, framework=framework, top_k=top_k)



def rrf_fusion(results_a: list[dict], results_b: list[dict]) -> list[dict]:
    """
    Reciprocal Rank Fusion — merge two ranked lists.
    score(d) = Σ 1/(k + rank(d))  where k=60
    Returns merged list sorted by RRF score descending.
    """
    scores: dict[str, float] = {}
    merged: dict[str, dict]  = {}

    for rank, doc in enumerate(results_a):
        key = doc.get("article_num", str(rank))
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
        merged[key] = doc

    for rank, doc in enumerate(results_b):
        key = doc.get("article_num", str(rank))
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
        merged[key] = doc

    fused = sorted(merged.values(), key=lambda d: scores[d.get("article_num", "")], reverse=True)
    for doc in fused:
        doc["rrf_score"] = scores[doc.get("article_num", "")]
    return fused


async def hybrid_retrieve(
    query:     str,
    framework: Optional[str] = None,
    top_k:     int = 10,
) -> list[dict]:
    """
    Full hybrid retrieval: raw query + HyDE query, fused with RRF.
    Best of both worlds — direct match + semantic expansion.
    """
    raw_results, hyde_results = await asyncio.gather(
        vector_search(query, framework=framework, top_k=top_k * 2),
        hyde_retrieve(query,  framework=framework, top_k=top_k * 2),
    )
    fused = rrf_fusion(raw_results, hyde_results)
    logger.info(f"Hybrid retrieve: {len(raw_results)} raw + {len(hyde_results)} HyDE → {len(fused)} fused")
    return fused[:top_k]
