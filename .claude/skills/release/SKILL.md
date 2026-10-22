---
name: release
description: Rebuilding and publishing the quiz data after any change — make data, make check, make test, commit order, removing statements that fail the threshold, updating the front handoff and the docs. Use at the end of every step that changes labels, themes or statements.
---

# Release

1. **Commit the inputs** first (labels, overrides, plans, `statements_v4.csv`, registry, coverage) — one topic per commit.
2. `make data` (positions → export v2 + golden). The export warns if inputs are uncommitted — then go back to 1.
3. `make check` — must print OK. A statement failing I1 is set to `status=removed` with a dated note (customer rule: remove and
   report, do not ask), registry updated, then `make data` again. I4 FAIL = a theme left without a decision → route it (quiz-pipeline).
4. `make test` (web tests incl. golden: TS port == Python reference).
5. Commit `export/` and `jef/positions/` separately («Export rebuilt: …»).
6. **Docs, only what changed**:
   - `docs/SHARED_UNDERSTANDING.md` — the decision (one line, date, [У]/[А]);
   - `docs/WORKLOG.md` — the step's outcome with numbers; open items under «Открыто»;
   - `docs/TECHNICAL.md` — the funnel / method if the method changed;
   - `export/WEB_CONTRACT.md` §0 — a short dated note for the web (ids added/removed, changed texts/titles/keys, core, sizes; facts only);
     §6 methodology texts if a listed topic changed status.
7. Report to the customer: what changed, statements removed (by title), what needs their decision. Never present a step as done while
   `make check` fails.
