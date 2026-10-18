# Blind annotation, pass 2: direction of Israeli Knesset bills

You are an independent annotator. Use only `jef/independent/blind/direction_items.json` (relative to the current directory). It has 60 items: `sample_id`, `bill_id`, `title_he`, `notes_he` (start of the explanatory notes, may be empty), `question` and `levels` (5 levels, index 0..4).

For EVERY item:
1. `scale_fits`: yes if the question makes sense for this bill (the bill really bears on that dispute), otherwise no.
2. `level`: if it fits, the level index 0..4 that best describes what the bill would actually do; use 2 when it is neutral or procedural. If it does not fit, write na.
3. `certainty`: high / medium / low.
4. `note`: a few English words explaining your choice.

Judge the bill's real effect, not how its authors frame it: explanatory notes argue for the bill and may use favourable wording. Do not look at any other file.

Write `jef/independent/blind/labels_direction.csv` with header:
sample_id,bill_id,scale_fits,level,certainty,note
(quote the note field). All 60 rows. Then reply with a one-line summary.
