# THEMIS — rag\reranker.py

from __future__ import annotations
import asyncio
from typing  import Optional
from loguru  import logger
from rag.hyde import hybrid_retrieve

# Lazy load — only downloaded once (~80MB)
_reranker = None

def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        logger.info("Loading cross-encoder (first load ~80MB)...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.success("Cross-encoder loaded")
    return _reranker



async def retrieve_and_rerank(
    query:      str,
    framework:  Optional[str] = None,
    top_k_pre:  int = 20,   # candidates before reranking
    top_k_post: int = 5,    # final results after reranking
) -> list[dict]:
    """
    Full retrieval pipeline:
      1. Hybrid retrieve (raw + HyDE + RRF)  → top_k_pre candidates
      2. Cross-encoder reranking              → top_k_post final results
    Cross-encoder scores each (query, passage) pair jointly —
    much more accurate than vector similarity alone.
    """
    candidates = await hybrid_retrieve(query, framework=framework, top_k=top_k_pre)
    if not candidates:
        return []

    reranker = _get_reranker()
    loop     = asyncio.get_event_loop()
    pairs    = [(query, doc["text"]) for doc in candidates]
    scores   = await loop.run_in_executor(None, reranker.predict, pairs)

    for doc, score in zip(candidates, scores):
        doc["rerank_score"] = float(score)

    ranked = sorted(candidates, key=lambda d: d["rerank_score"], reverse=True)
    logger.info(f"Reranked {len(candidates)} → top {top_k_post} | best={ranked[0]['rerank_score']:.3f}")
    return ranked[:top_k_post]



if __name__ == "__main__":
    # Quick test — run: python -m rag.reranker
    import asyncio as aio

    queries = [
        "transparency obligations for high-risk AI systems",
        "technical documentation requirements Article 11",
        "human oversight measures for automated decisions",
    ]
    async def _test():
        for q in queries:
            results = await retrieve_and_rerank(q, top_k_post=3)
            print(f"\nQuery: {q}")
            for r in results:
                print(f"  [{r['rerank_score']:.3f}] {r['article_num']} — {r['article_title']}")

    aio.run(_test())
