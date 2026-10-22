# v2 for the web: what changes and how results are explained

Data side → web, 2026-10-18; updated 2026-10-21 (section 0). The v2 export is **generated** as three files (section 5 «Loading»): `quiz_core.v2.json`,
`quiz_data.v2.json`, `quiz_bills.v2.json`; one schema for their merge (`quiz_data.v2.schema.json`); `golden.v2.json` (34 cases,
6 of them «flow N» with `flow.core` and `flow.clarifying`) — tests only, never shipped. v1 files are left as they were. Python stays the reference: `pipeline/quiz_match.py` (closeness, trade-offs),
`pipeline/quiz_flow.py` (order of questions), `pipeline/quiz_report.py` (explanations); `pipeline/quiz_cli.py` runs the whole
flow in the terminal. Decisions are in `docs/SHARED_UNDERSTANDING.md` (Russian).

## 0b. Update 2026-10-22 — position formula: government bills count for both camps (V4)

- **Formula**: P = A + 0.25 V + 0.25 O + **0.25 G**; G = a coalition MK's votes on the government's own bills (mirror of O); votes on
  the budget packages (חוק ההסדרים) count for nobody. The web only reads P — nothing to compute; `e` now includes G votes.
- **Statements: 117** — removed q66 «Support for families with children» and q142 «Power of labor unions» (fail the selection
  after the change). **Core changed**: 45, 7, 37, 63, 49, 40, **15**, 4 (q9 → q15). Read both from the export.
- `lists[].positions[d]` has a new required field **`n_gov`** (votes on the coalition's own government bills); `votes` «own» now
  includes government bills of the MK's camp (a bill with no `sponsors` is a government bill).
- Explanation basis line (section 3, golden `details[].items[].lines`): «M votes on private bills, K votes on the other camp's bills
  and J votes on the government's own bills on this topic» — the last clause only when J > 0.
- Methodology page (section 6): the sentence on government bills; «Power of labor unions» and «Support for families with children»
  move to the topics outside the quiz. 13 topics newly pass the selection and are in the new-statements procedure.
- `golden.v2.json` regenerated.

## 0a. Update 2026-10-21, evening — question order changed (`pipeline/quiz_flow.py`, section 2; schema extended)

- **Core changed** (`core` in `quiz_core.v2.json`): 45, 7, 37, 63, 49, 40, 9, 4 — markers of the main axes of the list × statement
  matrix, weighted by voter interest, one per area. Read it from the export; do not hard-code.
- **Clarifying questions: new rule** (section 2): the candidate that best separates the current leader from the lists close behind
  it, among statements on which the compared lists stand on both sides, weighted by interest, skipping the previous question's
  area and any statement that feels like one already asked (`sim_group`). The old «max SD among the top 4» is gone.
- **Statements carry three new fields** (`quiz_data.v2.json` `statements[]`, required): `interest` (1–5), `area` (string),
  `sim_group` (string or null). They are used only for the order of questions, never for closeness.
- **`flow` has new keys** (`core_axes`, `core_slots`, `core_min_interest`, `core_area_cap`, `interest_alpha`, `pair_gap`,
  `pair_eps`, `near_dup_r`, `same_area_in_row`, `sim_groups`); `core_r_max`, `core_gov_share`, `gov_r`, `core_one_sided`,
  `core_axes`, `core_slots`, `core_min_interest`, `core_area_cap` are informational (already applied in `core`).
- `golden.v2.json` regenerated: the 6 «flow N» cases now follow the new rule (same core for all, different clarifying sequences).
- Trade-offs, closeness, explanations, the «answer more» button: unchanged.
- **TypeScript port already written by the data side:** `web/src/engine/flow.ts` (`nextClarify`, `shouldStop`, `rankedLists` on
  the v2 shape; self-contained, the v1 engine is untouched) with `web/src/engine/flow.test.ts` — the six flow cases and the
  v2 ranking of all 34 cases pass. Wire it into the screens when the web moves to v2; do not re-port.

## 0. Update 2026-10-21 (data only; schema, files and algorithms unchanged)

- **119 statements** (was 74 in the previous export): new `q` ids **q109–q157**; removed q1, q16, q61, q107 (gone from the export). `q` stays stable — never map by position.
- Changed texts (and keys where noted) of kept ids: **q52** (key +), **q64** — new title «Immunity of elected officials», **q66** — new title «Support for families with children» (key +). Take texts, titles and keys only from the export.
- **Core changed** (`core` in `quiz_core.v2.json`): 2, 3, 63, 14, 7, 20, 81, 117. Read it from the export; do not hard-code.
- New direction ids have suffixes such as `1s1`, `163p2`, `256s3p2` — treat `d` as an opaque string.
- Sizes: `quiz_data.v2.json` ≈ 217 KB, `quiz_bills.v2.json` ≈ 1.8 MB (6 422 bills). `golden.v2.json` regenerated (34 cases); the TS port must match it again.
- Methodology page (section 6): the lists of topics not in the quiz were updated.

## 1. What changes

| Area | v1 | v2 |
|---|---|---|
| Files | one `quiz_data.v1.json` (1.6 MB), bundled | three files fetched in order (section 5); bills lose `url` (built from `params.BILL_URL`) and `summary_en` |
| Statements | 65 | 119 (`q` ids stable, gaps allowed; removed ones are gone, new ones up to q157). Texts and titles changed for many |
| List position P | (A + 0.25 V) / weights, A centered | P = A + 0.25 V + 0.25 O + 0.25 G; A (sponsored bills) is **not centered**; O = votes on the other camp's bills (2026-10-18); G = the coalition's votes on its own government bills (2026-10-22); budget packages count for nobody. Comes ready in `lists[].positions` — the web only reads P |
| Ranking | coverage ≥ MIN_COVERAGE | also `ex_mks ≥ params.MIN_EX_MKS` (2): a list with one former MK goes to «Not ranked» with its note (2026-10-18) |
| Shrinkage | p = P · e / (e + K), K = 2 | **K = 0: p = P**. Keep the formula generic and read K from `params` |
| Question order | every statement in file order | **core → clarifying → trade-offs** (section 2) |
| Trade-offs | up to MAX_TRADE | unchanged algorithm; the limit comes from `flow.trade` |
| Answer words in explanations | «somewhat agree / somewhat disagree» | **«agree / disagree»** (same as the buttons); «strongly …» unchanged |
| Explanation caveat | «… positions are measured relative to the average MK» | **removed** (no longer true) |
| |p| < CLOSE | «close to the average MK on this statement» | **«has no clear position on this statement»** (customer, 2026-10-18); a position is clear when |p| ≥ `params.CLOSE` (0.2) and it rests on ≥ 2 former MKs and ≥ 2 distinct bills (2026-10-18, after the second external audit) |

Nothing changes in: cosine closeness, weights 1/n per direction (a/b pairs), coverage threshold 0.5 and the «Not ranked» block,
the two notes, what is not shown (no coalition/opposition, no number of MKs).

## 2. Order of questions (`pipeline/quiz_flow.py`, rule of 2026-10-21)

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

## 5. Loading (customer, 2026-10-18)

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

## 6. Methodology page texts (customer, 2026-10-18)

Texts for the methodology / FAQ page, English as shown. Numbers come from the export where noted; the rest is fixed text.

**How topics are chosen.** A topic gets a statement only if the parties' former MKs actually differ on it in the Knesset record:
at least 8 evaluated lists with 3 or more former MKs on the topic, a spread of their positions of at least 0.25, and at least 5
distinct bills (a re-submitted bill counts once) sponsored by them. These thresholds were fixed in advance and are the same for every topic. Topics where all lists
did the same, or where too few bills exist, are left out — even when they are important. When one topic lies almost entirely inside another, a shared bill counts toward only one of them, chosen by whether voters would see two different questions.

**Important topics that are not in the quiz, and why.**
- *The lists' records hardly differ (nearly everyone pushed the same way):* tax enforcement; support for charities; support for
  families with children.
- *Too few lists with a record once budget votes are set aside:* the power of labor unions.
- *Too few bills by the candidates to place the lists:* abortion; who is registered as a Jew; gun licensing; immunity for
  soldiers; the death penalty for terrorists; immigration rights of grandchildren of Jews (Law of Return); laws tied to a state of
  emergency; a shorter working week.
- *Covered by another statement:* civil marriage and divorce
  (in «Civil marriage» and «Divorce»); conditions on funding religious schools (in «Funding schools without the core curriculum»);
  alternatives to military service (in «Drafting yeshiva students»); international law and UNRWA (in «Foreign states and
  international organizations in Israel»).

**Where a list's position comes from.** Only from what its candidates who were MKs in the 24th–25th Knesset did: the bills they
sponsored, their votes on private bills, their votes on the other camp's bills and, for coalition parties, their votes on the government's
own bills. A government bill counts for both camps the same way; votes on the omnibus budget laws count for nobody, because a vote for
or against the whole budget says nothing about its hundred separate articles. Promises and speeches are not used.

**Leaders with few bills of their own.** Ministers and prime ministers rarely sponsor bills, so a list's position rests mostly on
its other former MKs and on votes.

**Candidates who moved to another list.** A former MK's record counts for the list they run with in 2026: it is the same person and
their own votes.

**Lists with one former MK** are shown but not ranked: one person's record is too thin to call a list the closest.

**The answer scale.** Closeness compares directions, not intensity: if you answer «strongly agree» to everything, the result is the
same as «agree» to everything; the strength of an answer matters when your answers are mixed.

**«No clear position».** A list is marked so when its position is weaker than 0.2 (`params.CLOSE`) — below that, the side of the
same list did not hold between the two Knessets in most cases — or when it rests on a single former MK or a single bill.

**Limitations — what this quiz can and cannot tell you.** The quiz is an orientation, not a precise measurement. We state openly
where the data and the analysis are noisy:
- *Only the Knesset record of former MKs* (24th–25th Knesset) is used. New candidates, platforms and statements are not seen. 12 of
  38 lists can be evaluated; 4 lists with a single former MK are shown but not ranked; 22 lists have no record.
- *Bloc discipline.* About 98 % of votes follow the voter's bloc. A party's opposition to the other camp's laws is read from its votes
  against them — partly party discipline, not only conviction.
- *Leaders and ministers sponsor few bills,* so a list's position rests mostly on its other former MKs and on votes.
- *Topic labels were made by a language model.* Independent model checks found main topics right in about 93 % and secondary topics
  in about 80 % of cases; individual mistakes remain. Labels were corrected only where two independent checks agreed.
- *Checks so far were done by models, not by people.* Agreement figures measure consistency, not accuracy for real voters. A human
  check is planned.
- *Closeness is approximate.* Lists with close values cannot be told apart reliably, so values are shown rounded and should be read
  as «about as close». «No clear position» means the record is weak or rests on a single former MK or a single bill.
- *The price in a statement* («even if …») is not measured: the record shows what a list's bills and votes pushed for, not whether
  it accepts that price.
