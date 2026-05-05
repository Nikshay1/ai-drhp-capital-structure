# Open Questions & Flags

Total flags: **16**

## [!] WARNING (9)

- **Event:** `evt_01_2019_mar` | **Field:** `meeting_type`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_01_2019_mar` | **Field:** `meeting_type_source_doc`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_01_2019_mar` | **Field:** `meeting_type_source_quote`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_02_2021_aug` | **Field:** `meeting_type`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_02_2021_aug` | **Field:** `meeting_date`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_03_2023_jul` | **Field:** `capital_before.breakdown`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_03_2023_jul` | **Field:** `capital_after.breakdown`
  Audit: . Orig=None, Fixed=None

- **Event:** `evt_03_2023_jul` | **Field:** `capital_before`
  Continuity break: previous event (evt_02_2021_aug) capital_after = ₹1,000,000 but this event's capital_before = ₹1,000,000. Possible missing alteration between these events.

- **Event:** `evt_04_2025_jan` | **Field:** `capital_before.breakdown.num_shares`
  Audit: . Orig=None, Fixed=None

## [i] INFO (7)

- **Event:** `evt_incorporation` | **Field:** `event`
  Incorporation row inferred — no incorporation document provided. Capital derived from first alteration's 'before' amount.

- **Event:** `evt_01_2019_mar` | **Field:** `unknown`
  

- **Event:** `evt_02_2021_aug` | **Field:** `unknown`
  

- **Event:** `evt_02_2021_aug` | **Field:** `attachments`
  PAS-3 excluded: sh7_02_2021_aug/PAS3_Return_of_Allotment.md

- **Event:** `evt_03_2023_jul` | **Field:** `unknown`
  

- **Event:** `evt_04_2025_jan` | **Field:** `unknown`
  

- **Event:** `evt_04_2025_jan` | **Field:** `capital_after`
  Sub-division detected: FV ₹10 → ₹2 (ratio 5:1). Total authorised capital unchanged at ₹5,000,000.
