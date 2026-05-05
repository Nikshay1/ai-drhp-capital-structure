"""Stage 5 -- Render.

Outputs:
1. capital_structure.md -- the Authorised Share Capital change table matching DRHP format
2. audit.json -- full structured output
3. flags.md -- human-readable flags
"""
from __future__ import annotations
import json, logging
from .schemas import CapitalAlteration, Flag, FlagSeverity, Citation, PipelineResult

log = logging.getLogger(__name__)


def _fmt_rupees(amount: int) -> str:
    """Indian comma notation: 55,00,000."""
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


def _fmt_capital_drhp(cap) -> str:
    """Format capital in DRHP style: 'Rs. X,XX,XXX divided into N Equity Shares of Rs. Y each'."""
    if cap is None:
        return "-"
    if cap.raw_text and "divided into" in cap.raw_text:
        return cap.raw_text
    parts = []
    for t in cap.breakdown:
        name = "Equity Shares" if t.share_class == "equity" else "Preference Shares"
        parts.append(f"{_fmt_rupees(t.num_shares)} {name} of Rs. {t.face_value} each")
    return f"Rs. {_fmt_rupees(cap.total_rupees)} divided into " + " and ".join(parts)


def _fmt_date_drhp(ev) -> str:
    """Format date like 'November 17, 2016' or 'On incorporation'."""
    if ev.meeting_date is None:
        return "On incorporation"
    return ev.meeting_date.strftime("%B %d, %Y")


def _sev_icon(sev: FlagSeverity) -> str:
    return {"info": "[i]", "warning": "[!]", "error": "[X]"}.get(sev.value, "?")


def render_table_md(events: list[CapitalAlteration], sources: dict[str, Citation]) -> str:
    """Render the DRHP-style Authorised Share Capital change table."""
    lines = [
        "# Draft Authorised Share Capital Change",
        "",
        "| Date of Shareholder's Meeting | Particulars of Change | | AGM/EGM | Sources |",
        "|---|---|---|---|---|",
        "| | **From** | **To** | | |",
    ]
    for ev in events:
        dt = _fmt_date_drhp(ev)
        frm = _fmt_capital_drhp(ev.capital_before)
        to = _fmt_capital_drhp(ev.capital_after)
        mt = ev.meeting_type.value if ev.meeting_type else "-"
        srefs = ", ".join(f"[{s.citation_id}]" for s in ev.sources) if ev.sources else "-"

        flag_marker = ""
        if any(f.severity in (FlagSeverity.WARNING, FlagSeverity.ERROR) for f in ev.flags):
            flag_marker = " [!]"

        lines.append(f"| {dt}{flag_marker} | {frm} | {to} | {mt} | {srefs} |")

    # Sources
    lines.extend(["", "## Sources", ""])
    seen = set()
    for ev in events:
        for c in ev.sources:
            if c.citation_id in seen:
                continue
            seen.add(c.citation_id)
            pg = f", p.{c.page}" if c.page else ""
            qt = f' -- "{c.quote[:100]}..."' if len(c.quote) > 100 else (f' -- "{c.quote}"' if c.quote else "")
            lines.append(f"- **[{c.citation_id}]** `{c.doc_id}`{pg}{qt}")

    return "\n".join(lines)


def render_flags_md(events: list[CapitalAlteration]) -> str:
    lines = ["# Open Questions & Flags", ""]
    total = sum(len(e.flags) for e in events)
    lines.append(f"Total flags: **{total}**\n")

    for sev_val in ("error", "warning", "info"):
        sev_flags = [(e, f) for e in events for f in e.flags if f.severity.value == sev_val]
        if not sev_flags:
            continue
        icon = _sev_icon(FlagSeverity(sev_val))
        lines.append(f"## {icon} {sev_val.upper()} ({len(sev_flags)})\n")
        for ev, f in sev_flags:
            lines.append(f"- **Event:** `{f.event_id}` | **Field:** `{f.field}`")
            lines.append(f"  {f.reason}")
            lines.append("")

    return "\n".join(lines)


def render_audit_json(events: list[CapitalAlteration], company: str = "") -> str:
    result = PipelineResult(
        company_name=company, events=events,
        all_flags=[f for e in events for f in e.flags],
    )
    for ev in events:
        for s in ev.sources:
            result.sources_registry[s.citation_id] = s
    return result.model_dump_json(indent=2)


def write_outputs(events: list[CapitalAlteration], output_dir: str, company: str = ""):
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sources = {}
    for ev in events:
        for s in ev.sources:
            sources[s.citation_id] = s

    (out / "capital_structure.md").write_text(render_table_md(events, sources), encoding="utf-8")
    (out / "audit.json").write_text(render_audit_json(events, company), encoding="utf-8")
    (out / "flags.md").write_text(render_flags_md(events), encoding="utf-8")
    log.info("Outputs written to %s/", out)
