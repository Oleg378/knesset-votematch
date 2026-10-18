# Task for the checker (Opus), 2026-10-18

A voter quiz for the 2026 Knesset election matches users to lists by what the lists' former MKs did in Knessets 24–25 (bills they
sponsored, and with weight 0.25 their votes on private bills). Each statement is attached to a direction; all bills labeled with it
count. Bills that were not about the statement's question have just been removed from 30 statements. Input: `wording_input.md`
(same folder). Work only from it: no web search, no other files. Write only `wording_result.md` and `wording_result.csv`.

**Part 1 (P1-q…, 23 statements).** Does the title and the statement still describe what the driving bills share? Bills marked NEW
were not reviewed before. Verdict per statement:
- `ok` — the wording fits the bills that separate the lists;
- `rewrite` — the bills share a clear question that the wording misses or narrows; give a new English title (≤ 5 words) and statement
  (one sentence, pattern «…, even if …», neutral, no party names; keep which end «agree» means unless you say why);
- `misfit_bills` — wording fine, but some driving bills (ids) are not about the question (as before: substance, not a shared word).
A statement can be both `rewrite` and `misfit_bills`.

**Part 2 (P2-…, 48 pairs).** A list's side comes only from votes. For each listed voted bill: is it about the statement's question
(`about` / `not_about` / `borderline`)? Then: is the list's side on the statement supported by the bills that are `about`
(`supported` / `not_supported` / `unclear`)?

**Part 3 (P3-…, 58 items).** A bill whose MAIN label is the statement's direction and that weighs a lot. Is it about the
statement's question (`about` / `not_about` / `borderline`)? Is its sign plausible?

Outputs:
- `wording_result.csv`: `id,item,verdict,detail` — Part 1: one row per statement (item = `statement`, verdict as above, detail = the
  new title | statement for `rewrite`, or the misfit ids); Part 2: one row per bill (item = bill id) plus one row item = `side`;
  Part 3: one row per item (item = bill id; detail = ≤ 15 words why, and «sign wrong» if so).
- `wording_result.md`: Part 1 table `| q | verdict | new title | new statement | misfit bills | note |` (only for statements that are
  not `ok`, plus a count of `ok`), then ≤ 100 words on Parts 2 and 3 (patterns).
Final reply ≤ 8 lines (counts).
