# Task for the auditor (Opus), 2026-10-18, wave 3

Context: a voter quiz for the 2026 Knesset election. A list's position on a statement comes only from what its candidates who are former
MKs did in Knessets 24–25: bills they sponsored (each bill is labeled with 1–2 main topics and up to 5 secondary topics, each with a
sign) and private-bill votes. A statement is attached to one direction (topic); every bill labeled with that direction counts, main or
secondary, with equal weight. Labels can bring in bills from a different question (e.g. a bill repealing the Nation-State Law labeled
«less state support for Jewish identity» under a statement about community heritage centers).

Work only from `audit_statements.md` in this folder. No web search, no other sources. Write only `audit_result.md`.

For each statement, look at the driving bills (the bills that create the difference between lists, with their share of the spread).
For each driving bill decide: does a voter who agrees / disagrees with the statement text recognise this bill as being about the
same question, in the same direction (sign)? A bill FITS if its substance is the question the statement asks. It is a MISFIT if it is
about another question that only touches the direction formally (another law, another population, another conflict), or if its sign
is wrong for the statement.

Write `audit_result.md`: one table, one row per statement, ordered as in the input:
`| q | verdict | misfit share | misfit bills | remedy | note |`
- verdict: `fits` (misfit share < 0.15), `partly` (0.15–0.5), `misfit` (> 0.5). misfit share = sum of «share» of the misfit bills.
- misfit bills: ids, each with 3–8 words of what it really is about.
- remedy (one): `none`; `relabel` (the bill should not carry this direction); `rewrite` (the statement should cover what the fitting
  bills share — draft in English, one sentence, «…, even if …», neutral); `split` (two different questions — name the parts).
- note: anything a reviewer must know (≤ 20 words).
Final reply ≤ 5 lines (counts of verdicts).
