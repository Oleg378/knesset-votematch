"""Algorithm work (2026-10-18): stopping rule instead of a fixed number of questions.
After CORE core statements, clarifying statements (quiz_flow rule) are asked until the closeness of the leader exceeds the second
list's by GAP (and at least MIN questions were asked), or MAX questions are reached. Persona as in flow_grid.py with FLIP share of
answers against its list. Reports: own list 1st / in top 3, mean and 90th percentile of questions asked.
Usage: python3 local/research/scripts/flow_stop.py
"""
import collections, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import flow_grid as fg
import quiz_match as qm, quiz_flow as qf

def persona(l, rnd, flip):
    ans = {}
    for r in fg.st:
        x = fg.pos[l].get(r["d"])
        if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
        a = 0 if abs(x[0]) < 0.1 else (1 if abs(x[0]) < 0.5 else 2); a = int(np.sign(x[0]) * r["key_s"] * a)
        if a and rnd.random() < flip: a = -a
        ans[r["q"]] = a
    return ans

def scores(ans):
    rows = []
    for m in fg.ranked_lists:
        c, cv = qm.score(fg.st, ans, fg.vec[m])
        if c == c and cv >= qm.MIN_COVERAGE: rows.append((c, m))
    return sorted(rows, reverse=True)

def run(full, core, gap, mn, mx):
    asked = qf.core({**qf.FLOW, "core": core}, fg.ctx); ans = {q: full[q] for q in asked}
    while True:
        sc = scores(ans)
        if len(asked) >= mx or (len(asked) >= mn and len(sc) > 1 and sc[0][0] - sc[1][0] >= gap): return sc, len(asked)
        q = qf.next_clarify(ans, set(asked), ctx=fg.ctx)
        if q is None: return sc, len(asked)
        asked.append(q); ans[q] = full[q]

def main():
  N = 12
  for flip in (0.1, 0.2):
    print(f"\n== answers against own list: {flip:.0%}")
    for core in (5, 8):
        for gap in (0.05, 0.1, 0.15, 0.2):
            for mx in (25, 40):
                rnd = random.Random(1); t1 = t3 = 0; ns = []
                for _ in range(N):
                    for l in fg.ok:
                        sc, n = run(persona(l, rnd, flip), core, gap, 10, mx); top = [m for _, m in sc[:3]]
                        t1 += top[:1] == [l]; t3 += l in top; ns.append(n)
                k = N * len(fg.ok)
                print(f"core {core}, gap {gap:.2f}, max {mx}: 1st {t1 / k:.2f}, top-3 {t3 / k:.2f}, questions mean {np.mean(ns):.1f}, p90 {np.percentile(ns, 90):.0f}", flush=True)

if __name__ == "__main__": main()
