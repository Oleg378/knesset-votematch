# v2 for the web: what changes and how results are explained

Data side → web, 2026-10-18. The v2 export is **generated** as three files (section 5 «Loading»): `quiz_core.v2.json`,
`quiz_data.v2.json`, `quiz_bills.v2.json`; one schema for their merge (`quiz_data.v2.schema.json`); `golden.v2.json` (34 cases,
6 of them «flow N» with `flow.core` and `flow.clarifying`) — tests only, never shipped. v1 files are left as they were. Python stays the reference: `pipeline/quiz_match.py` (closeness, trade-offs),
`pipeline/quiz_flow.py` (order of questions), `pipeline/quiz_report.py` (explanations); `pipeline/quiz_cli.py` runs the whole
flow in the terminal. Decisions are in `docs/SHARED_UNDERSTANDING.md` (Russian).

## 1. What changes

| Area | v1 | v2 |
|---|---|---|
| Files | one `quiz_data.v1.json` (1.6 MB), bundled | three files fetched in order (section 5); bills lose `url` (built from `params.BILL_URL`) and `summary_en` |
| Statements | 65 | 78 (`q` ids stable, gaps allowed; removed ones are gone, new ones up to q105). Texts and titles changed for many |
| List position P | (A + 0.25 V) / weights, A centered | P = A + 0.25 V + 0.25 O; A (sponsored bills) is **not centered**; O = votes against the other camp's bills (2026-10-18). Comes ready in `lists[].positions` — the web only reads P |
| Ranking | coverage ≥ MIN_COVERAGE | also `ex_mks ≥ params.MIN_EX_MKS` (2): a list with one former MK goes to «Not ranked» with its note (2026-10-18) |
| Shrinkage | p = P · e / (e + K), K = 2 | **K = 0: p = P**. Keep the formula generic and read K from `params` |
| Question order | every statement in file order | **core → clarifying → trade-offs** (section 2) |
| Trade-offs | up to MAX_TRADE | unchanged algorithm; the limit comes from `flow.trade` |
| Answer words in explanations | «somewhat agree / somewhat disagree» | **«agree / disagree»** (same as the buttons); «strongly …» unchanged |
| Explanation caveat | «… positions are measured relative to the average MK» | **removed** (no longer true) |
| |p| < CLOSE | «close to the average MK on this statement» | **«has no clear position on this statement»** (customer, 2026-10-18); CLOSE = 0.2 (measured: below it the side is a coin flip between the two Knessets) |

Nothing changes in: cosine closeness, weights 1/n per direction (a/b pairs), coverage threshold 0.5 and the «Not ranked» block,
the two notes, what is not shown (no coalition/opposition, no number of MKs).

## 2. Order of questions (`pipeline/quiz_flow.py`)

All numbers come from `flow` in the export (now `core 8, clarify 7, trade 5`); **never hard-code them**.

1. **Core** — the same statements for everyone, in the exported order (`core`: list of `q`). Asked first.
2. **Clarifying** — one at a time, chosen after each answer (`next_clarify`):
   - candidates: statements not shown yet (answered, skipped or «don't know» all count as shown);
   - compare lists: the top `clarify_top` (4) lists of the current ranking (ranked lists only, as in Results); if fewer than 2
     are ranked (e.g. nothing answered yet), all lists with status `ok`;
   - pick the candidate with the largest population SD of the compared lists' values p on it (only lists that have a position;
     at least 2); ties → the lower statement number; none left → stop.
3. **Stop** after `clarify` clarifying questions (`flow.stop_gap` is null). An optional stopping rule exists (`should_stop`:
   stop when the leader is ahead of the second list by `stop_gap` after at least `min_questions`, at most `max_questions`);
   it is off — implement it only if `stop_gap` is not null.
4. **Trade-offs** — as in v1 (`tradeoffs()`), at most `flow.trade`.
5. **Results.** A button «Answer more questions» continues clarifying questions (same rule) until the pool ends, then Results again.

The counter on the question screen: `n / (core + clarify)` while the fixed number is used.

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
     (the third variant when |p| < CLOSE; wording changed 2026-10-18);
  3. basis: `Basis: N bills sponsored by the list's former MKs — X your way, Y the other way; M votes on private bills and K votes on the other camp's bills on this topic.`
     or `Basis: no bills of their own on this topic, only M votes on private bills and K votes on the other camp's bills on this topic.`
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

## 4. Golden v2

Same structure as v1 plus 6 flow cases («flow 0» … «flow 5»): a synthetic user's answers to every statement; `flow.core` and
`flow.clarifying` are the statements asked, in order; `answers` holds only the answers given to them, and `ranking`,
`tradeoffs`, `details` are computed on those. The TS port must match to 1e-9.

## 5. Loading (customer, 2026-10-18)

Goal: the start page never waits for data, and a loader almost never appears.

| File | Size (gzip) | Contents | Needed by |
|---|---|---|---|
| `quiz_core.v2.json` | ~2 KB (1 KB) | `flow`, `core`, the core statements | the first `flow.core` questions |
| `quiz_data.v2.json` | ~120 KB (27 KB) | `params`, all statements, `directions`, `lists` with positions | clarifying questions, trade-offs, Results |
| `quiz_bills.v2.json` | ~1.2 MB (180 KB) | `mks`, `by_direction`, `bills` | List details and «Bills of one statement» only |

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
