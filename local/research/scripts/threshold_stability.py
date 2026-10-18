"""Test for the «close to the average MK» threshold (SU 27.3, п. 6, 2026-10-17): below which strength |p| is the side of a list
no more reliable than a coin?

The list positions are computed separately from Knesset 24 only and from Knesset 25 only (same formula as pipeline/positions.py:
P = A + 0.25 V, A centered per Knesset × direction, V the residual on the government share), for list × quiz direction pairs
that have data in both. Pairs are binned by the strength of the production position |p| = |P · e/(e + K)|; for each bin: how
often the side (sign) is the same in the two Knessets. 50 % = coin.

Usage: python3 local/research/scripts/threshold_stability.py   (after pipeline/positions.py)  -> local/research/threshold_stability/summary.txt
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/threshold_stability")
os.makedirs(f"{OUT}/pos", exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
assert "OUT = f'{ROOT}/jef/positions'" in src
src = src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {OUT + '/pos'!r}")
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "threshold_stability"}
exec(compile(src, "positions.py", "exec"), ns)
A, V, cm, W_A, W_V = ns["A"], ns["V"], ns["cm"], ns["W_A"], ns["W_V"]
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm

st, pos, cov = qm.load()
quiz_d = {r["d"] for r in st}
shown = {l for l, c in cov.items() if c["status"] != "not_evaluated"}

per_k = A[["mk_id", "knesset", "d", "A"]].merge(V[["mk_id", "knesset", "d", "V"]], on=["mk_id", "knesset", "d"], how="outer")
per_k = per_k[per_k.d.isin(quiz_d)]
per_k["P"] = W_A * per_k.A.fillna(0) + W_V * per_k.V.fillna(0)
M = cm[["letters", "mk_id"]].merge(per_k, on="mk_id")
M = M[M.letters.isin(shown)]
LK = M.groupby(["letters", "d", "knesset"]).agg(P=("P", "mean"), n=("mk_id", "size")).reset_index()
W = LK.pivot_table(index=["letters", "d"], columns="knesset", values="P").dropna()
W.columns = ["P24", "P25"]
W = W.reset_index()
W["p"] = [pos[l][d][0] * pos[l][d][1] / (pos[l][d][1] + qm.K) if d in pos.get(l, {}) else np.nan for l, d in zip(W.letters, W.d)]
W = W.dropna()
W["same"] = np.sign(W.P24) == np.sign(W.P25)
W["ap"] = W.p.abs()

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1])
p(f"list × quiz direction pairs with data in both Knessets: {len(W)} of {sum(1 for l in pos if l in shown for d in pos[l] if d in quiz_d)}; K = {qm.K}")
p(f"overall same side K24 vs K25: {W.same.mean():.0%}")
p("\n|p| bin       pairs  same side")
edges = [0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 9]
for a, b in zip(edges[:-1], edges[1:]):
    x = W[(W.ap >= a) & (W.ap < b)]
    p(f"[{a:.3f}, {b:.3f})  {len(x):5}  {x.same.mean():.0%}" if len(x) else f"[{a:.3f}, {b:.3f})      0")
p("\nthreshold t: positions below t shown as «close to the average MK»")
p("t      share of positions below t   same side below t   same side at/above t")
allp = [abs(pos[l][d][0] * pos[l][d][1] / (pos[l][d][1] + qm.K)) for l in pos if l in shown for d in pos[l] if d in quiz_d]
for t in (0.025, 0.05, 0.075, 0.1, 0.15, 0.2):
    lo, hi = W[W.ap < t], W[W.ap >= t]
    p(f"{t:<6} {np.mean([v < t for v in allp]):>27.0%} {lo.same.mean():>19.0%} {hi.same.mean():>22.0%}")
W.round(4).to_csv(f"{OUT}/pairs.csv", index=False)
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
