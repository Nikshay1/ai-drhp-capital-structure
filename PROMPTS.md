# Prompts Log

This document records the prompts used during development, grouped by component. For each prompt, I note what I asked, what came back, and what I changed.

---

## 1. Dataset Generation

### Prompt 1.1 — Company Timeline Design
**What I asked:** Designed a fictional company "Acme Analytics Private Limited" timeline with 4 capital alterations covering: simple increase, mixed capital (equity + preference), AGM-based increase, and face-value sub-division.

**What came back:** Ground truth JSON with 5 events (incl. incorporation).

**What I changed:** Added deliberate complications:
- PAS-3 noise document in event 2
- Board resolution date discrepancy (15-Sep vs 22-Sep EGM) in event 2
- Sub-division where total remains unchanged but share count and FV change in event 4

---

## 2. Document Classification

### Prompt 2.1 — Classification Prompt
**What I asked the LLM:**
```
Classify this Indian corporate regulatory document.
[first 2 pages of text]
document_type: SH-7 | PAS-3 | BOARD_RESOLUTION | ...
```

**What came back:** Correct classifications on all 16 test documents.

**What I changed:** Added rules-based pre-filter using regex on form headers. This catches 80%+ of documents without an LLM call, saving cost and latency. LLM is only used as fallback when regex confidence is below 0.85.

---

## 3. Structured Extraction

### Prompt 3.1 — Extraction Prompt (v1)
**What I asked:** 
```
Extract capital alteration details from these documents.
```

**What came back:** Correct values but no source citations, and the model occasionally used the SH-7 filing date instead of the shareholder meeting date.

**What I changed:** 
1. Added explicit instruction: "meeting_date = shareholder meeting date (AGM/EGM), NOT board meeting or filing date"
2. Added per-field `_source` attributes to force grounding
3. Added "Quote exact text, then extract" instruction

### Prompt 3.2 — Extraction Prompt (v2)
**What I asked:** Added the quote-then-extract pattern and per-field source attribution.

**What came back:** Much better — citations were grounded, and the model correctly distinguished filing dates from meeting dates.

**What I changed:** Added the "explicitly allow null" instruction: *"If a field cannot be determined, return null and add a flag. Do NOT guess."*

### Prompt 3.3 — Audit Prompt
**What I asked:**
```
Review this extraction against source documents for errors.
Check for: numerical errors, date inconsistencies, misattributed fields, missing info, hallucinations.
```

**What came back:** Caught the board resolution date discrepancy in event 2 (15-Sep board res vs 22-Sep EGM). Also verified arithmetic on all capital amounts.

**What I changed:** Made the audit response structured (corrections + additional_flags) so results could be programmatically applied.

---

## 4. Reconciliation

No LLM prompts used in this stage — it's pure deterministic validation logic. The key insight was comparing structured `CapitalAmount` objects rather than raw text strings, which correctly handles Indian number formatting (₹5,00,000 = 500000).

---

## 5. Rendering

No LLM prompts used — pure formatting logic. The footnote-style citation format (`[S1]`, `[S2]`) was chosen for readability in the Markdown table.

---

## 6. Iteration Notes

- **Total LLM calls per run:** ~12 (4 events × 2 passes for extraction + ~4 classification fallbacks)
- **Estimated cost per run:** ~$0.05 (using Claude Sonnet)
- **Key lesson:** The two-pass pattern (extract + audit) catches errors that a single-pass misses, at only 2x token cost
