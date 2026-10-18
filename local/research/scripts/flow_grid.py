"""Algorithm work (2026-10-18, customer's plan): target = recognition when the persona answers every statement; then configs
core + clarifying (+ trade-offs) to find how few questions reach it.

Ranking as in the product (quiz_match.match): evaluated lists (ok and warning), closeness = cosine, lists below the coverage
threshold not ranked. Persona of an ok list as in flow_recognition.py (strength by |P|, 20 % flipped, 20 % «don't know»).
Core = quiz_flow.core(); clarifying = quiz_flow rule (max SD over the current top 4). Sequences are nested, so one run per persona
gives every (core, clarify) prefix. Trade-offs (stage 2, optional): the persona prefers the statement on which its list's |P| is
larger («=» if within 0.1), asked as in quiz_cli.exchange.

Usage: python3 local/research/scripts/flow_grid.py [N]            core × clarify grid, N personas per list (default 30)
       python3 local/research/scripts/flow_grid.py --trade C K N    trade-offs 0..5 for core C, clarify K
"""
import collections, functools, os, random, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm
qm.load = functools.lru_cache(maxsize=None)(qm.load)
import quiz_flow as qf
OUT = os.path.join(ROOT, "local/research/flow_grid"); os.makedirs(OUT, exist_ok=True)
st, pos, cov = qm.load()
ok = [l for l, c in cov.items() if c["status"] == "ok"]
ranked_lists = [l for l, c in cov.items() if c["status"] != "not_evaluated"]
ctx = qf._ctx(); vec = ctx[2]
CORES, CLAR = (3, 5, 8, 10, 12, 15, 20), (0, 2, 4, 6, 8, 10, 15, 20, 30)

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

def top(ans, n=3, mult=None):
    rows = []
    for m in ranked_lists:
        c, cv = qm.score(st, ans, vec[m], mult)
        if c == c and cv >= qm.MIN_COVERAGE: rows.append((c, m))
    return [m for _, m in sorted(rows, reverse=True)[:n]]

def sequence(full, n_core, n_cl):
    asked = qf.core({**qf.FLOW, "core": n_core}, ctx); ans = {q: full[q] for q in asked}; out = []
    for _ in range(n_cl):
        q = qf.next_clarify(ans, set(asked), ctx=ctx)
        if q is None: break
        asked.append(q); ans[q] = full[q]; out.append(q)
    return asked[:n_core], out

def grid(N):
    R1, R3 = collections.Counter(), collections.Counter(); full1 = full3 = 0
    rnd = random.Random(20261018)
    for _ in range(N):
        for l in ok:
            full = persona(l, rnd)
            t = top(full); full1 += t[:1] == [l]; full3 += l in t
            for c in CORES:
                core, cl = sequence(full, c, max(CLAR))
                for k in CLAR:
                    ans = {q: full[q] for q in core + cl[:k]}
                    t = top(ans); R1[(c, k)] += t[:1] == [l]; R3[(c, k)] += l in t
    n = N * len(ok)
    L = [f"Target (all {len(st)} statements answered): own list 1st {full1 / n:.2f}, in top 3 {full3 / n:.2f}; {N} personas per list", "",
         "own list 1st (top 3), by core × clarifying; total questions = core + clarifying", "core\\clar " + "".join(f"{k:>11}" for k in CLAR)]
    for c in CORES:
        L.append(f"{c:>9} " + "".join(f"{R1[(c, k)] / n:.2f}({R3[(c, k)] / n:.2f})".rjust(11) for k in CLAR))
    best = collections.defaultdict(lambda: (0, None))
    for (c, k), v in R1.items():
        tot = c + k
        if v > best[tot][0]: best[tot] = (v, (c, k))
    L += ["", "best split for a given total number of questions:"]
    L += [f"  {tot:>3} questions: {best[tot][1][0]} core + {best[tot][1][1]} clarifying -> {best[tot][0] / n:.2f}" for tot in sorted(best)]
    open(f"{OUT}/grid.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))

def trade(C, K, N):
    rnd = random.Random(7); R = collections.Counter()
    for _ in range(N):
        for l in ok:
            full = persona(l, rnd); core, cl = sequence(full, C, K)
            ans = {q: full[q] for q in core + cl}; mult, used, lists = {}, set(), set()
            R[0] += top(ans, 1) == [l]
            for t in range(1, 6):
                pairs = qm.tradeoffs(ans, mult, exclude=used, skip_lists=lists)
                if pairs:
                    qa, qb, L_ = pairs[0]
                    da = {r["q"]: r["d"] for r in st}
                    pa = abs(pos[l].get(da[qa], (0,))[0]); pb = abs(pos[l].get(da[qb], (0,))[0])
                    if pa > pb + 0.1: mult[qa] = mult.get(qa, 1) * qm.TRADE_W
                    elif pb > pa + 0.1: mult[qb] = mult.get(qb, 1) * qm.TRADE_W
                    used |= {qa, qb}; lists.add(L_)
                R[t] += top(ans, 1, mult) == [l]
    n = N * len(ok)
    print(f"core {C} + clarify {K}: own list 1st by number of trade-offs " + ", ".join(f"{t}: {R[t] / n:.2f}" for t in range(6)))

if __name__ == "__main__":
    if sys.argv[1:2] == ["--trade"]: trade(*map(int, sys.argv[2:5]))
    else: grid(int(sys.argv[1]) if sys.argv[1:] else 30)
