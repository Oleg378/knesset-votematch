"""Basis of the spread (SD) threshold of the quiz selection after the formula change and the relevance filter (2026-10-17).

Variants = positions in local/research/relevance_impact/ (made by relevance_impact.py) + production v1 (old formula, no filter):
  1. scale: median SD over all directions (>= 8 ok lists with >= 3 ex-MKs) and the SD that is as strict as 0.3 was on the
     old scale (same multiple of the median, same percentile);
  2. scale-free check: is the spread between lists larger than chance? Ex-MKs are shuffled between lists (list sizes kept,
     2,000 shuffles); a direction passes if its SD is above the 95th percentile of the shuffled SDs;
  3. what each choice keeps: statements (65 statements on 61 directions), their topics, per-list share of statements with
     a position (ranking needs >= 50 % of the answers, MIN_COVERAGE).
Volume and coverage criteria (>= 8 lists, sum_nA >= 30) are applied as in pipeline/quiz_select.py; the gov-axis cap is not.

Usage: python3 local/research/scripts/sd_threshold_basis.py   -> local/research/sd_threshold/summary.txt
"""
import csv, os, statistics
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/sd_threshold"); os.makedirs(OUT, exist_ok=True)
RI = f"{ROOT}/research/relevance_impact"
VAR = {"v1 old formula": f"{ROOT}/jef/positions", "new, no filter": f"{RI}/pos_0", "A votes-only 0.2": f"{RI}/pos_votes_0.2",
       "V both 0.1": f"{RI}/pos_0.1", "B both 0.2": f"{RI}/pos_0.2"}
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
quiz_d = list(dict.fromkeys(r["d"] for r in st))
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv")
ok = set(cov[cov.status == "ok"].letters); shown = list(cov[cov.status != "not_evaluated"].letters)
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv")
cm = cand[cand.match.isin(["exact", "manual"])].copy(); cm["mk_id"] = cm.mk_id.astype(int); cm = cm.drop_duplicates("mk_id")
rng = np.random.default_rng(20261017)

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)

def sds(LP):
    x = LP[LP.letters.isin(ok) & (LP.n_mk >= 3)]
    g = x.groupby("d").agg(n=("P", "size"), sd=("P", lambda v: statistics.pstdev(v) if len(v) > 1 else 0.0), nA=("sum_nA", "sum"))
    return g

def chance(MK, d):
    """95th percentile of the list SD with ex-MKs shuffled between ok lists (sizes kept), for the lists counted in selection."""
    m = MK[(MK.d == d) & MK.letters.isin(ok)]
    sizes = m.letters.value_counts()
    keep = sizes[sizes >= 3]
    if len(keep) < 2: return np.nan
    P = m.P.to_numpy(); lab = m.letters.to_numpy(); idx = {l: np.where(lab == l)[0].size for l in sizes.index}
    cuts = np.cumsum([idx[l] for l in sizes.index])[:-1]; use = [i for i, l in enumerate(sizes.index) if l in keep.index]
    res = np.empty(2000)
    for k in range(2000):
        parts = np.split(rng.permutation(P), cuts)
        res[k] = np.std([parts[i].mean() for i in use])
    return np.quantile(res, 0.95)

data = {}
for name, path in VAR.items():
    LP = pd.read_csv(f"{path}/list_topic_positions.csv", dtype={"d": str})
    MK = pd.read_csv(f"{path}/mk_topic_positions.csv", dtype={"d": str}).merge(cm[["mk_id", "letters"]], on="mk_id")
    data[name] = (LP, MK, sds(LP))

p("1. Scale. All directions with >= 8 ok lists (>= 3 ex-MKs each).")
p(f"{'variant':18} {'dirs':>4} {'median SD':>9} {'0.3 as ×median':>14} {'0.3 as percentile':>17}")
g0 = data["v1 old formula"][2]; g0 = g0[g0.n >= 8]
k = 0.3 / g0.sd.median(); q = (g0.sd < 0.3).mean()
for name, (LP, MK, g) in data.items():
    g = g[g.n >= 8]
    p(f"{name:18} {len(g):4} {g.sd.median():9.3f} {k * g.sd.median():14.3f} {g.sd.quantile(q):17.3f}")
p(f"(0.3 on the old scale = {k:.2f} × median = percentile {q:.0%} of all directions)")

p("\n2. Spread above chance (ex-MKs shuffled between lists; pass = SD above the 95th percentile of shuffles). Quiz directions.")
rows = []
for name, (LP, MK, g) in data.items():
    for d in quiz_d:
        n = g.n.get(d, 0); sd = g.sd.get(d, 0.0); nA = g.nA.get(d, 0)
        rows.append(dict(variant=name, d=d, n=n, sd=sd, nA=nA, chance95=chance(MK, d) if n >= 8 else np.nan))
R = pd.DataFrame(rows)
R["base"] = (R.n >= 8) & (R.nA >= 30)
R["above_chance"] = R.base & (R.sd > R.chance95)
R.round(4).to_csv(f"{OUT}/directions.csv", index=False)
SDS = (0.3, 0.2, 0.15, 0.1)
nst = {d: sum(r["d"] == d for r in st) for d in quiz_d}
p(f"{'variant':18} {'median chance95':>15} " + " ".join(f"{'SD>=' + str(s):>8}" for s in SDS) + f" {'>chance':>8}   (statements; directions in brackets)")
for name in VAR:
    x = R[R.variant == name]
    def cnt(m): return f"{sum(nst[d] for d in x[m].d):>3} ({m.sum():>2})"
    p(f"{name:18} {x.chance95.median():15.3f} " + " ".join(f"{cnt(x.base & (x.sd >= s)):>8}" for s in SDS) + f" {cnt(x.above_chance):>8}")

p("\n3. What is kept. Per statement: passes SD >= 0.2 / above chance, by variant (+ pass, . fail).")
title = {}
for r in st: title.setdefault(r["d"], []).append(f"q{r['q']} {r['title_en']}")
names = list(VAR)[1:]
p("    " + " | ".join(f"{n[:12]:>12}" for n in names) + "   statement")
p("    " + " | ".join(f"{'0.2  chance':>12}" for _ in names))
for d in quiz_d:
    cells = []
    for n in names:
        x = R[(R.variant == n) & (R.d == d)].iloc[0]
        cells.append(f"{'+' if x.base and x.sd >= 0.2 else '.':>4} {'+' if x.above_chance else '.':>7}")
    for t in title[d]: p("    " + " | ".join(f"{c:>12}" for c in cells) + "   " + t)

p("\n   Per list: statements with a position (>= 1 ex-MK) among the kept ones; share < 50 % = not ranked even if all are answered.")
for rule in ("SD>=0.2", "chance"):
    p(f"\n   rule {rule}:")
    p(f"   {'list':42} " + " ".join(f"{n[:16]:>16}" for n in names))
    for l in shown:
        cells = []
        for n in names:
            x = R[R.variant == n]
            kept = set(x[x.base & (x.sd >= 0.2)].d) if rule == "SD>=0.2" else set(x[x.above_chance].d)
            LP = data[n][0]; have = set(LP[(LP.letters == l) & (LP.n_mk >= 1)].d)
            tot = sum(nst[d] for d in kept); h = sum(nst[d] for d in kept & have)
            cells.append(f"{h}/{tot} {h / tot if tot else 0:.0%}")
        nm = cov[cov.letters == l].list_name.iloc[0][:42]
        p(f"   {nm:42} " + " ".join(f"{c:>16}" for c in cells))
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
