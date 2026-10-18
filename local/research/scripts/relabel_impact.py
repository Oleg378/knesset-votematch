"""Impact of the label removals on the quiz, two policies: «agreed» (second check not_about) and «agreed+borderline».
Reuses relabel_preview.py (positions recomputed without the removed (bill, direction) labels).
-> stdout; local/research/secondary_weight_v2/relabel_impact.txt
"""
import os, sys, csv
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/secondary_weight_v2"
sys.argv = ["x", "164"]
src = open(f"{ROOT}/local/research/scripts/relabel_preview.py").read().split("B, A_ = lists(set()), lists(DROP)")[0]
exec(compile(src, "relabel_preview.py", "exec"))
m = pd.read_csv(f"{OUT}/check2_merged.csv", dtype=str); m = m[m.kind != "control"]
POL = {"agreed": m[m.verdict == "not_about"], "agreed+borderline": m[m.verdict != "about"]}
LPs = {"now": lists(set())}
for k, v in POL.items(): LPs[k] = lists({(int(b), d) for b, d in zip(v.bill, v.d)})
CLOSE = 0.2; side = lambda x: "none" if abs(x) < CLOSE else ("+" if x > 0 else "−")
lines = []
def p(*a): lines.append(" ".join(str(x) for x in a)); print(lines[-1], flush=True)
K = {s["q"]: s["agree_key"] for s in st}
sp = pd.read_csv(f"{OUT}/spot_key.csv", dtype={"q": str}).merge(pd.read_csv(f"{OUT}/spot_result.csv"), on="id")
truth = ["none" if r.side == "unclear" else ("+" if (r.side == "agree") == (K[r.q] == "+") else "−") for r in sp.itertuples()]
p(f"{'policy':18} {'labels':>6} {'stmts':>5} {'side changed':>12} {'+/− swap':>8} {'SD<0.25':>7} {'median SD':>9} {'spot':>6}  core")
for k, LP in LPs.items():
    n = 0 if k == "now" else len(POL[k]); nst = 0 if k == "now" else POL[k].q.nunique()
    ch = sw = 0; sds = []
    for s in st:
        b, x = vals(LPs["now"], s["d"]), vals(LP, s["d"])
        if len(x) >= 2: sds.append(np.std(list(x.values())))
        for l in OK:
            sb, sx = side(b.get(l, 0) or 0), side(x.get(l, 0) or 0)
            if sb != sx: ch += 1; sw += {sb, sx} == {"+", "−"}
    got = [side(LP.P.get((r.list, r.d), 0)) for r in sp.itertuples()]
    p(f"{k:18} {n:6} {nst:5} {ch:12} {sw:8} {sum(v < 0.25 for v in sds):7} {np.median(sds):9.2f} {sum(g == t for g, t in zip(got, truth)):3}/24  " + ",".join(core(LP)))
p("\nstatements whose SD changes by >= 0.05 (now → agreed → agreed+borderline; rank by SD among 83):")
rk = {k: [q for _, q, _ in ranking(LP)] for k, LP in LPs.items()}
for s in st:
    v = {k: np.std(list(vals(LP, s["d"]).values())) for k, LP in LPs.items()}
    if max(abs(v[k] - v["now"]) for k in v) >= 0.05:
        p(f"  q{s['q']:>3} {s['title_en'][:40]:40} " + " → ".join(f"{v[k]:.2f} (#{rk[k].index(s['q'])+1})" for k in LPs))
open(f"{OUT}/relabel_impact.txt", "w").write("\n".join(lines) + "\n")
for k, LP in LPs.items():
    low = [(s["q"], s["title_en"], np.std(list(vals(LP, s["d"]).values())), np.std(list(vals(LPs["now"], s["d"]).values()))) for s in st
           if len(vals(LP, s["d"])) >= 2 and np.std(list(vals(LP, s["d"]).values())) < 0.25]
    p(f"{k}: below 0.25: " + "; ".join(f"q{q} {t} {b:.2f}←{a0:.2f}" for q, t, b, a0 in low))
open(f"{OUT}/relabel_impact.txt", "w").write("\n".join(lines) + "\n")
