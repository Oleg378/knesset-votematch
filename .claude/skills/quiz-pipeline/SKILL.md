---
name: quiz-pipeline
description: Map of the theme → statement cycle of this project (labels, theme splits, nested themes, new statements, label checks, release). Use before any work that changes labels, themes or quiz statements, to pick the right procedure skill and to know the exit checks.
---

# Quiz pipeline: the map

Terms (use them, do not invent others): **законопроект** (bill), **тема** (theme = direction, a quantity a bill moves «+»/«−»),
**основная / второстепенная тема** (main / secondary label), **вопрос по теме** (statement). Bills are counted **by name without the
year** (a re-submission is one bill). Decisions live in `docs/SHARED_UNDERSTANDING.md`; the work log in `docs/LABEL_CHECK_PROGRESS.md`.

## The cycle (each step is a skill)

| Step | Skill | Leaves behind |
|---|---|---|
| Labels of a theme wrong / bills newly in a quiz theme | `label-check` | `overrides.json` remove / flip / add, `label_check_coverage.csv` |
| A theme whose bills are about unrelated things (basket) | `split-themes` | `jef/directions/split/planN.json`, `labels/splitN_choice.jsonl`, `labels.LATER` |
| One theme lies mostly inside another (≥ 50 % of the smaller) | `nested-themes` | `labels/nested_removals.json` |
| A theme passes the selection and has no statement | `new-statements` | rows in `jef/quiz/statements_v4.csv` |
| Agent tasks of any step | `subagents` | prompt files, blind inputs, results |
| Rebuild, check, publish | `release` | `export/`, commits, front note |

## Routing rule — every theme ends somewhere

After **any** change of labels or themes, every theme that passes the selection (`pipeline/quiz_select.py`) must either carry a
statement or have a decision in `jef/directions/registry.csv` (duplicate / split / basket / technical / no_statement / dropped_dup;
`pending` while in a procedure). Typical misses of the 2026-10-20 cycle — check them explicitly:
- a split agent marks a basket «keep» → the theme goes to `new-statements`, it does not stop there;
- transfers of a split make *other* themes pass the selection → they go to `new-statements` too;
- step 2 of `new-statements` marks a theme «basket» → `split-themes`, then its parts back to `new-statements`;
- a later split or a new statement creates nested pairs → `nested-themes` again for the new themes;
- a theme that was a duplicate keeps its bills out of the quiz until its bills are add-checked into the duplicated statement.

## Order and state

- `pipeline/labels.py` applies, in order: Jev labels → split stages 1…N (`LATER`) → `overrides.json` labels → remove → flip → add →
  `nested_removals.json`. A new stage is appended to `LATER`; never insert in the middle.
- Positions on disk (`jef/positions/`) change when labels change. A rule that needs the state *before* a change must read a frozen
  copy (example: `local/research/theme_overlap/passing_before.json` for rule (а) of `nested-themes`).
- Applied steps are not re-run: their files in `jef/` are the source of truth. Scripts write to `jef/` only with an explicit flag.

## Exit checks of every step

`make check` (pipeline/check_invariants.py) — must print OK before you report a step done or commit an export:
I1 statements pass the selection · I2 one theme ↔ one statement · I3 no statement on a remainder / technical theme ·
I4 every passing theme has a statement or a registry decision · I5 no nested pair among statement themes · I6 every bill label on a
statement theme was label-checked · I7 export = current statements.

## Customer rules that apply everywhere (see CLAUDE.md)

- Name questions **by their English text / title**, never by number. Show both themes in pair tables. Russian in chat.
- A statement whose theme fails the selection is **removed and reported**, not asked about.
- New criteria, thresholds or methods: list options and ask (P1). An obvious engineering default: take it and say so.
