# Third check (Opus, blind), label check of bills moved into quiz topics by stage 5 (2026-10-20)

A voter quiz for the 2026 Knesset election matches users to lists by the bills the lists' former MKs sponsored. Each quiz statement is
attached to a direction (topic); every bill labeled with that direction counts toward the lists' position on the statement.

For each item T… in <ROOT>/local/research/label_check_qt5/check3_items.md: is this bill about the question the statement asks?

- `about` — a voter who agrees or disagrees with the statement would recognise the bill as being about that same question (its substance, not a word in common).
- `not_about` — the bill is about another question (another law, population or conflict) and touches the direction only formally, or by a shared word.
- `borderline` — reasonable people would disagree.

Judge each item on its own, from the statement, the direction, the bill's name and the notes. No web search, no other files, no scripts.
Write <ROOT>/local/research/label_check_qt5/check3_result.csv with the Write tool: header `id,verdict,reason` (reason ≤ 15 words, English, in double quotes). One row per item.
Do not modify any other file. Final reply: one line.
