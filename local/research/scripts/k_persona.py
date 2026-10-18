"""K recalibration without the neutrality criterion (2026-10-18): random-answer first-place shares depend on list clusters,
not on K (SU, decisions 2026-10-18). Persona recovery only, as in quiz_match.calibrate (sign of the list's raw position,
strength by |P|, 20 % flipped, 20 % «don't know»), more personas to see the noise. Output: top-1 / top-3 per K with 95 % CI.
Usage: python3 local/research/scripts/k_persona.py
"""
import os, sys, random, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline")); import quiz_match as qm
st, pos, cov = qm.load(); ev = [l for l, c in cov.items() if c["status"] == "ok"]
N = 150
for k in (0, 1, 2, 3, 5, 10, 20):
    rnd = random.Random(20261018); vecs = {l: qm.list_vec(st, pos, l, k) for l in ev}; t1 = t3 = 0
    for _ in range(N):
        for l in ev:
            ans = {}
            for r in st:
                x = pos[l].get(r["d"])
                if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
                s = np.sign(x[0]) * r["key_s"] * (2 if abs(x[0]) > 0.5 else 1)
                ans[r["q"]] = int(-s if rnd.random() < 0.2 else s)
            ranked = sorted(ev, key=lambda m: -np.nan_to_num(qm.score(st, ans, vecs[m])[0], nan=-9))
            t1 += ranked[0] == l; t3 += l in ranked[:3]
    n = N * len(ev); ci = lambda p: 1.96 * (p * (1 - p) / n) ** .5
    print(f"K={k:>2}  top-1 {t1/n:.3f} ±{ci(t1/n):.3f}   top-3 {t3/n:.3f} ±{ci(t3/n):.3f}")
