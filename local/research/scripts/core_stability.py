"""Core rule checks (customer, 2026-10-18): (1) adjusted R² in the uniqueness factor; (2) stability of the core.
Rules: «now» = quiz_flow.core (SD × coverage, r_max 0.8); «R²» = SD × sqrt(1 − R²); «adj R²» = SD × sqrt(1 − adjusted R²)
(R²_adj = 1 − (1 − R²)(n − 1)/(n − k − 1), n = 12 lists, k = statements already chosen). Same constraints (one per direction,
gov-axis share). Stability:
  A. bootstrap over ex-MKs (each list's ex-MKs resampled with replacement, list position = mean, 200 times): how many of the 8
     core statements stay, and how often each statement is in the core;
  B. labels before today's removals (positions of commit 427e11a) vs now, on the statements present in both.
Accuracy for the adj-R² core as in core_diverse.py. Usage: python3 local/research/scripts/core_stability.py
"""
import collections, csv, io, os, random, subprocess, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline")); import quiz_flow as qf
st, ok, vec0, gov = qf._ctx()
T = {r["q"]: r["title_en"] for r in st}; D = {r["q"]: r["d"] for r in st}
G = np.array([gov[l] for l in ok])
def corr(a, b): return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else 0.0
def core_unique(vec, adj, n=8, sts=None):
    sts = sts or st
    X = {r["q"]: np.array([vec[l].get(r["q"], 0.0) for l in ok]) for r in sts}
    cov = {q: sum(1 for l in ok if q in vec[l]) / len(ok) for q in X}
    sep = {q: float(np.std(X[q])) * cov[q] for q in X}
    ongov = {q: abs(corr(X[q], G)) >= qf.FLOW["gov_r"] for q in X}
    out, dirs, ng, cap = [], set(), 0, int(n * qf.FLOW["core_gov_share"])
    while len(out) < n:
        best = None
        for q in X:
            if q in out or D[q] in dirs or (ongov[q] and ng >= cap) or sep[q] == 0: continue
            if out:
                A = np.column_stack([np.ones(len(ok))] + [X[c] for c in out]); y = X[q]
                b, *_ = np.linalg.lstsq(A, y, rcond=None); r2 = 1 - (y - A @ b).var() / y.var()
                if adj: r2 = 1 - (1 - r2) * (len(ok) - 1) / max(1, len(ok) - len(out) - 1)
                k = np.sqrt(max(0.0, 1 - max(0.0, r2)))
            else: k = 1.0
            g = sep[q] * k
            if best is None or g > best[0] or (g == best[0] and int(q) < int(best[1])): best = (g, q)
        if best is None: break
        out.append(best[1]); dirs.add(D[best[1]]); ng += ongov[best[1]]
    return out
RULES = {"now": lambda vec, sts=None: qf.core(qf.FLOW, ((sts or st), ok, vec, gov)),
         "r_max 0.7": lambda vec, sts=None: qf.core({**qf.FLOW, "core_r_max": 0.7}, ((sts or st), ok, vec, gov)),
         "R²": lambda vec, sts=None: core_unique(vec, False, sts=sts), "adj R²": lambda vec, sts=None: core_unique(vec, True, sts=sts)}
base = {k: f(vec0) for k, f in RULES.items()}
print("cores on current data:")
for k, c in base.items(): print(f"  {k:7}: " + " · ".join(T[q] for q in c))
# ---- A. bootstrap over ex-MKs ----
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str})
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
MT["l"] = MT.mk_id.map(mk2l); MT = MT[MT.l.isin(ok) & MT.d.isin(set(D.values()))]
P = {(m, d): p for m, d, p in zip(MT.mk_id, MT.d, MT.P)}
mks = {l: sorted(MT[MT.l == l].mk_id.unique()) for l in ok}
dq = collections.defaultdict(list)
for q, d in D.items(): dq[d].append(q)
def vec_from(sample):
    v = {}
    for l in ok:
        acc = collections.defaultdict(list)
        for m in sample[l]:
            for d, qs in dq.items():
                if (m, d) in P: acc[d].append(P[(m, d)])
        v[l] = {q: float(np.mean(x)) for d, x in acc.items() for q in dq[d]}
    return v
chk = vec_from(mks)
print("check: list vectors rebuilt from MKs == production:", max(abs(chk[l][q] - vec0[l][q]) for l in ok for q in vec0[l] if q in chk[l]) < 1e-3)
rnd = random.Random(20261018); R = 200
stay = {k: [] for k in RULES}; freq = {k: collections.Counter() for k in RULES}
for _ in range(R):
    v = vec_from({l: [rnd.choice(mks[l]) for _ in mks[l]] for l in ok})
    for k, f in RULES.items():
        c = f(v); stay[k].append(len(set(c) & set(base[k]))); freq[k].update(c)
print(f"\nA. bootstrap over ex-MKs ({R}): core statements kept out of 8 (mean, 10th percentile); statements in the core in >= 80 % of runs")
for k in RULES:
    s = np.array(stay[k]); solid = [q for q, n in freq[k].items() if n >= 0.8 * R]
    print(f"  {k:7}: mean {s.mean():.1f}, p10 {np.percentile(s, 10):.0f}; solid {len(solid)}: " + " · ".join(T[q] for q in sorted(solid, key=lambda q: -freq[k][q])))
    print("           top by frequency: " + ", ".join(f"{T[q]} {n / R:.0%}" for q, n in freq[k].most_common(11)))
# ---- B. labels before today's removals ----
old = pd.read_csv(io.StringIO(subprocess.check_output(["git", "show", "427e11a:jef/positions/list_topic_positions.csv"], cwd=ROOT).decode()), dtype={"d": str})
oldP = {(l, d): p for l, d, p in zip(old.letters, old.d, old.P)}
sts_both = [r for r in st if all((l, r["d"]) in oldP or r["q"] not in vec0[l] for l in ok) and any((l, r["d"]) in oldP for l in ok)]
vold = {l: {r["q"]: oldP[(l, r["d"])] for r in sts_both if (l, r["d"]) in oldP} for l in ok}
vnew = {l: {q: x for q, x in vec0[l].items() if q in {r["q"] for r in sts_both}} for l in ok}
print(f"\nB. before vs after today's label removals ({len(sts_both)} statements present in both):")
for k, f in RULES.items():
    a, b = f(vold, sts_both), f(vnew, sts_both)
    print(f"  {k:7}: kept {len(set(a) & set(b))} of 8; left: " + ", ".join(T[q] for q in a if q not in b) + " | came: " + ", ".join(T[q] for q in b if q not in a))
