# Blind annotation, pass 1: main topic of Israeli Knesset bills

You are an independent annotator. Work only with files in the folder `jef/independent/blind/` (relative to the current directory):
- `jef/independent/blind/bills.json`: 100 bills: `sample_id`, `bill_id`, `knesset`, `period`, `title_he` (Hebrew title), `notes_he` (start of the explanatory notes, may be empty).
- `jef/independent/blind/issue_catalog.json`: 134 issue ids with English descriptions.

For EVERY bill, read the Hebrew title and notes and choose:
- `primary`: the one issue id from the catalog that best describes the specific policy dispute the bill is about;
- `secondary`: a second issue id if the bill clearly also belongs to another issue, else empty;
- `certainty`: high / medium / low — how sure you are about `primary`.

Rules: use only the ids from the catalog. Judge what the bill actually does, not only how it is framed. Do not look for other files.

Write the result to `jef/independent/blind/labels_topic.csv` with header:
sample_id,bill_id,primary,secondary,certainty
Write rows as you go (all 100 rows at the end). Then reply with a one-line summary.
