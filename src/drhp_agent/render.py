"""Stage 5 — Render.

Produces three output artifacts:
1. capital_structure.md — the table with footnote-style citations and ⚠ markers
2. audit.json — full structured output for analyst review
3. flags.md — human-readable list of open questions
"""
from __future__ import annotations
import json, logging
from .schemas import CapitalAlteration, Flag, FlagSeverity, Citation, PipelineResult

log = logging.getLogger(__name__)


def _fmt_rupees(amount: int) -> str:
    """Format rupees in Indian notation (e.g., 55,00,000)."""
    s = str(amount)
    if len(s) <= 3:
        return s
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while rest:
        parts.append(rest[-2:] if len(rest) >= 2 else rest)
        rest = rest[:-2]
    parts.reverse()
    return ",".join(parts) + "," + last3


def _fmt_capital(cap) -> str:
    """Format a CapitalAmount as human-readable text."""
    if cap is None:
        return "—"
    if cap.raw_text:
        return cap.raw_text
    parts = []
    for t in cap.breakdown:
        parts.append(f"{t.num_shares:,} {t.share_class.title()} Shares of ₹{t.face_value} each")
    return " and ".join(parts) + f" aggregating to ₹{_fmt_rupees(cap.total_rupees)}"


def _severity_icon(sev: FlagSeverity) -> str:
    return {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(sev.value, "❓")


def render_table_md(events: list[CapitalAlteration], sources: dict[str, Citation]) -> str:
    """Render the capital structure table as Markdown."""
    lines = [
        "# Authorised Share Capital History",
        "",
        "| # | Date of Shareholder's Meeting | From | Particulars of Change | To | AGM/EGM | Sources |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, ev in enumerate(events, 1):
        dt = str(ev.meeting_date) if ev.meeting_date else "Incorporation"
        frm = _fmt_capital(ev.capital_before)
        to = _fmt_capital(ev.capital_after)
        part = ev.particulars or "—"
        mt = ev.meeting_type.value if ev.meeting_type else "—"
        src_refs = ", ".join(f"[{s.citation_id}]" for s in ev.sources) if ev.sources else "—"

        # Add flag markers
        if any(f.severity in (FlagSeverity.WARNING, FlagSeverity.ERROR) for f in ev.flags):
            dt += " ⚠"

        lines.append(f"| {i} | {dt} | {frm} | {part} | {to} | {mt} | {src_refs} |")

    # Sources section
    lines.extend(["", "## Sources", ""])
    all_citations = []
    for ev in events:
        all_citations.extend(ev.sources)
    seen = set()
    for c in all_citations:
        if c.citation_id in seen:
            continue
        seen.add(c.citation_id)
        pg = f", p.{c.page}" if c.page else ""
        qt = f' — "{c.quote[:80]}..."' if len(c.quote) > 80 else (f' — "{c.quote}"' if c.quote else "")
        lines.append(f"- **[{c.citation_id}]** `{c.doc_id}`{pg}{qt}")

    return "\n".join(lines)


def render_flags_md(events: list[CapitalAlteration]) -> str:
    """Render flags as a human-readable Markdown document."""
    lines = ["# Open Questions & Flags", ""]
    total = sum(len(e.flags) for e in events)
    lines.append(f"Total flags: **{total}**\n")

    for sev_val in ("error", "warning", "info"):
        sev_flags = [(e, f) for e in events for f in e.flags if f.severity.value == sev_val]
        if not sev_flags:
            continue
        icon = _severity_icon(FlagSeverity(sev_val))
        lines.append(f"## {icon} {sev_val.upper()} ({len(sev_flags)})\n")
        for ev, f in sev_flags:
            lines.append(f"- **Event:** `{f.event_id}` | **Field:** `{f.field}`")
            lines.append(f"  {f.reason}")
            if f.sources:
                lines.append(f"  Sources: {', '.join(s.citation_id for s in f.sources)}")
            lines.append("")

    return "\n".join(lines)


def render_audit_json(events: list[CapitalAlteration], company: str = "") -> str:
    """Render full structured output as JSON."""
    result = PipelineResult(
        company_name=company,
        events=events,
        all_flags=[f for e in events for f in e.flags],
    )
    # Build sources registry
    for ev in events:
        for s in ev.sources:
            result.sources_registry[s.citation_id] = s

    return result.model_dump_json(indent=2)


def write_outputs(events: list[CapitalAlteration], output_dir: str, company: str = ""):
    """Write all output artifacts to the output directory."""
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sources = {}
    for ev in events:
        for s in ev.sources:
            sources[s.citation_id] = s

    # 1. Capital structure table
    table_md = render_table_md(events, sources)
    (out / "capital_structure.md").write_text(table_md, encoding="utf-8")
    log.info("Wrote %s", out / "capital_structure.md")

    # 2. Audit JSON
    audit = render_audit_json(events, company)
    (out / "audit.json").write_text(audit, encoding="utf-8")
    log.info("Wrote %s", out / "audit.json")

    # 3. Flags
    flags_md = render_flags_md(events)
    (out / "flags.md").write_text(flags_md, encoding="utf-8")
    log.info("Wrote %s", out / "flags.md")
