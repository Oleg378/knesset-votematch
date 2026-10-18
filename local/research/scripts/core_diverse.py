"""Core by uniqueness of the list signature (customer's idea, 2026-10-18).
Seeds: the first S statements by separation (SD × coverage), as now (one per direction, gov-axis share cap). Then greedily the
statement that adds the most NEW separation:
  V1 «residual»: gain = SD(q) · sqrt(1 − R²), R² = multiple correlation of q's list vector with the chosen ones (OLS, 12 lists);
  V2 «max-r»:   gain = SD(q) · (1 − max |r| with a chosen one).
Same constraints as now (one statement per direction, at most half of the core on the government axis).
Reported per variant: the core, its diversity (mean and max |r| inside, effective number of independent axes = participation
ratio of the eigenvalues of the inside correlation matrix), accuracy as in core_rmax_sim.py (core only; 8 + 7).
Usage: python3 local/research/scripts/core_diverse.py [N]"""
import os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flow_grid as fg
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../pipeline")); import quiz_flow as qf
from flow_curve import persona
N = int(sys.argv[1]) if sys.argv[1:] else 40
st, ok, vec, gov = fg.ctx
T = {r["q"]: r["title_en"] for r in st}; D = {r["q"]: r["d"] for r in st}
X = {r["q"]: np.array([vec[l].get(r["q"], 0.0) for l in ok]) for r in st}
cov = {q: sum(1 for l in ok if q in vec[l]) / len(ok) for q in X}
G = np.array([gov[l] for l in ok])
def corr(a, b): return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else 0.0
ongov = {q: abs(corr(X[q], G)) >= qf.FLOW["gov_r"] for q in X}
sep = {q: float(np.std(X[q])) * cov[q] for q in X}
def r2(q, chosen):
    if not chosen: return 0.0
    A = np.column_stack([np.ones(len(ok))] + [X[c] for c in chosen]); y = X[q]
    b, *_ = np.linalg.lstsq(A, y, rcond=None); res = y - A @ b
    return 1 - res.var() / y.var() if y.var() > 0 else 1.0
def build(seeds, variant, n=8):
    out, dirs, ng = [], set(), 0
    cap = int(n * qf.FLOW["core_gov_share"])
    def ok_(q): return D[q] not in dirs and not (ongov[q] and ng >= cap)
    for q in sorted(X, key=lambda q: (-sep[q], int(q))):
        if len(out) >= seeds: break
        if ok_(q) and all(abs(corr(X[q], X[c])) < qf.FLOW["core_r_max"] for c in out): out.append(q); dirs.add(D[q]); ng += ongov[q]
    while len(out) < n:
        best = None
        for q in X:
            if q in out or not ok_(q): continue
            g = sep[q] * (np.sqrt(max(0.0, 1 - r2(q, out))) if variant == "residual" else 1 - max(abs(corr(X[q], X[c])) for c in out))
            if best is None or g > best[0]: best = (g, q)
        out.append(best[1]); dirs.add(D[best[1]]); ng += ongov[best[1]]
    return out
def diversity(core):
    C = np.corrcoef(np.array([X[q] for q in core])); iu = np.triu_indices(len(core), 1)
    ev = np.clip(np.linalg.eigvalsh(C), 0, None)
    return np.abs(C[iu]).mean(), np.abs(C[iu]).max(), ev.sum() ** 2 / (ev ** 2).sum()
def accuracy(core, flip):
    r1c = r1 = r3 = 0; rnd = random.Random(4)
    for _ in range(N):
        for l in ok:
            full = persona(l, rnd, flip); asked = list(core); ans = {q: full[q] for q in asked}
            t = fg.top(ans); r1c += t[:1] == [l]
            for _ in range(7):
                q = qf.next_clarify(ans, set(asked), ctx=fg.ctx)
                if q is None: break
                asked.append(q); ans[q] = full[q]
            t = fg.top(ans); r1 += t[:1] == [l]; r3 += l in t
    k = N * len(ok); return r1c / k, r1 / k, r3 / k
SEEDS = [int(x) for x in os.environ.get("SEEDS", "2,3").split(",")]
cores = {} if os.environ.get("SEEDS") else {"now (SD, r_max 0.8)": qf.core(qf.FLOW, fg.ctx), "r_max 0.7": qf.core({**qf.FLOW, "core_r_max": 0.7}, fg.ctx)}
for s in SEEDS:
    for v in ("residual", "max-r"): cores[f"{v}, {s} seeds"] = build(s, v)
for name, c in cores.items():
    m, mx, eff = diversity(c); a10 = accuracy(c, 0.1); a20 = accuracy(c, 0.2)
    print(f"\n### {name}\n  diversity: mean |r| {m:.2f}, max |r| {mx:.2f}, independent axes {eff:.1f}; mean SD {np.mean([sep[q] for q in c]):.2f}")
    print(f"  accuracy 10%: core only {a10[0]:.2f}; 8+7 1st {a10[1]:.2f} top-3 {a10[2]:.2f} | 20%: core only {a20[0]:.2f}; 8+7 1st {a20[1]:.2f} top-3 {a20[2]:.2f}")
    print("  " + " · ".join(f"{T[q]} ({sep[q]:.2f})" for q in c), flush=True)
