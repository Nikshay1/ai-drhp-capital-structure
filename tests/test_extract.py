"""Tests for ground truth and extraction validation."""
import json, pytest
from pathlib import Path

GT = Path(__file__).parent.parent / "data" / "ground_truth.json"

@pytest.fixture
def gt():
    with open(GT) as f:
        return json.load(f)

class TestGroundTruth:
    def test_loads(self, gt):
        assert gt["company_name"] == "Nexus Brightlearn Solutions Private Limited"
        assert len(gt["events"]) == 5

    def test_continuity(self, gt):
        evts = gt["events"]
        for i in range(1, len(evts)):
            prev = evts[i-1]["capital_after"]
            curr = evts[i]["capital_before"]
            if curr is not None:
                assert prev["total_rupees"] == curr["total_rupees"], f"Break at {i}"

    def test_arithmetic(self, gt):
        for ev in gt["events"]:
            for label in ("capital_before", "capital_after"):
                cap = ev.get(label)
                if not cap: continue
                calc = sum(t["num_shares"] * t["face_value"] for t in cap["breakdown"])
                assert calc == cap["total_rupees"], f"{ev['event_id']}.{label}"

    def test_subdivision(self, gt):
        sub = [e for e in gt["events"] if "2025" in e["event_id"]]
        assert len(sub) == 1
        assert sub[0]["capital_before"]["total_rupees"] == sub[0]["capital_after"]["total_rupees"]

    def test_expected_table(self, gt):
        tbl = gt["expected_table"]
        assert len(tbl) == 5
        assert tbl[0]["date"] == "On incorporation"
        assert tbl[0]["from"] == "-"
