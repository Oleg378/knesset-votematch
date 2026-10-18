"""Algorithm work (2026-10-18): which rule for choosing the next clarifying question recognises lists best.
Same personas as flow_recognition.py. Variants of next_clarify (core unchanged, quiz_flow.core):
  sd4    — current: max SD of p over the top 4 lists;
  gap2   — max |p1 − p2| between the current top 2;
  pair3  — max Σ |pi − pj| over pairs of the top 3;
  wpair  — Σ over pairs of the top 5 of |pi − pj| weighted by how close both are to the leader (e^{−(c1−ci)/0.05});
  random — a random unasked statement (baseline).
Usage: python3 local/research/scripts/flow_variants.py
"""
import collections, functools, math, os, random, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm
qm.load = functools.lru_cache(maxsize=None)(qm.load)
import quiz_flow as qf
st, pos, cov = qm.load(); ev = [l for l, c in cov.items() if c["status"] == "ok"]
ctx = qf._ctx(); vec = ctx[2]; allv = ev if os.environ.get("OKONLY") else [l for l in vec]   # OKONLY=1: rank only lists with status ok

def persona(l, rnd):
    ans = {}
    for r in st:
        x = pos[l].get(r["d"])
        if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
        a = 0 if abs(x[0]) < 0.1 else (1 if abs(x[0]) < 0.5 else 2)
        a = int(np.sign(x[0]) * r["key_s"] * a)
        if a and rnd.random() < 0.2: a = -a
        ans[r["q"]] = a
    return ans

def scores(ans):
    return sorted(((np.nan_to_num(qm.score(st, ans, vec[m])[0], nan=-9), m) for m in allv), reverse=True)

def pick(rule, ans, asked, rnd):
    sc = scores(ans) if any(v not in ("dk", 0) for v in ans.values()) else [(0, m) for m in allv]
    cand = [r["q"] for r in st if r["q"] not in asked]
    if not cand: return None
    if rule == "random": return rnd.choice(cand)
    def val(q):
        if rule == "sd4":
            p = [vec[m][q] for _, m in sc[:4] if q in vec[m]]; return np.std(p) if len(p) >= 2 else -1
        if rule == "gap2":
            a, b = sc[0][1], sc[1][1]; return abs(vec[a][q] - vec[b][q]) if q in vec[a] and q in vec[b] else -1
        if rule == "pair3":
            t = [m for _, m in sc[:3]]; return sum(abs(vec[a][q] - vec[b][q]) for i, a in enumerate(t) for b in t[i + 1:] if q in vec[a] and q in vec[b])
        if rule == "wpair":
            c0 = sc[0][0]; t = [(math.exp(-(c0 - c) / 0.05), m) for c, m in sc[:5]]
            return sum(wa * wb * abs(vec[a][q] - vec[b][q]) for i, (wa, a) in enumerate(t) for wb, b in t[i + 1:] if q in vec[a] and q in vec[b])
    return max(cand, key=lambda q: (val(q), -int(q)))

def run(rule, full, n_core, n_cl, rnd):
    asked = qf.core({**qf.FLOW, "core": n_core}, ctx); ans = {q: full[q] for q in asked}
    for _ in range(n_cl):
        q = pick(rule, ans, set(asked), rnd)
        if q is None: break
        asked.append(q); ans[q] = full[q]
    return scores(ans)[0][1]

N = 40; rnd = random.Random(3); R = collections.Counter()
for _ in range(N):
    for l in ev:
        full = persona(l, rnd)
        for rule in ("sd4", "gap2", "pair3", "wpair", "random"):
            for cfg in ((5, 5), (5, 10)):
                R[(rule, cfg)] += run(rule, full, *cfg, rnd) == l
for cfg in ((5, 5), (5, 10)):
    print(f"{cfg[0]}+{cfg[1]}: " + ", ".join(f"{rule} {R[(rule, cfg)] / N / len(ev):.2f}" for rule in ("sd4", "gap2", "pair3", "wpair", "random")))
