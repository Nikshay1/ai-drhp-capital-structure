"""Stage 4 — Reconcile & Validate.

Runs post-extraction checks accumulating flags:
1. Within-event consistency (do SH-7, board res, MoA agree?)
2. Cross-event continuity (row N+1 "From" == row N "To")
3. Incorporation row synthesis (if missing)
4. Schema completeness (any None = flag)
5. Arithmetic validation (shares × FV == total)
"""
from __future__ import annotations
import logging
from datetime import date
from .schemas import (
    CapitalAlteration, CapitalAmount, Flag, FlagSeverity,
    MeetingType, ShareTranche,
)

log = logging.getLogger(__name__)


def _check_arithmetic(cap: CapitalAmount, event_id: str, label: str) -> list[Flag]:
    """Verify that sum(shares × face_value) == total_rupees."""
    flags = []
    if not cap.breakdown:
        return flags
    computed = sum(t.num_shares * t.face_value for t in cap.breakdown)
    if computed != cap.total_rupees:
        flags.append(Flag(
            field=f"capital_{label}",
            event_id=event_id,
            reason=(
                f"Arithmetic mismatch in {label} capital: "
                f"sum(shares×FV) = ₹{computed:,} but total_rupees = ₹{cap.total_rupees:,}"
            ),
            severity=FlagSeverity.ERROR,
        ))
    return flags


def _capitals_equal(a: CapitalAmount | None, b: CapitalAmount | None) -> bool:
    """Compare two CapitalAmounts structurally."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if a.total_rupees != b.total_rupees:
        return False
    # Compare breakdowns
    a_sorted = sorted(a.breakdown, key=lambda t: t.share_class)
    b_sorted = sorted(b.breakdown, key=lambda t: t.share_class)
    if len(a_sorted) != len(b_sorted):
        return False
    for ta, tb in zip(a_sorted, b_sorted):
        if ta.share_class != tb.share_class:
            return False
        if ta.num_shares != tb.num_shares or ta.face_value != tb.face_value:
            return False
    return True


def _check_continuity(events: list[CapitalAlteration]) -> list[Flag]:
    """Cross-event continuity: E[n+1].capital_before == E[n].capital_after."""
    flags = []
    for i in range(1, len(events)):
        prev = events[i - 1]
        curr = events[i]
        if not _capitals_equal(curr.capital_before, prev.capital_after):
            pa = prev.capital_after
            cb = curr.capital_before
            # Build helpful detail
            if pa and cb and pa.total_rupees == cb.total_rupees:
                reason = (
                    f"Continuity mismatch (breakdown differs): previous event ({prev.event_id}) "
                    f"capital_after and this event's capital_before both total ₹{pa.total_rupees:,} "
                    f"but share counts or face values differ. Verify extraction accuracy."
                )
            elif pa and cb:
                reason = (
                    f"Continuity break: previous event ({prev.event_id}) capital_after "
                    f"= ₹{pa.total_rupees:,} but this event's capital_before = ₹{cb.total_rupees:,}. "
                    f"Possible missing alteration between these events."
                )
            else:
                reason = (
                    f"Continuity break between {prev.event_id} and {curr.event_id}. "
                    f"One or both capital amounts are missing."
                )
            flags.append(Flag(
                field="capital_before",
                event_id=curr.event_id,
                reason=reason,
                severity=FlagSeverity.WARNING,
            ))
    return flags


def _check_completeness(event: CapitalAlteration) -> list[Flag]:
    """Flag any None fields in the event."""
    flags = []
    if event.meeting_date is None and not event.is_inferred:
        flags.append(Flag(field="meeting_date", event_id=event.event_id, reason="Meeting date is missing.", severity=FlagSeverity.WARNING))
    if event.meeting_type is None and not event.is_inferred:
        flags.append(Flag(field="meeting_type", event_id=event.event_id, reason="Meeting type (AGM/EGM) not determined.", severity=FlagSeverity.WARNING))
    if event.capital_after is None:
        flags.append(Flag(field="capital_after", event_id=event.event_id, reason="Capital after alteration is missing.", severity=FlagSeverity.ERROR))
    if not event.particulars:
        flags.append(Flag(field="particulars", event_id=event.event_id, reason="Particulars of change not extracted.", severity=FlagSeverity.WARNING))
    return flags


def _detect_subdivision(event: CapitalAlteration) -> list[Flag]:
    """Detect face-value sub-division events."""
    flags = []
    if event.capital_before and event.capital_after:
        if event.capital_before.total_rupees == event.capital_after.total_rupees:
            # Check if share counts changed (subdivision)
            before_eq = [t for t in event.capital_before.breakdown if t.share_class == "equity"]
            after_eq = [t for t in event.capital_after.breakdown if t.share_class == "equity"]
            if before_eq and after_eq:
                if before_eq[0].face_value != after_eq[0].face_value:
                    ratio = before_eq[0].face_value / after_eq[0].face_value
                    flags.append(Flag(
                        field="capital_after",
                        event_id=event.event_id,
                        reason=(
                            f"Sub-division detected: FV ₹{before_eq[0].face_value} → "
                            f"₹{after_eq[0].face_value} (ratio {ratio:.0f}:1). "
                            f"Total authorised capital unchanged at ₹{event.capital_after.total_rupees:,}."
                        ),
                        severity=FlagSeverity.INFO,
                    ))
    return flags


def _ensure_incorporation_row(events: list[CapitalAlteration]) -> list[CapitalAlteration]:
    """If the first event has capital_before, synthesise an incorporation row."""
    if not events:
        return events
    first = events[0]
    if first.capital_before is not None:
        # We have a "From" on the first event — need an incorporation row
        inc = CapitalAlteration(
            event_id="evt_incorporation",
            meeting_date=None,
            meeting_type=None,
            capital_before=None,
            capital_after=first.capital_before,
            particulars="Initial Authorised Share Capital at the time of incorporation of the Company.",
            is_inferred=True,
            flags=[Flag(
                field="event",
                event_id="evt_incorporation",
                reason="Incorporation row inferred — no incorporation document provided. Capital derived from first alteration's 'before' amount.",
                severity=FlagSeverity.INFO,
            )],
        )
        return [inc] + events
    return events


def reconcile(events: list[CapitalAlteration]) -> list[CapitalAlteration]:
    """Run all reconciliation checks and return events with accumulated flags."""
    # Ensure chronological order
    events.sort(key=lambda e: e.meeting_date or date.min)

    # Ensure incorporation row
    events = _ensure_incorporation_row(events)

    all_new_flags: list[Flag] = []

    # Per-event checks
    for event in events:
        # Arithmetic
        if event.capital_before:
            event.flags.extend(_check_arithmetic(event.capital_before, event.event_id, "before"))
        if event.capital_after:
            event.flags.extend(_check_arithmetic(event.capital_after, event.event_id, "after"))
        # Completeness
        event.flags.extend(_check_completeness(event))
        # Subdivision detection
        event.flags.extend(_detect_subdivision(event))

    # Cross-event continuity
    continuity_flags = _check_continuity(events)
    all_new_flags.extend(continuity_flags)

    # Attach continuity flags to relevant events
    for f in continuity_flags:
        for e in events:
            if e.event_id == f.event_id:
                e.flags.append(f)
                break

    # Deduplicate flags per event
    for event in events:
        seen = set()
        unique = []
        for f in event.flags:
            key = (f.field, f.event_id, f.reason)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        event.flags = unique

    log.info("Reconciliation complete. Total flags: %d", sum(len(e.flags) for e in events))
    return events
