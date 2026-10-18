"""Quiz direction selection criteria, exactly as in the original selection of the 74 directions (2026-10-15, METHOD_AUDIT п. 7).

Over evaluated lists (status ok) whose position on the direction rests on >= 3 ex-MKs:
  coverage   — at least 8 such lists;
  spread     — population SD of their positions P >= 0.25 ([У] 2026-10-17, new formula P = A + 0.25 V; before: 0.3 on the old scale);
  volume     — sum of sum_nA over them >= MIN_NA (25 since 2026-10-18 [У]; MK × bill authorship pairs, not distinct bills —
               to be replaced by distinct bills after the sensitivity report, customer decision Р5 2026-10-18);
  gov axis   — |r| between P and the list's share of votes with the government in K25 >= 0.8: shown, not a drop and no cap
               ([У] 2026-10-18; the cap of 5 from 2026-10-16 is lifted: with the core → clarifying flow the balance is kept in the
               core instead, quiz_flow.FLOW core_gov_share).
  remainder  — [У] 2026-10-17: what is left of a split direction (bills that fit none of its sub-directions) gets no statement
               even if it passes: mostly secondary topics, largely covered by other statements, the rest unrelated laws.

Usage: python3 pipeline/quiz_select.py [d ...]   -> table for the given directions (default: all quiz directions + all others passing)
"""
import csv, collections, os, statistics as st, sys
import json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POS = os.path.join(ROOT, "jef/positions")
MIN_LISTS, MIN_SD, MIN_NA, GOV_R = 8, 0.25, 25, 0.8   # MIN_NA [У] 2026-10-18: 30 → 25 (q64 at 29; one rule instead of an exception)

def criteria():
    cov = {r["letters"]: r for r in csv.DictReader(open(os.path.join(POS, "list_coverage.csv")))}
    ok = {l for l, r in cov.items() if r["status"] == "ok"}
    G = {(r["letters"], r["knesset"]): float(r["share_with_gov"]) for r in csv.DictReader(open(os.path.join(POS, "government_layer_list.csv")))}
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(POS, "list_topic_positions.csv"))):
        if r["letters"] in ok and int(r["n_mk"]) >= 3: by[(r["d"], r["direction"])].append(r)
    out = {}
    for (d, name), xs in by.items():
        P = [float(x["P"]) for x in xs]; nA = sum(int(x["sum_nA"]) for x in xs)
        g = [G[(x["letters"], "25")] for x in xs]
        c = float(np.corrcoef(P, g)[0, 1]) if np.std(P) > 0 else float("nan")
        sd = st.pstdev(P) if len(P) > 1 else 0.0
        base = len(xs) >= MIN_LISTS and sd >= MIN_SD and nA >= MIN_NA
        out[d] = dict(d=d, name=name, lists=len(xs), sd=sd, nA=nA, r=c, base=base, gov=base and abs(c) >= GOV_R)
    return out

if __name__ == "__main__":
    C = criteria()
    quiz = {r["d"]: r["q"] for r in csv.DictReader(open(os.path.join(ROOT, "jef/quiz/statements_v4.csv"))) if r["status"] == "ok"}
    ds = sys.argv[1:] or sorted(set(quiz) | {d for d, x in C.items() if x["base"]}, key=lambda d: (d not in quiz, d))
    plan = json.load(open(os.path.join(ROOT, "jef/directions/split/plan.json")))
    import labels   # later split stages (2026-10-18): their parents are remainders too
    remainder = (set(plan["parents"]) - set(plan["keep"])) | {d for p in labels.later_plans() for d in p["parents"]}
    gov = sorted([x for x in C.values() if x["gov"]], key=lambda x: -x["nA"])
    print(f"gov-axis directions passing the other criteria (no cap): {[(x['d'], x['nA']) for x in gov]}")
    print(f"{'d':6} {'q':>3} {'lists':>5} {'SD':>5} {'nA':>5} {'r_gov':>6}  verdict  direction")
    for d in ds:
        x = C.get(d)
        if not x: print(f"{d:6} {quiz.get(d, ''):>3}  no lists with >= 3 ex-MKs"); continue
        v = ("pass (gov axis)" if x["gov"] else "pass") if x["base"] else "FAIL"
        if d in remainder and x["base"]: v = "remainder"
        print(f"{d:6} {quiz.get(d, ''):>3} {x['lists']:>5} {x['sd']:>5.2f} {x['nA']:>5} {x['r']:>6.2f}  {v:8} {x['name']}")
