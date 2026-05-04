# DRHP Capital Structure Drafting Agent

AI agent that ingests regulatory filings (SH-7, PAS-3, board resolutions, etc.) and generates a traceable Authorised Share Capital history table for DRHP preparation.

## Problem Statement

When a company files a Draft Red Herring Prospectus (DRHP) for an IPO, its Capital Structure section must narrate how authorised share capital evolved from incorporation to the filing date. This involves reading dozens of regulatory filings (SH-7 forms, board resolutions, meeting notices, altered MoAs), cross-referencing dates and amounts, and building a table where every number traces back to a source document. This agent automates that process with full traceability and honest uncertainty handling.

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up API key
cp .env.example .env
# Edit .env with your Anthropic API key

# 3. Generate sample dataset (16 PDFs)
python scripts/generate_dataset.py

# 4. Run the agent
python -m drhp_agent --input data/ --output out/

# 5. Run tests
pytest tests/ -v
```

### Single Command Demo
```bash
pip install -e ".[dev]" && python scripts/generate_dataset.py && python -m drhp_agent -i data/ -o out/ -v
```

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐    ┌───────────────┐
│ 1. Ingest & │ →  │ 2. Classify  │ →  │ 3. Extract     │ →  │ 4. Reconcile │ →  │ 5. Render     │
│    Parse    │    │   Document   │    │   Structured   │    │   & Validate │    │   Table +     │
│             │    │     Type     │    │     Fields     │    │              │    │   Flags       │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘    └───────────────┘
```

| Stage | Module | What it does |
|-------|--------|--------------|
| 1. Ingest | `ingest.py` | PDF → text (pdfplumber + pymupdf + OCR fallback) |
| 2. Classify | `classify.py` | Label each doc (SH-7, PAS-3, Board Resolution, etc.) — rules-first, LLM fallback |
| 3. Extract | `extract.py` | Two-pass LLM extraction: extract fields → audit for errors |
| 4. Reconcile | `reconcile.py` | Validate continuity, arithmetic, completeness; synthesise incorporation row |
| 5. Render | `render.py` | Output: `capital_structure.md`, `audit.json`, `flags.md` |

## Sample Run Output

### Capital Structure Table

| # | Date | From | Particulars | To | AGM/EGM |
|---|------|------|-------------|-----|---------|
| 1 | Incorporation | — | Initial capital at incorporation | 10,000 Equity × ₹10 = ₹1,00,000 | — |
| 2 | 2019-08-05 | 10,000 Equity × ₹10 = ₹1,00,000 | Increase to ₹5,00,000 | 50,000 Equity × ₹10 = ₹5,00,000 | EGM |
| 3 | 2021-09-22 ⚠ | 50,000 Equity × ₹10 = ₹5,00,000 | Increase + preference shares | 1,00,000 Equity + 50,000 Pref × ₹10 = ₹15,00,000 | EGM |
| 4 | 2023-07-14 | ₹15,00,000 | Increase equity to ₹50,00,000 | 5,00,000 Equity + 50,000 Pref × ₹10 = ₹55,00,000 | AGM |
| 5 | 2025-02-09 | ₹55,00,000 | Sub-division: FV ₹10 → ₹2 | 25,00,000 Equity × ₹2 + 50,000 Pref × ₹10 = ₹55,00,000 | EGM |

> ⚠ Event 3: Board resolution dated 2021-09-15 but SH-7 references EGM on 2021-09-22

## Dataset

The `data/` directory contains 16 programmatically generated PDFs:
- **4 SH-7 forms** (one per capital alteration event)
- **12 attachments** (board resolutions, meeting notices, altered MoAs)
- **1 PAS-3 noise document** (deliberately included to test classification rejection)
- **1 date discrepancy** (board resolution vs. EGM date mismatch)
- **1 sub-division event** (face value changes, total unchanged)

## Known Limitations

1. **Synthetic dataset only.** Generated PDFs are cleaner than real MCA filings. Real-world OCR would be messier.
2. **No image-based OCR testing.** pytesseract path exists but synthetic PDFs are all text-based.
3. **Single LLM provider.** Currently Anthropic-only; OpenAI could be added by swapping `llm.py`.
4. **No caching.** Each run re-extracts everything. A content-hash cache would help during development.
5. **Indian number format only.** The system assumes ₹ amounts in Indian comma notation.
6. **No interactive UI.** Output is static Markdown/JSON files.

## Project Structure

```
├── README.md                 # This file
├── DESIGN.md                 # Hand-written design document
├── PROMPTS.md                # Log of prompts used during development
├── pyproject.toml            # Project configuration
├── .env.example              # Environment variables template
├── src/drhp_agent/
│   ├── __init__.py
│   ├── __main__.py           # python -m drhp_agent
│   ├── cli.py                # CLI entry point
│   ├── schemas.py            # Pydantic models
│   ├── llm.py                # LLM client wrapper
│   ├── ingest.py             # Stage 1: PDF parsing
│   ├── classify.py           # Stage 2: Document classification
│   ├── extract.py            # Stage 3: Structured extraction
│   ├── reconcile.py          # Stage 4: Validation
│   └── render.py             # Stage 5: Output rendering
├── scripts/
│   └── generate_dataset.py   # Sample dataset generator
├── data/                     # Generated sample dataset
│   ├── sh7_01_2019_aug/      # 4 PDFs
│   ├── sh7_02_2021_sep/      # 4 PDFs (incl. PAS-3)
│   ├── sh7_03_2023_jul/      # 4 PDFs
│   ├── sh7_04_2025_feb/      # 4 PDFs
│   └── ground_truth.json     # Expected output for evaluation
├── out/                      # Sample run output
└── tests/
    ├── test_classify.py      # Classification unit tests
    ├── test_extract.py       # Ground truth validation
    └── test_reconcile.py     # Reconciliation unit tests
```
