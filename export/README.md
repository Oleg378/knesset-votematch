# export/ — where to look (for the web)

The only link between the data side (`pipeline/`) and the web (`web/`). The web reads nothing else and never calls Python.
Moving from v1 to v2: start with `V2_HANDOFF.md`.

## Files here

| File | What | Shipped to the browser |
|---|---|---|
| `V2_HANDOFF.md` | **Read first.** What changes in v2, the question order and the clarifying rule, the list-details format field by field, loading | — |
| `quiz_core.v2.json` | `flow` numbers, `core` order, the core statements — enough to start answering | yes, fetched first |
| `quiz_data.v2.json` | `params`, all statements, `directions`, `lists` with positions — for clarifying questions, trade-offs, Results | yes, fetched second |
| `quiz_bills.v2.json` | `mks`, `by_direction`, `bills` — only for List details and «Bills of one statement» | yes, fetched third |
| `quiz_data.v2.schema.json` | JSON Schema of the three files merged | no (tests) |
| `golden.v2.json` | Answer sets → expected ranking, notes, trade-off pairs, explanation lines, evidence order, question order («flow N» cases). The TS port must match to 1e-9 | no (tests) |
| `quiz_data.v1.json`, `quiz_data.v1.schema.json`, `golden.v1.json` | The current contract of the live site; kept until the web moves to v2 | v1 only |

## Elsewhere in the repo

| Where | What |
|---|---|
| `web/DATA_REQUESTS.md` | The channel between the web and the data side: #3 answer words, #4 question order, #5 everything in v2, #6 loading task |
| `pipeline/quiz_match.py` | Reference: closeness (cosine), coverage, notes, trade-offs |
| `pipeline/quiz_flow.py` | Reference: core order, `next_clarify`, `should_stop`; numbers in `FLOW` |
| `pipeline/quiz_report.py` | Reference: list details — `contributions()`, `explain()` (lines), `evidence()` (order) |
| `pipeline/quiz_cli.py` | The whole flow in the terminal: `python3 pipeline/quiz_cli.py --no-save` (reference UX) |
| `docs/QUIZ_MATCHING.md` | Formulas and why (Russian) |
| `docs/SHARED_UNDERSTANDING.md` | Customer decisions with dates (Russian) |

Regenerate everything here with `make data` (positions, then `pipeline/export.py`).
