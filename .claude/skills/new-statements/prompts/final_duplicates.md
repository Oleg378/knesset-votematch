# Final duplicate check across all statements (blind, Opus), 2026-10-20

A voter quiz for the 2026 Knesset election. Read only <ROOT>/local/research/new_statements_round2/all_statements.md: existing statements (E…) and new ones (N…). No other files, no web, no scripts.

Find every pair where at least one statement is new (N…) and the two ask voters the same question: most voters would answer both the same way for the same reason, so one adds nothing. A pair that merely overlaps but lets a voter hold different views is not a duplicate. Also list pairs that are mirror images (the same question asked from opposite sides).

Write <ROOT>/local/research/new_statements_round2/dups_X.csv with the Write tool: header `a,b,kind,reason` (a, b = ids like N103c, E45; kind = same|mirror; reason ≤ 20 words, English, in double quotes). Only duplicate pairs; an empty file with the header if none. Do not modify any other file. Final reply: one line with the count.
