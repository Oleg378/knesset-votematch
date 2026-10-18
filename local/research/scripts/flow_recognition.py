"""Point 6 (2026-10-18): how well the quiz recognises each list, in the full mode and in the core → clarifying flow.

Persona of list L (fixed version): for each statement the answer follows the sign of L's raw position P (× statement key), with
strength by |P|: |P| < 0.1 → 0 (neutral), < 0.5 → ±1, otherwise ±2; then 20 % of non-neutral answers flipped and 20 % «don't know».
Ideal persona: the same without noise — can L reach first place at all if the user answers exactly as L does?
Flow: quiz_flow.core() then next_clarify() one at a time, the persona answering each asked statement; trade-offs not simulated.

Usage: python3 local/research/scripts/flow_recognition.py   -> local/research/flow_recognition/summary.txt
"""
import collections, functools, os, random, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm
qm.load = functools.lru_cache(maxsize=None)(qm.load)   # the files do not change during the run
import quiz_flow as qf
OUT = os.path.join(ROOT, "local/research/flow_recognition"); os.makedirs(OUT, exist_ok=True)

st, pos, cov = qm.load(); ev = [l for l, c in cov.items() if c["status"] == "ok"]
ctx = qf._ctx(); vec = ctx[2]
name = {l: cov[l]["list_name"].split(",")[0].split("(")[0].split("–")[0].strip()[:16] for l in ev}

def persona(l, rnd, noise=True):
    ans = {}
    for r in st:
        x = pos[l].get(r["d"])
        if not x or (noise and rnd.random() < 0.2): ans[r["q"]] = "dk"; continue
        a = 0 if abs(x[0]) < 0.1 else (1 if abs(x[0]) < 0.5 else 2)
        a = int(np.sign(x[0]) * r["key_s"] * a)
        if noise and a and rnd.random() < 0.2: a = -a
        ans[r["q"]] = a
    return ans

def rank(ans):
    return sorted(ev, key=lambda m: -np.nan_to_num(qm.score(st, ans, vec[m])[0], nan=-9))

def flow(full, n_core, n_cl):
    flow_ = {**qf.FLOW, "core": n_core}
    asked = qf.core(flow_, ctx)
    ans = {q: full[q] for q in asked}
    for _ in range(n_cl):
        q = qf.next_clarify(ans, set(asked), flow_, ctx=ctx)
        if q is None: break
        asked.append(q); ans[q] = full[q]
    return ans

MODES = [("full", None), ("5+5", (5, 5)), ("8+4", (8, 4)), ("5+10", (5, 10)), ("3+7", (3, 7))]
N = 60
res = {m: (collections.Counter(), collections.Counter()) for m, _ in MODES}
rnd = random.Random(20261018)
for _ in range(N):
    for l in ev:
        full = persona(l, rnd)
        for m, cfg in MODES:
            rk = rank(full if cfg is None else flow(full, *cfg))
            res[m][0][l] += rk[0] == l; res[m][1][l] += l in rk[:3]
L = ["Recognition of each list by its noisy persona (share of runs where the list is 1st / in the top 3); trade-offs not simulated",
     f"{N} personas per list; persona strength by |P| (neutral below 0.1)", "",
     f"{'list':16} " + " ".join(f"{m:>11}" for m, _ in MODES)]
for l in sorted(ev, key=lambda l: res["full"][0][l]):
    L.append(f"{name[l]:16} " + " ".join(f"{res[m][0][l] / N:.2f}/{res[m][1][l] / N:.2f}".rjust(11) for m, _ in MODES))
L.append(f"{'all lists':16} " + " ".join(f"{sum(res[m][0].values()) / N / len(ev):.2f}/{sum(res[m][1].values()) / N / len(ev):.2f}".rjust(11) for m, _ in MODES))
L += ["", "Ideal persona (answers exactly as the list, no noise): position of the list"]
for l in ev:
    ideal = persona(l, rnd, noise=False)
    row = []
    for m, cfg in MODES:
        rk = rank(ideal if cfg is None else flow(ideal, *cfg)); row.append(f"{m} #{rk.index(l) + 1}" + ("" if rk[0] == l else f" (1st: {name[rk[0]]})"))
    L.append(f"{name[l]:16} " + "; ".join(row))
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
