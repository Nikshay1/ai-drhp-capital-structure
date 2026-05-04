"""Stage 2 — Document Classification.

For each parsed document, label it with:
  - Document type (SH-7, PAS-3, BOARD_RESOLUTION, etc.)
  - Event ID (stable key linking docs for the same corporate event)
  - Whether it's an official RoC filing or an internal/draft document
  - Confidence score

Strategy: rules-first with LLM fallback.
  1. Regex on headers — fast, free, catches well-structured docs.
  2. If regex is low-confidence, call LLM with first 2 pages.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from pydantic import BaseModel, Field

from .schemas import (
    ClassifiedDocument,
    DocumentType,
    ParsedDocument,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM response model for classification
# ---------------------------------------------------------------------------

class ClassificationResponse(BaseModel):
    document_type: str = Field(..., description="One of: SH-7, PAS-3, BOARD_RESOLUTION, SHAREHOLDER_RESOLUTION, EGM_NOTICE, AGM_NOTICE, ALTERED_MOA, OTHER")
    is_official: bool = Field(True, description="Whether this is an official filing with RoC")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    reasoning: str = Field("", description="Brief explanation of why this classification was chosen")


# ---------------------------------------------------------------------------
# Rule-based classification
# ---------------------------------------------------------------------------

_RULES: list[tuple[re.Pattern, DocumentType, float]] = [
    (re.compile(r"Form\s+(?:No\.?\s*)?SH[\s-]*7", re.IGNORECASE), DocumentType.SH7, 0.9),
    (re.compile(r"Form\s+(?:No\.?\s*)?PAS[\s-]*3", re.IGNORECASE), DocumentType.PAS3, 0.9),
    (re.compile(r"Return\s+of\s+Allotment", re.IGNORECASE), DocumentType.PAS3, 0.8),
    (re.compile(r"Board\s+Resolution", re.IGNORECASE), DocumentType.BOARD_RESOLUTION, 0.85),
    (re.compile(r"Extra[\s-]*ordinary\s+General\s+Meeting|EGM\s+Notice", re.IGNORECASE), DocumentType.EGM_NOTICE, 0.85),
    (re.compile(r"Annual\s+General\s+Meeting|AGM\s+Notice", re.IGNORECASE), DocumentType.AGM_NOTICE, 0.85),
    (re.compile(r"Memorandum\s+of\s+Association|Altered\s+MoA|MoA", re.IGNORECASE), DocumentType.ALTERED_MOA, 0.75),
]


def _classify_by_rules(text: str) -> tuple[DocumentType | None, float]:
    """Attempt rule-based classification from document text."""
    best_type: DocumentType | None = None
    best_conf: float = 0.0

    for pattern, doc_type, conf in _RULES:
        if pattern.search(text[:3000]):  # Only check first ~3000 chars
            if conf > best_conf:
                best_type = doc_type
                best_conf = conf

    return best_type, best_conf


def _classify_by_llm(doc: ParsedDocument) -> tuple[DocumentType, float, bool]:
    """LLM-based classification using first 2 pages."""
    from .llm import call_llm_structured, CLASSIFICATION_MODEL

    # Use first 2 pages
    text = "\n\n".join(p.text for p in doc.pages[:2])[:4000]

    prompt = f"""Classify this Indian corporate regulatory document. 

The document text (first 2 pages):
---
{text}
---

Based on the content, determine:
1. document_type: The type of document. Must be one of:
   - "SH-7" (Form SH-7 — notice to RoC of capital alteration)
   - "PAS-3" (Form PAS-3 — return of allotment of shares)
   - "BOARD_RESOLUTION" (Board resolution approving a corporate action)
   - "SHAREHOLDER_RESOLUTION" (Shareholder resolution)
   - "EGM_NOTICE" (Notice of Extra-ordinary General Meeting)
   - "AGM_NOTICE" (Notice of Annual General Meeting)
   - "ALTERED_MOA" (Altered Memorandum of Association)
   - "OTHER" (Doesn't fit any of the above)

2. is_official: true if this was filed with the Registrar of Companies (RoC), false if it's an internal/draft document.

3. confidence: Your confidence in the classification (0.0 to 1.0).

4. reasoning: Brief explanation."""

    resp = call_llm_structured(
        prompt,
        ClassificationResponse,
        system="You are an expert in Indian corporate law and MCA filings.",
        model=CLASSIFICATION_MODEL,
    )

    # Map string to enum
    type_map = {
        "SH-7": DocumentType.SH7,
        "PAS-3": DocumentType.PAS3,
        "BOARD_RESOLUTION": DocumentType.BOARD_RESOLUTION,
        "SHAREHOLDER_RESOLUTION": DocumentType.SHAREHOLDER_RESOLUTION,
        "EGM_NOTICE": DocumentType.EGM_NOTICE,
        "AGM_NOTICE": DocumentType.AGM_NOTICE,
        "ALTERED_MOA": DocumentType.ALTERED_MOA,
        "OTHER": DocumentType.OTHER,
    }
    doc_type = type_map.get(resp.document_type, DocumentType.OTHER)

    return doc_type, resp.confidence, resp.is_official


def _infer_event_id(doc_id: str) -> str:
    """Infer event grouping from folder name.
    
    Documents in the same folder belong to the same corporate event.
    E.g., "sh7_01_2019_aug/sh7.pdf" → event_id "evt_01_2019_aug"
    """
    folder = doc_id.split("/")[0] if "/" in doc_id else doc_id
    # Strip 'sh7_' prefix and make it an event id
    event_id = folder.replace("sh7_", "evt_")
    return event_id


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_document(doc: ParsedDocument) -> ClassifiedDocument:
    """Classify a single parsed document.
    
    Runs rules first; if confident, skips LLM. Otherwise calls LLM.
    """
    rule_type, rule_conf = _classify_by_rules(doc.total_text)

    if rule_type is not None and rule_conf >= 0.85:
        log.info(
            "Rules classified %s as %s (conf=%.2f)",
            doc.id, rule_type.value, rule_conf,
        )
        return ClassifiedDocument(
            doc=doc,
            doc_type=rule_type,
            event_id=_infer_event_id(doc.id),
            official=rule_type in (DocumentType.SH7, DocumentType.PAS3),
            confidence=rule_conf,
        )

    # LLM fallback
    log.info(
        "Rules low-confidence (%.2f) for %s — calling LLM",
        rule_conf, doc.id,
    )
    try:
        llm_type, llm_conf, is_official = _classify_by_llm(doc)
        # If rules had a type, and LLM agrees, boost confidence
        if rule_type == llm_type:
            llm_conf = min(1.0, llm_conf + 0.1)
        return ClassifiedDocument(
            doc=doc,
            doc_type=llm_type,
            event_id=_infer_event_id(doc.id),
            official=is_official,
            confidence=llm_conf,
        )
    except Exception as e:
        log.warning("LLM classification failed for %s: %s — using rules result", doc.id, e)
        return ClassifiedDocument(
            doc=doc,
            doc_type=rule_type or DocumentType.OTHER,
            event_id=_infer_event_id(doc.id),
            official=False,
            confidence=rule_conf,
        )


def classify_documents(docs: list[ParsedDocument]) -> list[ClassifiedDocument]:
    """Classify all documents and return classified list."""
    classified = [classify_document(d) for d in docs]
    
    # Log summary
    type_counts: dict[str, int] = {}
    for c in classified:
        type_counts[c.doc_type.value] = type_counts.get(c.doc_type.value, 0) + 1
    log.info("Classification summary: %s", type_counts)

    return classified
