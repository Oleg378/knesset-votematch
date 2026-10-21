# Step 3 of the new-statement procedure: drafts (Opus), 2026-10-20

A voter quiz for the 2026 Knesset election: the voter answers statements (strongly agree … strongly disagree, don't know); each statement is about one theme (a quantity a bill increases «+» or decreases «−»); agreeing means moving the theme to «+» or to «−» — that is the statement's key.

Read only these files (no other files, no web, no scripts):
- <ROOT>/jef/quiz/GUIDELINES.md — the rules for statements (follow them strictly).
- <ROOT>/local/research/new_statements_round2/statements.md — the current statements (style reference; do not duplicate them).
- <ROOT>/local/research/new_statements_round2/draft_items_1.md — themes to draft: id, name, «+»/«−», list positions, the bills with the most weight (sign, weight, Hebrew title). A theme marked MOVE takes over an existing statement: rewrite that statement to cover the whole theme.

For each theme write one statement in English that a voter would understand, built on what the weighty bills actually do (not on the theme name alone): one thought, ≤ 25 words, a price for every «more of something good» ("even if …"), no evaluative words, no party names, meaningful for any voter. Give a short title (2–5 words), the key (+ if agreeing moves the theme to «+», − otherwise), and a Russian translation for the customer. If no honest statement is possible (the weighty bills are about unrelated things, or there is no position a voter would hold), say so instead of forcing one.

Write <ROOT>/local/research/new_statements_round2/drafts_1.json with the Write tool:
[{"d": "<id>", "key": "+|−", "title_en": "...", "statement_en": "...", "statement_ru": "...", "note": "(Russian) what the weighty bills are about; doubts", "no_statement": false}]
For a theme without an honest statement: {"d": "<id>", "no_statement": true, "note": "(Russian) why"}. One entry per theme. Do not modify any other file. Final reply: one line with counts.
