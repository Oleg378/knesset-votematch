"""Point «authorship zeroed in one-sided directions» (2026-10-17): impact of centering A over ALL MKs of the Knesset instead of only
over the MKs who authored bills on the direction.

Production (pipeline/positions.py): A = mean sign of the MK's bills on d, minus the mean of A over the MKs who authored on d in that
Knesset. In a direction where (almost) all bills push one way every author gets A ≈ 0, and a non-author gets 0 too: authoring a
dozen bills and authoring none look the same.
Variant «all MKs»: the mean is over all MKs of the Knesset, non-authors counted with raw A = 0 (as documented: «stronger or weaker
than the average MK», METHOD_AUDIT); an author gets raw − m, a MK with a position from votes only gets −m. Everything else as in
production (P = A + 0.25 V, Knesset pooling by nA for authors; a non-author's −m is averaged over the Knessets he sat in).
Not a production change: outputs to local/research/a_centering/.

Usage: python3 local/research/scripts/a_centering.py
"""
import contextlib, csv, io, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/a_centering"); os.makedirs(f"{OUT}/prod", exist_ok=True); os.makedirs(f"{OUT}/all", exist_ok=True); os.makedirs(f"{OUT}/none", exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
src0 = open(os.path.join(ROOT, "pipeline/positions.py")).read()
CENTER = "A['A'] = A.A - A.groupby(['knesset', 'd']).A.transform('mean')   # center per Knesset × direction"
POOL = "T[['nA', 'nV']] = T[['nA', 'nV']].fillna(0).astype(int)"
assert CENTER in src0 and POOL in src0
NEW_CENTER = """_mks = fm[fm.knesset.isin([24, 25])][['mk_id', 'knesset']].drop_duplicates()
_N = _mks.groupby('knesset').size()
_S = A.groupby(['knesset', 'd']).A.sum().reset_index(); _S['m'] = _S.A / _S.knesset.map(_N); _M = _S.set_index(['knesset', 'd']).m
A = A.join(_M, on=['knesset', 'd']); A['A'] = A.A - A.m; A = A.drop(columns='m')"""
NEW_POOL = POOL + """
_mm = _mks.merge(_M.reset_index(), on='knesset').groupby(['mk_id', 'd']).m.sum().reset_index()
_mm['m'] = _mm.m / _mm.mk_id.map(_mks.groupby('mk_id').size()); _mm = _mm.set_index(['mk_id', 'd']).m
_fill = T.A.isna()
T.loc[_fill, 'A'] = [-_mm.get((m, d), 0.0) for m, d in zip(T.mk_id[_fill], T.d[_fill])]"""
def run(src, out):
    src = src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {out!r}")
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, "positions_variant", "exec"), {"__file__": os.path.join(ROOT, "pipeline/positions.py"), "__name__": "pv"})
run(src0, f"{OUT}/prod")
run(src0.replace(CENTER, NEW_CENTER).replace(POOL, NEW_POOL), f"{OUT}/all")
run(src0.replace(CENTER, "pass   # variant: A not centered"), f"{OUT}/none")

def crit(d):
    LP = pd.read_csv(f"{d}/list_topic_positions.csv", dtype={"d": str})
    ok = set(pd.read_csv(f"{d}/list_coverage.csv").query("status == 'ok'").letters)
    LP = LP[LP.letters.isin(ok) & (LP.n_mk >= 3)]
    g = LP.groupby("d").agg(lists=("P", "size"), sd=("P", lambda x: x.std(ddof=0)), nA=("sum_nA", "sum"),
                            sdA=("P_A", lambda x: x.std(ddof=0)))
    return LP, g
LPp, gp = crit(f"{OUT}/prod"); LPa, ga = crit(f"{OUT}/all"); LPn, gn = crit(f"{OUT}/none")
st = [r for r in csv.DictReader(open(os.path.join(ROOT, "jef/quiz/statements_v4.csv"))) if r["status"] == "ok"]
plan = json.load(open(os.path.join(ROOT, "jef/directions/split/plan.json"))); rem = set(plan["parents"]) - set(plan["keep"])
L = []; p = L.append
el = lambda g: g[(g.lists >= 8) & (g.nA >= 30) & ~g.index.isin(rem)]
for name, g in (("production (authors only)", gp), ("all MKs", ga), ("not centered", gn)):
    e = el(g)
    p(f"{name:28} eligible {len(e)}; median SD {e.sd.median():.3f}; SD of the authorship part = 0: {(e.sdA < 1e-9).sum()}; "
      f"pass SD>=0.25: {(e.sd >= .25).sum()}, >=0.3: {(e.sd >= .3).sum()}")
p("\nquiz statements (status ok): SD production -> all MKs; pass at 0.25")
tp = tf = 0
for r in sorted(st, key=lambda r: int(r["q"])):
    d = r["d"]
    if d not in gp.index: continue
    a, b = gp.sd[d], ga.sd.get(d, np.nan); pa, pb = a >= .25 and gp.nA[d] >= 30, b >= .25 and ga.nA.get(d, 0) >= 30
    tp += pa; tf += pb
    p(f"  q{r['q']:>2} {d:5} {a:.2f} -> {b:.2f}  {'+' if pa else '.'} -> {'+' if pb else '.'}  {r['title_en']}")
p(f"pass: production {tp}, all MKs {tf} (of {len(st)}); not centered {sum(1 for r in st if r['d'] in gn.index and gn.sd[r['d']] >= .25 and gn.nA[r['d']] >= 30)}")
for nm, LPx in (("all MKs", LPa), ("not centered", LPn)):
    x = LPx[LPx.d == "173"].set_index("list_name")[["P", "P_A", "P_V"]].round(3)
    p(f"\nq13 (173), {nm}:\n" + x.sort_values("P").to_string())
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
