"""Core similarity limit (customer, 2026-10-18): accuracy of the 8 + 7 flow for core_r_max 0.8 / 0.7 / 0.6 / 0.5.
Persona and ranking as in flow_core_clar.py. Usage: python3 local/research/scripts/core_rmax_sim.py [N]"""
import collections, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flow_grid as fg
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../pipeline")); import quiz_flow as qf
from flow_curve import persona
N = int(sys.argv[1]) if sys.argv[1:] else 40
for flip in (0.1, 0.2):
    print(f"\n== answers against own list {flip:.0%}; {N} personas per list")
    for rm in (0.8, 0.7, 0.6, 0.5):
        core = qf.core({**qf.FLOW, "core_r_max": rm}, fg.ctx); r1 = r3 = r1c = 0; rnd = random.Random(4)
        for _ in range(N):
            for l in fg.ok:
                full = persona(l, rnd, flip); asked = list(core); ans = {q: full[q] for q in asked}
                t = fg.top(ans); r1c += t[:1] == [l]
                for _ in range(7):
                    q = qf.next_clarify(ans, set(asked), ctx=fg.ctx)
                    if q is None: break
                    asked.append(q); ans[q] = full[q]
                t = fg.top(ans); r1 += t[:1] == [l]; r3 += l in t
        k = N * len(fg.ok)
        print(f"core_r_max {rm}: after core only 1st {r1c / k:.2f} | after 8 + 7: 1st {r1 / k:.2f}, top-3 {r3 / k:.2f}", flush=True)
