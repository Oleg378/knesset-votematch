# Contract for the web: what to compute and what to show

_The only link between the data side (`pipeline/`) and the web (`web/`): the web reads `export/` and nothing else, never calls Python.
Python is the reference (`pipeline/quiz_match.py`, `quiz_flow.py`, `quiz_report.py`); the TypeScript port (`web/src/engine/`) must
reproduce `golden.v2.json` to 1e-9. Texts of the methodology and positions pages — `METHODOLOGY_PAGE.md`. No history here: the
current contract only; what changed and why is in `docs/WORKLOG.md`._

## 1. Files and loading

| File | What | Shipped |
|---|---|---|
| `quiz_core.v2.json` | `flow` (parameters of the question order), `core` (the first statements, in order), the core statements | yes, fetched first |
| `quiz_data.v2.json` | `params`, all statements (with `interest`, `area`, `sim_group`), `directions`, `lists` with `positions` and `composition` | yes, fetched second |
| `quiz_bills.v2.json` | `mks` (with `party_en`), `by_direction`, `votes`, `bills` — only for List details and «Bills of one statement» | yes, fetched third |
| `quiz_data.v2.schema.json` | JSON Schema of the three files merged | tests |
| `golden.v2.json` | answer sets → ranking, notes, trade-off pairs, explanation lines, evidence order, question order («flow N» cases) | tests |

Goal: the start page never waits for data, and a loader almost never appears.

| File | Size (gzip) | Contents | Needed by |
|---|---|---|---|
| `quiz_core.v2.json` | ~2 KB (1 KB) | `flow`, `core`, the core statements | the first `flow.core` questions |
| `quiz_data.v2.json` | ~217 KB | `params`, all statements, `directions`, `lists` with positions | clarifying questions, trade-offs, Results |
| `quiz_bills.v2.json` | ~1.8 MB | `mks`, `by_direction`, `bills` | List details and «Bills of one statement» only |

- The data is **not bundled** into the JS: the app shell (start page, styles, fonts) loads alone; the three files are fetched
  as static files from the site itself (CSP `connect-src 'self'` already allows it).
- Fetch order: start `quiz_core` immediately on page load (before the user presses Start), then `quiz_data` as soon as
  `quiz_core` has arrived, then `quiz_bills` as soon as `quiz_data` has arrived. The user is answering the core questions
  meanwhile, so the next file is normally ready before it is needed.
- A loader is shown only if the user reaches a screen whose file has not arrived yet (e.g. the first clarifying question
  before `quiz_data`, List details before `quiz_bills`), and only for that screen.
- All three files carry the same `version`, `generated` and `source_commit`; if they differ (a deploy mid-session), reload.
- Caching: give the files content-hashed names at build time (or short cache + revalidation); never `immutable` under a
  fixed name.

## 2. Order of questions (`pipeline/quiz_flow.py`)

All numbers come from `flow` in the export (now `core 8, clarify 7, trade 5`); **never hard-code them**.

1. **Core** — the same statements for everyone, in the exported order (`core`: list of `q`). Asked first. (How it was built —
   axes of the list × statement matrix, interest, one per area — is already applied; the web only reads the list.)
2. **Clarifying** — one at a time, chosen after each answer (`next_clarify(answers, shown)`; `shown` = statements already shown,
   **in order**, answered, skipped or «don't know»):
   - **ranking**: the ranked lists by closeness, exactly as on the Results screen (`match`, `ranked`), with `mult` = {} during
     the questions; only lists with `status == "ok"` take part below («evaluated lists»);
   - **candidates** = statements not shown yet, filtered in this order, each filter relaxed (ignored) if it would leave nothing:
     (a) `flow.sim_groups`: drop a candidate whose `sim_group` equals the `sim_group` of any shown statement (null never matches);
     (b) drop a candidate whose `area` equals the area of the **last shown** statement, or whose |r| with any shown statement is
         ≥ `flow.near_dup_r` — if that leaves nothing, keep only the area rule; if still nothing, skip both;
         (|r| = absolute Pearson correlation of the two statements' list values p over evaluated lists that have both, 0 if
         fewer than 3 such lists or a constant column — a 119 × 119 table the web can compute once from `lists[].positions`);
     (c) two-sided: take the top `flow.clarify_top` ranked lists that are evaluated; if at least 2 — keep candidates on which
         those lists have **clear** positions (|p| ≥ `params.CLOSE`, `n_mk` ≥ `MIN_CLEAR_MKS`, `n_names` ≥ `MIN_CLEAR_BILLS`)
         on both sides (some p > 0 and some p < 0); if that leaves nothing, keep all;
   - **score** of a candidate q (evaluated ranked lists only): leader = the first; contenders = the next up to `clarify_top − 1`
     lists whose closeness is within `flow.pair_gap` of the leader's; if none, the runner-up alone;
     `score = Σ_contenders |p_leader(q) − p_contender(q)| / (closeness_leader − closeness_contender + flow.pair_eps)` over
     contenders that have a position on q; the candidate needs a leader position and a score > 0;
     then `score ×= (interest / 5) ** flow.interest_alpha`;
     **before any ranking exists** (fewer than 2 evaluated ranked lists, e.g. nothing answered): score = population SD of p over
     all evaluated lists with a position (at least 2), times the same interest factor;
   - pick the highest score; ties → the lower statement number; no finite score → stop.
3. **Stop** after `clarify` clarifying questions (`flow.stop_gap` is null). An optional stopping rule exists (`should_stop`:
   stop when the leader is ahead of the second list by `stop_gap` after at least `min_questions`, at most `max_questions`);
   it is off — implement it only if `stop_gap` is not null.
4. **Trade-offs** — as in v1 (`tradeoffs()`), at most `flow.trade`.
5. **Results.** A button «Answer more questions» continues clarifying questions (same rule) until the pool ends, then Results again.

The counter on the question screen: `n / (core + clarify)` while the fixed number is used.
The 6 «flow N» golden cases give the exact sequences for six full answer sets: port `next_clarify` and check them first.

## 3. List details: what the result explains and in which format

Per list, everything comes from `quiz_report.contributions()` and `explain()`; golden `details[].items[]` has it field by field.

**Header:** list name (`name_en`), closeness `+0.35`, note (if any).

**Items.** For each answered statement (answer not 0, not «don't know») on which the list has a position:
- `contribution` = w × trade-off multiplier × u × p, where u = answer / 2 × key, p = list value. Positive → «Why it fits»
  (largest first), negative → «Why it doesn't fit» (most negative first). Section headers show the counts. 5 per section,
  then «Show all».
- `lines` — shown exactly as given, in order:
  1. the statement in quotes;
  2. `Your answer: <agree / strongly agree / …>. The record of the list's former MKs <points toward this statement | points against this statement | shows no clear position on this statement>.`
     (the third variant when the position is not clear: |p| < `params.CLOSE` (0.2), or fewer than `params.MIN_CLEAR_MKS` former MKs, or fewer than `params.MIN_CLEAR_BILLS` distinct bills (`n_names`); wording changed 2026-10-18);
  3. basis: `Basis: N bills sponsored by the list's former MKs — X your way, Y the other way; M votes on private bills, K votes on the other camp's bills[ and J votes on the government's own bills] on this topic.`
     or `Basis: no bills of their own on this topic, only M votes on private bills, K votes on the other camp's bills[ and J votes on the government's own bills] on this topic.`
     (M = `n_votes`, K = `n_other` of the list's position);
  4. optional: `Weight ×2: you chose this topic in a trade-off question.`;
  5. optional: `The list's side comes from how its former MKs voted, not from the bills they sponsored.`
     (when the list's own bills give nothing or point the other way);
  6. when line 2 says «points toward»: `This shows what their bills and votes pushed for, not whether they accept the price named in the statement.`
- `evidence` — the bills behind the item, already in display order (bills that explain the verdict first, then by the best
  list position of their sponsors). Each: `bill` (id → `bills[id]`: Hebrew name `name_he`, `knesset`; link =
  `params.BILL_URL` with `{id}` replaced), `sign`
  (+1 raises / −1 lowers the direction), `role` (main / secondary topic), `same` (true = same way as the user's answer, ✓;
  false = the opposite way, ✗), `authors` — [list position, English name] of the list's ex-MKs who sponsored it.

**Bills of one statement** (tap on an item): two groups, «Your way (N)» (`same` true) and «The other way (N)»; each line:
✓/✗ · Hebrew bill name linking to `params.BILL_URL` · `Knesset N` · `main / secondary topic` · `raises / lowers “<direction name_en>”` ·
`sponsored by: <name> (#<position> on the list)` (first two by list position). Bill names are never translated.

**Votes of the list's former MKs** (2026-10-19, `quiz_bills.v2.json` → `votes`): `votes[list][direction]` = rows
`[bill, sign, camp, for, against]` — the bills of that direction its former MKs voted on, with the bill's sign on the direction
(+1 raises / −1 lowers), whether the bill came from the MK's own camp (`own`, counted in V) or from the other camp (`other`, counted in
O), and how many of them voted for and against. These are exactly the votes behind the position. Name and Knesset: `bills[bill]`.
Suggested place: under «Bills of one statement», a third group «How its former MKs voted (N)», each line:
`Hebrew name · Knesset N · raises / lowers “<direction>” · for X, against Y · own camp’s bill / the other camp’s bill`. Not part of the
golden cases (no formula), plain display.

## 4. Golden v2

Same structure as v1 plus 6 flow cases («flow 0» … «flow 5»): a synthetic user's answers to every statement; `flow.core` and
`flow.clarifying` are the statements asked, in order; `answers` holds only the answers given to them, and `ranking`,
`tradeoffs`, `details` are computed on those. The TS port must match to 1e-9.

## 5. Composition of a list's record

`mks[].party_en` — the component party of the 2026 list the former MK runs with (Central Elections Committee candidate list; null = the list itself); `lists[].composition` — the same aggregated, most first: `[{"party_en": "Yesh Atid", "ex_mks": 17}, …]`. Proposed line on the List details screen: «Based on 19 former MKs: 17 from Yesh Atid, 2 from Be’Yahad» (whether and how to show it — the customer's decision).

## 6. Positions page

Structure and texts — `METHODOLOGY_PAGE.md`, section «Positions of the lists page»: the 123 statements × the evaluated lists, cell = measured side by the explanations' rule, click → the bills; the right-to-contest text with the GitHub issues link.
