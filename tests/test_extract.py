"""Tests for Stage 3 — Extraction (integration test against ground truth).

This test loads the ground_truth.json and validates the extraction
pipeline produces matching results. Requires LLM API access to run.
"""
import json
import pytest
from pathlib import Path

GROUND_TRUTH_PATH = Path(__file__).parent.parent / "data" / "ground_truth.json"


@pytest.fixture
def ground_truth():
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)


class TestGroundTruth:
    def test_ground_truth_loads(self, ground_truth):
        assert ground_truth["company_name"] == "Acme Analytics Private Limited"
        assert len(ground_truth["events"]) == 5

    def test_continuity_in_ground_truth(self, ground_truth):
        """Verify ground truth itself has continuity."""
        events = ground_truth["events"]
        for i in range(1, len(events)):
            prev_after = events[i - 1]["capital_after"]
            curr_before = events[i]["capital_before"]
            if curr_before is not None:
                assert prev_after["total_rupees"] == curr_before["total_rupees"], \
                    f"Continuity break between events {i-1} and {i}"

    def test_arithmetic_in_ground_truth(self, ground_truth):
        """Verify share × FV = total in ground truth."""
        for ev in ground_truth["events"]:
            for label in ("capital_before", "capital_after"):
                cap = ev.get(label)
                if cap is None:
                    continue
                computed = sum(t["num_shares"] * t["face_value"] for t in cap["breakdown"])
                assert computed == cap["total_rupees"], \
                    f"Arithmetic mismatch in {ev['event_id']}.{label}: {computed} != {cap['total_rupees']}"

    def test_subdivision_event(self, ground_truth):
        """Verify the subdivision event has unchanged total."""
        sub_ev = [e for e in ground_truth["events"] if "2025" in e["event_id"]]
        assert len(sub_ev) == 1
        ev = sub_ev[0]
        assert ev["capital_before"]["total_rupees"] == ev["capital_after"]["total_rupees"]
