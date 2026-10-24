---
name: split-themes
description: Splitting a basket theme (bills about unrelated subjects) into parts — Opus proposes parts or transfers to existing themes, Sonnet assigns each bill to a part with a sign, then the parts go through the selection. Use for baskets found by screening, by a statement audit, or by step 2 of new-statements.
---

# Split themes

Procedure [У] 2026-10-16, applied as split stages: each run is a new stage N appended to `pipeline/labels.py` `LATER`
(`data/directions/split/planN.json`, `data/directions/labels/splitN_choice.jsonl`). A split theme becomes a **remainder**: no statement.

## Steps

1. **Input** — `BASKETS="d1 d2" TAG=<dir> NO_REASONS=1 PARTS=<n> python3 tools/basket_split_input.py`
   → `local/research/<dir>/input_K.json` (all bills by name, role, sign) and a fresh `catalog.md`. ~650 names per part.
2. **Parts** — `prompts/propose_parts.md`, Opus, one agent per part: keep / split into 2–4 parts (each ≥ 5 names; `same_as` an
   existing theme only if it is the same quantity by that theme's own «+»/«−») / technical.
   Audit splits: write the audit's parts into `out_1.json` in the same format (see `local/research/audit_split7/out_1.json`).
3. **Plan** — `TAG=<dir> STAGE=N CHUNK=30 python3 tools/basket_split_plan.py` → `planN.json`, `choice_K.json`.
   A transfer target that is itself split is expanded into its parts; a part «same as» its own basket is dropped.
4. **Assignment** — Sonnet instead of Jev (benchmark: `local/jef/directions/split/check/REVIEW.md`, Sonnet 26–27/30 vs Jev 24/30;
   use only the file mode below — the no-tools prompt mode scored 22–25):
   `TAG=<dir> PAR=3 python3 tools/basket_choice_run.py` (`claude -p --model sonnet`, Read/Write, `prompts/sonnet_choice.md`,
   notes 3 000 chars; stops itself at the subscription limit — rerun later, it resumes).
5. **Apply** — `TAG=<dir> STAGE=N python3 tools/basket_choice_apply.py`; append `(N, 'planN.json', 'splitN_choice.jsonl')`
   to `LATER`; `python3 pipeline/positions.py`.
6. **After** — registry: basket → `split`; «keep» → `new-statements`; technical → `technical`. Bills **transferred into statement
   themes** → `label-check` (`label_check_t5_input.py` with `STAGE=N`). Parts and other themes that now pass → `new-statements`.
   New nested pairs → `nested-themes`. `make check`.

## Pitfalls seen

- Signs: parts can be oriented against the basket; Sonnet sets the sign per part by the target theme's definition — never copy the basket sign.
- The 2026-10-20 misses: «keep» baskets not sent on; themes that started passing after transfers not sent on (`make check` I4 now catches both).
- Re-running `basket_split_plan.py` rewrites `planN.json` in `data/` — only for a new stage.
