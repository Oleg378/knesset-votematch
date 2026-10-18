# Task for the second checker (Opus), 2026-10-18

A voter quiz for the 2026 Knesset election matches users to lists by the bills the lists' former MKs sponsored. Each quiz statement is
attached to a direction (topic); every bill labeled with that direction counts toward the lists' position on the statement.

For each item I1… in `check2_items.md`: is this bill about the question the statement asks?

- `about` — a voter who agrees or disagrees with the statement would recognise the bill as being about that same question (its
  substance, not a word in common). The bill's direction label sign is plausible for it.
- `not_about` — the bill is about another question (another law, population or conflict) and touches the direction only formally,
  or by a shared word; or it belongs to the question but its sign is clearly wrong.
- `borderline` — reasonable people would disagree.

Judge each item on its own, from the statement, the bill's name, its main topics and the notes. No web search, no other files.
Write `check2_result.csv` in the same folder: `id,verdict,reason` (reason ≤ 15 words, English). One row per item, all items.
Do not modify any other file. Final reply: ≤ 5 lines (counts per verdict).
