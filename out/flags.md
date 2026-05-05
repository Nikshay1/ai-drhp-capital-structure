# Open Questions & Flags

Total flags: **6**

## [X] ERROR (1)

- **Event:** `evt_04_2025_jan` | **Field:** `capital_before`
  Arithmetic mismatch in before capital: sum(shares×FV) = ₹5,500,000 but total_rupees = ₹5,000,000

## [!] WARNING (2)

- **Event:** `evt_03_2023_jul` | **Field:** `capital_before`
  Continuity mismatch (breakdown differs): previous event (evt_02_2021_aug) capital_after and this event's capital_before both total ₹1,000,000 but share counts or face values differ. Verify extraction accuracy.

- **Event:** `evt_04_2025_jan` | **Field:** `capital_before`
  Continuity mismatch (breakdown differs): previous event (evt_03_2023_jul) capital_after and this event's capital_before both total ₹5,000,000 but share counts or face values differ. Verify extraction accuracy.

## [i] INFO (3)

- **Event:** `evt_incorporation` | **Field:** `event`
  Incorporation row inferred — no incorporation document provided. Capital derived from first alteration's 'before' amount.

- **Event:** `evt_02_2021_aug` | **Field:** `attachments`
  PAS-3 excluded: sh7_02_2021_aug/PAS3_Return_of_Allotment.md

- **Event:** `evt_04_2025_jan` | **Field:** `capital_after`
  Sub-division detected: FV ₹10 → ₹2 (ratio 5:1). Total authorised capital unchanged at ₹5,000,000.
