# DRHP Capital Structure Drafting Agent

AI agent that ingests regulatory filings (SH-7, PAS-3, board resolutions, etc.) and generates a traceable draft Authorised Share Capital change table for DRHP preparation.

## Problem Statement

When a company files a Draft Red Herring Prospectus (DRHP) for an IPO, its Capital Structure section must show how authorised share capital evolved from incorporation to the filing date. Each row in this table corresponds to a shareholder resolution that altered the authorised capital, and must be traceable to specific source documents (SH-7 forms, board resolutions, EGM/AGM notices, altered MoA). If a field can't be confirmed from the available documents, it should be flagged -- not filled with a best guess.

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set up API key
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Generate sample dataset (15 markdown files)
python scripts/generate_dataset.py

# 4. Run the agent
python -m drhp_agent --input data/ --output out/ -v

# 5. Run tests
pytest tests/ -v
```

## Architecture

```
 Ingest & Parse  -->  Classify Doc Type  -->  Extract Fields  -->  Reconcile & Validate  -->  Render Table
   (Stage 1)           (Stage 2)              (Stage 3)             (Stage 4)                 (Stage 5)
```

| Stage | Module | What it does |
|-------|--------|--------------|
| 1 | `ingest.py` | PDF/Markdown -> text with page metadata |
| 2 | `classify.py` | Label each doc (SH-7, PAS-3, Board Resolution, etc.) -- rules-first, LLM fallback |
| 3 | `extract.py` | Two-pass LLM extraction: extract fields then audit for errors |
| 4 | `reconcile.py` | Validate continuity, arithmetic, completeness; synthesise incorporation row |
| 5 | `render.py` | Output: `capital_structure.md`, `audit.json`, `flags.md` |

## Sample Output: Draft Authorised Share Capital Change

| Date of Shareholder's Meeting | From | To | AGM/EGM |
|---|---|---|---|
| On incorporation | - | Rs. 1,00,000 divided into 10,000 Equity Shares of Rs. 10 each | - |
| March 22, 2019 | Rs. 1,00,000 divided into 10,000 Equity Shares of Rs. 10 each | Rs. 3,00,000 divided into 30,000 Equity Shares of Rs. 10 each | EGM |
| August 15, 2021 [!] | Rs. 3,00,000 divided into 30,000 Equity Shares of Rs. 10 each | Rs. 10,00,000 divided into 50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | EGM |
| July 28, 2023 | Rs. 10,00,000 divided into 50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | Rs. 50,00,000 divided into 4,50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | AGM |
| January 18, 2025 | Rs. 50,00,000 divided into 4,50,000 Equity Shares of Rs. 10 each and 50,000 Preference Shares of Rs. 10 each | Rs. 50,00,000 divided into 22,50,000 Equity Shares of Rs. 2 each and 50,000 Preference Shares of Rs. 10 each | EGM |

> [!] Event 2: Board resolution dated 2021-08-05 but SH-7 references EGM on 2021-08-15

## Dataset

The `data/` directory contains 15 markdown files modeled after real MCA filings:
- **4 SH-7 forms** (one per capital alteration event)
- **11 attachments** (board resolutions, meeting notices, altered MoAs)
- **1 PAS-3 noise document** (tests classification rejection -- PAS-3 relates to issued capital, not authorised)
- **1 date discrepancy** (board resolution vs EGM date mismatch -- tests flagging)
- **1 sub-division event** (face value changes, total unchanged)
- **1 mixed capital structure** (equity + preference shares)

## Known Limitations

1. LLM required for extraction (OpenAI GPT-4o). Non-LLM stages work offline.
2. No image-based OCR testing -- synthetic data is text-based.
3. Indian number format only (Rs. notation with Indian comma style).
4. No caching -- each run re-extracts everything.

## Project Structure

```
├── README.md
├── DESIGN.md                 # Design document
├── PROMPTS.md                # Prompts log
├── pyproject.toml
├── .env.example
├── src/drhp_agent/
│   ├── cli.py                # CLI entry point
│   ├── schemas.py            # Pydantic models
│   ├── llm.py                # OpenAI LLM wrapper
│   ├── ingest.py             # Stage 1
│   ├── classify.py           # Stage 2
│   ├── extract.py            # Stage 3
│   ├── reconcile.py          # Stage 4
│   └── render.py             # Stage 5
├── scripts/generate_dataset.py
├── data/                     # Sample dataset (4 SH-7 folders)
│   └── ground_truth.json
├── sample input documents for capital structure/
│   ├── SH-7/                 # Reference SH-7 and attachments
│   └── PAS-3/                # Reference PAS-3 and attachments
└── tests/
```
