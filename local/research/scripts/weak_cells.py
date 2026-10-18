"""External audit К1 / С1 (2026-10-18): what if list positions with |p| < CLOSE («has no clear position») do not enter closeness?
Variants: base (now); A = weak cells left out of the cosine, coverage unchanged; B = weak cells left out of both (a weak cell counts
as «no position», which also lowers coverage and can drop a list below the 0.5 ranking threshold).
Metrics: archetype users (anti / pro judicial reform), random answers (first places, all ranked lists incl. warning), «agree to all»,
persona recovery (ok lists, all statements, 20 % flipped, 20 % don't know). -> stdout, local/research/weak_cells/summary.txt
"""
import collections, os, random, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import quiz_match as qm, quiz_report as qr
OUT = f"{ROOT}/local/research/weak_cells"; os.makedirs(OUT, exist_ok=True)
st, pos, cov = qm.load(); CL = qr.CLOSE
ranked = [l for l, c in cov.items() if c["status"] in ("ok", "warning")]; okl = [l for l, c in cov.items() if c["status"] == "ok"]
name = {l: cov[l]["list_name"][:26] for l in cov}
full = {l: qm.list_vec(st, pos, l, 0) for l in ranked}
def vecs(v):
    if v == "base": return full, full
    strong = {l: {q: p for q, p in full[l].items() if abs(p) >= CL} for l in ranked}
    return (strong, full) if v == "A" else (strong, strong)
def rank(ans, v):
    cosv, covv = vecs(v); out = []
    for l in ranked:
        c, _ = qm.score(st, ans, cosv[l]); _, cv = qm.score(st, ans, covv[l])
        if c == c and cv >= qm.MIN_COVERAGE: out.append((c, l))
    return [l for c, l in sorted(out, reverse=True)]
L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)
anti = {"1": 2, "24": -2, "61": -2, "62": -2, "63": -2, "64": 2, "74": 2, "105": 2}
pro = {q: -a for q, a in anti.items()}
for v in ("base", "A", "B"):
    p(f"\n=== variant {v}")
    for nm, a in (("anti judicial reform", anti), ("pro judicial reform", pro), ("agree to all", {r['q']: 1 for r in st}), ("disagree to all", {r['q']: -1 for r in st})):
        p(f"  {nm:22}: " + " > ".join(name[l] for l in rank(a, v)[:5]))
    rnd = random.Random(1); first = collections.Counter(); N = 1500
    for _ in range(N):
        r = rank({x["q"]: rnd.choice([-2, -1, 1, 2]) for x in st}, v)
        if r: first[r[0]] += 1
    p(f"  random answers, first place (equal share {1 / len(ranked):.3f}): " + ", ".join(f"{name[l]} {n / N:.3f}" for l, n in first.most_common(5)))
    rnd = random.Random(4); t1 = t3 = n = 0
    for _ in range(25):
        for l in okl:
            ans = {}
            for r in st:
                x = pos[l].get(r["d"])
                if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
                s = np.sign(x[0]) * r["key_s"] * (2 if abs(x[0]) > 0.5 else 1)
                ans[r["q"]] = int(-s if rnd.random() < 0.2 else s)
            rk = rank(ans, v); t1 += rk[:1] == [l]; t3 += l in rk[:3]; n += 1
    p(f"  persona recovery (all statements): 1st {t1 / n:.2f}, top-3 {t3 / n:.2f}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
