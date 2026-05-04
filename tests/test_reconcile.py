"""Tests for Stage 4 — Reconcile & Validate."""
import pytest
from datetime import date
from drhp_agent.schemas import (
    CapitalAlteration, CapitalAmount, ShareTranche, Flag, FlagSeverity,
)
from drhp_agent.reconcile import (
    reconcile, _check_arithmetic, _capitals_equal, _detect_subdivision,
)


def _cap(total, shares):
    """Helper to build CapitalAmount."""
    return CapitalAmount(
        total_rupees=total,
        breakdown=[ShareTranche(share_class=s[0], num_shares=s[1], face_value=s[2]) for s in shares],
        raw_text="",
    )


def _evt(eid, dt, mt, before, after, particulars="test"):
    return CapitalAlteration(
        event_id=eid, meeting_date=dt, meeting_type=mt,
        capital_before=before, capital_after=after, particulars=particulars,
    )


class TestArithmetic:
    def test_correct_arithmetic(self):
        cap = _cap(500000, [("equity", 50000, 10)])
        flags = _check_arithmetic(cap, "e1", "after")
        assert len(flags) == 0

    def test_incorrect_arithmetic(self):
        cap = _cap(600000, [("equity", 50000, 10)])  # 50000*10 = 500000 ≠ 600000
        flags = _check_arithmetic(cap, "e1", "after")
        assert len(flags) == 1
        assert flags[0].severity == FlagSeverity.ERROR

    def test_mixed_capital(self):
        cap = _cap(1500000, [("equity", 100000, 10), ("preference", 50000, 10)])
        flags = _check_arithmetic(cap, "e2", "after")
        assert len(flags) == 0


class TestCapitalsEqual:
    def test_equal(self):
        a = _cap(500000, [("equity", 50000, 10)])
        b = _cap(500000, [("equity", 50000, 10)])
        assert _capitals_equal(a, b)

    def test_different_total(self):
        a = _cap(500000, [("equity", 50000, 10)])
        b = _cap(600000, [("equity", 60000, 10)])
        assert not _capitals_equal(a, b)

    def test_none_handling(self):
        assert _capitals_equal(None, None)
        assert not _capitals_equal(_cap(100, []), None)


class TestContinuity:
    def test_continuous_events(self):
        events = [
            _evt("e1", date(2019, 8, 5), None,
                 None, _cap(500000, [("equity", 50000, 10)])),
            _evt("e2", date(2021, 9, 22), None,
                 _cap(500000, [("equity", 50000, 10)]),
                 _cap(1500000, [("equity", 100000, 10), ("preference", 50000, 10)])),
        ]
        result = reconcile(events)
        continuity_flags = [f for e in result for f in e.flags if "Continuity" in f.reason]
        assert len(continuity_flags) == 0

    def test_broken_continuity(self):
        events = [
            _evt("e1", date(2019, 8, 5), None,
                 None, _cap(500000, [("equity", 50000, 10)])),
            _evt("e2", date(2021, 9, 22), None,
                 _cap(700000, [("equity", 70000, 10)]),  # mismatch!
                 _cap(1500000, [("equity", 100000, 10), ("preference", 50000, 10)])),
        ]
        result = reconcile(events)
        continuity_flags = [f for e in result for f in e.flags if "Continuity" in f.reason]
        assert len(continuity_flags) >= 1


class TestSubdivision:
    def test_detects_subdivision(self):
        ev = _evt("e4", date(2025, 2, 9), None,
                  _cap(5500000, [("equity", 500000, 10), ("preference", 50000, 10)]),
                  _cap(5500000, [("equity", 2500000, 2), ("preference", 50000, 10)]))
        flags = _detect_subdivision(ev)
        assert len(flags) == 1
        assert "Sub-division" in flags[0].reason


class TestIncorporationRow:
    def test_synthesises_incorporation(self):
        events = [
            _evt("e1", date(2019, 8, 5), None,
                 _cap(100000, [("equity", 10000, 10)]),
                 _cap(500000, [("equity", 50000, 10)])),
        ]
        result = reconcile(events)
        assert len(result) == 2
        assert result[0].event_id == "evt_incorporation"
        assert result[0].is_inferred
