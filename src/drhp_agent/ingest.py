"""Stage 1 — Ingest & Parse.

Turn each PDF into clean text plus per-page metadata.
  - Text-based PDFs: pdfplumber (best for tables) with pymupdf fallback.
  - Scanned PDFs: detect low text yield and route through pytesseract OCR.
  - Preserve (document_id, page_number) tuples for downstream citations.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .schemas import PageContent, ParsedDocument

log = logging.getLogger(__name__)

# Minimum characters per page to consider it text-based (not scanned)
_MIN_TEXT_CHARS = 50


def _extract_text_pdfplumber(pdf_path: str) -> list[PageContent]:
    """Extract text using pdfplumber (good table extraction)."""
    import pdfplumber

    pages: list[PageContent] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageContent(page_no=i, text=text))
    return pages


def _extract_text_pymupdf(pdf_path: str) -> list[PageContent]:
    """Fallback text extraction using pymupdf (fitz)."""
    import fitz  # pymupdf

    pages: list[PageContent] = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append(PageContent(page_no=i, text=text))
    doc.close()
    return pages


def _ocr_pdf(pdf_path: str) -> list[PageContent]:
    """OCR a scanned PDF using pytesseract."""
    try:
        import fitz
        from PIL import Image
        import pytesseract
        import io
    except ImportError as e:
        log.warning("OCR dependencies not available: %s", e)
        return []

    pages: list[PageContent] = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        # Render page to image at 300 DPI
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img) or ""
        pages.append(PageContent(page_no=i, text=text))
    doc.close()
    return pages


def _is_scanned(pages: list[PageContent]) -> bool:
    """Heuristic: if average characters per page is below threshold, assume scan."""
    if not pages:
        return True
    avg_chars = sum(len(p.text) for p in pages) / len(pages)
    return avg_chars < _MIN_TEXT_CHARS


def parse_pdf(pdf_path: str, doc_id: str) -> ParsedDocument:
    """Parse a single PDF into a ParsedDocument.
    
    Tries pdfplumber first; falls back to pymupdf; routes to OCR if scanned.
    """
    log.info("Parsing: %s", pdf_path)

    # Try pdfplumber first
    try:
        pages = _extract_text_pdfplumber(pdf_path)
    except Exception as e:
        log.warning("pdfplumber failed on %s: %s — falling back to pymupdf", pdf_path, e)
        try:
            pages = _extract_text_pymupdf(pdf_path)
        except Exception as e2:
            log.error("Both extractors failed on %s: %s", pdf_path, e2)
            pages = []

    is_ocr = False
    if _is_scanned(pages):
        log.info("Low text yield on %s — attempting OCR", pdf_path)
        ocr_pages = _ocr_pdf(pdf_path)
        if ocr_pages and sum(len(p.text) for p in ocr_pages) > sum(len(p.text) for p in pages):
            pages = ocr_pages
            is_ocr = True
        else:
            log.warning("OCR did not improve text yield for %s", pdf_path)

    total_text = "\n\n".join(p.text for p in pages)

    return ParsedDocument(
        id=doc_id,
        source_path=pdf_path,
        pages=pages,
        is_ocr=is_ocr,
        total_text=total_text,
    )


def ingest_folder(data_dir: str) -> list[ParsedDocument]:
    """Ingest all PDFs from the data directory.
    
    Expected structure:
        data/
          sh7_01_2019_aug/
            sh7.pdf
            board_resolution.pdf
            ...
          sh7_02_2021_sep/
            ...
    
    Returns a flat list of ParsedDocuments with doc_id set to
    the relative path from data_dir (e.g. "sh7_01_2019_aug/sh7.pdf").
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    documents: list[ParsedDocument] = []

    for folder in sorted(data_path.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        for pdf_file in sorted(folder.glob("*.pdf")):
            doc_id = f"{folder.name}/{pdf_file.name}"
            doc = parse_pdf(str(pdf_file), doc_id)
            documents.append(doc)

    log.info("Ingested %d documents from %s", len(documents), data_dir)
    return documents
