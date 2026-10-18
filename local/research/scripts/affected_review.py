"""Statements touched by the label removals (2026-10-18): selection metrics before/after, core rank, and whether the bills that now
drive the list spread were reviewed by the audit (wording check needed only where unreviewed bills now matter).
Usage: python3 local/research/scripts/affected_review.py <before list_topic_positions.csv>  -> local/research/secondary_weight_v2/affected.md
"""
import csv, json, os, re, sys
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB, quiz_flow as QF
W = f"{ROOT}/local/research/secondary_weight_v2"
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]; SQ = {s["q"]: s for s in st}
rm = json.load(open(f"{ROOT}/jef/directions/labels/overrides.json"))["remove"]["items"]
AFF = sorted({i["q"] for i in rm}, key=int)
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
gl = pd.read_csv(f"{ROOT}/jef/positions/government_layer_list.csv"); gl = gl[gl.knesset == 25]; GOV = dict(zip(gl.letters, gl.share_with_gov))
LPS = {"before": pd.read_csv(sys.argv[1], dtype={"d": str}).set_index(["letters", "d"]),
       "after": pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"])}
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
def vals(LP, d): return {l: LP.P[(l, d)] for l in OK if (l, d) in LP.index and LP.n_mk[(l, d)] >= 3}   # as quiz_select: lists with >= 3 MKs
def allvals(LP, d): return {l: LP.P[(l, d)] for l in OK if (l, d) in LP.index}
def nA(LP, d): return int(LP.xs(d, level="d").sum_nA.sum()) if d in LP.index.get_level_values("d") else 0
def loo(x): x = np.array(x); return min(np.std(np.delete(x, i)) for i in range(len(x)))
def ranking(LP):
    rows = []
    for s in st:
        v = allvals(LP, s["d"])
        if len(v) >= 2: x = list(v.values()); rows.append((np.std(x) * len(v) / len(OK), s["q"]))
    return [q for _, q in sorted(rows, key=lambda t: (-t[0], int(t[1])))]
sel_before = open(f"{os.path.dirname(sys.argv[1])}/../sel_before.txt").read(); sel_after = open(f"{os.path.dirname(sys.argv[1])}/../sel_after.txt").read()
def verdict(txt, d):
    m = re.search(rf"^{re.escape(d)}\s+\d+\s+(\d+)\s+([\d.]+)\s+(\d+)\s+(-?[\d.]+)\s+(pass \(gov axis\)|pass|FAIL|remainder)", txt, flags=re.M)
    return m.groups() if m else None
core_after = QF.core()
rk = {k: ranking(LP) for k, LP in LPS.items()}
# drivers now (after removals) and whether the audit saw them
bill_lab = LB.load()["bill_lab"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bi = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str})
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
MT["l"] = MT.mk_id.map(mk2l); MT = MT.dropna(subset=["l"])
SGN = {"+": 1, "−": -1, "-": -1}
lab = pd.DataFrame([(b, str(t["n"]), SGN[t["sign"]]) for b, (m, s) in bill_lab.items() for t in m + s if t.get("sign") in SGN],
                   columns=["bill_id", "d", "s"]).drop_duplicates(["bill_id", "d"])
X = bi.merge(lab, on="bill_id")
inp = open(f"{W}/audit_statements.md").read()
seen = {blk.split(" ")[0]: set(re.findall(r"^- (\d+) \|", blk, flags=re.M)) for blk in re.split(r"^## q", inp, flags=re.M)[1:]}
res = open(f"{W}/audit_result.md").read()
verd = {m.group(1): m.group(2) for m in re.finditer(r"^\| q(\d+) \| (\w+) \|", res, flags=re.M)}
def drivers(d):
    LP = LPS["after"]; P = allvals(LP, d); mu = np.mean(list(P.values())); ss = sum((v - mu) ** 2 for v in P.values())
    nL = MT[MT.d == d].groupby("l").size(); NA = MT[MT.d == d].set_index("mk_id").nA
    sh = {}
    for r in X[X.d == d].itertuples():
        l = mk2l.get(r.mk_id)
        if l in P and r.mk_id in NA.index and NA[r.mk_id] > 0: sh[str(r.bill_id)] = sh.get(str(r.bill_id), 0) + r.s / (NA[r.mk_id] * nL[l]) * (P[l] - mu) / ss
    top, acc, pos = [], 0, sum(v for v in sh.values() if v > 0)
    for b, v in sorted(sh.items(), key=lambda t: -t[1]):
        if v <= 0 or len(top) >= 8 or acc >= 0.85 * pos: break
        top.append((b, v)); acc += v
    return top
L = ["| q | title | removed | SD before → after | SD w/o extreme | nA before → after | pool | rank by SD (of 83) | core | audit verdict | new driving bills not seen by the audit (share) |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for q in AFF:
    d = SQ[q]["d"]; b, a = verdict(sel_before, d), verdict(sel_after, d)
    vb, va_ = vals(LPS["before"], d), vals(LPS["after"], d)
    top = drivers(d); new = [(x, v) for x, v in top if x not in seen.get(q, set())]
    L.append(f"| q{q} | {SQ[q]['title_en']} | {sum(i['q'] == q for i in rm)} | {float(b[1]):.2f} → {float(a[1]):.2f} | {loo(list(va_.values())):.2f} | {b[2]} → {a[2]} | {a[4].strip()} | "
             f"{rk['before'].index(q)+1} → {rk['after'].index(q)+1} | {'yes' if q in core_after else '—'} | {verd.get(q, '—')} | "
             f"{len(new)} ({sum(v for _, v in new):.2f})" + (": " + ", ".join(x for x, _ in new) if new else "") + " |")
open(f"{W}/affected.md", "w").write("\n".join(L) + "\n")
print("\n".join(L)); print("core after:", core_after)
