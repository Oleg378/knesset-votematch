# Standard audit of draft statements against their bills (Opus, blind), 2026-10-20

A voter quiz for the 2026 Knesset election: each statement is about one direction (a quantity a bill increases «+» or decreases «−»); a list's position on the statement rests on the bills below (weight = 2026 candidates who initiated the bill + 0.25 × their votes on it). These are DRAFTS of new statements.

Read only <ROOT>/local/research/statement_audit_round2/input_1.md (no other files, no web, no scripts). For each direction: does the statement ask what the weighty bills actually do? The customer's algorithm:
- `keep` — the statement matches what the bills with most of the weight do;
- `rewrite` — the statement is narrower than or off its direction: give a broader text that matches the weighty bills (same rules: one thought, ≤ 25 words, a price "even if …", no evaluative words, no party names) and its key (+ if agreeing means more of the direction);
- `split` — no single honest statement can cover the weighty bills (they are about different things): propose 2–3 parts, each with name_en, plus_en, minus_en and the bill numbers (#) from the table that belong to it;
- `unsuitable` — no position a voter would hold.
List the bill numbers (#) that are off-topic for the (new) statement.

Write <ROOT>/local/research/statement_audit_round2/out_1.jsonl with the Write tool, one JSON object per line:
{"d": "<direction id>", "verdict": "keep|rewrite|split|unsuitable", "statements": [{"q": "<q as given, e.g. n100c>", "new_statement_en": "", "new_agree_key": ""}], "split": [{"name_en": "...", "plus_en": "...", "minus_en": "...", "bills": [1, 3]}], "bills_off": [7, 8], "reason": "≤ 40 words, English"}
One line per direction, all directions of the file. Do not modify any other file. Final reply: one line with counts per verdict.
