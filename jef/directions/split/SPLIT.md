You are a political-science analyst for an Israeli election quiz. Some "directions" (quantities a bill increases "+" or decreases "−") turned out to be baskets: bills with the same sign are about unrelated subjects, or are pushed by opposite camps for different target groups (e.g. "property protection": return of Ikrit/Biram and absentee property for Arab citizens vs. return of pre-1948 Jewish land in Judea and Samaria). An average party position on such a direction is meaningless.

Input: jef/directions/split/input_K.json — for each direction: names, plus/minus definitions, and ALL bills labeled with it (Hebrew title, role main/secondary, sign).

For each direction decide:
- "keep" — actually coherent (one subject; same-sign bills pushed for the same reason) — explain;
- "split" — define 2–4 sub-directions. Each sub-direction must be a coherent quantity of the same kind as the original (a law can increase or decrease it), defined by SUBJECT or by TARGET GROUP, whichever separates the camps. Rules: neutral names (no evaluative words, no party names); clear "+" and "−" in English (these are fed to a classifier); together they should cover the substantive bills; bills that fit none stay only in the original direction (say roughly how many). Don't invent sub-directions without bills: each needs ≥5 bills from the list (main or secondary).
- "technical" — the direction is a technical/administrative basket with no value for a voter's choice.

Write via Python jef/directions/split/out_K.json:
{"<d>": {"decision": "keep|split|technical", "reason": "...(Russian)",
  "subs": [{"key": "<d>a", "name_ru": "...", "name_en": "...", "plus_en": "...", "minus_en": "...",
            "camp_note": "(Russian) who tends to push + / −", "example_bill_ids": ["..", ".."], "approx_bills": N}],
  "leftover_bills": N}}
Also print a short Russian summary per direction. Do not modify other files.
