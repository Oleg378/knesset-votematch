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

**Answer (data side, 2026-10-18):** the customer chose the UI words. `ANS` is now `agree` / `disagree` (and `strongly …`) in
`pipeline/quiz_report.py`; it reaches the web with the v2 export and its golden cases.

## 4. Question order in v2: core → clarifying → trade-offs (data side → web, 2026-10-18) [coming with v2, no action yet]
The customer approved a new flow: not every statement, but N core statements (same for everyone), then M clarifying ones
chosen one at a time from the answers so far, then up to T trade-offs; «answer more» continues clarifying questions.
Reference: `pipeline/quiz_flow.py` (`FLOW`, `core()`, `next_clarify()`), terminal UX in `pipeline/quiz_cli.py`.
v2 will carry `flow` (the numbers) and the core order; the clarifying choice must be ported to TS and is covered by golden
cases. Numbers must not be hard-coded on the web (now 8 + 7 + up to 5 trade-offs, decided 2026-10-18; may change). An optional
stopping rule (`should_stop`: stop_gap / min_questions / max_questions) exists but is off.
