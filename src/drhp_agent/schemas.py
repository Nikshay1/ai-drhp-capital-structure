"""Pydantic models for the DRHP Capital Structure pipeline.

These schemas define the data contract between pipeline stages:
  ParsedDocument  →  ClassifiedDocument  →  CapitalAlteration  →  rendered output

Every value-carrying field has a sibling `_source` Citation so that the final
table is fully traceable back to a specific document, page, and quoted passage.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocumentType(str, Enum):
    SH7 = "SH-7"
    PAS3 = "PAS-3"
    BOARD_RESOLUTION = "BOARD_RESOLUTION"
    SHAREHOLDER_RESOLUTION = "SHAREHOLDER_RESOLUTION"
    EGM_NOTICE = "EGM_NOTICE"
    AGM_NOTICE = "AGM_NOTICE"
    ALTERED_MOA = "ALTERED_MOA"
    OTHER = "OTHER"


class FlagSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class MeetingType(str, Enum):
    AGM = "AGM"
    EGM = "EGM"


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """A pointer back to the exact location in a source document."""
    citation_id: str = Field(..., description="Short key like 'S1', 'S2' for footnotes")
    doc_id: str = Field(..., description="Relative path to the source PDF, e.g. 'sh7_01_2019_aug/sh7.pdf'")
    page: int | None = Field(None, description="1-indexed page number")
    quote: str = Field("", description="Exact passage from the source that backs the value")


# ---------------------------------------------------------------------------
# Stage 1 — Ingest
# ---------------------------------------------------------------------------

class PageContent(BaseModel):
    """Text extracted from a single PDF page."""
    page_no: int
    text: str


class ParsedDocument(BaseModel):
    """Output of the ingest stage for one PDF."""
    id: str = Field(..., description="Unique identifier, e.g. 'sh7_01_2019_aug/sh7.pdf'")
    source_path: str
    pages: list[PageContent]
    is_ocr: bool = False
    total_text: str = Field("", description="Concatenation of all page texts for convenience")


# ---------------------------------------------------------------------------
# Stage 2 — Classification
# ---------------------------------------------------------------------------

class ClassifiedDocument(BaseModel):
    """A parsed document with its type label and event grouping."""
    doc: ParsedDocument
    doc_type: DocumentType
    event_id: str = Field("", description="Stable key linking docs that describe the same corporate event")
    official: bool = Field(True, description="Whether filed with RoC (True) or internal/draft")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Stage 3 — Extraction
# ---------------------------------------------------------------------------

class ShareTranche(BaseModel):
    """One class of shares within a capital structure."""
    share_class: Literal["equity", "preference"]
    num_shares: int
    face_value: int  # rupees per share


class CapitalAmount(BaseModel):
    """Structured representation of a share-capital amount."""
    total_rupees: int
    breakdown: list[ShareTranche]
    raw_text: str = Field("", description="Exact phrase from the source document")


class Flag(BaseModel):
    """An open question or data-quality issue."""
    field: str
    event_id: str
    reason: str
    severity: FlagSeverity
    sources: list[Citation] = Field(default_factory=list)


class CapitalAlteration(BaseModel):
    """One row in the Authorised Share Capital history table."""
    event_id: str
    meeting_date: date | None = None
    meeting_type: MeetingType | None = None
    capital_before: CapitalAmount | None = None
    capital_after: CapitalAmount | None = None
    particulars: str = ""
    sources: list[Citation] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    is_inferred: bool = Field(False, description="True if this row was synthesised (e.g. incorporation)")


# ---------------------------------------------------------------------------
# Pipeline output
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    """Complete output of the DRHP agent pipeline."""
    company_name: str = ""
    events: list[CapitalAlteration]
    all_flags: list[Flag] = Field(default_factory=list)
    sources_registry: dict[str, Citation] = Field(default_factory=dict)
