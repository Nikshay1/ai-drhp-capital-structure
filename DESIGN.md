# DRHP Capital Structure Drafting Agent — Design Document

## 1. Problem Framing

### What is Authorised Share Capital?

Authorised share capital is the maximum share capital a company is legally permitted to issue, as stated in its Memorandum of Association (MoA). Unlike issued or paid-up capital, it represents a ceiling — the company cannot issue shares beyond this amount without a formal alteration.

Every change to authorised capital requires:
1. A shareholder resolution at an AGM or EGM
2. Filing Form SH-7 with the Registrar of Companies within 30 days
3. Payment of stamp duty on the increased amount

### Why Traceability Matters

In DRHP preparation, the capital structure table must be legally defensible. Every number must trace back to a specific regulatory filing. An analyst doing this manually would:
1. Collect all SH-7 filings from the MCA portal
2. Cross-reference each SH-7 with its attachments (resolutions, MoA)
3. Verify dates match between the SH-7 and the actual meeting notice
4. Build a chronological table ensuring continuity (row N's "To" equals row N+1's "From")
5. Flag any discrepancies for legal review

This is tedious, error-prone, and expensive. Automating it with AI isn't just faster — it's potentially more reliable, *provided* the system is honest about what it doesn't know.

### What an Analyst Would Do Manually

The manual workflow takes 2-4 hours per company:
- Download SH-7 forms from MCA portal
- Read each form to identify the alteration event
- Cross-check with board resolutions and meeting notices
- Manually type the capital structure table
- Flag inconsistencies with hand-written notes

The risk isn't speed — it's consistency. A human analyst reading 16 documents will miss the board resolution date being 7 days before the EGM. Our system catches this automatically.

---

## 2. Inputs & Outputs

### Inputs
- **4 SH-7 documents** (the primary RoC filings for capital alteration)
- **12 attachments** (3 per SH-7): mix of board resolutions, EGM/AGM notices, altered MoA, and one deliberate PAS-3 noise document
- Total: **16 PDF documents** organised in folders by event

### Outputs
1. **`capital_structure.md`** — The authorised share capital history table with footnote-style citations (`[S1]`, `[S2]`) and `⚠` markers on flagged cells
2. **`audit.json`** — Full structured output: every event, every field, every source, every flag. This is what an analyst actually reviews.
3. **`flags.md`** — Human-readable list of open questions, grouped by severity (error → warning → info)

### Data Contract
Every field in the output has a `sources` list pointing to `Citation` objects with `(doc_id, page, quote)` tuples. No value exists without provenance.

---

## 3. Architecture

### The 5-Stage Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐    ┌───────────────┐
│ 1. Ingest & │ →  │ 2. Classify  │ →  │ 3. Extract     │ →  │ 4. Reconcile │ →  │ 5. Render     │
│    Parse    │    │   Document   │    │   Structured   │    │   & Validate │    │   Table +     │
│             │    │     Type     │    │     Fields     │    │              │    │   Flags       │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘    └───────────────┘
```

### Why This Split?

Each stage has a single responsibility and a clear data contract:

- **Stage 1 (Ingest)** converts PDFs to text. No intelligence — just faithful extraction. This isolation means we can swap PDF libraries without touching any other code.
- **Stage 2 (Classify)** labels documents. Separated from extraction because the classifier should reject irrelevant documents (PAS-3) before they pollute the extraction prompt.
- **Stage 3 (Extract)** is where the LLM does heavy lifting. Isolated so we can iterate on prompts without touching ingestion or validation.
- **Stage 4 (Reconcile)** is pure validation — no LLM calls. This is deterministic logic that catches errors the LLM might make.
- **Stage 5 (Render)** is pure presentation. Multiple output formats from the same data.

### State Between Stages

```
PDF files → ParsedDocument[] → ClassifiedDocument[] → CapitalAlteration[] → (reconciled) → files on disk
```

Each intermediate type is a Pydantic model, so the data contract is enforced at runtime.

---

## 4. Key Decisions

### 4.1 LLM-based classification vs regex

**Decision:** Rules-first with LLM fallback.

**Alternatives:**
- Pure regex: Fast and free, but brittle on OCR'd text where headers get garbled
- Pure LLM: Reliable but ~$0.001 per doc adds up, and introduces latency

**Trade-off:** Rules handle 80%+ of well-structured PDFs instantly. LLM catches the rest. Cost: ~$0.004 total for 16 docs (only 2-3 need LLM fallback).

### 4.2 Two-pass extraction

**Decision:** Extract first, then audit with a separate LLM call.

**Alternative:** Single-pass extraction with self-checking instructions.

**Trade-off:** Two passes cost 2x tokens but catch significantly more errors. The audit pass sees the extraction as an external artifact, which makes it better at spotting inconsistencies. A reviewer told us to "build in adversarial review" — this is the cheapest way.

### 4.3 Structured types over string comparison

**Decision:** Compare `CapitalAmount` objects (with `total_rupees` and `breakdown`), not raw text strings.

**Why:** "₹5,00,000" and "Rupees Five Lakh" must compare equal. String matching would miss this. Structured comparison also catches arithmetic errors (shares × face_value ≠ total).

### 4.4 Plain Python over LangChain

**Decision:** Plain functions in a pipeline. No framework.

**Alternative:** LangChain/LlamaIndex for document loading and chain orchestration.

**Trade-off:** Frameworks add ceremony and obscure decisions. On a task this size (15 docs, 5 stages), plain Python is clearer, easier to debug, and shows the reviewer we understand what we're building. The entire codebase is <800 lines.

### 4.5 OpenAI GPT-4o as LLM backend

**Decision:** GPT-4o for extraction, GPT-4o-mini for classification.

**Why:** Cost-effective, supports JSON mode (`response_format=json_object`), widely available. GPT-4o-mini handles classification cheaply; GPT-4o provides the reasoning depth needed for two-pass extraction + audit.

---

## 5. Handling Uncertainty

### Flag Severity Levels

| Severity | Meaning | Example |
|----------|---------|---------|
| `info` | Notable but not problematic | PAS-3 excluded from extraction; sub-division detected |
| `warning` | Needs human review | Board resolution date ≠ EGM date; continuity break |
| `error` | Data integrity issue | Arithmetic mismatch; critical field missing |

### What the Analyst Sees

In `capital_structure.md`, cells with warning/error flags get a `⚠` marker. The analyst clicks through to `flags.md` for the full explanation with source citations. `audit.json` gives them the raw data to verify.

The system never silently drops information. If it can't determine a value, it emits `null` and a flag — never a guess.

---

## 6. Failure Modes

| Failure | System response |
|---------|-----------------|
| PDF cannot be parsed at all | `ParsedDocument` with empty pages; error-level flag emitted |
| OCR yields garbage | Flag as low-confidence; extraction proceeds with sibling documents |
| LLM returns invalid JSON | Retry once; if still fails, skip with error flag |
| Two documents contradict | Pick higher-authority source (resolution > MoA > board res > cover letter); flag the disagreement |
| Missing document for an event | Continuity check catches the gap; warning flag with "possible missing alteration" |
| API rate limit / timeout | Fail fast with clear error message; pipeline can be re-run |

### When Does the System Give Up?

It never silently gives up. Every problem becomes a flag. The exit code is non-zero if any error-level flag exists, signaling to the analyst that the output needs review.

---

## 7. What I'd Do With Another Week

1. **Confidence scoring per cell.** Right now flags are binary. A probability score would let analysts triage faster.
2. **Interactive HTML output.** Click a cell → see the source document with the relevant passage highlighted.
3. **Multi-company support.** Process multiple companies in parallel; share classification prompts across runs.
4. **Fine-tuned classifier.** Train a small model on MCA form headers to replace the LLM fallback entirely.
5. **Integration testing against real MCA filings.** The synthetic dataset is clean; real filings are messier.
6. **Caching layer.** Cache LLM responses keyed by document content hash to avoid re-extraction during development.
7. **Better OCR pipeline.** Use Azure Document Intelligence or AWS Textract for production-grade OCR instead of pytesseract.
