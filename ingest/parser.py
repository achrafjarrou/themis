from __future__ import annotations
import re, json
from pathlib    import Path
from typing     import Optional
from pydantic   import BaseModel, Field
from loguru     import logger

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# ── OCR : auto-détection Tesseract ───────────────────────────────
_OCR_AVAILABLE  = False
_TESS_WARNED    = False   # n'affiche l'avertissement qu'une seule fois

try:
    import pytesseract
    from PIL import Image as _PIL

    # Cherche Tesseract dans les emplacements Windows standard
    _TESS_CANDIDATES = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
            __import__("os").environ.get("USERNAME", "")
        ),
    ]
    for _candidate in _TESS_CANDIDATES:
        if Path(_candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = _candidate
            logger.info(f"[OCR] Tesseract trouvé : {_candidate}")
            break

    # Vérification finale
    pytesseract.get_tesseract_version()
    _OCR_AVAILABLE = True
    logger.info("[OCR] pytesseract opérationnel")

except Exception as _ocr_init_err:
    _OCR_AVAILABLE = False
    logger.warning(
        f"[OCR] pytesseract non opérationnel ({_ocr_init_err}). "
        f"Les pages scannées seront ignorées. "
        f"Pour activer l'OCR : installez Tesseract depuis "
        f"https://github.com/UB-Mannheim/tesseract/wiki "
        f"puis relancez."
    )

from core.exceptions import ParseError


class ParsedArticle(BaseModel):
    article_num:   str
    article_title: str
    text:          str
    framework:     str
    chapter:       Optional[str] = None
    word_count:    int = Field(default=0)

    def model_post_init(self, _) -> None:
        object.__setattr__(self, "word_count", len(self.text.split()))


def parse_system_doc(pdf_path: str) -> str:
    """
    Extrait le texte d'un PDF de documentation système.
    - pdfplumber pour les pages avec texte sélectionnable
    - pytesseract OCR pour les pages scannées (si Tesseract installé)
    - Un seul warning global si Tesseract est absent (pas de spam par page)
    """
    global _TESS_WARNED

    path = Path(pdf_path)
    if not path.exists():
        raise ParseError(f"PDF non trouvé : {pdf_path}")
    if pdfplumber is None:
        raise ParseError("pdfplumber manquant — pip install pdfplumber")

    pages: list[str] = []
    ocr_pages:     list[int] = []
    skipped_pages: list[int] = []

    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t and len(t.strip()) > 20:
                pages.append(t.strip())
            else:
                # Page sans texte sélectionnable
                if _OCR_AVAILABLE:
                    try:
                        img      = page.to_image(resolution=200).original
                        ocr_text = pytesseract.image_to_string(img, lang="fra+eng")
                        if ocr_text.strip():
                            pages.append(ocr_text.strip())
                            ocr_pages.append(i + 1)
                        else:
                            skipped_pages.append(i + 1)
                    except Exception as ocr_err:
                        logger.debug(f"[OCR] Page {i+1} échouée : {ocr_err}")
                        skipped_pages.append(i + 1)
                else:
                    skipped_pages.append(i + 1)

    # ── Résumé des pages ignorées (1 seul log, pas un par page) ───
    if skipped_pages and not _OCR_AVAILABLE and not _TESS_WARNED:
        logger.warning(
            f"[PDF] {len(skipped_pages)} page(s) sans texte sélectionnable ignorées "
            f"(ex : pages {skipped_pages[:5]}). "
            f"Pour les lire, installez Tesseract OCR : "
            f"https://github.com/UB-Mannheim/tesseract/wiki"
        )
        _TESS_WARNED = True
    elif skipped_pages and _OCR_AVAILABLE:
        logger.warning(
            f"[PDF] {len(skipped_pages)} page(s) ignorées même avec OCR "
            f"(pages vides ou images illisibles) : {skipped_pages[:10]}"
        )

    if ocr_pages:
        logger.warning(
            f"[PDF] OCR utilisé sur {len(ocr_pages)} page(s) : {ocr_pages}. "
            f"Vérifiez la précision avant de vous fier aux résultats de conformité."
        )

    full = "\n\n".join(pages)
    if len(full.strip()) < 100:
        tip = (
            "OCR tenté mais résultat insuffisant — vérifiez que Tesseract est installé."
            if _OCR_AVAILABLE else
            "Installez Tesseract pour lire les PDFs scannés : "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        )
        raise ParseError(
            f"Texte extrait trop court ({len(full)} chars) — PDF peut-être scanné. {tip}"
        )

    logger.success(
        f"[PDF] Parsé : {path.name} — {len(full):,} chars, "
        f"{len(pages)} pages ({len(ocr_pages)} via OCR, "
        f"{len(skipped_pages)} ignorées)"
    )
    return full


def parse_regulation_pdf(pdf_path: str, framework: str) -> list[ParsedArticle]:
    """Parse un PDF réglementaire en articles structurés. Cache JSON local."""
    cache = Path(f"data/{framework}_articles.json")
    if cache.exists():
        logger.info(f"[PDF] Cache hit : {cache}")
        raw = json.loads(cache.read_text(encoding="utf-8"))
        return [ParsedArticle(**a) for a in raw]

    path = Path(pdf_path)
    if not path.exists():
        raise ParseError(f"PDF réglementaire non trouvé : {pdf_path}")

    full_text = ""
    with pdfplumber.open(str(path)) as pdf:
        full_text = "\n\n".join(p.extract_text() or "" for p in pdf.pages)

    articles = _split_into_articles(full_text, framework)
    if not articles:
        raise ParseError(f"Aucun article parsé depuis {pdf_path}")

    cache.parent.mkdir(exist_ok=True)
    cache.write_text(
        json.dumps([a.model_dump() for a in articles], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.success(f"[PDF] {len(articles)} articles parsés depuis {path.name} -> {cache}")
    return articles


def _split_into_articles(text: str, framework: str) -> list[ParsedArticle]:
    pattern = re.compile(
        r'(?m)^(?:Article|ARTICLE)\s+(\d+[a-z]?)(?:\s*[-—]\s*|\s*\n\s*)([^\n]{3,120})',
    )
    chapter_re = re.compile(
        r'(?m)^(?:Chapter|CHAPTER|SECTION)\s+[IVXivx\d]+\s*[-—]\s*(.+)$'
    )
    matches = list(pattern.finditer(text))
    articles: list[ParsedArticle] = []
    current_chapter: Optional[str] = None

    for idx, m in enumerate(matches):
        num   = m.group(1).strip()
        title = m.group(2).strip().rstrip(".")
        start = m.end()
        end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body  = text[start:end].strip()

        for cm in chapter_re.finditer(text[:m.start()]):
            current_chapter = cm.group(1).strip()

        if len(body.split()) < 5:
            continue

        articles.append(ParsedArticle(
            article_num=f"Article {num}",
            article_title=title,
            text=body[:4000],
            framework=framework,
            chapter=current_chapter,
        ))

    logger.info(f"[PDF] {len(articles)} articles extraits pour {framework}")
    return articles
