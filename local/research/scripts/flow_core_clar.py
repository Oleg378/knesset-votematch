"""Customer's request (2026-10-18): schemes «core C + K clarifying» with C = 3..15 and small fixed K (5, 7, 10), to see for which
core size the clarifying questions work best. Compared with «all core» of the same total length (C + K core statements, no
clarifying), so the column «clar. gain» = what the adaptive questions add over plain core questions.
Persona and ranking as in flow_grid.py / flow_curve.py. Usage: python3 local/research/scripts/flow_core_clar.py [N]"""
import collections, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flow_grid as fg, quiz_flow as qf
from flow_curve import persona
N = int(sys.argv[1]) if sys.argv[1:] else 40
CS, KS = list(range(3, 16)), (5, 7, 10)
CORE = {c: qf.core({**qf.FLOW, "core": c}, fg.ctx) for c in range(3, 26)}
for flip in (0.1, 0.2):
    R1, R3 = collections.Counter(), collections.Counter(); rnd = random.Random(4)
    for _ in range(N):
        for l in fg.ok:
            full = persona(l, rnd, flip)
            for c in CS:
                asked = list(CORE[c]); ans = {q: full[q] for q in asked}
                for i in range(max(KS)):
                    q = qf.next_clarify(ans, set(asked), ctx=fg.ctx)
                    if q is None: break
                    asked.append(q); ans[q] = full[q]
                    if i + 1 in KS:
                        t = fg.top(ans); R1[(c, i + 1)] += t[:1] == [l]; R3[(c, i + 1)] += l in t
                        t = fg.top({x: full[x] for x in CORE[c + i + 1]}); R1[("core", c + i + 1)] += t[:1] == [l]
    k = N * len(fg.ok)
    print(f"\n== answers against own list {flip:.0%}; {N} personas per list (±{1.96 * (0.25 / k) ** .5:.2f})")
    print("core | " + " | ".join(f"+{K}: 1st/top3 (all-core same length, clar. gain)" for K in KS))
    for c in CS:
        print(f"{c:>4} | " + " | ".join(f"{R1[(c, K)] / k:.2f}/{R3[(c, K)] / k:.2f} ({R1[('core', c + K)] / k:.2f}, {(R1[(c, K)] - R1[('core', c + K)]) / k:+.2f})" for K in KS), flush=True)
