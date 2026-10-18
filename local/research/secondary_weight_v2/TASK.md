# Task for the auditor (Opus), 2026-10-18

Context: a voter quiz for the 2026 Knesset election. A list's position on a statement comes only from what its candidates who are former
MKs did in Knessets 24–25: bills they sponsored (each bill is labeled with 1–2 main topics and up to 5 secondary topics, each with a
sign) and private-bill votes. A statement is attached to one direction (topic); every bill labeled with that direction counts, main or
secondary, with equal weight. Problem found: secondary labels can bring in bills from a different conflict. Example: q5 «Community
heritage centers» — the Joint Arab List's −1.23 comes from bills repealing the Nation-State Law and the Keren Kayemeth LeIsrael Law,
labeled secondary «less state support for Jewish identity». The label is literally defensible, but a voter answering about heritage
centers is matched on the Nation-State Law.

Work only from the two input files. No web search, no other sources. Do not edit any file except the two outputs below.

## Part 1 — `audit_statements.md` (48 statements, q5 included)

For each statement, look at the driving bills (the bills that create the difference between lists, with their share of the spread).
For each driving bill decide: does a voter who agrees / disagrees with the statement text recognise this bill as being about the
same question, in the same direction (sign)? A bill FITS if its substance is the question the statement asks. It is a MISFIT if it is
about another question that only touches the direction formally (another law, another population, another conflict), or if its sign
is wrong for the statement.

Write `audit_result.md`:

1. One table, one row per statement, ordered as in the input:
   `| q | verdict | misfit share | misfit bills | remedy | note |`
   - verdict: `fits` (misfit share < 0.15), `partly` (0.15–0.5), `misfit` (> 0.5). misfit share = sum of «share» of the misfit bills.
   - misfit bills: ids, each with 3–8 words of what it really is about.
   - remedy (one): `none`; `relabel` (the bill should not carry this direction — say which direction it belongs to instead, if any);
     `rewrite` (the statement text should cover what the fitting bills really share — give a draft in English, same pattern
     «…, even if …», one sentence, neutral, no party names); `split` (the direction holds two different questions that each deserve a
     statement — name the two parts).
   - note: anything a reviewer must know (≤ 20 words).
2. After the table: q5 in detail (≤ 150 words): what the fitting bills share, what the misfit bills share, and your recommended
   remedy with a draft statement if any. Note that «Jewish character of the state» (q4: «The Jewish character of the state and its
   Jewish majority should be anchored more firmly in law, even if non-Jews feel less equal.») already exists.
3. Patterns (≤ 150 words): what kinds of bills typically leak in through secondary labels (e.g. repeal bills, omnibus bills,
   temporary orders), and whether a rule could catch them.

## Part 2 — `spot_checks.md` (24 pairs, blind)

For each pair S1…S24: from the list's bills (and the V part, weight 0.25, ±0.5 is large), what is the list's side on the
statement **text** — `agree`, `disagree`, or `unclear` (no bills that are about this question, or they point both ways)?
Judge by substance: ignore bills that are not about the statement's question, whatever their label. Write `spot_result.csv`:
`id,side,confidence,fitting_bills,reason` — confidence high/medium/low; fitting_bills = how many of the listed bills are really about
the question; reason ≤ 25 words, English.

Keep the outputs compact. Total answer to the caller: ≤ 10 lines (counts of verdicts, the q5 recommendation in one line).
