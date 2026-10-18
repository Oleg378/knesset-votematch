"""Impact of the relevance threshold (SU 27.3, 2026-10-17) with the new formula P = A + 0.25 V.

For each threshold t (0 = no filter): pipeline/positions.py is run with labels.REL_T = t into local/research/relevance_impact/pos_<t>/;
then per variant:
  - which quiz directions pass «>= 8 ok lists with >= 3 ex-MKs, SD >= s, sum_nA >= 30» for several s (the SD threshold was set
    on the old scale, so it is recalibrated together);
  - fragile sides: list × statement pairs where the own bills give nothing or the other side (side from votes);
  - rankings of the golden answer sets vs production v1 (export/golden.v1.json): same leader, top-3 overlap.
Gold test of the threshold itself: local/jef/directions/relevance/pilot_gold.csv.

Usage: python3 local/research/scripts/relevance_impact.py   -> local/research/relevance_impact/summary.txt
"""
import contextlib, csv, io, json, os, shutil, statistics, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/relevance_impact")
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels, quiz_match as qm

src = open(f"{ROOT}/pipeline/positions.py").read()
assert "OUT = f'{ROOT}/jef/positions'" in src
golden = json.load(open(f"{ROOT}/export/golden.v1.json"))["cases"]
quiz_d = list(dict.fromkeys(r["d"] for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"))
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv")
ok = set(cov[cov.status == "ok"].letters)
shown = set(cov[cov.status != "not_evaluated"].letters)
gold = {(r["bill_id"], r["d"]): r["gold"] for r in csv.DictReader(open(f"{ROOT}/jef/directions/relevance/pilot_gold.csv"))}
rel = {(r["bill_id"], r["d"]): r["p"] for r in map(json.loads, open(labels.REL_FILE))}

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)

p("gold test (agent's blind labels, 80 pairs; '?' = disputed):")
p("t     relevant kept   noise removed   disputed kept   all pairs removed")
for t in (0.1, 0.2, 0.3):
    k = [x for x in gold if gold[x] in "01"]
    tp = sum(rel[x] >= t for x in k if gold[x] == "1"); tn = sum(rel[x] < t for x in k if gold[x] == "0")
    q = [x for x in gold if gold[x] == "?"]
    p(f"{t:<5} {tp:>6}/{sum(gold[x] == '1' for x in k):<8} {tn:>6}/{sum(gold[x] == '0' for x in k):<8} {sum(rel[x] >= t for x in q):>6}/{len(q):<8} "
      f"{np.mean([v < t for v in rel.values()]):>10.0%}")

def run(t):
    d = f"{OUT}/pos_{t}"; os.makedirs(d, exist_ok=True)
    labels.REL_T = t if t > 0 else -1.0
    ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "relevance_impact"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {d!r}"), "positions.py", "exec"), ns)
    return pd.read_csv(f"{d}/list_topic_positions.csv", dtype={"d": str})

def rank(d):
    qm.POS = d
    return [[r["letters"] for r in qm.match(c["answers"], mult=c["mult"])
             if r["closeness"] is not None and r["closeness"] == r["closeness"] and r["coverage"] >= qm.MIN_COVERAGE] for c in golden]

base = [[r["id"] for r in c["ranking"] if r["ranked"]] for c in golden]
cases = [i for i, b in enumerate(base) if len(b) >= 3]
SDS = (0.3, 0.2, 0.15, 0.1)
p(f"\nnew formula P = A + 0.25 V; quiz directions {len(quiz_d)}; rankings compared with production v1 on {len(cases)} golden answer sets")
p(f"{'t':5} {'pairs':>5} {'by votes':>8} {'med|P|':>6} " + " ".join(f"{'pass SD>=' + str(s):>12}" for s in SDS) + f" {'leader same':>11} {'top3 ovl':>8}")
res = {}
for t in (0, 0.1, 0.2, 0.3):
    LP = run(t)
    for f in ("list_coverage.csv", "government_layer_list.csv"): shutil.copy(f"{ROOT}/jef/positions/{f}", f"{OUT}/pos_{t}")
    q = LP[LP.d.isin(quiz_d) & LP.letters.isin(shown)]
    byv = ((q.P_A.abs() < 1e-9) | (np.sign(q.P_A) != np.sign(q.P))).sum()
    x = LP[LP.d.isin(quiz_d) & LP.letters.isin(ok) & (LP.n_mk >= 3)]
    g = x.groupby("d").agg(n=("P", "size"), sd=("P", lambda v: statistics.pstdev(v) if len(v) > 1 else 0.0), nA=("sum_nA", "sum")).reindex(quiz_d)
    passes = {s: set(g[(g.n >= 8) & (g.sd >= s) & (g.nA >= 30)].index) for s in SDS}
    R = rank(f"{OUT}/pos_{t}")
    lead = np.mean([R[i][:1] == base[i][:1] for i in cases]); t3 = np.mean([len(set(R[i][:3]) & set(base[i][:3])) / 3 for i in cases])
    res[t] = (g, passes)
    p(f"{t:<5} {len(q):5} {byv:8} {q.P.abs().median():6.2f} " + " ".join(f"{len(passes[s]):>12}" for s in SDS) + f" {lead:11.0%} {t3:8.0%}")
p("\nold formula, no filter (production v1): SD median of quiz directions and all pass SD >= 0.3 by construction")
for t in (0, 0.2):
    g, passes = res[t]
    fail = [d for d in quiz_d if d not in passes[0.3]]
    p(f"\nt={t}: SD of quiz directions — median {g.sd.median():.2f}; failing at SD>=0.3: {len(fail)}")
    p("  failing at SD>=0.15: " + ", ".join(f"{d}(n={int(g.n[d]) if g.n[d] == g.n[d] else 0}, sd={g.sd[d]:.2f}, nA={int(g.nA[d]) if g.nA[d] == g.nA[d] else 0})" for d in quiz_d if d not in passes[0.15]))
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
