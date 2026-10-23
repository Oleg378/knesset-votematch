# Blind check (Opus), measurement of label accuracy for the methodology page (2026-10-24)

A voter quiz for the 2026 Knesset election matches users to lists by the bills the lists' former members of the Knesset sponsored. Each quiz statement is
attached to a direction (topic); every bill labeled with that direction counts toward the lists' position on the statement.

For each item A… in <ROOT>/local/research/label_accuracy_sample/items_<K>.md: is this bill about the question the statement asks, and which way does it move the direction?

- `about` — a voter who agrees or disagrees with the statement would recognise the bill as being about that same question (its
  substance, not a word in common).
- `not_about` — the bill is about another question (another law, population or conflict) and touches the direction only formally, or by a shared word.
- `borderline` — reasonable people would disagree.
- sign: `+` if the bill moves the direction toward its «+» definition, `−` toward «−»; leave empty for `not_about`.

Judge each item on its own, from the statement, the direction, the bill's name and the notes. No web search, no other files (in particular never open key.csv or any other result file), no scripts.
Write <ROOT>/local/research/label_accuracy_sample/result_<K>_<J>.csv with the Write tool: header `id,verdict,sign,reason` (reason ≤ 15 words, English, in double quotes). One row per item, all 50 items.
Do not modify any other file. Final reply: ≤ 5 lines (counts per verdict).
