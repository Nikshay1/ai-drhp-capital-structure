"""Tests for Stage 2 — Document Classification."""
import pytest
from drhp_agent.schemas import DocumentType, ParsedDocument, PageContent
from drhp_agent.classify import _classify_by_rules, _infer_event_id


def _make_doc(doc_id: str, text: str) -> ParsedDocument:
    return ParsedDocument(
        id=doc_id,
        source_path=f"data/{doc_id}",
        pages=[PageContent(page_no=1, text=text)],
        total_text=text,
    )


class TestRulesClassification:
    def test_sh7_detected(self):
        doc_type, conf = _classify_by_rules("Form No. SH-7\nNotice to Registrar...")
        assert doc_type == DocumentType.SH7
        assert conf >= 0.85

    def test_pas3_detected(self):
        doc_type, conf = _classify_by_rules("Form PAS-3\nReturn of Allotment...")
        assert doc_type == DocumentType.PAS3
        assert conf >= 0.8

    def test_board_resolution_detected(self):
        doc_type, conf = _classify_by_rules("BOARD RESOLUTION\nCertified true copy...")
        assert doc_type == DocumentType.BOARD_RESOLUTION
        assert conf >= 0.85

    def test_egm_notice_detected(self):
        doc_type, conf = _classify_by_rules("NOTICE OF EXTRA-ORDINARY GENERAL MEETING...")
        assert doc_type == DocumentType.EGM_NOTICE
        assert conf >= 0.85

    def test_agm_notice_detected(self):
        doc_type, conf = _classify_by_rules("NOTICE OF ANNUAL GENERAL MEETING...")
        assert doc_type == DocumentType.AGM_NOTICE
        assert conf >= 0.85

    def test_moa_detected(self):
        doc_type, conf = _classify_by_rules("ALTERED MEMORANDUM OF ASSOCIATION\nof Acme...")
        assert doc_type == DocumentType.ALTERED_MOA
        assert conf >= 0.75

    def test_unknown_returns_none(self):
        doc_type, conf = _classify_by_rules("This is a random cover letter with no form headers.")
        assert doc_type is None or conf < 0.5


class TestEventIdInference:
    def test_standard_folder(self):
        assert _infer_event_id("sh7_01_2019_aug/sh7.pdf") == "evt_01_2019_aug"

    def test_preserves_folder_structure(self):
        assert _infer_event_id("sh7_02_2021_sep/board_resolution.pdf") == "evt_02_2021_sep"
