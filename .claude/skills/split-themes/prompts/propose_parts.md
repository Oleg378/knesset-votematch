You are a political-science analyst for an Israeli election quiz. Some "directions" (quantities a bill increases "+" or decreases "−") turned out to be baskets: bills with the same sign are about unrelated subjects, or are pushed by opposite camps for different target groups.

Work only with the files named here. Do not open other files and do not run scripts.

Input: <ROOT>/local/research/basket_split2/input_K.json — for each direction: name, plus/minus definitions, and ALL bills labeled with it, grouped by name without the year (Hebrew title, role main/secondary, sign). 
Catalog: <ROOT>/local/research/basket_split2/catalog.md — all current directions (id — name, +, −).

For each direction decide:
- "keep" — actually coherent (one subject; same-sign bills pushed for the same reason) — explain;
- "split" — define 2–4 sub-directions. Each sub-direction must be a coherent quantity of the same kind as the original (a law can increase or decrease it), defined by SUBJECT or by TARGET GROUP, whichever separates the camps. Rules: neutral names (no evaluative words, no party names); clear "+" and "−" in English (these are fed to a classifier); together they should cover the substantive bills; bills that fit none stay only in the original direction (say roughly how many). Don't invent sub-directions without bills: each needs ≥5 distinct names from the list (main or secondary). If a sub-direction is the same quantity as a direction in the catalog (by that direction's own + and − definitions, not merely a related or broader one), give its id in "same_as" — its bills will be transferred there; otherwise "same_as": null.
- "technical" — the direction is a technical/administrative basket with no value for a voter's choice.

Write the result with the Write tool to <ROOT>/local/research/basket_split2/out_K.json:
{"<d>": {"decision": "keep|split|technical", "reason": "...(Russian)",
  "subs": [{"key": "<d>s1", "same_as": "<catalog id or null>", "name_ru": "...", "name_en": "...", "plus_en": "...", "minus_en": "...",
            "camp_note": "(Russian) who tends to push + / −", "example_bill_ids": ["..", ".."], "approx_names": N}],
  "leftover_names": N}}
Every direction of the input must be in the output. Reply with one line per direction (Russian): decision and the sub-direction names.
