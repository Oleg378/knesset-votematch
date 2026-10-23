# Label accuracy on a random sample (2026-10-24)

100 labels (bill × statement theme) drawn uniformly from the labels that feed the positions (export/quiz_bills.json by_direction,
seed 2026): 44 main, 56 secondary. Blind: two Opus judges (a, b) per item saw the statement, the direction definition, the bill's
name and ≤ 700 chars of notes — not our sign or role. Verdict about / borderline / not_about + sign; items with a borderline
or a disagreement went to a third Opus judge, forced choice; majority decides.

- Judge a: {'about': 73, 'borderline': 25, 'not_about': 2}; judge b: {'about': 73, 'borderline': 24, 'not_about': 3}; no direct about/not_about disagreement.
- 27 items to the third judge: 15 about, 12 not_about.
- **Final: topic right 86 / 100; sign right (both judges = ours) 84 / 86 = 98 %** among the right topics; by role: {('main', 'about'): 40, ('secondary', 'not_about'): 10, ('secondary', 'about'): 46, ('main', 'not_about'): 4}.
- Items judged not_about (candidates for the label-check procedure, not removed here): ['A1-2', 'A1-8', 'A1-12', 'A1-23', 'A1-24', 'A1-25', 'A2-4', 'A2-17', 'A2-20', 'A2-26', 'A2-28', 'A2-29', 'A2-44', 'A2-46'].

Files: make_sample.py, items_1.md, items_2.md, key.csv, result_K_J.csv, check3_items.md, check3_result.csv, merge.py.
