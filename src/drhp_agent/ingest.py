"""Stage 1 -- Ingest & Parse.

Turns each document (PDF or markdown) into clean text with metadata.
- Markdown files (.md): read directly as text.
- PDF files: pdfplumber with pymupdf fallback; OCR for scanned docs.
- Preserves (doc_id, page_number) for citations.
"""
from __future__ import annotations
import logging
from pathlib import Path
from .schemas import PageContent, ParsedDocument

log = logging.getLogger(__name__)
_MIN_TEXT_CHARS = 50


def _read_markdown(path: str) -> list[PageContent]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return [PageContent(page_no=1, text=text)]


def _extract_text_pdfplumber(path: str) -> list[PageContent]:
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            pages.append(PageContent(page_no=i, text=page.extract_text() or ""))
    return pages


def _extract_text_pymupdf(path: str) -> list[PageContent]:
    import fitz
    pages = []
    doc = fitz.open(path)
    for i, page in enumerate(doc, 1):
        pages.append(PageContent(page_no=i, text=page.get_text()))
    doc.close()
    return pages


def _ocr_pdf(path: str) -> list[PageContent]:
    try:
        import fitz, io, pytesseract
        from PIL import Image
    except ImportError as e:
        log.warning("OCR deps unavailable: %s", e)
        return []
    pages = []
    doc = fitz.open(path)
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        pages.append(PageContent(page_no=i, text=pytesseract.image_to_string(img) or ""))
    doc.close()
    return pages


def parse_document(file_path: str, doc_id: str) -> ParsedDocument:
    """Parse a single file (PDF or markdown) into ParsedDocument."""
    log.info("Parsing: %s", file_path)
    ext = Path(file_path).suffix.lower()

    if ext == ".md":
        pages = _read_markdown(file_path)
        is_ocr = False
    elif ext == ".pdf":
        try:
            pages = _extract_text_pdfplumber(file_path)
        except Exception:
            try:
                pages = _extract_text_pymupdf(file_path)
            except Exception:
                pages = []
        is_ocr = False
        if pages and sum(len(p.text) for p in pages) / max(len(pages), 1) < _MIN_TEXT_CHARS:
            ocr = _ocr_pdf(file_path)
            if ocr and sum(len(p.text) for p in ocr) > sum(len(p.text) for p in pages):
                pages, is_ocr = ocr, True
    else:
        log.warning("Unsupported file type: %s", ext)
        pages = []
        is_ocr = False

    return ParsedDocument(
        id=doc_id, source_path=file_path, pages=pages,
        is_ocr=is_ocr, total_text="\n\n".join(p.text for p in pages),
    )


def ingest_folder(data_dir: str) -> list[ParsedDocument]:
    """Ingest all documents (.md and .pdf) from the data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    documents = []
    for folder in sorted(data_path.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in (".md", ".pdf"):
                doc_id = f"{folder.name}/{f.name}"
                documents.append(parse_document(str(f), doc_id))

    log.info("Ingested %d documents from %s", len(documents), data_dir)
    return documents
