"""Р6 (customer 2026-10-18, external audit С8): salience of topics by official Knesset data, to compare with the current
statement pool (selected by spread and volume). Per direction, counting bills where it is a MAIN topic (Knessets 24–25):
  passed  — bills passed in the third reading (status 118);
  votes   — roll-call votes on those bills (all four stages);
  mks     — distinct MKs who sponsored them.
Salience = mean of the three percentile ranks among all directions. Shown for the current statements and for directions that pass
the data criteria but have no statement. -> local/research/salience/report.md
"""
import csv, json, os, sys
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/salience"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB, quiz_select as qs
lab = LB.load(); bl = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: r["name_en"] for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = v["name_en"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
B = con.execute("select bill_id, status_id from bills where knesset in (24,25)").df().set_index("bill_id").status_id
V = con.execute("select a.bill_id, count(distinct a.vote_id) n from vote_attrs a where a.kind='bill' and a.stage in ('preliminary','first','second','third') group by 1").df().set_index("bill_id").n
I = con.execute("select bill_id, mk_id from bill_initiators where is_initiator").df()
main = {}
for b, (m, s) in bl.items():
    for t in m:
        if t.get("sign") in ("+", "−", "-"): main.setdefault(str(t["n"]), set()).add(b)
rows = []
for d, bs in main.items():
    bs = [b for b in bs if b in B.index]
    rows.append(dict(d=d, passed=int(sum(B.get(b) == 118 for b in bs)), votes=int(sum(V.get(b, 0) for b in bs)),
                     mks=I[I.bill_id.isin(bs)].mk_id.nunique()))
S = pd.DataFrame(rows)
for c in ("passed", "votes", "mks"): S[c + "_r"] = S[c].rank(pct=True)
S["salience"] = S[["passed_r", "votes_r", "mks_r"]].mean(1)
st = {r["d"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
C = qs.criteria()
plan1 = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
rem = (set(plan1["parents"]) - set(plan1["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
removed = {r["d"] for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] != "ok" and r["d"]}
S["in_quiz"] = S.d.isin(st); S["passes"] = S.d.map(lambda d: bool(C.get(d, {}).get("base")) and d not in rem)
S = S.sort_values("salience", ascending=False).reset_index(drop=True); S["rank"] = S.index + 1
L = ["# Salience of topics by Knesset data (2026-10-18)", "", f"{len(S)} directions with main-topic bills. Salience = mean percentile of: laws passed (3rd reading), roll-call votes, distinct sponsoring MKs.", "",
     "## Current statements, by salience", "", "| rank | q | title | passed | votes | MKs | salience |", "|---|---|---|---|---|---|---|"]
for r in S[S.in_quiz].itertuples():
    q = st[r.d]; L.append(f"| {r.rank} | q{q['q']} | {q['title_en']} | {r.passed} | {r.votes} | {r.mks} | {r.salience:.2f} |")
L += ["", "## Directions that pass the data criteria but have no statement, top 25 by salience", "", "| rank | direction | passed | votes | MKs | salience | why no statement |", "|---|---|---|---|---|---|---|"]
for r in S[S.passes & ~S.in_quiz].head(25).itertuples():
    why = "statement removed earlier" if r.d in removed else "not written (basket / duplicate / narrow — local/research/new_statements/drafts.md)"
    L.append(f"| {r.rank} | {r.d} {D.get(r.d, '')} | {r.passed} | {r.votes} | {r.mks} | {r.salience:.2f} | {why} |")
q_sal = S[S.in_quiz].salience; L += ["", f"Current statements: median salience {q_sal.median():.2f}; in the bottom third of all directions: {int((S[S.in_quiz]['rank'] > len(S) * 2 / 3).sum())} of {len(q_sal)}."]
open(f"{OUT}/report.md", "w").write("\n".join(L) + "\n"); S.to_csv(f"{OUT}/salience.csv", index=False)
print("\n".join(L[-1:])); print(S[S.in_quiz].tail(10)[["rank", "d", "passed", "votes", "mks"]].to_string())
