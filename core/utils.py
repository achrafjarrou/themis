from __future__ import annotations
import re

# Matches: "art.13", "Art 13 §2", "article13", "ARTICLE 13(1)"
_ART_RE = re.compile(
    r'(?i)^art(?:icle)?\.?\s*(\d+(?:\s*§\s*\d+)?(?:\s*\(\d+\))?(?:\s*\(\w\))?)'
)

def normalise_article_ref(ref: str) -> str:
    """
    Canonicalise article references.

    Examples:
        'art.13'       -> 'Article 13'
        'Art 13 §2'    -> 'Article 13 §2'
        'article13'    -> 'Article 13'
        'ARTICLE 13'   -> 'Article 13'
        'Article 13'   -> 'Article 13'  (no-op)
        'System Doc §4' -> 'System Doc §4'  (unchanged — not an article ref)
    """
    ref = ref.strip()
    m = _ART_RE.match(ref)
    if m:
        num = re.sub(r'\s+', ' ', m.group(1).strip())
        return f'Article {num}'
    # Not an article ref — just normalise whitespace
    return re.sub(r'\s+', ' ', ref)


def normalise_article_list(refs: list[str]) -> list[str]:
    """Normalise a list of article references in-place."""
    return [normalise_article_ref(r) for r in refs]
