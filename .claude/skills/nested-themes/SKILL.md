---
name: nested-themes
description: Removing double counting between themes where one lies mostly inside another — the 50 % rule, the meaning check (would a voter see two different questions), strategies 1/2 and rules (а)/(б), customer overrides. Use after any split or relabeling that can create nested pairs, and when make check reports I5.
---

# Nested themes

Rule [У] 2026-10-20: a pair «narrow — broad» is nested when ≥ 50 % of the narrow theme's bills (by name, ≥ 5 shared) are also in the
broad one. By meaning:
- **strategy 1** — a voter sees two different questions → the narrow theme stays, the shared bills leave the **broad** theme;
- **strategy 2** — the same question → the shared bills leave the **narrow** theme (it effectively disappears).
- **Rule (а)**: strategy 2 only if the broad theme can carry a statement (passes the selection *before* the removals, is not a remainder
  or technical); otherwise strategy 1. The pre-removal selection is frozen in `local/research/theme_overlap/passing_before.json`.
- **Rule (б)**: if strategy 2 empties a statement's theme, the statement moves to the broad theme (`new-statements`, MOVE) or merges
  with the broad theme's statement.
- Customer decisions per pair override all of this: `local/research/theme_overlap/nested_customer.csv`.

## Steps

1. Pairs — `python3 tools/theme_overlap.py` (all themes) → `nested_small_in_big.csv`; for a single new pair compute it directly.
2. Blind input — `python3 tools/nested_pairs_input.py` (names and «+»/«−» only, shuffled).
3. Meaning check — `prompts/meaning_check.md` (the customer-approved file), two agents; disagreements and «borderline» →
   `prompts/meaning_check_third.md` (forced choice). Decision: two agreeing checks, otherwise the 3rd check.
4. `python3 tools/nested_apply.py merge` / `final` → `nested_decision.csv`, `nested_removals.computed.json`.
   Show the customer the strategy table (`nested_report.py`: both themes in every row, sections by strategy and by rule (а)).
5. After approval: `APPLY=1 ... nested_apply.py final` writes `jef/directions/labels/nested_removals.json`. For a few new pairs,
   append items to that file instead (see the «post-stage6» items) — never recompute the whole file: it was computed on the labels of
   2026-10-20.
6. `python3 pipeline/positions.py`; statements that lost the selection → rule (б) or removal; `make check` (I5 must be clean).

## Pitfalls seen

- The meaning prompt must have **one** criterion. «…or a part/example of it» made every nested pair «same»; «can a
  voter hold different views» made 98 % «different» (archived under `local/research/theme_overlap/`). The approved file plus the customer's
  reviewed decisions is the reference.
- Never use correlation of list positions to judge sameness: almost all themes correlate on the left–right axis.
- Strategy 2 into a theme with no statement drops bills out of the quiz — rule (а) exists for that.
