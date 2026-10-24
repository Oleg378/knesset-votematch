---
name: new-statements
description: Procedure for themes that pass the selection but have no quiz statement — duplicate/technical/basket screening, drafting, standard audit, label check, threshold, final duplicate check, customer approval, writing into statements.csv. Also moving a statement to a broad theme (rule (б)).
---

# New statements

Input: themes that pass `quiz_select.py`, are not remainders / technical, have no statement and no registry decision
(`make check` lists them as I4). Every outcome is written to `jef/directions/registry.csv`.

## Steps

1. **Material** — `DIRS=d1,d2,... TAG=roundN python3 tools/new_statements.py` → `local/research/new_statements_roundN/input.md`.
   For step 2 strip the «Lists …» lines and SD (blind to positions); copy the current statements to `statements.md`.
2. **Step 2: screening** — `prompts/step2_check.md`, two blind agents (A, B), parts of ≤ ~35 themes. Per theme: `duplicate` (qN or
   none: most voters answer both the same way for the same reason), `technical`, `basket`. Agreement decides; both say basket → basket;
   otherwise a 3rd check, majority per field. Outcomes:
   - duplicate → registry `duplicate`, then the theme's bills go to the **add check** of `label-check` (variant (б) [У]);
   - technical → registry `technical`;
   - basket → `split-themes`; parts that pass come back here; if no part reaches 5 names → registry `basket`;
   - clean → step 3. A customer decision overrides the agents (e.g. conversion therapy for minors is a separate question).
3. **Draft** — `prompts/draft.md` (rules: `jef/quiz/GUIDELINES.md`), one agent per ~20 themes. A theme that takes over a statement
   (rule (б)) is marked MOVE with the old text. `no_statement` → registry.
4. **Standard audit** — `DRAFTS=... TAG=roundN PARTS=k python3 tools/statement_audit.py build`, `prompts/audit.md`:
   keep / rewrite (broader text) / split (→ `split-themes`, parts back to step 2) / unsuitable.
5. **Label check** of every bill of the theme against the final text — `label-check` (`label_check_drafts_input.py`).
6. **Threshold** — `python3 pipeline/positions.py`; a theme that now fails is dropped and reported.
7. **Final duplicate check** — all new texts against each other and the current statements: `prompts/final_duplicates.md`, two agents,
   disagreements → a 3rd. Per pair keep one: an existing statement wins; between new ones the theme with more bills.
8. **Customer** — show every text verbatim (English as stored), grouped, with the duplicate choices; name statements by title.
9. **Write** into `jef/quiz/statements.csv` and add the row to `jef/quiz/statement_meta.csv` (interest 1–5, area, sim_group — the
   same blind agent tasks as in `local/research/flow_models/agents/PROMPT_interest.md`, `PROMPT_areas.md`, `PROMPT_fine.md`;
   two runs, agreement or tie-break) (next free `q`, `source`, `status=ok`, dated `change`; RU text from the draft if the
   audit did not rewrite it), registry `quiz`, then `release`. A new statement can create a nested pair with an existing one
   (`make check` I5) → `nested-themes`; the final duplicate check already answers the meaning question for that pair.

## Moving a statement (rule (б) of nested-themes)

Its old theme loses its bills to a broad theme that can carry a statement → the statement moves: same `q`, new `d`, text rewritten by
step 3 (MOVE) and audited; if the broad theme already has a statement — merge into it (audit whether its text covers the moved one) and
remove the moved statement with a note.

## Pitfalls seen

- Positions of lists are hidden from screening and audit; drafting may see them.
- A draft built on the theme name instead of the weighty bills fails the audit — the prompt says «built on what the weighty bills do».
- Keys may flip when a statement moves; titles must still match the new text (e.g. «Support for families with children»).
