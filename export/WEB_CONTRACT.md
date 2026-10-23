# Contract for the web: what to compute and what to show

_The only link between the data side (`pipeline/`) and the web (`web/`): the web reads `export/` and nothing else, never calls Python.
Python is the reference (`pipeline/quiz_match.py`, `quiz_flow.py`, `quiz_report.py`); the TypeScript port (`web/src/engine/`) must
reproduce `golden.json` to 1e-9. Every text the user reads — `quiz_texts.json` (§7). No history here: the
current contract only; what changed and why is in `docs/WORKLOG.md`._

## 1. Files and loading

| File | What | Shipped |
|---|---|---|
| `quiz_core.json` | `flow` (parameters of the question order), `core` (the first statements, in order), the core statements | yes, fetched first (preloaded from `index.html`) |
| `quiz_data.json` | `params`, all statements (with `interest`, `area`, `sim_group`), `directions`, `lists` with `positions` and `composition` | yes, fetched second |
| `quiz_bills.json` | `mks` (with `party_en`), `by_direction`, `votes`, `bills` — only for List details and «Bills of one statement» | yes, fetched third |
| `quiz_texts.json` | every text the user reads on the site (§7); edited by hand, not written by `export.py` | yes, bundled into the JS |
| `quiz_texts.schema.json` | JSON Schema of `quiz_texts.json`, generated from `web/src/texts.ts` | `make check` (I8), tests |
| `quiz_data.schema.json` | JSON Schema of the three data files merged | tests |
| `golden.json` | answer sets → ranking, notes, trade-off pairs, explanation lines, evidence order, question order («flow N» cases) | tests |
| `stats.json` | the current numbers of the export (statements, lists by status, bills, MKs, directions, file sizes in KB), written by `export.py` | no; `make check` (I9) compares the numbers typed in the documents with it |

Goal: the start page never waits for data, and a loader almost never appears.

| File | Size (gzip) | Contents | Needed by |
|---|---|---|---|
| `quiz_core.json` | ~3 KB (1 KB) | `flow`, `core`, the core statements | the start page and the first `flow.core` questions |
| `quiz_data.json` | ~258 KB (50 KB) | `params`, all statements, `directions`, `lists` with positions | clarifying questions, trade-offs, Results, Methodology |
| `quiz_bills.json` | ~2.0 MB (312 KB) | `mks`, `by_direction`, `votes`, `bills` | List details, «Bills of one statement», Methodology |
| `quiz_texts.json` | ~15 KB (6 KB), inside the JS | every text of the site | every screen, from the first |

- The texts are **bundled** into the JS: the start page needs them before any data file arrives. The app parses the file once
  with its schema when it loads (§7); a file that fails the schema fails the tests and the build, never the live page. The
  page `<title>` is `app.title`, written into `index.html` at build time.
- The three data files are **not bundled**: the app shell (start page, styles, fonts, texts) loads alone; the data files are
  fetched as static files from the site itself (CSP `connect-src 'self'` allows it).
- Fetch order: `quiz_core` first (`index.html` preloads it with the start page's fonts and picture), then — once the start page
  is drawn — `quiz_data`, then `quiz_bills` as soon as the previous one has arrived. The user is answering the core questions
  meanwhile, so the next file is normally ready before it is needed.
- A loader is shown only if the user reaches a screen whose file has not arrived yet (e.g. the first clarifying question
  before `quiz_data`, List details before `quiz_bills`), and only for that screen.
- The three data files carry the same `generated` and `source_commit`; a fetched file from another export (a deploy
  mid-session) is a load error that asks to reload the page.
- Caching: the files get content-hashed names at build time (Vite assets, `immutable`); the app always references the files
  of its own build.

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
4. **Trade-offs** — `tradeoffs()` of `pipeline/quiz_match.py`, at most `flow.trade`.
5. **Results.** A button «Answer more questions» continues clarifying questions (same rule) until the pool ends, then Results again.

The counter on the question screen: `n / (core + clarify)` while the fixed number is used.
The 6 «flow N» golden cases give the exact sequences for six full answer sets: port `next_clarify` and check them first.

## 3. List details: what the result explains and in which format

Per list, everything comes from `quiz_report.contributions()` and `explain()`; golden `details[].items[]` has it field by field.
The lines are the templates `explain.*` of `quiz_texts.json` (§7), with the answer word from `answers`, rendered the same way
by `pipeline/quiz_report.py` and by the web; the examples below are those templates filled.

**Header:** list name (`name_en`), closeness `+0.35`, note (if any).

**Items.** For each answered statement (answer not 0, not «don't know») on which the list has a position:
- `contribution` = w × trade-off multiplier × u × p, where u = answer / 2 × key, p = list value. Positive → «Why it fits»
  (largest first), negative → «Why it doesn't fit» (most negative first). Section headers show the counts. 5 per section,
  then «Show all».
- `lines` — shown exactly as given, in order:
  1. the statement in quotes (`quote`);
  2. `answer`, with `side` = `sideFor`, `sideAgainst` or `sideNoClear`: `Your answer: <agree / strongly agree / …>. The record of the list's former MKs <points toward this statement | points against this statement | shows no clear position on this statement>.`
     (the third variant when the position is not clear: |p| < `params.CLOSE` (0.2), or fewer than `params.MIN_CLEAR_MKS` former MKs, or fewer than `params.MIN_CLEAR_BILLS` distinct bills (`n_names`));
  3. `basis` (or `basisVotesOnly` when the list sponsored no bill on the topic), with `votes` filled from `votes` and `votesGov`: `Basis: N bills sponsored by the list's former MKs — X your way, Y the other way; M votes on private bills, K votes on the other camp's bills[ and J votes on the government's own bills] on this topic.`
     or `Basis: no bills of their own on this topic, only M votes on private bills, K votes on the other camp's bills[ and J votes on the government's own bills] on this topic.`
     (M = `n_votes`, K = `n_other`, J = `n_gov` of the list's position — the bracketed part
     only when J > 0; «1 vote», «1 bill» in the singular);
  4. optional, `weight`: `Weight ×2: you chose this topic in a trade-off question.`;
  5. optional, `caveatByVotes`: `The list's side comes from how its former MKs voted, not from the bills they sponsored.`
     (when the list's own bills give nothing or point the other way);
  6. when line 2 says «points toward», `caveatPrice`: `This shows what their bills and votes pushed for, not whether they accept the price named in the statement.`
- `evidence` — the bills behind the item, already in display order (bills that explain the verdict first, then by the best
  list position of their sponsors). Each: `bill` (id → `bills[id]`: Hebrew name `name_he`, `knesset`; link =
  `params.BILL_URL` with `{id}` replaced), `sign`
  (+1 raises / −1 lowers the direction), `role` (main / secondary topic), `same` (true = same way as the user's answer, ✓;
  false = the opposite way, ✗), `authors` — [list position, English name] of the list's ex-MKs who sponsored it.

**Bills of one statement** (tap on an item): two groups, «Your way (N)» (`same` true) and «The other way (N)»; each line:
✓/✗ · Hebrew bill name linking to `params.BILL_URL` · `Knesset N` · `main / secondary topic` · `raises / lowers “<direction name_en>”` ·
`sponsored by: <name> (#<position> on the list)` (first two by list position); the labels are `bills.*` of `quiz_texts.json`. Bill names are never translated.

**Votes of the list's former MKs** (2026-10-19, `quiz_bills.json` → `votes`): `votes[list][direction]` = rows
`[bill, sign, camp, for, against]` — the bills of that direction its former MKs voted on, with the bill's sign on the direction
(+1 raises / −1 lowers), whether the bill came from the MK's own camp (`own`, counted in V) or from the other camp (`other`, counted in
O), and how many of them voted for and against. These are exactly the votes behind the position. Name and Knesset: `bills[bill]`.
Suggested place: under «Bills of one statement», a third group «How its former MKs voted (N)», each line:
`Hebrew name · Knesset N · raises / lowers “<direction>” · for X, against Y · own camp’s bill / the other camp’s bill`. Not part of the
golden cases (no formula), plain display.

## 4. Golden cases

34 cases: answer sets (synthetic, random, edge cases), and 6 flow cases («flow 0» … «flow 5»): a synthetic user's answers to every statement; `flow.core` and
`flow.clarifying` are the statements asked, in order; `answers` holds only the answers given to them, and `ranking`,
`tradeoffs`, `details` are computed on those. The TS port must match to 1e-9.

## 5. Composition of a list's record

`mks[].party_en` — the component party of the 2026 list the former MK runs with (Central Elections Committee candidate list; null = the list itself); `lists[].composition` — the same aggregated, most first: `[{"party_en": "Yesh Atid", "ex_mks": 17}, …]`. Proposed line on the List details screen: «Based on 19 former MKs: 17 from Yesh Atid, 2 from Be’Yahad» (whether and how to show it — the customer's decision).

## 6. Positions page (not built yet)

Established voting advice applications let parties see and dispute their coded positions before publication. Our equivalent is a
public, complete table of what the quiz holds about every list, built only from data already in the export — no new fields.

**Page «Positions of the lists»** (linked from Methodology and from Results; English):
- Rows: the statements (`title_en`, grouped by `area` from `statements[]`, in the quiz's area order). Columns: the evaluated
  lists (`status == "ok"`), then the ranked-with-warning lists in a second block; lists without a record are not columns.
- Cell: the list's measured side on the statement — «toward» / «against» / «no clear position» — by the same rule as the
  explanations (`params.CLOSE`, `MIN_CLEAR_MKS`, `MIN_CLEAR_BILLS` on `lists[].positions[d]`); a small marker when the side comes
  from votes only (`P_bills` is 0 or opposite to `P`, as in the «side comes from votes» line). No numbers in the cell.
- Click on a cell → the same bill list as the List details screen for that statement (bills toward / against, votes), so the
  claim is checkable down to the Knesset record.
- Header text (fixed): «This is everything the quiz holds about each list, measured from the bills its candidates who were MKs
  sponsored and how they voted in the 24th–25th Knesset. If you represent a list and believe a cell is wrong, the bills behind
  it are listed — open an issue at https://github.com/Oleg378/knesset-votematch/issues with the bill and the reason; corrections
  are published here.» (customer, 2026-10-22: contact = GitHub issues).
- Export: `quiz_data.json` + `quiz_bills.json` only; the page is static like the rest.

## 7. Texts of the site: `quiz_texts.json`

Nothing the user reads is written in the code: the app's name and title, the answers, the notes, the explanation lines, the
labels of every screen and the whole methodology page come from `export/quiz_texts.json`. Change the file, and the site
changes. The file is edited by hand on the data side — the one file in `export/` that `pipeline/export.py` does not write.
Statement texts and titles (`statement_en`, `title_en`) are not in it: they are data, in `quiz_data.json`.

**Who reads it.**
- The web: `web/src/texts.ts` imports the file into the JS bundle and parses it once with its zod schema when the app loads;
  `web/src/strings.ts` builds the UI strings from it and holds no text of its own; the page `<title>` is `app.title`
  (a Vite plugin in `web/vite.config.ts`).
- The Python reference renders from the same file: `pipeline/texts.py` (`load`, `fill`); `pipeline/quiz_report.py` — the answer
  words (`answers`) and the explanation lines (`explain`, §3); `pipeline/quiz_match.py` — the notes of a list (`notes`); the
  terminal quiz uses the same words. The `answers`, `notes` and `explain` texts are therefore rendered identically by Python and
  TypeScript, and `golden.json` checks the result character for character.

**Sections.** Every key is required, no other key is allowed.

| Section | Keys | Shown |
|---|---|---|
| `updated` | ISO date of the last change of the texts | — |
| `app` | `title`, `name`, `eyebrow`, `loading`, `loadError`, `reload`, `newTab` | page title, menu title, loading and load error, the screen-reader note on links that open a new tab |
| `answers` | `"2"`, `"1"`, `"0"`, `"-1"`, `"-2"` | the answer inside sentences («Your answer: agree»): explanations, trade-off questions |
| `answerButtons` | the same keys and `dk` («don't know») | the answer buttons |
| `notes` | `noRecord`, `fewMks`, `lowCoverage`, `join` | the note of a list on Results and List details (`join` separates two notes) |
| `explain` | `quote`, `sideFor`, `sideAgainst`, `sideNoClear`, `answer`, `votes`, `votesGov`, `basis`, `basisVotesOnly`, `weight`, `caveatByVotes`, `caveatPrice` | the lines of List details (§3) |
| `start` | `title`, `tagline`, `chipStatements`, `chipTime`, `chipAnonymous`, `steps` (exactly three), `button`, `howItWorks` | Start |
| `menu` | `open`, `close`, `startOver`, `results`, `methodology` | the menu |
| `nav` | `back`, `next` | the bottom buttons of the question screens |
| `question` | `progress`, `progressLabel`, `or`, `skip`, `noAnswers`, `answersLabel` | the question screen |
| `trade` | `counter`, `lead`, `title`, `explain`, `yourAnswer`, `labelA`, `labelB`, `equalTitle`, `equalSub` | the trade-off question |
| `results` | `heading`, `scaleFar`, `scaleClose`, `closestOne`, `closestMany`, `basedOn`, `basedOnTrade`, `hintBefore`, `hintAfter`, `seeAll`, `seeLess`, `notRanked`, `notComputable`, `noMore`, `changeAnswers`, `rank`, `closenessLabel` | Results |
| `details` | `back`, `closeness`, `fits`, `misfits`, `showAll`, `showLess`, `none`, `openBills` | List details |
| `bills` | `back`, `yourWay`, `otherWay`, `none`, `meta`, `roleMain`, `roleSecondary`, `raises`, `lowers`, `sponsoredBy`, `sponsor`, `link`, `yourWayMark`, `otherWayMark`, `showMore` | «Bills of one statement» |
| `methodology` | `heading`, `back`, `sections[]`, `statements` | Methodology (below) |

**Template language.** `{name}` is replaced by the value; `{name?one|many}` by `one` when the value is 1, else by `many`
(`{single} {single?list|lists}`). Numbers are never typed into the texts. The names each key may use are listed explicitly in
`web/src/texts.ts` (`PLACEHOLDERS`, `STEP_PLACEHOLDERS`, `DATA_PLACEHOLDERS`, `STATEMENT_PLACEHOLDERS`), never derived from the
file: any other name, or a stray brace, fails the schema. A key not listed below takes no placeholder and no brace.

| Section | Key → allowed names |
|---|---|
| `notes` | `fewMks`: `n` (former MKs) · `lowCoverage`: `pct` (with the % sign) |
| `explain` | `quote`: `text` (the statement) · `answer`: `answer` (an `answers` word), `side` (the filled `sideFor`, `sideAgainst` or `sideNoClear`) · `votes`: `votes` (on private bills), `other` (on the other camp's bills), `gov` (the filled `votesGov`, or empty when there are none) · `votesGov`: `gov` · `basis`: `bills`, `same`, `opp`, `votes` (the filled `votes`) · `basisVotesOnly`: `votes` (the filled `votes`) |
| `start` | `chipStatements`: `n` · each of `steps`: `n` (the planned number of statements), `top` (the number of lists highlighted on Results) |
| `question` | `progress`: `n`, `total` |
| `trade` | `counter`: `n`, `max` · `yourAnswer`: `answer` |
| `results` | `closestMany`: `n` · `basedOn`: `n`, `total`, `trade` · `rank`: `n` |
| `details` | `closeness`: `c` · `fits`, `misfits`, `showAll`: `n` |
| `bills` | `yourWay`, `otherWay`, `showMore`: `n` · `meta`: `knesset`, `role`, `verb`, `direction` · `sponsoredBy`: `names` · `sponsor`: `name`, `pos` |
| `methodology.sections` | `text`, `after` and both fields of a bullet (not `title`): the numbers of `quiz_data.json` — `lists` (all lists), `evaluable` (evaluated with `ex_mks >= params.MIN_EX_MKS`), `single` (evaluated below it: shown, not ranked), `no_record`, `close` (`params.CLOSE`), `statements`, `core` and `clarify` (`flow`), `vote_ratio` (`round(1 / params.VOTE_WEIGHT)`), `min_lists`, `min_mks`, `min_spread`, `min_names` (`params.SELECT_*`, the selection thresholds of `pipeline/quiz_select.py`) |
| `methodology.statements` | `heading`: `statements` · `topic`: `name` · `up`, `down`: `text` · `billsCount`, `showMore`: `n` · `billMeta`: `side`, `knesset`, `role` · `sponsors`: `names` · `dataVersion`: `generated`, `commit` |

**Methodology page.**
- `heading`, `back`.
- `sections[]`: `title` (bold run-in start of the paragraph, with its own punctuation), optional `text`, optional `bullets[]`
  of `{lead, text}` (`lead` in italics as the run-in start of the bullet), optional `after` (a paragraph after the bullets).
- `statements`: the labels of the block «All N statements, their topics and the bills behind them» — `heading`, `topic`, `up`,
  `down`, `agreeCountsUp`, `agreeCountsDown`, `billsCount`, `billMeta`, `sideUp`, `sideDown`, `roleMain`, `roleSecondary`,
  `sponsors`, `noSponsors`, `showMore`, `billLink`, `dataVersion`.

The methodology texts are derived from `docs/METHODOLOGY.md` (concept) and `docs/TECHNICAL.md` (numbers); the data side keeps
them current. Statement titles named in the texts are quoted «as stored» (`title_en`).

**Checks.**
- The schema is the zod schema (zod/mini) in `web/src/texts.ts`; `export/quiz_texts.schema.json` is generated from it
  (`cd web && npm run schema:texts` after any change of the structure or of the allowed names; a web test fails while the file
  on disk is stale).
- `make check` I8: `quiz_texts.json` validates against `quiz_texts.schema.json`. I10: `golden.json` is current — the golden
  cases recomputed with the current templates give the same ranking, notes and explanation lines.
- Web tests: the file parses, every template fills with sample values of its allowed names and leaves no brace, the
  methodology sections fill with the numbers of `quiz_data`, unknown names and stray braces are rejected.

**How to change a text.**
1. Edit `export/quiz_texts.json` and set `updated`.
2. A text of `answers`, `notes` or `explain`: `make data` — the golden lines and notes change with it (I10 fails until then).
3. `make check` — must print OK.
4. `cd web && npm test`.
5. A new key or placeholder name is a change of the structure: first `web/src/texts.ts` and the code that fills the template
   (on both sides for `answers`, `notes`, `explain`), then `npm run schema:texts`.

**Composition of the list's record** on the List details screen — §5 — is not shown yet; the methodology text says only that
the results carry a note when few former MKs stand behind a list.
