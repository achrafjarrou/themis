from __future__ import annotations
from rag.embedder import embed_query, embed_texts
import hashlib, uuid
from pathlib    import Path
from typing     import Optional
from loguru     import logger
from qdrant_client        import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import httpx
from core.exceptions import RetrievalError

QDRANT_PATH = "data/qdrant_db"
COLLECTION  = "themis_regulations"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM   = 768
OLLAMA_URL  = "http://localhost:11434"

_client: Optional[QdrantClient] = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=QDRANT_PATH)
        logger.info(f"Qdrant client initialised at {QDRANT_PATH}")
    return _client

async def embed(text: str) -> list[float]:
    return embed_query(text)

def build_regulation_index(articles: list[dict], framework: str, force_rebuild: bool = False) -> None:
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing and not force_rebuild:
        logger.info(f"Collection exists — skipping. Use force_rebuild=True to override.")
        return
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    client.create_collection(collection_name=COLLECTION,
                             vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))
    logger.info(f"Created Qdrant collection dim={EMBED_DIM}")
    import asyncio
    points: list[PointStruct] = []
    async def _build():
        for i, art in enumerate(articles):
            vec = await embed(art["text"])
            points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, art.get("article_num", str(i)))),
                vector=vec,
                payload={"article_num": art.get("article_num",""), "article_title": art.get("article_title",""),
                         "text": art["text"], "framework": framework, "chunk_idx": art.get("chunk_idx",0)},
            ))
            if (i+1) % 10 == 0:
                logger.debug(f"Embedded {i+1}/{len(articles)}")
        client.upsert(collection_name=COLLECTION, points=points)
        logger.success(f"Indexed {len(points)} points")
    asyncio.run(_build())

async def vector_search(query: str, framework: Optional[str] = None, top_k: int = 20) -> list[dict]:
    client = get_client()
    vec    = await embed(query)
    flt    = None
    if framework:
        flt = Filter(must=[FieldCondition(key="framework", match=MatchValue(value=framework))])
    def _search(f):
        try:
            return client.query_points(
                collection_name=COLLECTION, query=vec,
                limit=top_k, query_filter=f, with_payload=True,
            ).points
        except AttributeError:
            return client.search(
                collection_name=COLLECTION, query_vector=vec,
                limit=top_k, query_filter=f, with_payload=True,
            )
    results = _search(flt)
    if not results and flt:
        logger.warning(f"No results with framework filter — retrying without filter")
        results = _search(None)
    if not results:
        logger.warning(f"No results for query: {query[:60]}")
        return []
    return [{**r.payload, "vector_score": r.score} for r in results]





# ════════════════════════════════════════════════════════════════
# FIX 6 — verify_all_collections()  (ajouté par THEMIS patch)
# Vérifie que les collections Qdrant existent pour chaque framework
# avant de lancer le pipeline RAG.
# ════════════════════════════════════════════════════════════════
from core.models import Framework as _Framework

# Map framework enum -> Qdrant collection name
FRAMEWORK_COLLECTION_MAP: dict[str, str] = {
    _Framework.EU_AI_ACT.value:   COLLECTION,   # "themis_regulations" par défaut
    _Framework.GDPR.value:        COLLECTION,
    _Framework.NIST_AI_RMF.value: COLLECTION,
}

def verify_all_collections(frameworks: list) -> dict[str, bool]:
    """
    Verify Qdrant collections exist for the requested frameworks.

    Returns:
        dict mapping collection_name -> True/False (exists)

    Logs a WARNING for every missing collection so the developer
    knows to run: python -m ingest.parser && python -m rag.store

    Usage:
        from rag.store import verify_all_collections
        from core.models import Framework
        results = verify_all_collections([Framework.EU_AI_ACT, Framework.GDPR])
        # -> {"themis_regulations": True}
    """
    client = get_client()
    try:
        existing_names = {c.name for c in client.get_collections().collections}
    except Exception as e:
        logger.error(f"[RAG] Cannot connect to Qdrant at {QDRANT_PATH}: {e}")
        logger.error("[RAG] Make sure Qdrant is running or qdrant_path is writable.")
        return {}

    results: dict[str, bool] = {}
    seen_collections: set[str] = set()

    for fw in frameworks:
        fw_val = fw.value if hasattr(fw, "value") else str(fw)
        col = FRAMEWORK_COLLECTION_MAP.get(fw_val, COLLECTION)

        if col in seen_collections:
            continue
        seen_collections.add(col)

        exists = col in existing_names
        results[col] = exists

        if not exists:
            logger.warning(
                f"[RAG] Collection '{col}' MISSING for framework '{fw_val}'. "
                f"Run index build: python -m ingest.parser && "
                f"python -c \"from rag.store import build_regulation_index; "
                f"...\""
            )
        else:
            count = client.count(collection_name=col).count
            logger.info(
                f"[RAG] Collection '{col}' OK — {count:,} vectors "
                f"(framework: {fw_val})"
            )

    return results


# ═══════════════════════════════════════════════════════
# FIX C — safe_vector_search  (ajouté par THEMIS hotfix)
# ═══════════════════════════════════════════════════════

def collection_exists() -> bool:
    """True si la collection Qdrant existe ET contient des vecteurs."""
    try:
        c     = get_client()
        names = {col.name for col in c.get_collections().collections}
        if COLLECTION not in names:
            return False
        return c.count(collection_name=COLLECTION).count > 0
    except Exception:
        return False


async def safe_vector_search(
    query:     str,
    framework: str | None = None,
    top_k:     int = 5,
) -> list[dict]:
    """
    vector_search avec fallback [] si collection vide/absente.
    Ne lève jamais d exception — le pipeline continue sans RAG.
    """
    if not collection_exists():
        logger.warning(
            "[RAG] Collection Qdrant vide ou absente — pipeline sans RAG. "
            "Place eu_ai_act.pdf dans data/ et relance pour indexer."
        )
        return []
    try:
        return await vector_search(query, framework=framework, top_k=top_k)
    except Exception as e:
        logger.warning(f"[RAG] vector_search echoue: {e} — retourne []")
        return []