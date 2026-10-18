"""Independent re-check of the label-removal candidate rule (customer, 2026-10-18). Run on the positions BEFORE the removals.
Recomputes from pipeline/labels.py + the database (not from the export or the audit scripts):
  V1  list authorship P_A rebuilt from bills == production P_A (the decomposition the rule relies on);
  V2  r(P_A all labels, P_A main topics only) per statement; the set with r < 0.8 (or undefined) == the 48 audited statements;
  V3  driving bills: shares of all bills sum to the authorship share of the spread; the top bills (85 % / max 8) == audit input;
  V4  resubmissions added to the removals have the same name (without the year) as an audited misfit on the same direction.
"""
import csv, json, os, re, sys
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
W = f"{ROOT}/local/research/secondary_weight_v2"
bill_lab = LB.load()["bill_lab"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bi = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
bi = bi[bi.bill_id.isin(bill_lab.keys())]
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"])
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str})
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
MT["l"] = MT.mk_id.map(mk2l); MT = MT.dropna(subset=["l"])
SGN = {"+": 1, "−": -1, "-": -1}
rows = []
for b, (main, sec) in bill_lab.items():
    seen = set()
    for role, lst in (("main", main), ("sec", sec)):
        for t in lst:
            d, s = str(t["n"]), SGN.get(t.get("sign"))
            if s and d not in seen: seen.add(d); rows.append((b, d, s, role))
lab = pd.DataFrame(rows, columns=["bill_id", "d", "s", "role"])
X = bi.merge(lab, on="bill_id")
def pa(d, roles):
    x = X[(X.d == d) & X.role.isin(roles)].groupby("mk_id").s.mean()
    out = {}
    for l in OK:
        mks = MT[(MT.l == l) & (MT.d == d)].mk_id
        if len(mks): out[l] = sum(x.get(m, 0) for m in mks) / len(mks)
    return out
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
err, R = 0, {}
for q, s in st.items():
    a, m_ = pa(s["d"], ("main", "sec")), pa(s["d"], ("main",))
    for l, v in a.items():
        if abs(v - LP.P_A.get((l, s["d"]), np.nan)) > 1e-3: err += 1
    R[q] = corr([a[l] for l in a], [m_[l] for l in a])
print(f"V1 P_A rebuilt vs production: {err} list×statement cells differ by > 0.001")
sel = {q for q in st if not R[q] >= 0.8}
aud = set(re.findall(r"^## q(\d+) ", open(f"{W}/audit_statements.md").read(), flags=re.M))
print(f"V2 r < 0.8: {len(sel)} statements; audited {len(aud)}; only in rule: {sorted(sel - aud, key=int)}; only audited: {sorted(aud - sel, key=int)}")
print("   r near 0.8 (0.75–0.85): " + ", ".join(f"q{q} {R[q]:.2f}" for q in sorted(st, key=int) if 0.75 <= R[q] <= 0.85))
# V3
inp = open(f"{W}/audit_statements.md").read(); bad = 0; sums = []; ties = []
for blk in re.split(r"^## q", inp, flags=re.M)[1:]:
    q = blk.split(" ")[0]; d = st[q]["d"]
    P = {l: LP.P.get((l, d)) for l in OK if (l, d) in LP.index}; mu = np.mean(list(P.values())); ss = sum((v - mu) ** 2 for v in P.values())
    nL = MT[MT.d == d].groupby("l").size(); NA = MT[MT.d == d].set_index("mk_id").nA
    sh = {}
    for r in X[X.d == d].itertuples():
        l = mk2l.get(r.mk_id)
        if l in P and r.mk_id in NA.index and NA[r.mk_id] > 0:
            sh[r.bill_id] = sh.get(r.bill_id, 0) + r.s / (NA[r.mk_id] * nL[l]) * (P[l] - mu) / ss
    pa_share = sum(LP.P_A.get((l, d), 0) * (P[l] - mu) for l in P) / ss
    sums.append(abs(sum(sh.values()) - pa_share))
    top, acc, pos = [], 0, sum(v for v in sh.values() if v > 0)
    for b, v in sorted(sh.items(), key=lambda t: -t[1]):
        if v <= 0 or len(top) >= 8 or acc >= 0.85 * pos: break
        top.append(str(b)); acc += v
    got = re.findall(r"^- (\d+) \|", blk, flags=re.M)
    if set(top) != set(got):
        diff = sorted(set(top) ^ set(got)); cut_ = sorted(sh.values(), reverse=True)[len(top) - 1]
        tie = all(abs(sh.get(int(b), 0) - cut_) < 1e-9 for b in diff)
        bad += not tie; ties.append(q) if tie else print(f"   q{q}: differ {[(b, round(sh.get(int(b), 0), 4)) for b in diff]}, cut {cut_:.4f}")
print(f"V3 max |sum of shares − authorship share| = {max(sums):.4f}; driving-bill sets differ from the audit input: {bad} (only by equal-share ties at the cut: {len(ties)}; order-only differences ignored)")
# V4
o = json.load(open(f"{ROOT}/jef/directions/labels/overrides.json"))["remove"]["items"]
bn = dict(con.execute("select cast(bill_id as varchar), name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", n).strip()
aud_b = {(i["bill_id"], i["d"]) for i in o if i["source"] == "audit"}
odd = [i for i in o if i["source"] == "resubmission" and not any(base(bn[i["bill_id"]]) == base(bn[b]) for b, d in aud_b if d == i["d"])]
print(f"V4 resubmissions: {sum(i['source']=='resubmission' for i in o)}; without a same-name audited misfit on the same direction: {len(odd)}")
if not os.environ.get("AFTER"): json.dump(sorted([b, d] for b, d in ((str(b), r) for b, (m, s) in bill_lab.items() for r in {str(t['n']) for t in m + s})),
          open(f"{W}/labels_before.json", "w"))
