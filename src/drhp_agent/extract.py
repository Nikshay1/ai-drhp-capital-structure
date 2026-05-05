"""Stage 3 — Structured Extraction.

Two-pass LLM strategy: extract fields, then audit for errors.
"""
from __future__ import annotations
import json, logging
from collections import defaultdict
from datetime import date
from pydantic import BaseModel, Field
from .schemas import (
    CapitalAlteration, CapitalAmount, Citation, ClassifiedDocument,
    DocumentType, Flag, FlagSeverity, MeetingType, ShareTranche,
)

log = logging.getLogger(__name__)

class ExtractedShareTranche(BaseModel):
    share_class: str = ""
    num_shares: int = 0
    face_value: int = 0

class ExtractedCapital(BaseModel):
    total_rupees: int = 0
    breakdown: list[ExtractedShareTranche] = Field(default_factory=list)
    raw_text: str = ""
    source_doc_id: str = ""
    source_page: int | None = None
    source_quote: str = ""

class ExtractionResponse(BaseModel):
    meeting_date: str | None = None
    meeting_date_source_doc: str = ""
    meeting_date_source_page: int | None = None
    meeting_date_source_quote: str = ""
    meeting_type: str | None = None
    meeting_type_source_doc: str = ""
    meeting_type_source_quote: str = ""
    capital_before: ExtractedCapital | None = None
    capital_after: ExtractedCapital | None = None
    particulars: str = ""
    particulars_source_doc: str = ""
    particulars_source_quote: str = ""
    flags: list[dict] = Field(default_factory=list)

class AuditResponse(BaseModel):
    corrections: list[dict] = Field(default_factory=list)
    additional_flags: list[dict] = Field(default_factory=list)
    is_valid: bool = True

def _group_by_event(docs):
    groups = defaultdict(list)
    for d in docs:
        groups[d.event_id].append(d)
    return dict(groups)

def _build_context(docs):
    parts = []
    for d in docs:
        parts.append(f'<doc id="{d.doc.id}" type="{d.doc_type.value}">\n{d.doc.total_text}\n</doc>')
    return "\n\n".join(parts)

def _make_cit(cid, doc_id, page, quote):
    return Citation(citation_id=cid, doc_id=doc_id, page=page, quote=quote)

_EXTRACT_SYS = "You are an expert in Indian corporate filings and share capital analysis."

_EXTRACT_PROMPT = """Analyse these Indian corporate documents for a single capital alteration event.

RULES:
1. Quote exact text from the documents, then extract the structured value.
2. If a value is genuinely unknown, return null and add a flag. Do NOT guess.
3. meeting_date = shareholder meeting date (AGM/EGM date), NOT board meeting or filing date. Format: YYYY-MM-DD.
4. meeting_type = "EGM" or "AGM" based on what type of meeting it was.
5. Amounts in whole rupees. Convert Indian notation: Rs. 1,00,000 = 100000, Rs. 3,00,000 = 300000, Rs. 50,00,000 = 5000000.
6. PAS-3 relates to issued/allotted capital — flag it and ignore for authorised capital extraction.
7. For sub-divisions, total rupees may not change but face value and share count will.

REQUIRED EXTRACTIONS:
- capital_before: The EXISTING/BEFORE authorised capital (from "Existing" field in SH-7, or the "from" amount in resolutions).
  - total_rupees: total amount in rupees (integer)
  - breakdown: list of share tranches, each with share_class ("equity" or "preference"), num_shares (integer), face_value (integer)
  - raw_text: exact quoted text describing this capital
  - source_doc_id: which document this came from
  - source_quote: exact quote from source
- capital_after: The REVISED/AFTER authorised capital (from "Revised" field in SH-7, or the "to" amount in resolutions).
  - Same structure as capital_before.
- particulars: A one-line description of what changed.

Documents:
{context}

Extract ALL the above fields. Do NOT leave capital_before or capital_after as null if the SH-7 contains Existing/Revised amounts."""

_AUDIT_PROMPT = """Review this extraction against source documents for errors.

Documents:
{context}

Extraction:
{extraction}

Check for: numerical errors, date inconsistencies, misattributed fields, missing info, hallucinations."""

def _extract_pass1(event_id, docs):
    from .llm import call_llm_structured
    ctx = _build_context(docs)
    result = call_llm_structured(_EXTRACT_PROMPT.format(context=ctx), ExtractionResponse, system=_EXTRACT_SYS)
    log.info("Pass1 result for %s: date=%s, type=%s, before=%s, after=%s",
             event_id, result.meeting_date, result.meeting_type,
             result.capital_before.total_rupees if result.capital_before else "NULL",
             result.capital_after.total_rupees if result.capital_after else "NULL")
    return result


def _audit_pass2(event_id, docs, extraction):
    from .llm import call_llm_structured
    ctx = _build_context(docs)
    ej = extraction.model_dump_json(indent=2)
    try:
        return call_llm_structured(_AUDIT_PROMPT.format(context=ctx, extraction=ej), AuditResponse, system="You are a meticulous auditor.")
    except Exception as e:
        log.warning("Audit failed for %s: %s", event_id, e)
        return AuditResponse()

def _norm_share_class(raw: str) -> str:
    """Normalize LLM share_class to 'equity' or 'preference'."""
    v = raw.lower().strip()
    if "prefer" in v:
        return "preference"
    return "equity"

def _parse_date(raw: str):
    """Parse dates from various formats the LLM might return."""
    from datetime import datetime
    raw = raw.strip().rstrip(".")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y", "%d %b %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None

def _to_alteration(event_id, ext, audit, ctr):
    sources, flags = [], []
    # meeting date
    md = None
    if ext.meeting_date:
        md = _parse_date(ext.meeting_date)
        if md is None:
            flags.append(Flag(field="meeting_date", event_id=event_id, reason=f"Could not parse date: {ext.meeting_date}", severity=FlagSeverity.WARNING))
    if ext.meeting_date_source_doc:
        cid = f"S{ctr[0]}"; ctr[0] += 1
        sources.append(_make_cit(cid, ext.meeting_date_source_doc, ext.meeting_date_source_page, ext.meeting_date_source_quote))
    # meeting type
    mt = None
    if ext.meeting_type:
        v = ext.meeting_type.upper().strip()
        if v in ("AGM","EGM"): mt = MeetingType(v)
    if ext.meeting_type_source_doc:
        cid = f"S{ctr[0]}"; ctr[0] += 1
        sources.append(_make_cit(cid, ext.meeting_type_source_doc, None, ext.meeting_type_source_quote))
    # capital before
    cb = None
    if ext.capital_before:
        c = ext.capital_before
        cb = CapitalAmount(total_rupees=c.total_rupees, breakdown=[ShareTranche(share_class=_norm_share_class(t.share_class), num_shares=t.num_shares, face_value=t.face_value) for t in c.breakdown], raw_text=c.raw_text)
        if c.source_doc_id:
            cid = f"S{ctr[0]}"; ctr[0] += 1
            sources.append(_make_cit(cid, c.source_doc_id, c.source_page, c.source_quote))
    # capital after
    ca = None
    if ext.capital_after:
        c = ext.capital_after
        ca = CapitalAmount(total_rupees=c.total_rupees, breakdown=[ShareTranche(share_class=_norm_share_class(t.share_class), num_shares=t.num_shares, face_value=t.face_value) for t in c.breakdown], raw_text=c.raw_text)
        if c.source_doc_id:
            cid = f"S{ctr[0]}"; ctr[0] += 1
            sources.append(_make_cit(cid, c.source_doc_id, c.source_page, c.source_quote))
    if ext.particulars_source_doc:
        cid = f"S{ctr[0]}"; ctr[0] += 1
        sources.append(_make_cit(cid, ext.particulars_source_doc, None, ext.particulars_source_quote))
    for f in ext.flags:
        reason = f.get("reason", "").strip()
        if reason:
            flags.append(Flag(field=f.get("field","unknown"), event_id=event_id, reason=reason, severity=FlagSeverity(f.get("severity","info"))))
    for f in audit.additional_flags:
        reason = f.get("reason", "").strip()
        if reason:
            flags.append(Flag(field=f.get("field","unknown"), event_id=event_id, reason=reason, severity=FlagSeverity(f.get("severity","warning"))))
    for corr in audit.corrections:
        reason = corr.get("reason", "").strip()
        if not reason:
            continue  # skip empty audit corrections
        orig = corr.get("original_value", "N/A")
        fixed = corr.get("corrected_value", "N/A")
        flags.append(Flag(field=corr.get("field",""), event_id=event_id, reason=f"Audit correction: {reason} (was: {orig}, corrected to: {fixed})", severity=FlagSeverity.WARNING))
        if corr.get("field") == "meeting_date" and corr.get("corrected_value"):
            try: md = date.fromisoformat(corr["corrected_value"])
            except: pass
    return CapitalAlteration(event_id=event_id, meeting_date=md, meeting_type=mt, capital_before=cb, capital_after=ca, particulars=ext.particulars, sources=sources, flags=flags)

def extract_events(classified_docs):
    groups = _group_by_event(classified_docs)
    alts = []
    ctr = [1]
    for eid in sorted(groups):
        edocs = groups[eid]
        relevant = [d for d in edocs if d.doc_type != DocumentType.PAS3]
        pas3 = [d for d in edocs if d.doc_type == DocumentType.PAS3]
        if not relevant:
            continue
        log.info("Extracting %s from %d docs", eid, len(relevant))
        ext = _extract_pass1(eid, relevant)
        aud = _audit_pass2(eid, relevant, ext)
        alt = _to_alteration(eid, ext, aud, ctr)
        if pas3:
            alt.flags.append(Flag(field="attachments", event_id=eid, reason=f"PAS-3 excluded: {', '.join(d.doc.id for d in pas3)}", severity=FlagSeverity.INFO))
        alts.append(alt)
    alts.sort(key=lambda a: a.meeting_date or date.min)
    log.info("Extracted %d events", len(alts))
    return alts
