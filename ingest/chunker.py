# THEMIS — ingest\chunker.py

from __future__ import annotations
from typing   import Iterator
from loguru   import logger
from core.exceptions import ChunkError


def smart_chunk(
    text:       str,
    chunk_size: int = 512,   # tokens approx
    overlap:    int = 64,    # overlap tokens
    min_words:  int = 15,    # discard tiny fragments
) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Strategy:
      1. Split by paragraph boundary (double newline)
      2. Merge short paragraphs until chunk_size reached
      3. Add overlap from end of previous chunk
    Returns list of non-empty string chunks.
    """
    if not text.strip():
        raise ChunkError("Input text is empty")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_words: list[str] = []
    prev_tail: list[str] = []

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        current_words.extend(words)

        if len(current_words) >= chunk_size:
            chunk_text = " ".join(prev_tail + current_words)
            if len(current_words) >= min_words:
                chunks.append(chunk_text)
            prev_tail     = current_words[-overlap:]
            current_words = []

    # Last partial chunk
    if current_words and len(current_words) >= min_words:
        chunks.append(" ".join(prev_tail + current_words))

    if not chunks:
        raise ChunkError(f"No valid chunks produced from text of {len(text.split())} words")

    logger.debug(f"smart_chunk: {len(paragraphs)} paragraphs → {len(chunks)} chunks")
    return chunks


def chunk_article(article_text: str, article_ref: str) -> list[dict]:
    """Chunk a single article and tag each chunk with its source reference."""
    chunks = smart_chunk(article_text, chunk_size=256, overlap=32)
    return [
        {"text": c, "article_ref": article_ref, "chunk_idx": i}
        for i, c in enumerate(chunks)
    ]
