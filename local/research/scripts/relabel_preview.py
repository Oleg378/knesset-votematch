"""Preview of removing (bill, direction) labels: list positions on one direction before/after, SD, rank, the core.
Usage: python3 local/research/scripts/relabel_preview.py <direction> <bill_id>...   (labels of those bills on <direction> removed)
"""
import csv, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D0, DROP = sys.argv[1], {(int(b), sys.argv[1]) for b in sys.argv[2:]}
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "relabel_preview", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bill_lab, bi, pv, va, share, SGN, signed_topics = (ns[k] for k in ("bill_lab", "bi", "pv", "va", "share", "SGN", "signed_topics"))
def vote_label(r):
    if r.vote_id in ns["pk_agent"]: return ns["pk_agent"][r.vote_id]
    if r.vote_id in ns["pk_whole"]: return ns["pk_whole"][r.vote_id]
    return bill_lab.get(r.bill_id)
AB = pd.DataFrame([(b, d, s) for b, lab in bill_lab.items() for d, s in signed_topics(lab).items()], columns=["bill_id", "d", "s"])
VT = {r.vote_id: (r.bill_id, signed_topics(vote_label(r)) if vote_label(r) is not None else {}) for r in va.itertuples()}
KEY = ["mk_id", "knesset", "d"]
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); cm = cand.drop_duplicates("mk_id"); mk2l = dict(zip(cm.mk_id, cm.letters))
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters); LN = dict(zip(cov.letters, cov.list_name))
gl = pd.read_csv(f"{ROOT}/jef/positions/government_layer_list.csv"); gl = gl[gl.knesset == 25]; GOV = dict(zip(gl.letters, gl.share_with_gov))
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]

def lists(drop):
    ab = AB[[(int(b), d) not in drop for b, d in zip(AB.bill_id, AB.d)]]
    A = bi.merge(ab, on="bill_id").groupby(KEY).s.agg(["mean", "size"]).reset_index().rename(columns={"mean": "A", "size": "nA"})
    vrows = [(r.mk_id, r.knesset, d, s * r.v) for r in pv.itertuples() for d, s in VT[r.vote_id][1].items()
             if (int(VT[r.vote_id][0]) if VT[r.vote_id][0] == VT[r.vote_id][0] and VT[r.vote_id][0] is not None else -1, d) not in drop]
    V = pd.DataFrame(vrows, columns=KEY + ["c"]).groupby(KEY).c.agg(["mean", "size"]).reset_index().rename(columns={"mean": "pos", "size": "nV"})
    V = V.join(share, on=["mk_id", "knesset"]).dropna(subset=["gov_share"])
    g = V.groupby(["knesset", "d"]); mx, my = g.gov_share.transform("mean"), g.pos.transform("mean")
    c_ = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform("mean")
    v_ = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform("mean")
    V["V"] = V.pos - my - (c_ / v_.where(v_ > 1e-9)).fillna(0) * (V.gov_share - mx)
    def pool(df, val, n):
        g = df.assign(x=df[val] * df[n]).groupby(["mk_id", "d"]); return pd.DataFrame({val: g.x.sum() / g[n].sum(), n: g[n].sum()})
    T = pool(A, "A", "nA").join(pool(V, "V", "nV"), how="outer").reset_index()
    T["P_A"] = T.A.fillna(0); T["P_V"] = 0.25 * T.V.fillna(0); T["P"] = T.P_A + T.P_V
    T = T.assign(l=T.mk_id.map(mk2l)).dropna(subset=["l"])
    return T.groupby(["l", "d"]).agg(P=("P", "mean"), P_A=("P_A", "mean"), P_V=("P_V", "mean"), mk=("mk_id", "size"),
                                     authors=("nA", lambda x: int((x > 0).sum())), nA=("nA", "sum"), nV=("nV", "sum"))
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
def vals(LP, d): return {l: LP.P.get((l, d)) for l in OK if (l, d) in LP.index}
def loo(x): x = np.array(x); return min(np.std(np.delete(x, i)) for i in range(len(x)))
def ranking(LP):
    rows = []
    for s in st:
        v = vals(LP, s["d"])
        if len(v) >= 2: x = list(v.values()); rows.append((np.std(x) * len(v) / len(OK), s["q"], abs(corr(x, [GOV[l] for l in v])) >= 0.8))
    return sorted(rows, key=lambda t: (-t[0], int(t[1])))
def core(LP, n=8):
    out, dirs, ng = [], set(), 0; dq = {s["q"]: s["d"] for s in st}
    for sep, q, og in ranking(LP):
        if len(out) >= n: break
        if dq[q] in dirs or (og and ng >= n // 2): continue
        vq = vals(LP, dq[q])
        if any(abs(corr(*zip(*[(vq[l], vals(LP, dq[o])[l]) for l in vq if l in vals(LP, dq[o])]))) >= 0.8 for o in out): continue
        out.append(q); dirs.add(dq[q]); ng += og
    return out
B, A_ = lists(set()), lists(DROP)
q0 = next(s["q"] for s in st if s["d"] == D0)
print(f"direction {D0} (q{q0}); labels removed: {len(DROP)}")
print(f"{'list':5} {'name':30} {'P before':>9} {'P after':>8} | {'A part':>13} {'votes part':>13} | {'authors':>9} {'bills':>9} {'votes':>9}")
for l in OK:
    b, a = B.loc[(l, D0)] if (l, D0) in B.index else None, A_.loc[(l, D0)] if (l, D0) in A_.index else None
    f = lambda r, k, fmt: (format(r[k], fmt) if r is not None else "—")
    print(f"{l:5} {LN[l][:30]:30} {f(b,'P','+.2f'):>9} {f(a,'P','+.2f'):>8} | {f(b,'P_A','+.2f'):>6}→{f(a,'P_A','+.2f'):>6} {f(b,'P_V','+.2f'):>6}→{f(a,'P_V','+.2f'):>6} | "
          f"{f(b,'authors','.0f'):>4}→{f(a,'authors','.0f'):>4} {f(b,'nA','.0f'):>4}→{f(a,'nA','.0f'):>4} {f(b,'nV','.0f'):>4}→{f(a,'nV','.0f'):>4}")
for name, LP in (("before", B), ("after", A_)):
    x = list(vals(LP, D0).values()); rk = [q for _, q, _ in ranking(LP)]
    print(f"{name}: SD {np.std(x):.2f}, without the most extreme list {loo(x):.2f}; rank by SD {rk.index(q0)+1} of {len(rk)}; core: {','.join(core(LP))}")
