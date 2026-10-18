You are an independent reviewer. Check whether each quiz statement actually corresponds to the real Knesset bills behind its direction. Party positions on a direction are computed from these bills (mainly from who authored them), so a statement that talks about something the bills don't contain will match voters to parties on the wrong basis.

Input: jef/quiz/align_input_K.json. For every item:
- direction: name, plus/minus definitions (a direction is a quantity a bill increases "+" or decreases "−");
- statement (Russian) and agree_key: agreeing with the statement = moving the direction to agree_key;
- bills_main_plus / bills_main_minus: how many bills have this direction as a main topic with each sign; bills_total;
- bills: up to 40 Hebrew titles of such bills (main topic, preferring bills authored by 2026 candidates; for thin directions secondary ones too), each with its sign.

For each item judge:
1. coverage: does the statement's subject match what most of these bills are about? "good" (the bills' core subject), "partial" (covers a minority subtheme or is broader/narrower), "poor" (the bills are mostly about something else, or the statement's specific example has no bills).
2. key_consistency: bills signed agree_key should be the ones an agreeing voter supports. "yes" / "no" / "unclear". Spot sign-label errors in bills if obvious.
3. heterogeneous: are the bills a mixed basket where "+" (or "−") is pushed by opposite camps for unrelated reasons, so an average position is meaningless? yes/no.
4. If coverage is partial/poor or key inconsistent: propose a better statement in Russian following the same style (≤25 words, neutral, no evaluative words, one idea, an explicit cost "даже если…" for any "more of a good thing", agree_key stated). If the direction is a heterogeneous basket, say "drop" and why. If the bills naturally split into two coherent subthemes, you may propose two statements (a/b) on the same direction.

Write via Python jef/quiz/align_out_K.csv with columns: no, d, coverage, key_consistency, heterogeneous, core_subject (short, Russian: what the bills are really about), problem (short Russian), proposal (Russian statement(s) or "drop" or empty), proposal_key. Do not modify other files. Print a summary: counts per column, list of poor/inconsistent/heterogeneous items.
