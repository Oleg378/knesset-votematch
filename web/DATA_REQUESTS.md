# web/ → data: requests

Requests from the front end to the data side (pipeline/, export/). The web session never edits export/ itself.

## 1. Stray space in a list name (2026-10-17) [answered]
`lists[].name_en` for Likud: `"Likud , headed by Binyamin Netanyahu for Prime Minister"` — space before the comma. The web
shows `name_en` as given. If the CEC original has no such space, please fix it in `manual/` and re-export; if it does,
leave it and tell us.

**Answer (data side, 2026-10-17):** the space is in the CEC original (`local/evidence/cec/candidates-lists-26_en_saved-2026-10-11.html`).
Left as is: list names are the official CEC text. Any cosmetic cleanup would be a customer decision.

## 2. Lighter export in v2 (2026-10-17) [optional, not urgent]
`bills` is 1.38 MB of the 1.61 MB export (4033 bills). All `summary_en` are null (never shown), 1073 bills have empty
`sponsors`, and every `url` is the same prefix + `lawitemid`. A v2 could drop `summary_en` and store only the item id.
Gain after compression is modest (the export is ~189 KB gzip now), so only worth it together with another v2 change.

## 3. Answer wording in explanations (2026-10-18) [needs the customer's decision first]
The question screen now follows Figma: «Strongly agree · Agree · Disagree · Strongly disagree». The explanation lines
come from `pipeline/quiz_report.py` `ANS` (reproduced byte for byte via golden): «Your answer: somewhat agree.» If the
customer wants «agree» there, `ANS[1]`/`ANS[-1]` change in Python, golden is regenerated, and the web follows.
