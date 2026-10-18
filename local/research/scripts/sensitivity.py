"""Sensitivity of the statement pool and the core to the selection thresholds (external audit С4 / С5, customer Р5, 2026-10-18).
Pool = statements whose direction passes: >= 8 ok lists with >= 3 ex-MKs on it, SD >= SD_T, volume >= V_T, not a remainder.
Volume two ways: «pairs» = sum_nA over those lists (MK × bill authorship pairs, current rule); «bills» = distinct bills sponsored by
the ex-MKs of those lists (proposed, Р5). For each setting: pool size, which current statements drop out, which directions without a
statement would pass; and the core (quiz_flow rule) for r_max 0.6 / 0.7 / 0.8.
-> local/research/sensitivity/report.md
"""
import csv, json, os, sys, statistics as stt
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/sensitivity"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import quiz_select as qs, quiz_flow as qf, labels as LB
cov = {r["letters"]: r for r in csv.DictReader(open(f"{ROOT}/jef/positions/list_coverage.csv"))}
ok = {l for l, r in cov.items() if r["status"] == "ok"}
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str})
LP3 = LP[LP.letters.isin(ok) & (LP.n_mk >= 3)]
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
QD = {r["d"]: r["q"] for r in st}; T = {r["q"]: r["title_en"] for r in st}
plan = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
rem = (set(plan["parents"]) - set(plan["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
# distinct bills by ex-MKs of the qualifying lists
bl = LB.load()["bill_lab"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bi = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy(); cand["mk_id"] = cand.mk_id.astype(int)
mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
bi["l"] = bi.mk_id.map(mk2l); bi = bi.dropna(subset=["l"])
d2b = {}
for b, (m, s) in bl.items():
    for t in m + s:
        if t.get("sign") in ("+", "−", "-"): d2b.setdefault(str(t["n"]), set()).add(b)
rows = []
for d, g in LP3.groupby("d"):
    lists = set(g.letters)
    nb = len(set(bi[bi.l.isin(lists) & bi.bill_id.isin(d2b.get(d, set()))].bill_id))
    rows.append(dict(d=d, lists=len(g), sd=stt.pstdev(g.P) if len(g) > 1 else 0, pairs=int(g.sum_nA.sum()), bills=nb, q=QD.get(d, "")))
C = pd.DataFrame(rows)
L = ["# Sensitivity of the pool and the core to the thresholds (2026-10-18)", "",
     f"Current rule: lists >= 8, SD >= 0.25, volume (pairs) >= 25. Pool now: {len(st)} statements.", "",
     "## Distinct bills vs pairs for the current statements", "",
     "| q | title | pairs | distinct bills |", "|---|---|---|---|"]
for r in C[C.q != ""].sort_values("bills").itertuples():
    L.append(f"| q{r.q} | {T[r.q]} | {r.pairs} | {r.bills} |")
def passes(r, sd_t, vt, vk): return r.lists >= 8 and r.sd >= sd_t and getattr(r, vk) >= vt and r.d not in rem
L += ["", "## Pool by thresholds", "", "Dropped = current statements that would fail; New = directions without a statement that would pass (would need the usual flow).", "",
      "| volume | SD | pool (current statements kept) | dropped | new candidates |", "|---|---|---|---|---|"]
for vk, vts in (("pairs", (20, 25, 30)), ("bills", (8, 10, 12, 15, 20))):
    for vt in vts:
        for sd_t in (0.20, 0.25, 0.30):
            ps = C[[passes(r, sd_t, vt, vk) for r in C.itertuples()]]
            kept = set(ps[ps.q != ""].q); drop = sorted(set(QD.values()) - kept, key=int); new = sorted(ps[ps.q == ""].d)
            L.append(f"| {vk} ≥ {vt} | ≥ {sd_t:.2f} | {len(kept)} | {len(drop)}: " + ", ".join(f"{T[q]}" for q in drop[:12]) + (" …" if len(drop) > 12 else "") + f" | {len(new)} |")
L += ["", "## Core by the similarity limit (current pool)", ""]
ctx = qf._ctx()
for rm in (0.6, 0.7, 0.8):
    L.append(f"- r_max {rm}: " + " · ".join(T[q] for q in qf.core({**qf.FLOW, "core_r_max": rm}, ctx)))
open(f"{OUT}/report.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
