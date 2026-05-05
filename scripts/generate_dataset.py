"""Generate sample dataset: 4 SH-7 folders with 3 attachments each as markdown files.
Mirrors the real SH-7/PAS-3 document structure from the sample inputs.
"""
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
CO = "NEXUS BRIGHTLEARN SOLUTIONS PRIVATE LIMITED"
CIN = "U85123DL2018PTC312456"
ADDR = "KRISHNA TOWER PLOT NO-45 SECTOR-12 DWARKA NEW DELHI DL 110075"

def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ── Event 1: Mar 2019 EGM ──
def ev1():
    d = DATA / "sh7_01_2019_mar"
    _write(d / "SH7.md", f"""# FORM NO. SH-7
**Notice to Registrar of any alteration of share capital**
[Pursuant to section 64(1) of the Companies Act, 2013]

1.(a) Corporate identity number (CIN): {CIN}
2.(a) Name of the company: {CO}
(b) Address: {ADDR}

3. Purpose: Increase in share capital independently by company

4. By Ordinary resolution at the meeting of the members held on 22/03/2019 (DD/MM/YYYY)

(a)(i) The authorised share capital has been increased from
| | (in Rs.) |
|---|---|
| Existing | 1,00,000.00 |
| Revised | 3,00,000.00 |
| Difference (addition) | 2,00,000.00 |

6. Additional capital divided as follows:
(a) Number of equity shares: 20,000 | Total amount of equity shares (in Rs.): 2,00,000.00
(b) Number of preference shares: 0

9. Revised capital structure:
(a) Authorised capital (in Rs.) 3,00,000.00
| Particulars | Count | Amount (Rs.) |
|---|---|---|
| Number of equity shares | 30,000 | 3,00,000.00 |
| Nominal amount per equity share | 10 | |
| Number of preference shares | 0 | 0.00 |

Attachments: CTC_EGM.pdf, MOA_New.pdf, Notice_of_EGM.pdf, CTC_Board_Meeting.pdf
eForm filing date: 22/03/2019
""")
    _write(d / "Board_Meeting.md", f"""# {CO}
## CERTIFIED TRUE COPY OF RESOLUTION PASSED IN THE MEETING OF THE BOARD OF DIRECTORS
Held on 22nd DAY OF MARCH 2019 at 1:00 PM

## INCREASE IN AUTHORISED SHARE CAPITAL & ALTERATION IN THE CAPITAL CLAUSE OF MOA

1. "RESOLVED THAT pursuant to Sections 61 and 64 of the Companies Act, 2013, the consent of the Board is hereby accorded, subject to shareholder approval, to increase the Authorized Share Capital from Rs. 1,00,000 (Rupees One Lakh) divided into 10,000 Equity Shares of Rs. 10 each to Rs. 3,00,000 (Rupees Three Lakh) divided into 30,000 Equity Shares of Rs. 10 each.

2. RESOLVED FURTHER THAT Clause V of the Memorandum of Association be substituted with:
V. The Authorised Share Capital of the Company is Rs. 3,00,000/- (Rupees Three Lakh) divided into 30,000 (Thirty thousand) Equity Shares of Rs. 10/- each."

BY ORDER OF THE BOARD
Date: 22/03/2019
Place: New Delhi
ARUN VIKRAM SETHI (DIRECTOR) DIN: 08745632
""")
    _write(d / "EGM_Notice.md", f"""# {CO}
NOTICE IS HEREBY GIVEN THAT THE EXTRA ORDINARY GENERAL MEETING OF THE MEMBERS OF {CO} WILL BE HELD ON 22nd DAY OF MARCH 2019 AT 1:00 P.M. AT {ADDR}

## SPECIAL BUSINESS:
### ITEM NO. 1
RESOLVED THAT the Authorized Share Capital be increased from Rs. 1,00,000/- (Rupees One Lakh) divided into 10,000 Equity Shares of Rs. 10/- each to Rs. 3,00,000/- (Rupees Three Lakh) divided into 30,000 Equity Shares of Rs. 10/- each.

### ITEM NO. 2
RESOLVED THAT Clause V of the Memorandum of Association be substituted with:
V. The Authorised Share Capital of the Company is Rs. 3,00,000/- (Rupees Three Lakh) divided into 30,000 (Thirty thousand) Equity Shares of Rs. 10/- each.

Date: 10/03/2019
BY ORDER OF THE BOARD
ARUN VIKRAM SETHI (DIRECTOR) DIN: 08745632
""")
    _write(d / "Altered_MOA.md", f"""THE COMPANIES ACT, 2013
MEMORANDUM OF ASSOCIATION OF {CO}

I. The Name of the Company is {CO}.
II. Registered Office situated in Delhi.
IV. The Liability of the members is Limited.
V. The Authorised Share Capital of the Company is Rs. 3,00,000/- (Rupees Three Lakh) divided into 30,000 (Thirty thousand) Equity Shares of Rs. 10/- (Rupees Ten) each.
""")

# ── Event 2: Aug 2021 EGM (with PAS-3 noise + date discrepancy) ──
def ev2():
    d = DATA / "sh7_02_2021_aug"
    _write(d / "SH7.md", f"""# FORM NO. SH-7
**Notice to Registrar of any alteration of share capital**

1.(a) CIN: {CIN}
2.(a) Name: {CO}
(b) Address: {ADDR}

3. Purpose: Increase in share capital independently by company

4. By Ordinary resolution at the meeting held on 15/08/2021 (DD/MM/YYYY)

(a)(i) Authorised share capital increased from:
| | (in Rs.) |
|---|---|
| Existing | 3,00,000.00 |
| Revised | 10,00,000.00 |
| Difference (addition) | 7,00,000.00 |

6. Additional capital:
(a) Number of equity shares: 20,000 | Total equity (in Rs.): 2,00,000.00
(b) Number of preference shares: 50,000 | Total preference (in Rs.): 5,00,000.00

9. Revised capital structure:
(a) Authorised capital (in Rs.) 10,00,000.00
| Particulars | Count | Amount (Rs.) |
|---|---|---|
| Equity shares | 50,000 | 5,00,000.00 |
| Nominal per equity share | 10 | |
| Preference shares | 50,000 | 5,00,000.00 |
| Nominal per preference share | 10 | |

eForm filing date: 01/09/2021
""")
    # Board resolution has date 05-Aug (10 days BEFORE EGM on 15-Aug) — deliberate discrepancy to test flagging
    _write(d / "Board_Meeting.md", f"""# {CO}
## CERTIFIED TRUE COPY OF RESOLUTION - BOARD OF DIRECTORS
Held on 05th DAY OF AUGUST 2021 at 11:00 AM

1. "RESOLVED THAT the Authorized Share Capital be increased from Rs. 3,00,000 divided into 30,000 Equity Shares of Rs. 10 each to Rs. 10,00,000 divided into 50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each.

2. RESOLVED FURTHER THAT an Extra-ordinary General Meeting be convened."

Date: 05/08/2021
ARUN VIKRAM SETHI (DIRECTOR)
""")
    _write(d / "Altered_MOA.md", f"""MEMORANDUM OF ASSOCIATION OF {CO}
V. The Authorised Share Capital of the Company is Rs. 10,00,000/- (Rupees Ten Lakh) divided into 50,000 (Fifty thousand) Equity Shares of Rs. 10/- each and 50,000 (Fifty thousand) Preference Shares of Rs. 10/- each.
""")
    # PAS-3 noise — should be classified and excluded
    _write(d / "PAS3_Return_of_Allotment.md", f"""# FORM NO. PAS-3 Return of Allotment
[Pursuant to section 39(4) of the Companies Act, 2013]

1.(a) CIN: {CIN}
2.(a) Name: {CO}

3. Securities allotted payable in cash
Date of allotment: 20/09/2021
Equity shares without Differential rights
Number of securities allotted: 5,000
Nominal amount per security (in Rs.): 10
Total nominal amount (in Rs.): 50,000

7. Capital structure after allotment:
| Particulars | Authorized | Issued | Subscribed | Paid up |
|---|---|---|---|---|
| Equity shares | 50,000 | 35,000 | 35,000 | 35,000 |
| Nominal per equity | 10 | 10 | 10 | 10 |
| Preference shares | 50,000 | 0 | 0 | 0 |
""")

# ── Event 3: Jul 2023 AGM ──
def ev3():
    d = DATA / "sh7_03_2023_jul"
    _write(d / "SH7.md", f"""# FORM NO. SH-7
**Notice to Registrar of any alteration of share capital**

1.(a) CIN: {CIN}
2.(a) Name: {CO}

3. Purpose: Increase in share capital independently by company

4. By Ordinary resolution at the Annual General Meeting held on 28/07/2023

(a)(i) Authorised share capital increased from:
| | (in Rs.) |
|---|---|
| Existing | 10,00,000.00 |
| Revised | 50,00,000.00 |
| Difference (addition) | 40,00,000.00 |

6. Additional capital:
(a) Number of equity shares: 4,00,000 | Total equity (in Rs.): 40,00,000.00
(b) Number of preference shares: 0

9. Revised capital structure:
(a) Authorised capital (in Rs.) 50,00,000.00
| Particulars | Count | Amount (Rs.) |
|---|---|---|
| Equity shares | 4,50,000 | 45,00,000.00 |
| Nominal per equity share | 10 | |
| Preference shares | 50,000 | 5,00,000.00 |
| Nominal per preference share | 10 | |

eForm filing date: 20/08/2023
""")
    _write(d / "Board_Meeting.md", f"""# {CO}
## CERTIFIED TRUE COPY OF RESOLUTION - BOARD OF DIRECTORS
Held on 10th DAY OF JULY 2023

1. "RESOLVED THAT the Authorised Equity Share Capital be increased from Rs. 5,00,000 to Rs. 45,00,000 by creation of 4,00,000 additional Equity Shares of Rs. 10 each. Preference Share Capital of Rs. 5,00,000 remains unchanged."

Date: 10/07/2023
ARUN VIKRAM SETHI (DIRECTOR)
""")
    _write(d / "AGM_Notice.md", f"""# {CO}
NOTICE IS HEREBY GIVEN THAT THE 5th ANNUAL GENERAL MEETING of the members will be held on 28th DAY OF JULY 2023 at 3:00 PM at {ADDR}

## SPECIAL BUSINESS:
### ITEM NO. 3 - Increase in Authorised Share Capital
RESOLVED THAT the Authorised Share Capital be increased from Rs. 10,00,000 to Rs. 50,00,000 by creation of additional 4,00,000 Equity Shares of Rs. 10 each.

Date: 15/07/2023
BY ORDER OF THE BOARD
ARUN VIKRAM SETHI (DIRECTOR)
""")
    _write(d / "Altered_MOA.md", f"""MEMORANDUM OF ASSOCIATION OF {CO}
V. The Authorised Share Capital of the Company is Rs. 50,00,000/- (Rupees Fifty Lakh) divided into 4,50,000 (Four Lakh Fifty Thousand) Equity Shares of Rs. 10/- each and 50,000 (Fifty Thousand) Preference Shares of Rs. 10/- each.
""")

# ── Event 4: Jan 2025 EGM (Sub-division) ──
def ev4():
    d = DATA / "sh7_04_2025_jan"
    _write(d / "SH7.md", f"""# FORM NO. SH-7
**Notice to Registrar of any alteration of share capital**

1.(a) CIN: {CIN}
2.(a) Name: {CO}

3. Purpose: Consolidation or division etc.

4. By Ordinary resolution at the EGM held on 18/01/2025

(a)(i) Authorised share capital:
| | (in Rs.) |
|---|---|
| Existing | 50,00,000.00 |
| Revised | 50,00,000.00 |
| Difference | 0.00 |

Note: Sub-division of equity shares. Face value changed from Rs. 10 to Rs. 2.

9. Revised capital structure:
(a) Authorised capital (in Rs.) 50,00,000.00
| Particulars | Count | Amount (Rs.) |
|---|---|---|
| Equity shares | 22,50,000 | 45,00,000.00 |
| Nominal per equity share | 2 | |
| Preference shares | 50,000 | 5,00,000.00 |
| Nominal per preference share | 10 | |

eForm filing date: 10/02/2025
""")
    _write(d / "Board_Meeting.md", f"""# {CO}
## CERTIFIED TRUE COPY OF RESOLUTION - BOARD OF DIRECTORS
Held on 05th DAY OF JANUARY 2025

1. "RESOLVED THAT each Equity Share of Rs. 10 be sub-divided into 5 Equity Shares of Rs. 2 each, the total Authorised Share Capital remaining unchanged at Rs. 50,00,000."

Date: 05/01/2025
ARUN VIKRAM SETHI (DIRECTOR)
""")
    _write(d / "EGM_Notice.md", f"""# {CO}
NOTICE IS HEREBY GIVEN THAT AN EXTRA ORDINARY GENERAL MEETING will be held on 18th DAY OF JANUARY 2025 at 10:00 AM

## SPECIAL BUSINESS:
RESOLVED THAT each Equity Share having face value of Rs. 10 each be sub-divided into 5 Equity Shares of Rs. 2 each, resulting in 22,50,000 Equity Shares. Preference Share Capital of Rs. 5,00,000 divided into 50,000 Preference Shares of Rs. 10 each remains unchanged. Total Authorised Share Capital remains at Rs. 50,00,000.

Date: 08/01/2025
BY ORDER OF THE BOARD
ARUN VIKRAM SETHI (DIRECTOR)
""")

def main():
    # Clean old PDF data
    import shutil
    for old in ["sh7_01_2019_aug","sh7_02_2021_sep","sh7_03_2023_jul","sh7_04_2025_feb"]:
        p = DATA / old
        if p.exists():
            shutil.rmtree(p)

    ev1(); print("  [OK] sh7_01_2019_mar (4 docs)")
    ev2(); print("  [OK] sh7_02_2021_aug (4 docs, incl. PAS-3 noise)")
    ev3(); print("  [OK] sh7_03_2023_jul (4 docs)")
    ev4(); print("  [OK] sh7_04_2025_jan (3 docs)")
    print("Dataset: 15 markdown files across 4 event folders")

if __name__ == "__main__":
    main()
