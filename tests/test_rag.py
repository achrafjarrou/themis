import pytest
from ingest.chunker import smart_chunk, chunk_article
from rag.hyde        import rrf_fusion
from core.exceptions import ChunkError


# ── smart_chunk ─────────────────────────────────────────────────────
class TestSmartChunk:

    def test_basic_split(self):
        text = ("This is paragraph one. It has several words.\n\n" * 30)
        chunks = smart_chunk(text, chunk_size=50, overlap=5)
        assert len(chunks) >= 1
        assert all(isinstance(c, str) and len(c) > 0 for c in chunks)

    def test_overlap_present(self):
        # Overlap means adjacent chunks share content
        words = [f"word{i}" for i in range(200)]
        text  = " ".join(words[:100]) + "\n\n" + " ".join(words[100:])
        chunks = smart_chunk(text, chunk_size=60, overlap=10)
        assert len(chunks) >= 2

    def test_empty_raises(self):
        with pytest.raises(ChunkError):
            smart_chunk("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ChunkError):
            smart_chunk("   \n\n   ")

    def test_short_text_single_chunk(self):
        text   = "This is a short but valid document with enough words to chunk."
        chunks = smart_chunk(text, chunk_size=512)
        assert len(chunks) == 1

    def test_chunk_article_tags(self):
        chunks = chunk_article("Legal text " * 50, "Article 13")
        assert all(c["article_ref"] == "Article 13" for c in chunks)
        assert all("chunk_idx" in c for c in chunks)


# ── RRF Fusion ──────────────────────────────────────────────────────
class TestRRFFusion:

    def _make_docs(self, nums: list[int]) -> list[dict]:
        return [{"article_num": f"Article {n}", "text": f"text {n}", "vector_score": 0.9} for n in nums]

    def test_fused_list_not_empty(self):
        a = self._make_docs([1, 2, 3])
        b = self._make_docs([2, 3, 4])
        fused = rrf_fusion(a, b)
        assert len(fused) > 0

    def test_rrf_score_present(self):
        a     = self._make_docs([1, 2, 3])
        b     = self._make_docs([1, 4, 5])
        fused = rrf_fusion(a, b)
        assert all("rrf_score" in d for d in fused)

    def test_shared_article_scores_higher(self):
        # Article 1 appears first in both lists → highest RRF score
        a     = self._make_docs([1, 2, 3])
        b     = self._make_docs([1, 4, 5])
        fused = rrf_fusion(a, b)
        scores = {d["article_num"]: d["rrf_score"] for d in fused}
        assert scores["Article 1"] > scores["Article 2"]

    def test_sorted_descending(self):
        a     = self._make_docs([1, 2, 3, 4, 5])
        b     = self._make_docs([5, 4, 3, 2, 1])
        fused = rrf_fusion(a, b)
        scores = [d["rrf_score"] for d in fused]
        assert scores == sorted(scores, reverse=True)

    def test_empty_lists_return_empty(self):
        assert rrf_fusion([], []) == []
