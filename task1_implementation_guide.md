# Task 1 — DRHP Capital Structure Drafting Agent: Implementation Guide

This document is a step-by-step playbook for building the system described in Task 1 of the S45 AI Engineer take-home. It is opinionated: it tells you what to build, in what order, and where the traps are. Read it end-to-end once before writing code — many of the design decisions later in the doc constrain the early ones.

---

## 1. Understand the Domain First

Before opening an editor, internalise what you are actually modelling. The grader will spot a system that "works on the sample" but doesn't understand the underlying document semantics.

### 1.1 What is a DRHP?

A **Draft Red Herring Prospectus** is the document a company files with SEBI before an IPO. It contains everything a prospective investor needs: financials, risk factors, business description, and — relevant to us — the **Capital Structure** section, which narrates how the company's authorised, issued, subscribed, and paid-up share capital evolved from incorporation to the filing date.

The Capital Structure section typically has several sub-tables. Task 1 specifically targets the **Authorised Share Capital history** table.

### 1.2 What is "Authorised Share Capital"?

Authorised share capital is the **maximum** share capital a company is legally permitted to issue, as stated in its Memorandum of Association (MoA). It is **not** the same as issued or paid-up capital.

A company can change its authorised capital only by:

1. Passing a shareholder resolution (ordinary or special, depending on Articles) at an AGM or EGM.
2. Filing **Form SH-7** with the Registrar of Companies (RoC) within 30 days, along with:
   - Certified copy of the resolution
   - Altered MoA
   - Notice of the meeting
3. Paying additional stamp duty / fees on the increased capital.

So every row in the target table corresponds to one such event.

### 1.3 The Document Types You'll See

| Document | What it is | Why it matters |
|---|---|---|
| **Form SH-7** | The MCA filing notifying RoC of capital alteration | Primary source of truth for date, before/after capital, type of meeting |
| **Form PAS-3** | Return of allotment (after issuing new shares) | Relevant to **issued** capital, not authorised. Useful for the broader DRHP table but **out of scope for Task 1's authorised-capital table** — be ready to filter it out |
| **Board Resolution** | Internal company decision to recommend the change | Confirms the event; useful as cross-check |
| **Shareholder Resolution / EGM/AGM Notice** | The actual approval | Authoritative for date and meeting type (AGM vs EGM) |
| **Altered MoA** | Updated charter document | Authoritative for the "To" capital description |

The trick: SH-7 carries most of the structured data, but its **attachments** (resolutions, MoA) are what give you the legal backing. If SH-7 and its attachment disagree, that's a flag worth surfacing.

### 1.4 Anatomy of the Target Table

Re-read the sample table in the assignment. Each row is one alteration event. Columns:

- **Date of Shareholder's Meeting** — from the resolution / EGM notice, not the SH-7 filing date.
- **From** — authorised capital text *before* this change (must equal previous row's "To").
- **Particulars of Change** — natural-language description; for the first row this is the incorporation capital.
- **To** — authorised capital text *after* this change.
- **AGM/EGM** — meeting type.

Two structural invariants worth enforcing:

1. **Chronological order** by meeting date.
2. **Continuity**: row N's "From" must equal row N-1's "To". A break here is a strong signal of a missing document.

---

## 2. Problem Decomposition

### 2.1 Inputs

- 4 SH-7 documents.
- 3 attachments per SH-7 (mix of board resolutions, EGM/AGM notices, altered MoA, and possibly noise like cover letters or PAS-3s).
- Total: 4 + 12 = 16 documents.

### 2.2 Outputs

- A draft Authorised Share Capital change table (rendered as Markdown / HTML / CSV).
- Per-cell **source citations** — which document(s) backed each value.
- A list of **flags / open questions** — fields the system couldn't confirm, or contradictions between sources.

### 2.3 Hard Constraints from the Brief

> "Every number and fact traces back to an actual source document."
> "If something's missing or unclear, the system should say so."

These are non-negotiable. Bake them into the schema before writing extraction logic.

---

## 3. Build the Sample Dataset

The assignment requires you to **generate** the dataset yourself (4 SH-7s × 3 attachments). This is itself a graded artifact — well-designed dummy data shows you understand the domain.

### 3.1 Design a Believable Company Timeline

Pick a fictional company (e.g., "Acme Analytics Private Limited") and lay out a 5–8 year history with roughly 4 authorised-capital alterations. Example:

| Event # | Date | Change |
|---|---|---|
| Incorporation | 12 Mar 2018 | ₹1,00,000 (10,000 equity shares @ ₹10) |
| Alteration 1 | 5 Aug 2019 (EGM) | Increase to ₹5,00,000 |
| Alteration 2 | 22 Sep 2021 (EGM) | Increase to ₹10,00,000, introduce 50,000 preference shares @ ₹10 |
| Alteration 3 | 14 Jul 2023 (AGM) | Increase equity portion to ₹50,00,000 |
| Alteration 4 | 9 Feb 2025 (EGM) | Sub-division of face value from ₹10 to ₹2; resulting capital re-stated |

Each alteration becomes one SH-7 plus three attachments. Embed at least one of each of these realistic complications:

- A **face-value sub-division** (tricky because the rupee total may not change — only share count and FV).
- A **mixed capital structure** (equity + preference) so your extractor can't assume single share class.
- One SH-7 whose attachment **disagrees** with the form (e.g., date typo, or MoA shows different number) — to test flagging.
- One SH-7 with a **scanned/image-based attachment** (force OCR path).
- One attachment that is **noise** (e.g., a PAS-3 mistakenly bundled in) — to test classification rejection.

### 3.2 How to Actually Produce the PDFs

You don't need to hand-fill the official MCA forms. Two pragmatic approaches:

**Approach A — Templated PDFs (recommended).** Take the real SH-7 / PAS-3 specimens provided in the assignment file, copy their structure into a Word/HTML template, fill in your fictional values, and export as PDF. Same for board resolutions (use a 1-page boilerplate). This keeps fidelity high.

**Approach B — Programmatic generation.** Use `reportlab` or `weasyprint` to generate PDFs from a Python script. Faster to vary, but the layout will be cleaner than real filings — which can flatter your extractor unrealistically.

Mix both: use Approach A for SH-7s, Approach B for resolution attachments, and scan-then-photograph one attachment to get a genuinely messy OCR target.

### 3.3 Folder Layout for the Dataset

```
data/
  sh7_01_2019_aug/
    sh7.pdf
    board_resolution.pdf
    egm_notice.pdf
    altered_moa.pdf
  sh7_02_2021_sep/
    sh7.pdf
    board_resolution.pdf
    altered_moa.pdf
    pas3_noise.pdf      # deliberate distractor
  sh7_03_2023_jul/
    ...
  sh7_04_2025_feb/
    ...
  ground_truth.json     # what the correct table should look like
```

`ground_truth.json` is for **your** evaluation — not part of the agent's input. Use it to score the agent during development.

---

## 4. System Architecture

A clean pipeline beats a clever monolith here. Five stages:

```
   ┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐    ┌───────────────┐
   │ 1. Ingest & │ →  │ 2. Classify  │ →  │ 3. Extract     │ →  │ 4. Reconcile │ →  │ 5. Render     │
   │    Parse    │    │   Document   │    │   Structured   │    │   & Validate │    │   Table +     │
   │             │    │     Type     │    │     Fields     │    │              │    │   Flags       │
   └─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘    └───────────────┘
```

### 4.1 Stage 1 — Ingest & Parse

**Goal:** turn each PDF into clean text plus per-page metadata.

- For text-based PDFs: `pypdf`, `pdfplumber`, or `pymupdf` (fitz). `pdfplumber` is best when tables matter.
- For scanned PDFs: detect (low text yield → OCR). Use `pytesseract` or a hosted OCR (Azure Document Intelligence, AWS Textract) if you have the budget.
- Preserve a `(document_id, page_number, char_offset)` tuple per chunk — you'll need it for citations.

**Output:** `ParsedDocument { id, source_path, pages: [{page_no, text}], is_ocr: bool }`.

### 4.2 Stage 2 — Document Classification

**Goal:** for each parsed document, label it with a type and a corporate event.

The taxonomy your classifier should output:

```
type: SH-7 | PAS-3 | BOARD_RESOLUTION | SHAREHOLDER_RESOLUTION |
      EGM_NOTICE | AGM_NOTICE | ALTERED_MOA | OTHER
event_id: <stable hash linking docs that describe the same event>
official: bool   # filed with RoC vs internal/draft
```

Two viable implementations:

- **LLM zero-shot.** Send the first 1–2 pages to an LLM with a strict JSON schema. Cheap, robust, easy to iterate. Use this.
- **Rules + classifier.** Regex on form headers ("Form No. SH-7", "Form PAS-3"). Faster and free, but brittle on OCR'd text. Use as a **fallback / sanity check** alongside the LLM.

Best practice: run rules first; if rules are confident, skip the LLM. Otherwise call LLM. Always emit a `confidence` score.

For event grouping, use the SH-7's date and resolution-meeting date; group attachments to the SH-7 they share a folder with **and** verify that the attachment's referenced date matches.

### 4.3 Stage 3 — Structured Extraction

**Goal:** for each event group, extract a typed record.

Define a Pydantic schema up front:

```python
class CapitalAmount(BaseModel):
    total_rupees: int
    breakdown: list[ShareTranche]  # [{class: equity|preference, count, face_value}]
    raw_text: str                  # exact phrase from source

class CapitalAlteration(BaseModel):
    event_id: str
    meeting_date: date | None
    meeting_type: Literal["AGM", "EGM"] | None
    capital_before: CapitalAmount | None
    capital_after: CapitalAmount | None
    particulars: str
    sources: list[Citation]        # which doc/page each field came from
    flags: list[Flag]              # [{field, reason, severity}]
```

Why structured types matter: the **continuity check** in Stage 4 needs `total_rupees` and `breakdown` as comparable values, not free text.

Extraction strategy: per event group, concatenate the SH-7 text + each attachment's text (with clear `<doc id="...">` separators), and ask the LLM to fill the schema. Two prompt techniques that pay off here:

1. **Force per-field source attribution.** Make every field in the JSON output have a sibling `_source` field pointing to the doc id and page. This forces the model to ground each value rather than hallucinate.
2. **Two-pass extraction.** Pass 1 extracts; Pass 2 (a separate call, maybe a different model) audits — given the same inputs and the Pass 1 output, find errors. Cheap and catches a lot.

### 4.4 Stage 4 — Reconcile & Validate

This is where most of the engineering value lives.

Run these checks in order, accumulating flags:

1. **Within-event consistency.** For event E, do the SH-7, board resolution, and altered MoA agree on date, meeting type, and capital amounts? Compare the structured `CapitalAmount` objects, not raw strings (₹5,00,000 and "Rupees Five Lakh" must compare equal).
2. **Cross-event continuity.** Sort events by date. For each pair (E_n, E_{n+1}), check that `E_{n+1}.capital_before == E_n.capital_after`. A break implies a missing alteration.
3. **Incorporation row.** The first row's "From" is empty (or "—") and "Particulars" describes the incorporation capital. If you don't have an incorporation document but you do have an SH-7 referencing a "before" amount that no other event explains, synthesise an inferred incorporation row and **flag it as inferred**.
4. **Schema completeness.** Any `None` field in the final table is a flag, not a failure.

Each flag should look like:

```python
Flag(
  field="meeting_date",
  event_id="evt_2021_09",
  reason="Board resolution dated 2021-09-15 but SH-7 references 2021-09-22; "
         "EGM notice missing.",
  severity="warning",   # info | warning | error
  sources=[...]
)
```

### 4.5 Stage 5 — Render

Output two artifacts:

1. **`capital_structure.md`** — the table itself, with footnote-style citations: `[1]`, `[2]` mapping to source docs in a "Sources" section. Cells with flags get a `⚠` marker.
2. **`audit.json`** — the full structured output: every event, every field, every source, every flag. This is what an analyst would actually review.

---

## 5. Implementation Notes

### 5.1 Tech Stack Suggestion

- **Language:** Python 3.11+.
- **PDF parsing:** `pdfplumber` + `pymupdf` fallback, `pytesseract` for OCR.
- **LLM client:** Anthropic Claude (Sonnet for extraction, Haiku for classification to save cost) or OpenAI — pick one and stick with it. Use the **structured output / tool-use** API so the model returns valid JSON, not free text.
- **Validation:** Pydantic v2.
- **Orchestration:** Plain Python functions in a clear pipeline. **Resist** reaching for LangChain/LlamaIndex on a task this size — they add ceremony and obscure your decisions, which is the opposite of what the grader wants to see.
- **Testing:** `pytest` with the `ground_truth.json` as fixture; assert table equality up to a tolerance for free-text fields.

### 5.2 Prompt Design Principles

- **Schema-first, not instruction-first.** The strongest signal to the model is a tight JSON schema. Spend more tokens on the schema than on prose instructions.
- **Few-shot with one good example.** Include one fully-worked event extraction in the prompt — it eliminates 80% of format errors.
- **Quote-then-extract.** Ask the model to first quote the relevant sentence from the source document, then extract the field. Reduces hallucination and gives you free citations.
- **Explicitly allow null.** Tell the model: *"If a field cannot be determined from the provided documents, return null and add an entry to `flags` explaining why. Do not guess."* This single instruction is the difference between an honest system and a confident-but-wrong one.

### 5.3 Citation Mechanism

Pick one citation format and use it everywhere. Suggested:

```
"S1": {"doc_id": "sh7_02_2021_sep/sh7.pdf", "page": 2, "quote": "..."}
```

Every value in `audit.json` should reference a citation key. Every `⚠` in the rendered table should resolve to a flag with citations.

### 5.4 Edge Cases to Handle Explicitly

| Edge case | How to handle |
|---|---|
| OCR garbles a date | Flag as low-confidence; let LLM try sibling documents |
| Two attachments contradict each other | Pick the higher-authority source (resolution > MoA > board resolution > cover letter) and flag |
| Same SH-7 references multiple alterations | Split into multiple events; very rare, but possible |
| Sub-division (FV change, total unchanged) | Detect via `total_rupees_before == total_rupees_after`; ensure "Particulars" describes the sub-division explicitly |
| PAS-3 mistakenly in input | Classifier should catch and exclude; log a notice |
| Scanned attachment with no OCR | Don't fail silently — emit an error-level flag for that event |

### 5.5 What "Done" Looks Like

You can run `python -m drhp_agent --input data/ --output out/` and get:

- `out/capital_structure.md` — clean table with citations
- `out/audit.json` — full structured output
- `out/flags.md` — human-readable list of open questions
- Exit code 0 on success, non-zero if any error-severity flag exists

---

## 6. Repository Layout

```
.
├── README.md                 # how to install & run; design summary; assumptions
├── DESIGN.md                 # the hand-written design doc (deliverable #3)
├── PROMPTS.md                # log of prompts used during development (deliverable #2)
├── pyproject.toml
├── src/drhp_agent/
│   ├── __init__.py
│   ├── ingest.py             # Stage 1
│   ├── classify.py           # Stage 2
│   ├── extract.py            # Stage 3
│   ├── reconcile.py          # Stage 4
│   ├── render.py             # Stage 5
│   ├── schemas.py            # Pydantic models
│   ├── llm.py                # thin LLM client wrapper
│   └── cli.py
├── data/                     # generated sample dataset
│   ├── sh7_01_2019_aug/...
│   ├── sh7_02_2021_sep/...
│   ├── sh7_03_2023_jul/...
│   ├── sh7_04_2025_feb/...
│   └── ground_truth.json
├── out/                      # checked-in sample run output
│   ├── capital_structure.md
│   ├── audit.json
│   └── flags.md
└── tests/
    ├── test_classify.py
    ├── test_extract.py
    └── test_reconcile.py
```

---

## 7. The Three Deliverables — What to Actually Submit

### 7.1 GitHub Repo

Make sure the README has, in this order:

1. One-paragraph problem statement (in your own words).
2. How to install and run (with a single command demo).
3. Architecture diagram (the 5-stage pipeline above is fine).
4. Sample run output, inline.
5. Known limitations.

Commit the generated dataset, the agent code, and a checked-in sample output. Reviewers will read the output before they read the code.

### 7.2 Prompts Log (`PROMPTS.md`)

If you used Cursor / Claude Code / Codex, keep a running log. Don't sanitise it after the fact — show the iteration. Group by the component you were building. For each prompt, note: what you asked, what came back, and what you changed about the prompt or the code afterward. This is a credibility signal more than a deliverable.

### 7.3 Design Doc (`DESIGN.md`)

The brief says "hand-written" and AI-checked. Take it seriously: write it yourself, in your own voice, with concrete decisions and trade-offs. Cover:

- **Problem framing.** What is authorised share capital, why traceability matters, what an analyst would do manually.
- **Inputs & outputs.** Be specific about the data contract.
- **Architecture.** The pipeline, why you split it that way, what state flows between stages.
- **Key decisions.** For each: alternatives considered, trade-off made, why. E.g.: "LLM-based classification vs regex — chose LLM-first with regex fallback because OCR'd headers break regex; cost is ~$0.001 per doc, acceptable."
- **Handling uncertainty.** How flags work, what severity levels mean, what an analyst sees.
- **Failure modes.** When does the system give up? How does it tell you?
- **What I'd do with another week.** Honest list of things you cut.

Length target: 4–8 pages. Less reads thin; more reads padded.

---

## 8. Recommended Order of Work

If you have ~2 days, do it in this order. Don't reorder — each stage de-risks the next.

1. **Half-day: dataset.** Build the 4 events, write `ground_truth.json` first, then generate the PDFs to match. Building the truth before the data is the single best discipline lever in this assignment.
2. **Half-day: schemas + ingest.** Pydantic models, PDF→text, citation plumbing. No LLM yet.
3. **Half-day: classify + extract.** Wire up the LLM, get one event extracting end-to-end against ground truth.
4. **Half-day: reconcile + render.** Continuity check, flagging, table output. Run on all 4 events.
5. **Buffer: evaluation, edge cases, design doc.** Iterate on prompts using flags from the audit; write the design doc last when you actually know what you built.

---

## 9. What Will Make This Submission Stand Out

The brief is explicit about what they care about: **honest handling of the unknown** and **traceability**. Three small things that disproportionately signal quality:

1. **A flag the system raises that a naive solution would miss.** E.g., the SH-7 / board-resolution date mismatch you deliberately seeded — show it in the output.
2. **Comparing structured capital amounts, not strings.** A system that knows ₹5,00,000 == "Rupees Five Lakh" has clearly thought about the problem.
3. **A `ground_truth.json` and a test that asserts the agent matches it.** Demonstrates you treat this as engineering, not a demo.

Everything else — pretty UI, clever prompting, more models — matters less than these three.
