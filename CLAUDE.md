# elections-research — quiz for the 26th Knesset election (27.10.2026)

A voter quiz: the user answers statements, the site shows which 2026 lists are closest. A list's position comes **only** from
what its candidates who are former MKs did in Knessets 24–25: bills they sponsored and how they voted.

## Read first
- `docs/SHARED_UNDERSTANDING.md` (SU) — terms and decisions with status: [У] approved by the customer, [А] agent's proposal,
  [О] open. Decisions are referred to as «SU п. N».
- `.claude/skills/quiz-pipeline/` — the map of the theme → statement cycle and its exit checks; each step is a skill
  (`label-check`, `split-themes`, `nested-themes`, `new-statements`, `subagents`, `release`) with its canonical prompts.
- `docs/LABEL_CHECK_PROGRESS.md` — the work log (what was done, numbers, «Открыто»).
- `docs/QUIZ_MATCHING.md` — how answers become closeness (the formula the web reproduces).
- `docs/METHOD_AUDIT.md` — the whole chain from raw data to the quiz, with numbers.

## Principles (mandatory)
- **P0 — uniformity.** One rule for all lists, directions and statements. No exceptions for a single case.
- **P1 — do not decide alone on ambiguity.** Thresholds, criteria, methods, wording that changes meaning: list the options
  and ask the customer. Engineering choices with an obvious default: take it and say so.
- Official sources only (Knesset OData, CEC). No scraping around Cloudflare.
- Only technical statements (no value for the voter's choice) may be removed; a meaningful one with a problem is rewritten or split.

## Structure
| Path | What |
|---|---|
| `pipeline/` | Python: fetch (OData, CEC), `build/` → `knesset.duckdb`, Jev labeling, positions, quiz selection/matching, **export** |
| `web/` | Front end: React + Vite + TypeScript static SPA. Reads only `export/` (v1 now; moving to v2) |
| `export/` | **The data contract** (in git): v2 = `quiz_core / quiz_data / quiz_bills.v2.json`, one schema, `golden.v2.json`, `V2_HANDOFF.md`; v1 kept until the web moves |
| `jef/` | Production data: directions and labels (`jef/directions/`), theme registry (`jef/directions/registry.csv`), positions (`jef/positions/`), statements (`jef/quiz/`) |
| `manual/` | Tables kept by hand: CEC lists and candidates, candidate ↔ MK matching, English MK names |
| `local/` | Research behind the decisions: experiments, checks, early approaches (`local/README.md`). Published selectively (scripts, texts, small result tables; no people's answers) — `local/` stays ignored, add new files with `git add -f`. **Not production**: do not import from it; the procedure scripts in `local/research/scripts/` named by the skills are run, never imported |
| `docs/` | Methodology, decisions, audits (Russian — the working language) |
| `data/`, `knesset.duckdb` | Raw downloads and the database. Not in git |

## Commands
```bash
make data      # pipeline/positions.py, then pipeline/export.py -> export/
make check     # invariants: statements pass the selection, one theme ↔ one statement, every passing theme routed (registry), …
make test      # web tests, including the golden cases (TypeScript port == Python reference)
make web-dev   # local dev server
python3 pipeline/quiz_cli.py --no-save --answers local/jef/quiz/pilot_answers_filled.csv   # terminal quiz (reference UX)
python3 pipeline/quiz_select.py   # which directions pass the selection criteria
```
Python deps: `requirements.txt` (pinned). Node: `web/package-lock.json`.

## Data contract
- `pipeline/export.py` writes the v2 files (`quiz_core`, `quiz_data`, `quiz_bills`), validated together against `export/quiz_data.v2.schema.json`.
- The front end never reads raw data and never calls Python.
- Changing the formula or the structure → bump the version (`v2`, new schema, new golden file). Never change v1 silently.
- `export/golden.v2.json` (v1 until the web moves): answer sets → expected ranking, question order (flow cases), coverage, notes, trade-off pairs, explanations and evidence order,
  computed by `pipeline/quiz_match.py` + `pipeline/quiz_report.py`. Python is the reference; the TS port must match (1e-9).

## Do not change without a customer decision
- The position formula (SU п. 27.2–27.3: A = mean sign of sponsored bills, not centered, V = vote residual weight 0.25, list = mean of ex-MKs).
- Matching: cosine, K = 0 (no shrinkage), weights 1/n per shared direction, coverage threshold 0.5, trade-offs (≤5, ×2, one per list, only if
  they change the top 5) — `docs/QUIZ_MATCHING.md`.
- Statement texts and keys (`jef/quiz/statements_v4.csv`), statement numbers (stable; gaps allowed).
- Question order (`pipeline/quiz_flow.py` FLOW, [У] 2026-10-21): core = axis markers × interest, one per area; clarifying = contending pair;
  statement metadata `jef/quiz/statement_meta.csv` (interest, area, sim_group) is used only for the order of questions.
- Selection criteria (`pipeline/quiz_select.py`), labels and overrides (`jef/directions/labels/`).
- What results show: no coalition/opposition layer, no number of MKs; only two notes (few former MKs: N; position known for
  only N% of your answers).

## Language
- Product: English. Bill names: Hebrew original only, never translated. List names: official English (CEC). MK names:
  transliteration from `manual/mk_names_en.csv`.
- Russian: chat with the customer and working docs only.

## Working with the customer (lessons of 2026-10-20/21)
- Russian in chat. Name statements by their **English title or text as stored**, never by number; never translate them.
- Use the project's terms only (законопроект, тема, основная / второстепенная тема, вопрос по теме); do not coin new ones. Write
  organization and law names in full, no abbreviations.
- Pair tables show **both** themes in every row. Interim messages: 1–2 lines; detail only when a decision is needed.
- A statement whose theme fails the selection is removed and reported — not asked about.
- Before reporting a step done: `make check` must print OK.

## Working rules
- Small tasks with a checkable result (one screen, one component, one test against the reference).
- Do not delete user data: `jef/quiz/sessions/` (gitignored; use `--no-save` for test runs).
- Budget: the customer is on the Max subscription (since 2026-10-20). Jev is out of credits: labeling goes to Sonnet subagents, each task type checked first on a benchmark with a known Jev score. Batch agent work (4–5 themes per agent).
- Commit only when asked or at the end of an agreed step; one topic per commit.
