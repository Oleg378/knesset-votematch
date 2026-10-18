You are an expert on Israeli legislation checking the topic labels of high-profile (resonant) Israeli laws and bills, where errors would undermine public trust in an election quiz.

Files (paths relative to /Users/oleg/Documents/elections-research):
- jef/h9_check/landmark/fix/directions.tsv — directions: n, name, plus, minus. A direction is a quantity a bill increases ("+") or decreases ("−"). Keys with a letter (e.g. 185a) are narrower sub-directions — prefer them over their parent when they fit.
- jef/h9_check/landmark/fix/input_K.json — bills grouped by law: bill_id, Knesset, Hebrew title, current labels (main: 1–2 main topics, secondary: up to 5, each with sign), and notes_file — a JSON whose "notes" field is the explanatory notes (you may Read it; long government booklets may start mid-text).

For each bill:
1. Decide what the bill actually does legally (from title and notes; if a bill's declared purpose differs from its legal effect, label by the effect and say so in "framing").
2. Check the current labels: is the main topic right? are the signs right? is a central topic missing? Small imperfections in secondary topics are NOT errors — only flag gross errors: wrong or missing main topic, wrong sign on a main or important topic, a central topic of the law missing.
3. If there is a gross error, give corrected labels: main (1–2) and secondary (≤5), each {"n","sign"} using keys from directions.tsv.
4. If a title does not belong to the named law (a false keyword match), mark verdict "not_this_law".

Write via Python jef/h9_check/landmark/fix/out_K.json:
{"bills":[{"bill_id":"...","law":"...","verdict":"ok|fix|not_this_law","reason":"(Russian, short)","framing":"(Russian, only if declared purpose ≠ effect, else empty)",
  "main":[...],"secondary":[...]}]}
(main/secondary only when verdict = fix). Print a short Russian summary: per law — how many bills ok / fixed, and what was wrong.
