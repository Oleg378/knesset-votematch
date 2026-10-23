---
name: label-check
description: Blind two-step check of bill labels against a statement's text — removing wrong labels, confirming sign flips on the full notes, and adding missing labels (add check). Use for any theme that gets or has a statement, and for any bills that newly enter a statement theme (transfers of a split, adds).
---

# Label check (remove / flip / add)

Rule [У] 2026-10-18/19: a label is **removed** when two blind checks say «not about the question» (if the 2nd says «borderline» —
a 3rd check, majority of three); a **sign flip** only if the 1st check and a check on the full notes (≤ 3 000 chars) agree; a label is
**added** only if two blind checks say «about» with the same sign. Checkers never see our label or sign.

## Steps (removal / flip)

1. **Material** — one of:
   - quiz statements: `QS=<q> TAG=<tag> PARTS=<n> python3 local/research/scripts/core_full_input.py`
   - draft statements: `DRAFTS=... AUDIT=... TAG=<tag> PARTS=<n> python3 local/research/scripts/label_check_drafts_input.py`
   - bills moved into quiz themes by split stage N: `STAGE=N python3 local/research/scripts/label_check_t5_input.py`
   → `local/research/label_check_q<tag>/items_K.md`, `key.csv`. Parts of ≤ ~90 items.
2. **1st check** — `prompts/check1.md` (paths: `items_K.md` → `result_K.csv`), Opus, one agent per part.
3. `python3 local/research/scripts/label_check_step.py <tag> merge1` → candidates + controls (≥ a third) and `flip_in.csv`.
   Large `check2_items.md`: split into parts of ~70 (`## C…` sections) and concatenate the results into `check2_result.csv`.
4. **2nd check** — `prompts/check2.md`. **Sign**: `flip_in.csv` with the `q` column emptied (draft ids are not in statements.csv) →
   `python3 local/research/scripts/flip_check.py <in.csv> <dir>` → `prompts/sign_full_notes.md` → `flip_result.csv`.
5. `label_check_step.py <tag> merge2` → **3rd check** of «borderline» — `prompts/check3.md`.
6. `SRC="<what, date>" label_check_step.py <tag> apply` → `overrides.json` remove / flip, `borderline_resolved.csv`.
7. Append the checked (bill, theme) pairs to `jef/directions/labels/label_check_coverage.csv`; `make data`; `make check`.

## Add check

`add_check_input.py` (duplicate themes → the duplicated statement; `DUPS=d:q,...` `TAG=` for a subset) → 1st check with
`prompts/check1.md` → `add_check_step.py <dir> merge1 <parts>` (candidates = «about» with a sign + «not_about» controls) → 2nd check
with `prompts/check2.md` → `SRC=... add_check_step.py <dir> apply` → `overrides.json` «add».

## Pitfalls seen

- Controls must come back «about» (removal) / «not_about» (add); if they don't, stop and report — the prompt or the material is wrong.
- A bill whose notes are cut off gets a guessed sign: the flip rule exists for that — never flip on the 1st check alone.
- After the check, the theme may fail the selection → the statement is removed and reported (customer rule).
- Keys of a split part change: coverage counts a check made under the theme the part was split from (I6 uses the lineage).
