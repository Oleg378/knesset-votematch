You are an independent reviewer for an Israeli election quiz (Likert: полностью согласен … полностью не согласен, «не знаю»). Read jef/quiz/GUIDELINES.md (rules for statements, Russian) first.

Input: jef/quiz/v4_input.json. Each item has a direction (a quantity a bill increases "+" or decreases "−", with definitions), counts of its bills by sign, up to 40 Hebrew titles of its bills with sign, and either:
- task "draft": write ONE Russian statement whose subject is what most of these bills are about; choose agree_key so that agreeing = supporting the bills with that sign; follow the guidelines (≤25 words, neutral, one idea, explicit cost "даже если…" for any "more of a good thing", no evaluative words, no party names);
- task "check": verify the given statement: does its subject match the core of the bills (good/partial/poor)? does agree_key match the bill signs (yes/no/unclear)? does it follow the guidelines? If any problem, propose a corrected statement and key; otherwise leave the proposal empty.

Write via Python jef/quiz/v4_out.csv with columns: no, d, task, coverage, key_ok, guideline_issues (short Russian or empty), statement_final (the drafted statement, or the corrected one, or the original if fine), agree_key_final, note (short Russian). Do not modify other files. Print a short summary listing items you changed and why.
