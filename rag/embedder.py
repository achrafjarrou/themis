from sentence_transformers import SentenceTransformer
_m = None
def _get():
    global _m
    if _m is None: _m = SentenceTransformer("all-MiniLM-L6-v2")
    return _m
def embed_texts(texts): return _get().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
def embed_query(text): return embed_texts([text])[0]
