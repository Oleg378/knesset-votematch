"""Weight of secondary topics, re-tested (customer approval 2026-10-17).

The test of 2026-10-14 (local/research/positions_test/test_weights.py) chose «secondary = main» by cross-Knesset prediction, but its
target in the test Knesset was itself computed with secondary = main, which favours that weight. Here the same kind of test is
run with two fixed targets, so the bias is visible:
  target «equal»  — the test-Knesset position with secondary topics = main (the old target);
  target «main»   — the test-Knesset position from main topics only.
If one weight wins on both targets, the result does not depend on how the target is defined; if each target picks its own
weight, the test cannot tell.

Position as in pipeline/positions.py (P = A + 0.25 V, A centered per Knesset × direction, V the residual of private-bill votes on
the government share), per MK × Knesset; a topic's weight is 1 for a main topic and w for a secondary one (w = 0, .25, .5, 1).
Prediction: train Knesset → test Knesset (24→25 and 25→24), MKs present in both; target cells need >= 3 actions (bills + votes).
r at MK × direction level and for lists 2026 (mean over the list's ex-MKs, cells with >= 2 MKs); all directions and quiz
directions; bootstrap over MKs (500) for the difference from w = 1.

Usage: python3 local/research/scripts/secondary_weight_test.py   -> local/research/secondary_weight/summary.txt
"""
import csv, os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/secondary_weight"); os.makedirs(OUT, exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
assert cut in src
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "secondary_weight_test", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bill_lab, bi, pv, va, share, SGN = (ns[k] for k in ("bill_lab", "bi", "pv", "va", "share", "SGN"))

def roles(lab):
    out = {}
    for role, lst in (("main", lab[0]), ("sec", lab[1])):
        for t in lst:
            s = SGN.get(t.get("sign"))
            if s and str(t["n"]) not in out: out[str(t["n"])] = (s, role)
    return out
def vote_label(r):
    if r.vote_id in ns["pk_agent"]: return ns["pk_agent"][r.vote_id]
    if r.vote_id in ns["pk_whole"]: return ns["pk_whole"][r.vote_id]
    return bill_lab.get(r.bill_id)
ab = pd.DataFrame([(b, d, s, r) for b, lab in bill_lab.items() for d, (s, r) in roles(lab).items()], columns=["bill_id", "d", "s", "role"])
AU = bi.merge(ab, on="bill_id")
vt = {r.vote_id: (roles(vote_label(r)) if vote_label(r) is not None else {}) for r in va.itertuples()}
VO = pd.DataFrame([(r.mk_id, r.knesset, d, s * r.v, ro) for r in pv.itertuples() for d, (s, ro) in vt[r.vote_id].items()],
                  columns=["mk_id", "knesset", "d", "c", "role"])
KEY = ["mk_id", "knesset", "d"]

def position(w):
    a = AU.assign(w=np.where(AU.role == "main", 1.0, w)); a = a[a.w > 0]
    A = a.assign(ws=a.w * a.s).groupby(KEY).agg(S=("ws", "sum"), N=("w", "sum"), nA=("s", "size")).reset_index()
    A["A"] = A.S / A.N; A["A"] = A.A - A.groupby(["knesset", "d"]).A.transform("mean")
    v = VO.assign(w=np.where(VO.role == "main", 1.0, w)); v = v[v.w > 0]
    V = v.assign(wc=v.w * v.c).groupby(KEY).agg(S=("wc", "sum"), N=("w", "sum"), nV=("c", "size")).reset_index()
    V["pos"] = V.S / V.N
    V = V.join(share, on=["mk_id", "knesset"]).dropna(subset=["gov_share"])
    g = V.groupby(["knesset", "d"]); mx, my = g.gov_share.transform("mean"), g.pos.transform("mean")
    cov = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform("mean")
    var = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform("mean")
    V["V"] = V.pos - my - (cov / var.where(var > 1e-9)).fillna(0) * (V.gov_share - mx)
    T = A.set_index(KEY)[["A", "nA"]].join(V.set_index(KEY)[["V", "nV"]], how="outer")
    T[["nA", "nV"]] = T[["nA", "nV"]].fillna(0)
    T["P"] = T.A.fillna(0) + 0.25 * T.V.fillna(0)
    return T

WS = [0, 0.25, 0.5, 1]
pos = {w: position(w) for w in WS}
targets = {"equal": pos[1.0], "main": pos[0]}
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])]
cand["mk_id"] = cand.mk_id.astype(int); mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
quiz = {r["d"] for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
both = set(pd.concat([p.reset_index() for p in pos.values()]).groupby("mk_id").knesset.nunique().loc[lambda s: s == 2].index)
rng = np.random.default_rng(20261017)

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan

p("r between the train-Knesset position (weight w of secondary topics) and the test-Knesset target; mean of 24→25 and 25→24")
p("Δ = r(w) − r(1) with a 95% bootstrap interval over MKs (MK level)\n")
for scope in ("all directions", "quiz directions"):
    for tname, T in targets.items():
        p(f"{scope}, target «{tname}»:")
        p(f"   {'w':>5} {'r MK':>6} {'Δ vs w=1 [95%]':>22} {'r list':>7} {'cells':>6}")
        res = {}
        for w in WS:
            rs, rl, cells, per_mk = [], [], 0, []
            for tr, te in ((24, 25), (25, 24)):
                t = T.reset_index(); t = t[(t.knesset == te) & t.mk_id.isin(both) & ((t.nA + t.nV) >= 3)]
                if scope == "quiz directions": t = t[t.d.isin(quiz)]
                x = pos[w].reset_index(); x = x[x.knesset == tr].set_index(["mk_id", "d"]).P
                pr = x.reindex(pd.MultiIndex.from_arrays([t.mk_id, t.d])).fillna(0).values
                rs.append(corr(pr, t.P.values)); cells += len(t)
                per_mk.append(pd.DataFrame({"mk": t.mk_id.values, "pred": pr, "t": t.P.values, "dir": f"{tr}"}))
                lst = t.mk_id.map(mk2l).values
                df = pd.DataFrame({"l": lst, "d": t.d.values, "pred": pr, "t": t.P.values}).dropna(subset=["l"])
                g = df.groupby(["l", "d"]).agg(pred=("pred", "mean"), t=("t", "mean"), n=("t", "size")); g = g[g.n >= 2]
                rl.append(corr(g.pred.values, g.t.values))
            res[w] = (np.mean(rs), np.mean(rl), cells, pd.concat(per_mk))
        base = res[1.0][3]; mks = base.mk.unique()
        boots = {w: [] for w in WS}
        for _ in range(500):
            s = rng.choice(mks, len(mks)); cnt = pd.Series(s).value_counts()
            def rb(D):
                out = []
                for dname, q in D.groupby("dir"):
                    q = q[q.mk.isin(cnt.index)]; wgt = q.mk.map(cnt).values
                    m1, m2 = np.average(q.pred, weights=wgt), np.average(q.t, weights=wgt)
                    c = np.average((q.pred - m1) * (q.t - m2), weights=wgt)
                    out.append(c / np.sqrt(np.average((q.pred - m1) ** 2, weights=wgt) * np.average((q.t - m2) ** 2, weights=wgt)))
                return np.mean(out)
            b1 = rb(base)
            for w in WS: boots[w].append(rb(res[w][3]) - b1)
        for w in WS:
            lo, hi = np.percentile(boots[w], [2.5, 97.5])
            d = res[w][0] - res[1.0][0]
            p(f"   {w:>5} {res[w][0]:6.3f} {d:+.3f} [{lo:+.3f}, {hi:+.3f}]".ljust(42) + f" {res[w][1]:7.3f} {res[w][2]:6}")
        p("")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
