import asyncio
from qdrant_client import QdrantClient
import httpx

QDRANT_PATH = "data/qdrant_db"
COLLECTION  = "themis_regulations"

async def embed(text):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("http://localhost:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": text})
        r.raise_for_status()
        return r.json()["embedding"]

async def main():
    client = QdrantClient(path=QDRANT_PATH)
    cols = [c.name for c in client.get_collections().collections]
    print(f"Collections: {cols}")
    if COLLECTION in cols:
        info = client.get_collection(COLLECTION)
        print(f"Points: {info.points_count}")
        vec = await embed("human oversight AI system")
        try:
            r = client.query_points(collection_name=COLLECTION, query=vec, limit=3, with_payload=True).points
        except Exception:
            r = client.search(collection_name=COLLECTION, query_vector=vec, limit=3, with_payload=True)
        print(f"Search results: {len(r)}")
        for x in r:
            print(f"  {x.payload.get('article_num')} | {x.payload.get('framework')} | {x.score:.3f}")
    else:
        print("COLLECTION NOT FOUND — need to seed")

asyncio.run(main())
