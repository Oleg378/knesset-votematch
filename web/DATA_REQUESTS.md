# web/ → data: requests

Requests from the front end to the data side (pipeline/, export/). The web session never edits export/ itself.

**Status 2026-10-23:** everything below is answered or superseded by `export/WEB_CONTRACT.md` and `export/METHODOLOGY_PAGE.md`; the engine, state and loader are on the three current data files (contract §1), the question order and the v2 explanations are ported and pass `golden.v2.json` (items 4, 6, 9, 11 in the logic); the screens are not wired yet (customer's decision, visual work on another machine); 12 — the votes group — and the methodology texts of 10 are still to show. New requests go above this line.

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

**Answer (data side, 2026-10-18):** done in v2: bills have no `url` (link = `params.BILL_URL` with `{id}`) and no `summary_en`.

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

## 5. Everything that changes in v2, and the format of list details (data side → web, 2026-10-18) [read before v2]
`export/V2_HANDOFF.md`: 89 statements, the new position formula (A not centered, K = 0), the question order with its exact
clarifying rule and numbers from `flow`, answer words, the removed caveat, the one wording still pending («close to the average
MK»), and the list-details format field by field (header, items, lines, evidence, bills of one statement). v2 is not generated
yet; v1 stays the contract until then.

## 6. Load data without blocking the start page (data side → web, 2026-10-18) [task, customer's request]
Now the 1.6 MB export is bundled into `App-*.js`, so nothing shows until it loads. v2 is split into three files
(`quiz_core.v2.json` ~2 KB, `quiz_data.v2.json` ~120 KB, `quiz_bills.v2.json` ~1.2 MB). Task: do not bundle the data; the
start page loads on its own; fetch the three files in this order from page load — core, then data, then bills — while the user
answers the core questions; show a loader only on a screen whose file has not arrived yet. Details: `export/V2_HANDOFF.md`
section 5 «Loading».

## 7. Where to look (data side → web, 2026-10-18)
`export/README.md` lists every file of the contract and where the reference code is. Start with `export/V2_HANDOFF.md`.

## 8. Data update (data side → web, 2026-10-18) [no code change]
The v2 export was regenerated: the number of statements comes from the export (76 on 2026-10-18; some removed, `q105` added; ids stay stable), a different core. Same format and
schema; golden cases regenerated. Nothing to change on the web — just make sure nothing assumes a fixed number of statements.

## 9. v2 changes after the external audit (data side → web, 2026-10-18) [port before v2 goes live]
- Ranking: a list ranks only if `ex_mks >= params.MIN_EX_MKS` (2) as well as coverage; otherwise it goes to «Not ranked» with its note.
- List details lines 2, 3, 5 changed and line 6 added — exact texts in `export/V2_HANDOFF.md` §3; line 3 uses the new `n_other` field.
- `flow.core_one_sided` added (the core is precomputed in the export; nothing to compute). Golden regenerated.

## 10. Methodology page texts (data side → web, 2026-10-18) [content]
Texts for the methodology / FAQ page are in `export/V2_HANDOFF.md` §6 (topics not in the quiz and why, where positions come from,
lists with one former MK, the answer scale, «no clear position», limitations). `params.CLOSE` is **0.2** (a short-lived 0.3 was reverted the same day); a position is clear only if also `n_mk >= params.MIN_CLEAR_MKS` and `n_names >= params.MIN_CLEAR_BILLS` (V2_HANDOFF §3).

## 11. Show closeness rounded to one decimal (customer, 2026-10-18) [task]
Results and list details: show closeness with one decimal (`+0.8`, not `+0.83`). The ranking order stays exactly as computed
(from the unrounded values); equal rounded values next to each other are expected and fine. Reason: the data and the analysis do not
support more precision (limitations — `export/V2_HANDOFF.md` §6, «Limitations»). The intro line may say «about as close» for equal
values; no other change.

## 12. How the list's former MKs voted (data side → web, 2026-10-19) [task]
New in `quiz_bills.v2.json`: `votes[list][direction]` = `[bill, sign, camp, for, against]` — the votes behind the list's position on
that statement. Format and suggested display (a third group «How its former MKs voted» under «Bills of one statement»):
`export/V2_HANDOFF.md` §3. Display only, no formula, not in golden.
