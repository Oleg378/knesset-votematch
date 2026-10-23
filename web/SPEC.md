# web/ — product spec

Static SPA. Input: the data contract — three files fetched at run time (`export/quiz_core.json`,
`quiz_data.json`, `quiz_bills.json`; one schema for their merge). Contract and loading order:
`export/WEB_CONTRACT.md`; page texts: `export/METHODOLOGY_PAGE.md`. Reference behaviour: `pipeline/quiz_cli.py` (run it to
see the flow), `pipeline/quiz_flow.py` (order of questions), `pipeline/quiz_report.py` (explanations). How everything is
computed: `docs/TECHNICAL.md`.

**Mobile first.** Design for 360–430 px wide screens. Desktop adaptation is out of scope for now: on wide screens show the
mobile layout centered with a max width (≈ 480 px). Base components: Figma
https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS (see «Design» below).

## Flow (approved, SU; same as quiz_cli.py)

```
Start → Core statements (flow.core) → Clarifying statements (flow.clarify, chosen one at a time) → Trade-offs
(0–flow.trade) → Results (full leaderboard) ⇄ List details → Bills of one statement
Methodology: reachable from Start and the menu. Positions of the lists (§7, not built yet): linked from
Methodology and Results (`export/METHODOLOGY_PAGE.md`).
```
Numbers of questions come from `flow` in the export; the clarifying statement after each answer — `nextClarify` in
`src/engine/flow.ts` (port of `pipeline/quiz_flow.py`, golden «flow N» cases).

**Screens with a Figma mockup follow the mockup** (Home, Questions, Clarifying question, Menu) — texts, controls and
interaction; the statement count comes from the data. Customer, 2026-10-18. Open points: `DECISIONS.md` section D.

Every screen: header with the menu button (Figma «Menu»: Start over · My results · Methodology); on Results, at the right end (where
other screens have the counter), Start over: the menu item's icon, no text; it clears the answers and opens the first
question at once, as «Start» on Home (customer 2026-10-22).

### 1. Start (Figma «Home»)
- Eyebrow, «Find your vote match», hero graphic, tagline, chips (N statements · 3–5 min · Anonymous), three steps.
  N = flow.core + flow.clarify (now 15) [У 2026-10-18]; the time «3–5 min» [У 2026-10-18]. The page renders before any
  data; the statements chip and the steps appear when quiz_core (~1 KB) has arrived.
- «Start the quiz». «Behind the results» → Methodology.

### 2. Statements (Figma «Questions»)
- Order (quiz_flow / quiz_cli.flow): the core statements in the exported order (`core`), then clarifying ones —
  each chosen after the previous answer with `next_clarify` (port: `src/engine/flow.ts`), until `should_stop`
  (fixed number while `flow.stop_gap` is null). Numbers always from `flow`, never hard-coded.
- Header: progress track and `n/(core + clarify)` (`n/15`); during «Answer more» `n/<all statements>`.
  One statement per screen: `statement_en`.
- Back / Next move along the statements already shown (the answer stays selected); a new statement is chosen only at
  the end of that sequence, from all answers given so far [А 2026-10-18; the terminal reference drops the last answer
  on «<» instead].
- Answers: Strongly agree (2) · Agree (1) · Disagree (−1) · Strongly disagree (−2). A tap selects; «Next» (inactive until
  an answer is selected) moves on; round «Back». «Not sure — skip this question» = no answer, moves on.
- Finishing early: menu «My results» (trade-offs follow). Going back shows the previous answer selected.
- Results need at least one answer; otherwise «No answers — nothing to compute» and stay.

### 3. Trade-offs
- Adaptive, one at a time, exactly as `exchange()` in quiz_cli.py: compute `tradeoffs(answers, mult, exclude=used,
  skip_lists=asked)`, take the first pair, ask, apply, repeat; stop at `flow.trade` or when no pair is returned.
- Figma «Clarifying question — Equal as option»: header counter `n/flow.trade`, «Thanks! Just a few clarifying
  questions», «Which matters more to you?» + explanation; cards A and B (`title_en`, «Your answer: …»), «or», card
  «Both matter equally». A tap selects; «Next» applies; «Back» undoes the previous trade-off (from the first: back to the
  statement where the questions were finished). Menu «My results» skips the remaining ones.
- A → mult[qa] ×= TRADE_W; B → mult[qb] ×= TRADE_W; Equally → nothing.
- The list behind a pair is never named.
- If no pair at all: skip the screen silently (no message needed on the web).

### 4. Results
- The title «Your result» stands in the header, centred between the menu button and Start over, pinned with it (Fraunces
  20/22; customer 2026-10-23); the page keeps it as a visually hidden h1. The screen starts with:
- «Based on N of M answers[, including trade-offs]» (no period) M = statements shown; then a thin line 12 under it, and 4 under the line «Tap › for details»
  in italic, the lighter grey, with the rows' round arrow between the words (customer 2026-10-23). Under it a thin line (12 below the text, 20 above the legend; customer 2026-10-23), then the scale legend in one line:
  «far from you» on the left, «close to you» on the right, no numbers, nothing in the middle (customer 2026-10-22, DECISIONS.md G15).
- At the bottom only «Change answers» (light blue, as before), pinned to the bottom of the screen as on Home and the
  question screens, with the fade over the lists under it (customer 2026-10-23): «Answer more questions», «Start over» and
  «How it works» are gone — Methodology is in the menu — Start over stays in the header and the menu. «Answer more» has no entry now (the
  reducer keeps `MORE`).
- Rows: rank, list name (`name_en`), closeness in tens of percent with its sign — `+40%`, `−30%`; zero is `0%`, no sign (customer 2026-10-22), then a round «›» button on a row
  that opens List details, the same on every row; every row on its own band (light translucent in the panel, light grey
  below), 8 apart (customer 2026-10-23), note; the order uses the exact values, not
  the rounded percents shown;
  under them a line −100%…+100% with the list's dot at the value shown (10 px for every list, blue in the panel, grey below; the line runs
  from the name to the end of the percent; the legend starts over the rank circles and ends over the arrow buttons) — the same line for every list, so all lists read as one scale. The 5
  closest stand out in a panel without a title (customer 2026-10-22; screen readers hear its list as «Your 5 closest lists»). No up/down arrows, no lines between rows, no zero mark
  on the line.
- Only the closest five are shown; at the bottom of their panel «See all ⌄», no line above it (as «Not sure — skip» in the
  question panel) drops the rest down from the panel and keeps them inside it (the same tint and bands, the bottom rounded); «See all» goes away (focus
  to the first list that dropped down). «Show less ⌃» is only at the end of the open list; it closes the list and returns to
  the panel (focus on «See all») (customer 2026-10-22).
- Ranked lists first; then a «Not ranked: not enough data» divider with lists below the coverage threshold or with
  too few former MKs (no rank number, no notes: the divider gives the one reason for all; List details keeps each list's note). Lists with status
  `not_evaluated` (no record in the Knesset) are not shown on Results (customer 2026-10-22); Methodology counts them.
- Notes, only these two: `few former MKs: N` (status warning) and `position known for only N% of your answers`.
- **Not shown** (customer decisions): coalition/opposition, number of MKs, party logos, anything about the government.
- Tap a row → List details. «Change answers» → back to statements. Start over (header, menu) clears everything.

### 5. List details
- Header: list name, closeness, note.
- «Why it fits — N matches» (items with contribution > 0, largest first) and «Why it doesn't fit — N mismatches» (contribution
  < 0, most negative first). 5 per section, «Show all».
- Item: `title_en`, then the explanation lines exactly as `explain()` (see golden `details[].items[].lines`):
  quoted statement · «Your answer: X. The list is for/against this statement.» · basis line · optional weight ×2 line ·
  optional relative-position caveat.
- Tap → Bills of this statement.

### 6. Bills of one statement
- The explanation lines again, then two groups: «Your way (n)» and «The other way (n)», order from the golden evidence.
- Bill row: Hebrew title (`name_he`, **dir="auto"**, never translated), under it in English: «Knesset N · main/secondary topic ·
  raises/lowers “direction name”», «Sponsored by: Name (#p on the list)» (first two by list position), link to the Knesset page.
- No per-bill English summary [У 2026-10-17]: bill names are not translated; the direction line above is the English context. `summary_en` is always null and not rendered.

### 7. Methodology and Positions of the lists
- Methodology: the texts of `export/METHODOLOGY_PAGE.md` as written (fixed text; numbers marked «from the export» are read from the data).
- Positions of the lists: the table described in `METHODOLOGY_PAGE.md` («Positions of the lists page») — statements × evaluated lists, cell = the measured side, click → the bills, the right-to-contest text.

## Computation (TypeScript port; Python is the reference)
Port `pipeline/quiz_match.py` (`list_vec`, `score`, `match`, `ranked_top`, `tradeoffs`) and from `pipeline/quiz_report.py`
(`contributions`, `evidence`, `explain`, `plural`). Pure functions in `src/engine/`, no React inside. Details that matter for
exact equality with the golden cases:
- `u = answer / 2 * key`; `w = statement.w * (mult[q] ?? 1)`; dk and missing answers are skipped; answer 0 counts in the
  answered weight (coverage) but adds nothing to the dot product.
- `p = P * e / (e + K)`; a list has a value on a statement only if it has a position on the statement's direction.
- closeness = `num / sqrt(uu * pp)`, NaN if `uu == 0 || pp == 0` (→ `null` in golden); coverage = covered weight / answered
  weight (0 if nothing answered).
- `not_evaluated` lists: closeness `null`, note `no record in the Knesset`.
- ranked = closeness finite and coverage ≥ MIN_COVERAGE. Coverage note appended with `; ` if a note exists. Percent as
  Python `f"{x:.0%}"`.
- Sort: key `(not ranked, closeness is null, -(ranked ? closeness : 0))`, **stable** over the `lists` order.
- Trade-offs: rows `(c, q)` with `c = w * a/2 * key * p` (base weight `w`, not multiplied); plus = sort by tuple `(c, q)`
  descending, keep `c > 0`, not used, first 3; minus = ascending, `c < 0`, first 3. Tuple compare = number, then string `q`.
  For each `qa` in plus, the first `qb` in minus such that doubling `qa` or `qb` (on top of current mult) changes the top
  TRADE_TOP list ids (order matters) → pair `(qa, qb, list)`. One pair per list, lists in current top order, skip
  `skip_lists`.
- contributions: answered (not dk, not 0) statements with a list value; `c = w * mult * u * p`; sort by `-c`, stable.
- evidence: bills of `by_direction[d]` with ≥ 1 sponsor among the list's ex-MKs; `same = sign * sign(u) > 0`; sort by
  `(not relevant, min author list_position)` stable, where relevant = `same` if c > 0 else `not same`.
- Strings in explanations come from `strings.ts` and must reproduce the golden `lines` exactly.

## Tests (Vitest) — migration Python → TypeScript
- `export/golden.json`, 34 cases (full synthetic answer set, full + trade-offs, adaptive step, 20 random, edge cases: no answers, all dk,
  all neutral, one answer, rare topics). For every case assert: ranking ids in order, closeness and coverage within
  `tolerance`, notes, ranked flags; trade-off pairs; for each `details[]` list: item order, contribution, p, `lines` (exact
  strings), evidence order (`bill`, `same`, `role`, `sign`, authors).
- «flow N» cases (6): replay the question order — the core, then every clarifying statement from `next_clarify`.
- Schema test: `quiz_data.json` + `quiz_bills.json` merged validate against `quiz_data.schema.json` (ajv); `quiz_core`
  is the head of `quiz_data` (same export, flow, core, statements).
- Screen tests also cover loading: the start page before any data, a loader on a screen whose file has not arrived.
- Reducer tests for the state machine (transitions, back/skip, start over).
- Python stays the reference: if a golden case fails, the TS code is wrong unless the customer changed the formula (then a
  new export and, for structural changes, a new schema and contract).

## State
`useReducer` state machine, no state library: `start | question(i) | tradeoff | results | details(list) | bills(list, q) |
methodology`. State: answers, mult, done trade-offs. Answers are kept **in memory only** [У 2026-10-17]: no
sessionStorage, localStorage or cookies; a reload starts over. Results never go into the URL. No accounts.

## Text, language, typography
- All UI strings in `src/strings.ts` (English). No string literals in components.
- Hebrew bill titles: `<span dir="auto" lang="he">`; numbers, brackets and quotes must not jump.
- Font with Hebrew support (e.g. Noto Sans + Noto Sans Hebrew, or system stack with `"Arial Hebrew", "Noto Sans Hebrew"`
  fallback).

## Metrics and privacy
- Events only: `started`, `finished` (optionally `reached_q10/30/50`). Never answers, results or list ids.
- `src/analytics.ts` with `track(event)`; no-op by default. Backend (Cloudflare Worker + KV, or Web Analytics) — later [О].
- No third-party trackers, no cookies.

## Hosting
Cloudflare Pages, static build (`npm run build` → `web/dist`). CI: GitHub Actions (`.github/workflows/web.yml`): install,
test, build; deploy only after the customer connects the repo and secrets.

## Design
Base components are in the Figma file above. Map them to CSS variables in `src/styles/tokens.css` (colors, type scale,
spacing, radii) and small components in `src/components/` (Button, AnswerButton, ProgressBar, Card, ListRow, Accordion,
Note/Badge). Until the Figma tokens are imported, use neutral placeholder tokens in that one file only.

## Open (customer decision needed)
- Topic selection before the questions (in the general recommendations) — not in the approved flow (direct «what matters to
  you» was rejected in favour of trade-offs).
- Analytics backend; Figma tokens import.
