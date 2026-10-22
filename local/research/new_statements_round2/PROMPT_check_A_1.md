# Step 2 of the new-statement procedure (blind, Opus), 2026-10-20

A voter quiz for the 2026 Knesset election: voters agree or disagree with statements; each statement is about one theme (a quantity a bill increases «+» or decreases «−»). Below are themes that pass the numeric selection but have no statement yet. Before drafting, each theme is checked.

Files (read only these; no other files, no web, no scripts):
- /Users/oleg/Documents/elections-research/local/research/new_statements_round2/check_items_1.md — themes: number, id, name, «+»/«−», and the bills with the most weight (sign, weight, Hebrew title).
- /Users/oleg/Documents/elections-research/local/research/new_statements_round2/statements.md — the current quiz statements.

For each theme answer three questions:
1. `duplicate`: qN if a statement on this theme would ask voters the same question as existing statement qN — most voters would answer both the same way for the same reason, so it adds nothing; otherwise `none`. A theme that overlaps a statement but asks something a voter could see differently is `none`.
2. `technical`: `yes` if the theme cannot be put honestly to an ordinary voter (procedural or administrative, no position a voter would hold); else `no`.
3. `basket`: `yes` if the weighty bills are about unrelated subjects, so no single statement could fairly cover them (the theme is a leftover mix); else `no`.

Write /Users/oleg/Documents/elections-research/local/research/new_statements_round2/check_A_1.csv with the Write tool: header `id,duplicate,technical,basket,reason` (id = the theme id after the number, e.g. 100c; reason ≤ 20 words, English, in double quotes). One row per theme, all themes of the file. Do not modify any other file. Final reply: one line with counts.
