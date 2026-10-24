# pipeline/ — local rules

Python 3.10, deps pinned in `../requirements.txt`. Scripts are run from the repo root (`python3 pipeline/x.py`); each one
finds the root as the parent of its own folder. Modules import each other by bare name (`import quiz_match as qm`).

## Order
1. Fetch: `export_votes.py`, `fetch_bills.py`, `bill_texts.py` (Knesset OData, Israeli IP only), `cec_parse.py`, `cec_match.py`.
2. Build: `build/build.py` → `knesset.duckdb` (SQL layers in `build/`).
3. Label: Jev runs (`jev_label.py`, `jev_packages.py`, `jev_split.py`, stages 1–4) → `jef/directions/labels/`. Jev credits are gone
   (2026-10-20): later split stages (5–9, `plan5…9.json`) were assigned by Sonnet (`tools/basket_choice_run.py`,
   skill `split-themes`). `labels.py` applies, in order: Jev labels → split stages (`LATER`, append only) → overrides labels → remove →
   flip → add → `nested_removals.json`.
4. Positions: `positions.py` → `jef/positions/`.
5. Quiz: `quiz_select.py` (criteria), `quiz_match.py` (closeness, trade-offs), `quiz_flow.py` (order of questions: core →
   clarifying → trade-offs, numbers in FLOW), `quiz_report.py` (explanations), `quiz_cli.py` (terminal quiz — the reference UX).
6. Export: `export.py` → `export/` (three data files + schema + golden cases). Run `make data` after any change in 3–5.
7. Check: `check_invariants.py` (`make check`) after every stage; `build_registry.py` built `jef/directions/registry.csv` once —
   new decisions are written into the registry, the builder is not re-run over it.

## Rules
- `quiz_match.py`, `quiz_flow.py` and `quiz_report.py` are the reference implementation for the web. A change there changes the golden cases:
  regenerate `export/`, and the web tests must be updated in the same commit (and, if the structure changes, the schema and the contract).
- Every user-facing string produced here is English (see root CLAUDE.md «Language").
- Decisions are marked in comments with the SU status: `[У] date` approved, `[А]` agent's proposal.
