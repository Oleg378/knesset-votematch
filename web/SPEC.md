# web/ — product spec

_The screens still read `quiz_data.v1.json` (every statement in file order); the engine, the state machine and the loader are on the
current contract and pass `golden.v2.json` — wiring the screens is the next step, on the machine with the visual work._

Static SPA. Input: the three data files of `export/` (`quiz_core`, `quiz_data`, `quiz_bills`; contract and loading order —
`export/WEB_CONTRACT.md`; page texts — `export/METHODOLOGY_PAGE.md`). Reference behaviour: `pipeline/quiz_cli.py` (run it to
see the flow) and `pipeline/quiz_report.py` (explanations). How everything is computed: `docs/TECHNICAL.md`.

**Mobile first.** Design for 360–430 px wide screens. Desktop adaptation is out of scope for now: on wide screens show the
mobile layout centered with a max width (≈ 480 px). Base components: Figma
https://www.figma.com/design/TTgHWki3flpBiQ6U9XQF7I/CSS (see «Design» below).

## Flow (approved, SU; same as quiz_cli.py)

```
Start → Core statements (flow.core) → Clarifying statements (flow.clarify, chosen one at a time) → Trade-offs (0–flow.trade)
      → Results (full leaderboard) ⇄ List details → Bills of one statement; «Answer more questions» continues the clarifying ones
      └→ Methodology · Positions of the lists (also reachable from Start and Results)
```
Numbers of questions come from `flow` in the export; the clarifying statement after each answer — `nextClarify` in
`src/engine/flow.ts` (port of `pipeline/quiz_flow.py`, golden «flow N» cases).

**Screens with a Figma mockup follow the mockup** (Home, Questions, Clarifying question, Menu) — texts, controls and
interaction; the statement count comes from the data. Customer, 2026-10-18. Open points: `DECISIONS.md` section D.

Every screen: header with the menu button (Figma «Menu»: Start over · My results · Methodology).

### 1. Start (Figma «Home»)
- Eyebrow, «Find your vote match», hero graphic, tagline, chips (N statements · 10–15 min · Anonymous), three steps.
- «Start the quiz». «Behind the results» → Methodology.

### 2. Statements (Figma «Questions»)
- Header: progress track and `n / (core + clarify)`. One statement per screen: `statement_en`.
- Answers: Strongly agree (2) · Agree (1) · Disagree (−1) · Strongly disagree (−2). A tap selects; «Next» (inactive until
  an answer is selected) moves on; round «Back». «Not sure — skip this question» = no answer, moves on.
- Finishing early: menu «My results» (trade-offs follow). Going back shows the previous answer selected.
- Results need at least one answer; otherwise «No answers — nothing to compute» and stay.

### 3. Trade-offs
- Adaptive, one at a time, exactly as `exchange()` in quiz_cli.py: compute `tradeoffs(answers, mult, exclude=used,
  skip_lists=asked)`, take the first pair, ask, apply, repeat; stop at MAX_TRADE or when no pair is returned.
- Figma «Clarifying question — Equal as option»: header counter `n/MAX_TRADE`, «Thanks! Just a few clarifying
  questions», «Which matters more to you?» + explanation; cards A and B (`title_en`, «Your answer: …»), «or», card
  «Both matter equally». A tap selects; «Next» applies; «Back» undoes the previous trade-off (from the first: back to the
  statement where the questions were finished). Menu «My results» skips the remaining ones.
- A → mult[qa] ×= TRADE_W; B → mult[qb] ×= TRADE_W; Equally → nothing.
- The list behind a pair is never named.
- If no pair at all: skip the screen silently (no message needed on the web).

### 4. Results
- «All lists by closeness to your answers (from −1 to +1). Based on N answers[, including trade-offs].» Closeness is shown with one decimal; the order uses exact values.
- Rows: rank, list name (`name_en`), closeness formatted `+0.35`, note. A simple bar (−1…+1, centered at 0) is welcome.
- Ranked lists first; then a «Not ranked» divider with lists below the coverage threshold (no rank number); then one collapsed
  line «No record in the Knesset (N)» listing lists with status `not_evaluated`.
- Notes, only these two: `few former MKs: N` (status warning) and `position known for only N% of your answers`.
- **Not shown** (customer decisions): coalition/opposition, number of MKs, party logos, anything about the government.
- Tap a row → List details. «Change answers» → back to statements. «Start over» clears everything.

### 5. List details
- Header: list name, closeness, note.
- «Why it fits — N matches» (items with contribution > 0, largest first) and «Why it doesn't fit — N mismatches» (contribution
  < 0, most negative first). 5 per section, «Show all».
- Item: `title_en`, then the explanation lines exactly as `explain()` (see golden `details[].items[].lines` and
  `export/WEB_CONTRACT.md` §3): quoted statement · «Your answer: X. The record of the list's former MKs points toward /
  points against / shows no clear position on this statement.» · basis line (bills your way / the other way; votes on
  private bills, on the other camp's bills and, if any, on the government's own bills) · optional weight ×2 line ·
  optional «the side comes from votes» line · optional «not whether they accept the price» line.
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
- ranked = closeness finite, coverage ≥ MIN_COVERAGE and the list's `ex_mks` ≥ MIN_EX_MKS (`is_ranked`). Coverage note
  appended with `; ` if a note exists. Percent as Python `f"{x:.0%}"`.
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
- `export/golden.v2.json`, 34 cases (full synthetic answer set, full + trade-offs, adaptive step, 20 random, edge cases: no answers, all dk,
  all neutral, one answer, rare topics, six «flow N» users). For every case assert: ranking ids in order, closeness and coverage within
  `tolerance`, notes, ranked flags; trade-off pairs; for each `details[]` list: item order, contribution, p, `lines` (exact
  strings), evidence order (`bill`, `same`, `role`, `sign`, authors) — `src/engine/golden.test.ts`; the «flow N» question
  order — `src/engine/flow.test.ts`.
- Schema test: the three data files merged validate against `quiz_data.v2.schema.json` (ajv) and come from one build.
- Reducer tests for the state machine (transitions, back/skip, start over).
- Python stays the reference: if a golden case fails, the TS code is wrong unless the customer changed the formula (then a
  new export and, for structural changes, v2).

## State
`useReducer` state machine, no state library: `start | question(i) | tradeoff | results | details(list) | bills(list, q) |
methodology | loading`. State: `shown` (statements shown so far, in order — the core, then each clarifying one; `question(i)`
shows `shown[i]`), answers, mult, done trade-offs, `more` (after «Answer more questions»), the fetched files and a pending
action waiting for one of them (`loading` screen, Back cancels). Answers are kept **in memory only** [У 2026-10-17]: no
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
