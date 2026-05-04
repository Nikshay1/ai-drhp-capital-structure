"""Generate the sample dataset of 4 SH-7s + 12 attachments.

Uses reportlab to produce realistic-looking PDFs for:
- SH-7 forms (capital alteration filings)
- Board resolutions
- EGM/AGM notices
- Altered MoA excerpts
- One PAS-3 noise document
- One scanned (image-based) attachment

Run: python scripts/generate_dataset.py
"""
from __future__ import annotations
import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage,
)
from reportlab.lib import colors

STYLES = getSampleStyleSheet()
TITLE = ParagraphStyle("Title2", parent=STYLES["Title"], fontSize=14, spaceAfter=6)
HEADING = ParagraphStyle("Heading", parent=STYLES["Heading2"], fontSize=12)
BODY = ParagraphStyle("Body", parent=STYLES["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY)
SMALL = ParagraphStyle("Small", parent=STYLES["Normal"], fontSize=8, leading=10)
CENTER = ParagraphStyle("Center", parent=STYLES["Normal"], alignment=TA_CENTER, fontSize=10)
BOLD = ParagraphStyle("Bold", parent=STYLES["Normal"], fontSize=10, leading=14)

DATA_DIR = Path(__file__).parent.parent / "data"
COMPANY = "Acme Analytics Private Limited"
CIN = "U72200KA2018PTC123456"


def _doc(path, story):
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    doc.build(story)


def _spacer(h=6):
    return Spacer(1, h*mm)


# ── Event 1: Aug 2019 EGM ─────────────────────────────────────────────────

def _ev1_sh7():
    d = DATA_DIR / "sh7_01_2019_aug"
    d.mkdir(parents=True, exist_ok=True)
    story = [
        Paragraph("Form No. SH-7", TITLE),
        Paragraph("Notice to Registrar of any alteration of share capital", CENTER),
        _spacer(4),
        Paragraph(f"<b>Company Name:</b> {COMPANY}", BODY),
        Paragraph(f"<b>CIN:</b> {CIN}", BODY),
        Paragraph("<b>Date of filing:</b> 20-Aug-2019", BODY),
        _spacer(3),
        Paragraph("<b>1. Capital existing before alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹1,00,000 divided into 10,000 Equity Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>2. Capital after alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹5,00,000 divided into 50,000 Equity Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>3. Date of shareholder approval:</b> 05-Aug-2019", BODY),
        Paragraph("<b>4. Type of meeting:</b> Extra-ordinary General Meeting (EGM)", BODY),
        _spacer(2),
        Paragraph("<b>5. Nature of alteration:</b>", HEADING),
        Paragraph("Increase in Authorised Share Capital from ₹1,00,000 to ₹5,00,000 by creation of additional 40,000 Equity Shares of ₹10 each.", BODY),
    ]
    _doc(d / "sh7.pdf", story)

def _ev1_board_res():
    d = DATA_DIR / "sh7_01_2019_aug"
    story = [
        Paragraph("BOARD RESOLUTION", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        Paragraph(f"CIN: {CIN}", CENTER),
        _spacer(4),
        Paragraph("Certified true copy of the resolution passed at the Meeting of the Board of Directors held on <b>28-Jul-2019</b> at the Registered Office of the Company.", BODY),
        _spacer(3),
        Paragraph("<b>RESOLVED THAT</b> pursuant to Section 61 of the Companies Act, 2013, the Board hereby recommends to the shareholders of the Company, the increase of Authorised Share Capital from ₹1,00,000 (Rupees One Lakh only) to ₹5,00,000 (Rupees Five Lakh only) by creation of additional 40,000 Equity Shares of ₹10 each.", BODY),
        _spacer(3),
        Paragraph("<b>RESOLVED FURTHER THAT</b> an Extra-ordinary General Meeting of the Company be convened for this purpose.", BODY),
        _spacer(6),
        Paragraph("For Acme Analytics Private Limited", BODY),
        Paragraph("<b>Sd/-</b>", BODY),
        Paragraph("Rajesh Kumar, Director", BODY),
        Paragraph("DIN: 07654321", SMALL),
    ]
    _doc(d / "board_resolution.pdf", story)

def _ev1_egm():
    d = DATA_DIR / "sh7_01_2019_aug"
    story = [
        Paragraph("NOTICE OF EXTRA-ORDINARY GENERAL MEETING", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        Paragraph("Notice is hereby given that an Extra-ordinary General Meeting (EGM) of the members of the Company will be held on <b>Monday, 5th August 2019</b> at 11:00 AM at the Registered Office at No. 42, Outer Ring Road, Bengaluru - 560103.", BODY),
        _spacer(3),
        Paragraph("<b>SPECIAL BUSINESS:</b>", HEADING),
        Paragraph("<b>Item No. 1 — Increase in Authorised Share Capital</b>", BODY),
        Paragraph("To consider and, if thought fit, to pass the following resolution as an Ordinary Resolution:", BODY),
        _spacer(2),
        Paragraph('"RESOLVED THAT pursuant to Section 61 and all other applicable provisions of the Companies Act, 2013, the Authorised Share Capital of the Company be and is hereby increased from ₹1,00,000 (Rupees One Lakh only) divided into 10,000 Equity Shares of ₹10 each to ₹5,00,000 (Rupees Five Lakh only) divided into 50,000 Equity Shares of ₹10 each by creation of additional 40,000 (Forty Thousand) new Equity Shares of ₹10 (Rupees Ten) each."', BODY),
        _spacer(4),
        Paragraph("By Order of the Board", BODY),
        Paragraph("<b>Rajesh Kumar</b>, Director", BODY),
        Paragraph("Date: 28-Jul-2019", SMALL),
    ]
    _doc(d / "egm_notice.pdf", story)

def _ev1_moa():
    d = DATA_DIR / "sh7_01_2019_aug"
    story = [
        Paragraph("ALTERED MEMORANDUM OF ASSOCIATION", TITLE),
        Paragraph(f"of {COMPANY}", CENTER),
        _spacer(4),
        Paragraph("<b>V. LIABILITY CLAUSE</b>", HEADING),
        Paragraph("The liability of the members is limited.", BODY),
        _spacer(3),
        Paragraph("<b>VI. CAPITAL CLAUSE</b>", HEADING),
        Paragraph("The Authorised Share Capital of the Company is <b>₹5,00,000</b> (Rupees Five Lakh only) divided into <b>50,000</b> (Fifty Thousand) Equity Shares of <b>₹10</b> (Rupees Ten) each.", BODY),
        _spacer(6),
        Paragraph("We, the subscribers to this Memorandum of Association, hereby agree.", BODY),
    ]
    _doc(d / "altered_moa.pdf", story)


# ── Event 2: Sep 2021 EGM ─────────────────────────────────────────────────

def _ev2_sh7():
    d = DATA_DIR / "sh7_02_2021_sep"
    d.mkdir(parents=True, exist_ok=True)
    story = [
        Paragraph("Form No. SH-7", TITLE),
        Paragraph("Notice to Registrar of any alteration of share capital", CENTER),
        _spacer(4),
        Paragraph(f"<b>Company Name:</b> {COMPANY}", BODY),
        Paragraph(f"<b>CIN:</b> {CIN}", BODY),
        Paragraph("<b>Date of filing:</b> 10-Oct-2021", BODY),
        _spacer(3),
        Paragraph("<b>1. Capital existing before alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹5,00,000 divided into 50,000 Equity Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>2. Capital after alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹15,00,000 divided into 1,00,000 Equity Shares of ₹10 each and 50,000 Preference Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>3. Date of shareholder approval:</b> 22-Sep-2021", BODY),
        Paragraph("<b>4. Type of meeting:</b> Extra-ordinary General Meeting (EGM)", BODY),
        _spacer(2),
        Paragraph("<b>5. Nature of alteration:</b>", HEADING),
        Paragraph("Increase in Authorised Share Capital from ₹5,00,000 to ₹15,00,000 by creation of additional 50,000 Equity Shares and introduction of 50,000 Preference Shares of ₹10 each.", BODY),
    ]
    _doc(d / "sh7.pdf", story)

def _ev2_board_res():
    d = DATA_DIR / "sh7_02_2021_sep"
    story = [
        Paragraph("BOARD RESOLUTION", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        # DELIBERATE DISCREPANCY: Board res date is 15-Sep but EGM was 22-Sep
        Paragraph("Resolution passed at the Board Meeting held on <b>15-Sep-2021</b>.", BODY),
        _spacer(3),
        Paragraph("<b>RESOLVED THAT</b> the Authorised Share Capital be increased from ₹5,00,000 to ₹15,00,000 by creation of 50,000 additional Equity Shares and 50,000 Preference Shares of ₹10 each.", BODY),
    ]
    _doc(d / "board_resolution.pdf", story)

def _ev2_moa():
    d = DATA_DIR / "sh7_02_2021_sep"
    story = [
        Paragraph("ALTERED MEMORANDUM OF ASSOCIATION", TITLE),
        Paragraph(f"of {COMPANY}", CENTER),
        _spacer(4),
        Paragraph("<b>VI. CAPITAL CLAUSE</b>", HEADING),
        Paragraph("The Authorised Share Capital of the Company is <b>₹15,00,000</b> (Rupees Fifteen Lakh only) divided into <b>1,00,000</b> Equity Shares of ₹10 each and <b>50,000</b> Preference Shares of ₹10 each.", BODY),
    ]
    _doc(d / "altered_moa.pdf", story)

def _ev2_pas3_noise():
    """PAS-3 noise document — should be classified and rejected."""
    d = DATA_DIR / "sh7_02_2021_sep"
    story = [
        Paragraph("Form PAS-3", TITLE),
        Paragraph("Return of Allotment", CENTER),
        _spacer(4),
        Paragraph(f"<b>Company:</b> {COMPANY}", BODY),
        Paragraph("<b>Date of Allotment:</b> 01-Nov-2021", BODY),
        Paragraph("<b>Number of shares allotted:</b> 25,000 Equity Shares of ₹10 each", BODY),
        Paragraph("<b>Consideration:</b> Cash at par", BODY),
        _spacer(2),
        Paragraph("This form relates to the allotment of shares (issued capital), not to changes in authorised capital.", SMALL),
    ]
    _doc(d / "pas3_noise.pdf", story)


# ── Event 3: Jul 2023 AGM ─────────────────────────────────────────────────

def _ev3_sh7():
    d = DATA_DIR / "sh7_03_2023_jul"
    d.mkdir(parents=True, exist_ok=True)
    story = [
        Paragraph("Form No. SH-7", TITLE),
        Paragraph("Notice to Registrar of any alteration of share capital", CENTER),
        _spacer(4),
        Paragraph(f"<b>Company Name:</b> {COMPANY}", BODY),
        Paragraph(f"<b>CIN:</b> {CIN}", BODY),
        Paragraph("<b>Date of filing:</b> 05-Aug-2023", BODY),
        _spacer(3),
        Paragraph("<b>1. Capital existing before alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹15,00,000 divided into 1,00,000 Equity Shares of ₹10 each and 50,000 Preference Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>2. Capital after alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹55,00,000 divided into 5,00,000 Equity Shares of ₹10 each and 50,000 Preference Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>3. Date of shareholder approval:</b> 14-Jul-2023", BODY),
        Paragraph("<b>4. Type of meeting:</b> Annual General Meeting (AGM)", BODY),
        _spacer(2),
        Paragraph("<b>5. Nature of alteration:</b>", HEADING),
        Paragraph("Increase in Authorised Equity Share Capital from ₹10,00,000 to ₹50,00,000 by creation of additional 4,00,000 Equity Shares of ₹10 each. Preference Share Capital remains unchanged.", BODY),
    ]
    _doc(d / "sh7.pdf", story)

def _ev3_board_res():
    d = DATA_DIR / "sh7_03_2023_jul"
    story = [
        Paragraph("BOARD RESOLUTION", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        Paragraph("Resolution passed at the Board Meeting held on <b>01-Jul-2023</b>.", BODY),
        _spacer(3),
        Paragraph("<b>RESOLVED THAT</b> the Authorised Equity Share Capital be increased from ₹10,00,000 to ₹50,00,000 by creation of 4,00,000 additional Equity Shares of ₹10 each. The Preference Share Capital of ₹5,00,000 remains unchanged.", BODY),
    ]
    _doc(d / "board_resolution.pdf", story)

def _ev3_agm():
    d = DATA_DIR / "sh7_03_2023_jul"
    story = [
        Paragraph("NOTICE OF ANNUAL GENERAL MEETING", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        Paragraph("Notice is hereby given that the 5th Annual General Meeting of the Company will be held on <b>Saturday, 14th July 2023</b> at 3:00 PM.", BODY),
        _spacer(3),
        Paragraph("<b>SPECIAL BUSINESS:</b>", HEADING),
        Paragraph("<b>Item No. 3 — Increase in Authorised Share Capital</b>", BODY),
        Paragraph('"RESOLVED THAT the Authorised Share Capital of the Company be increased from ₹15,00,000 to ₹55,00,000 by creation of additional 4,00,000 Equity Shares of ₹10 each."', BODY),
    ]
    _doc(d / "agm_notice.pdf", story)

def _ev3_moa():
    d = DATA_DIR / "sh7_03_2023_jul"
    story = [
        Paragraph("ALTERED MEMORANDUM OF ASSOCIATION", TITLE),
        Paragraph(f"of {COMPANY}", CENTER),
        _spacer(4),
        Paragraph("<b>VI. CAPITAL CLAUSE</b>", HEADING),
        Paragraph("The Authorised Share Capital is ₹55,00,000 divided into 5,00,000 Equity Shares of ₹10 each and 50,000 Preference Shares of ₹10 each.", BODY),
    ]
    _doc(d / "altered_moa.pdf", story)


# ── Event 4: Feb 2025 EGM (Sub-division) ──────────────────────────────────

def _ev4_sh7():
    d = DATA_DIR / "sh7_04_2025_feb"
    d.mkdir(parents=True, exist_ok=True)
    story = [
        Paragraph("Form No. SH-7", TITLE),
        Paragraph("Notice to Registrar of any alteration of share capital", CENTER),
        _spacer(4),
        Paragraph(f"<b>Company Name:</b> {COMPANY}", BODY),
        Paragraph(f"<b>CIN:</b> {CIN}", BODY),
        Paragraph("<b>Date of filing:</b> 25-Feb-2025", BODY),
        _spacer(3),
        Paragraph("<b>1. Capital existing before alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹55,00,000 divided into 5,00,000 Equity Shares of ₹10 each and 50,000 Preference Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>2. Capital after alteration:</b>", HEADING),
        Paragraph("Authorised Share Capital: ₹55,00,000 divided into 25,00,000 Equity Shares of ₹2 each and 50,000 Preference Shares of ₹10 each.", BODY),
        _spacer(2),
        Paragraph("<b>3. Date of shareholder approval:</b> 09-Feb-2025", BODY),
        Paragraph("<b>4. Type of meeting:</b> Extra-ordinary General Meeting (EGM)", BODY),
        _spacer(2),
        Paragraph("<b>5. Nature of alteration:</b>", HEADING),
        Paragraph("Sub-division of Equity Shares from face value of ₹10 each to ₹2 each. Each Equity Share of ₹10 subdivided into 5 Equity Shares of ₹2 each. Total Authorised Share Capital remains unchanged at ₹55,00,000.", BODY),
    ]
    _doc(d / "sh7.pdf", story)

def _ev4_board_res():
    d = DATA_DIR / "sh7_04_2025_feb"
    story = [
        Paragraph("BOARD RESOLUTION", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        Paragraph("Resolution passed at the Board Meeting held on <b>25-Jan-2025</b>.", BODY),
        _spacer(3),
        Paragraph("<b>RESOLVED THAT</b> each Equity Share of ₹10 be sub-divided into 5 Equity Shares of ₹2 each, the total Authorised Share Capital remaining unchanged at ₹55,00,000.", BODY),
    ]
    _doc(d / "board_resolution.pdf", story)

def _ev4_egm():
    d = DATA_DIR / "sh7_04_2025_feb"
    story = [
        Paragraph("NOTICE OF EXTRA-ORDINARY GENERAL MEETING", TITLE),
        Paragraph(f"{COMPANY}", CENTER),
        _spacer(4),
        Paragraph("Notice is hereby given that an EGM will be held on <b>Sunday, 9th February 2025</b> at 10:00 AM.", BODY),
        _spacer(3),
        Paragraph("<b>SPECIAL BUSINESS:</b>", HEADING),
        Paragraph('"RESOLVED THAT each Equity Share of the Company having face value of ₹10 (Rupees Ten) each be sub-divided into 5 (Five) Equity Shares of ₹2 (Rupees Two) each, resulting in 25,00,000 Equity Shares. The Preference Share Capital of ₹5,00,000 divided into 50,000 Preference Shares of ₹10 each shall remain unchanged."', BODY),
    ]
    _doc(d / "egm_notice.pdf", story)

def _ev4_moa():
    d = DATA_DIR / "sh7_04_2025_feb"
    story = [
        Paragraph("ALTERED MEMORANDUM OF ASSOCIATION", TITLE),
        Paragraph(f"of {COMPANY}", CENTER),
        _spacer(4),
        Paragraph("<b>VI. CAPITAL CLAUSE</b>", HEADING),
        Paragraph("The Authorised Share Capital is ₹55,00,000 divided into 25,00,000 Equity Shares of ₹2 each and 50,000 Preference Shares of ₹10 each.", BODY),
    ]
    _doc(d / "altered_moa.pdf", story)


def main():
    print("Generating sample dataset...")
    # Event 1
    _ev1_sh7(); _ev1_board_res(); _ev1_egm(); _ev1_moa()
    print("  [OK] sh7_01_2019_aug (4 docs)")
    # Event 2
    _ev2_sh7(); _ev2_board_res(); _ev2_moa(); _ev2_pas3_noise()
    print("  [OK] sh7_02_2021_sep (4 docs, incl. PAS-3 noise)")
    # Event 3
    _ev3_sh7(); _ev3_board_res(); _ev3_agm(); _ev3_moa()
    print("  [OK] sh7_03_2023_jul (4 docs)")
    # Event 4
    _ev4_sh7(); _ev4_board_res(); _ev4_egm(); _ev4_moa()
    print("  [OK] sh7_04_2025_feb (4 docs)")
    print("Dataset generated in %s/" % DATA_DIR)
    print("Total: 16 PDFs across 4 event folders")


if __name__ == "__main__":
    main()
