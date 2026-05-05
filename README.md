# DRHP Capital Structure Drafting Agent

AI-powered agent that ingests regulatory filings (SH-7, PAS-3, board resolutions, etc.) and generates a traceable, draft **Authorised Share Capital change table** for DRHP (Draft Red Herring Prospectus) preparation.

## Problem Statement

When a company files a DRHP for an IPO, the Capital Structure section must show how its authorised share capital evolved from incorporation to filing date. Each row in this table corresponds to a shareholder resolution that altered the authorised capital, and must be traceable to specific source documents (SH-7 forms, board resolutions, EGM/AGM notices, altered MoA).

**Core principle**: If a field can't be confirmed from the available documents, it is **flagged** — never filled with a best guess.

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set up API key
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Generate sample dataset (15 markdown files across 4 event folders)
python scripts/generate_dataset.py

# 4. Run the pipeline
python -m drhp_agent --input data/ --output out/ -v

# 5. Run tests (24 tests)
pytest tests/ -v
```

## Architecture

```
Ingest → Classify → Extract → Reconcile → Render
  (1)      (2)        (3)        (4)        (5)
```

| Stage | Module | What it does |
|-------|--------|--------------|
| 1 | `ingest.py` | PDF/Markdown → text with page metadata |
| 2 | `classify.py` | Label each doc (SH-7, PAS-3, Board Resolution, etc.) — rules-first, LLM fallback |
| 3 | `extract.py` | Two-pass LLM extraction: extract fields → audit for errors. Every value requires a citation. |
| 4 | `reconcile.py` | Validate continuity, arithmetic, completeness; detect sub-divisions; synthesise incorporation row |
| 5 | `render.py` | Output: `capital_structure.md`, `audit.json`, `flags.md` |

## Sample Output

The pipeline produces the following draft Authorised Share Capital change table from 4 SH-7 input events:

| Date of Shareholder's Meeting | From | To | AGM/EGM |
|---|---|---|---|
| On incorporation | - | Rs. 1,00,000 divided into 10,000 Equity Shares of Rs. 10 each | - |
| March 22, 2019 | Rs. 1,00,000 divided into 10,000 Equity Shares of Rs. 10 each | Rs. 3,00,000 divided into 30,000 Equity Shares of Rs. 10 each | EGM |
| August 15, 2021 | Rs. 3,00,000 divided into 30,000 Equity Shares of Rs. 10 each | Rs. 10,00,000 divided into 50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | EGM |
| July 28, 2023 | Rs. 10,00,000 divided into 50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | Rs. 50,00,000 divided into 4,50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | AGM |
| January 18, 2025 | Rs. 50,00,000 divided into 4,50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | Rs. 50,00,000 divided into 22,50,000 Equity Shares of Rs. 2 each and 50,000 Preference Shares of Rs. 10 each | EGM |

Each row is backed by **source citations** referencing the exact document and quoted text (see `out/capital_structure.md`).

## Verification Results

Cross-checked pipeline output against source SH-7 data files:

| Field | Event 1 | Event 2 | Event 3 | Event 4 |
|-------|---------|---------|---------|---------|
| Date | ✅ | ✅ | ✅ | ✅ |
| Total (Rs.) | ✅ | ✅ | ✅ | ✅ |
| "To" breakdown | ✅ | ✅ | ✅ | ✅ |
| "From" breakdown | ✅ | ✅ | ⚠️ flagged | ⚠️ flagged |
| Meeting type | ✅ | ✅ | ✅ | ✅ |

> **Note**: The "From" breakdown for events 3 and 4 may have LLM extraction inaccuracies (the SH-7 only lists the *revised* structure, not the "before" breakdown explicitly). These are automatically detected and flagged with `[!]` by the reconciliation stage.

## Dataset

The `data/` directory contains **15 markdown files** modeled after real MCA filings, organized into 4 event folders:

| Folder | Event | Documents | Test Cases |
|--------|-------|-----------|------------|
| `sh7_01_2019_mar/` | Rs. 1L → 3L | SH7, Board Res, EGM Notice, Altered MoA | Basic increase |
| `sh7_02_2021_aug/` | Rs. 3L → 10L | SH7, Board Res, Altered MoA, **PAS-3** | Preference shares introduced; PAS-3 noise; date discrepancy |
| `sh7_03_2023_jul/` | Rs. 10L → 50L | SH7, Board Res, AGM Notice, Altered MoA | AGM (not EGM); large equity increase |
| `sh7_04_2025_jan/` | Sub-division | SH7, Board Res, EGM Notice | Face value Rs. 10 → Rs. 2; total unchanged |

**Test cases covered:**
- PAS-3 classification & exclusion (relates to issued capital, not authorised)
- Board resolution date vs EGM date discrepancy
- Sub-division (face value change, total unchanged)
- Mixed capital structure (equity + preference shares)
- Incorporation row synthesis

## Output Files

| File | Purpose |
|------|---------|
| `out/capital_structure.md` | Draft authorised share capital change table with source citations |
| `out/audit.json` | Full structured extraction data (Pydantic-validated JSON) |
| `out/flags.md` | Human-readable flags: errors, warnings, and info notes |

## Flagging System

The pipeline uses a three-tier flagging system:

- **`[X] ERROR`** — Missing critical data (e.g., capital_after is null)
- **`[!] WARNING`** — Data inconsistency detected (e.g., continuity break, breakdown mismatch)
- **`[i] INFO`** — Informational (e.g., PAS-3 excluded, sub-division detected, incorporation row inferred)

Rows with warnings/errors show `[!]` in the output table.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | OpenAI GPT-4o (extraction), GPT-4o-mini (classification) |
| Validation | Pydantic v2 with strict schemas |
| PDF parsing | pdfplumber + pymupdf + pytesseract (fallback chain) |
| Config | `.env` file (`OPENAI_API_KEY`) |
| Tests | pytest (24 tests covering classification, extraction, reconciliation) |

## Project Structure

```
├── README.md
├── DESIGN.md                    # Design decisions document
├── PROMPTS.md                   # AI prompts log
├── pyproject.toml
├── .env.example
├── src/drhp_agent/
│   ├── cli.py                   # CLI orchestrator
│   ├── schemas.py               # Pydantic models (citations required)
│   ├── llm.py                   # OpenAI wrapper (JSON mode)
│   ├── ingest.py                # Stage 1: PDF/MD → text
│   ├── classify.py              # Stage 2: document classification
│   ├── extract.py               # Stage 3: two-pass LLM extraction
│   ├── reconcile.py             # Stage 4: validation & flags
│   └── render.py                # Stage 5: output generation
├── scripts/generate_dataset.py  # Synthetic dataset generator
├── data/                        # 4 SH-7 event folders (15 files)
│   └── ground_truth.json        # Expected output for verification
├── out/                         # Pipeline output
│   ├── capital_structure.md
│   ├── audit.json
│   └── flags.md
├── sample input documents for capital structure/
│   ├── SH-7/                    # Reference SH-7 format
│   └── PAS-3/                   # Reference PAS-3 format
└── tests/                       # 24 unit tests
```
