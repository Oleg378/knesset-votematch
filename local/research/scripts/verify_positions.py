"""Independent recomputation of the authorship part and the list aggregation from the database, by the documented rules
(METHOD_AUDIT §5–6, SU 27.2–27.3), compared with production jef/positions/ (customer, 2026-10-18: «formulas work as intended»).
Documented rules tested:
  A  = mean sign over the topics of the bills the MK initiated (IsInitiator = true), Knessets 24–25, technical bills excluded,
       main and secondary equal, unsigned topics skipped; both Knessets together (pooled = mean over all the MK's bills).
  P  = A + 0.25·V (missing component = 0); V taken from production (its government-share residual is not re-derived here).
  list P = mean over the list's ex-MKs (exact/manual matches) that have any action on the direction.
Also: sum_nA, n_mk; the CSV and the export agree; withdrawn initiators (KNS_BillHistoryInitiator «חזר בו») — are they in bill_initiators?
"""
import json, os, sys
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl, tech = lab["bill_lab"], lab["technical"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bi = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
bi = bi[~bi.bill_id.astype(str).isin(tech)]
S = {"+": 1, "−": -1, "-": -1}
rows = []
for b, (m, s) in bl.items():
    seen = set()
    for t in m + s:
        d = str(t["n"]); x = S.get(t.get("sign"))
        if x and d not in seen: seen.add(d); rows.append((b, d, x))
X = bi.merge(pd.DataFrame(rows, columns=["bill_id", "d", "s"]), on="bill_id")
A = X.groupby(["mk_id", "d"]).s.agg(["mean", "size"]).rename(columns={"mean": "A", "size": "nA"})
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str}).set_index(["mk_id", "d"])
j = MT.join(A, rsuffix="_ind")
dA = (j.A.fillna(0) - j.A_ind.fillna(0)).abs(); dn = (j.nA - j.nA_ind.fillna(0)).abs()
print(f"A: {len(j)} MK×direction rows; |A prod − A indep| > 1e-3: {(dA > 1e-3).sum()}; nA differs: {(dn > 0).sum()}")
missing = A.index.difference(MT.index); print(f"   MK×direction with own bills but no production row: {len(missing)}")
P_ind = j.A_ind.fillna(0) + MT.P_V
print(f"P = A + P_V: rows differing > 1e-3: {((P_ind - MT.P).abs() > 1e-3).sum()};  P_V = 0.25·V: {((0.25 * MT.V.fillna(0) - MT.P_V).abs() > 1e-3).sum()}")
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy(); cand["mk_id"] = cand.mk_id.astype(int)
mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
T = MT.reset_index(); T["l"] = T.mk_id.map(mk2l); T = T.dropna(subset=["l"])
L = T.rename(columns={"l": "letters"}).groupby(["letters", "d"]).agg(P=("P", "mean"), n=("mk_id", "size"), nA=("nA", "sum"))
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"])
k = LP.join(L, how="outer", rsuffix="_y"); k = k.rename(columns={"P": "P_x"})
print(f"list P = mean over ex-MKs with data: differing > 1e-3: {((k.P_x - k.P_y).abs() > 1e-3).sum()}; n_mk differs: {(k.n_mk != k.n).sum()}; sum_nA differs: {(k.sum_nA != k.nA).sum()}")
dup = cand.groupby("mk_id").letters.nunique(); print(f"ex-MKs matched to more than one list: {int((dup > 1).sum())}")
# all ex-MKs of a list vs those with data on a direction: the mean excludes MKs with no action on the direction
exm = cand.drop_duplicates("mk_id").groupby("letters").mk_id.size()
k2 = LP.reset_index(); k2["ex"] = k2.letters.map(exm); print(f"list×direction rows where n_mk < ex-MKs of the list: {(k2.n_mk < k2.ex).sum()} of {len(k2)}")
# withdrawn initiators
wd = con.execute("select count(*) from bill_initiator_history h join bill_initiators i using(bill_id, mk_id) where h.reason like '%חזר%' and i.is_initiator").fetchone()[0]
print(f"withdrawn initiators (history «חזר בו») still counted as initiators: {wd}")
# export vs CSV
D = json.load(open(f"{ROOT}/export/quiz_data.v2.json"))
st = {s["q"]: s["d"] for s in D["statements"]}; bad = 0
for Lx in D["lists"]:
    for q, p in Lx["positions"].items():
        d = q   # export keys are directions
        if (Lx["id"], d) in LP.index and abs(LP.P[(Lx["id"], d)] - p["P"]) > 1e-3:
            bad += 1
            if bad <= 3: print("   e.g.", Lx["id"], d, LP.P[(Lx["id"], d)], p)
print(f"export positions vs CSV: {bad} differ; export keys are {'statement ids' if set(D['lists'][0]['positions']) <= set(st) else 'directions'}")
