"""Customer 2026-10-18 (audit №2 К1, variant б): «clear position» by the reliability of the sign instead of its size.
Unit = a distinct bill (by name without the year) behind the list on the direction: a bill its ex-MKs sponsored gives the topic sign;
a bill they voted on (private bills — V, the other camp's bills — O) gives sign(Σ topic sign × vote) over the list's MKs.
The list's side = sign of P. Clear (variant б) if, among the n bills with a non-zero sign, k agree with the side and the one-sided
binomial test P(X >= k | n, 0.5) < ALPHA, with n >= 2. Compared with the current rule (|p| >= 0.2, >= 2 MKs, >= 2 distinct bills):
agreement of the two rules, clear cells in the core, gold set (40 pairs), and how often a clear cell keeps its side between K24 and K25.
-> local/research/clear_alt/summary.txt
"""
import collections, json, os, re, sys
import numpy as np, pandas as pd
from scipy.stats import binom
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/clear_alt"; os.makedirs(OUT, exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "clear_alt", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bi, ab, pv, ov, vt, va, con = (ns[k] for k in ("bi", "ab", "pv", "ov", "vt", "va", "con"))
sys.path.insert(0, f"{ROOT}/pipeline"); import quiz_match as qm, quiz_report as qr, quiz_flow as qf
st, pos, cov = qm.load(); ok = [l for l, c in cov.items() if c["status"] == "ok"]
K = {r["q"]: r["key_s"] for r in st}; D = {r["q"]: r["d"] for r in st}; Ds = set(D.values())
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy(); cand["mk_id"] = cand.mk_id.astype(int)
mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
bn = {b: base(n) for b, n in con.execute("select bill_id, name from bills").fetchall()}
vb = dict(zip(va.vote_id, va.bill_id))
S = collections.defaultdict(float)   # (list, d, name) -> signed evidence
for r in bi.merge(ab, on="bill_id").itertuples():
    l = mk2l.get(r.mk_id)
    if l in ok and r.d in Ds: S[(l, r.d, bn.get(r.bill_id))] += 10 * r.s   # sponsoring dominates the list's votes on the same bill
for frame in (pv, ov):
    for r in frame.itertuples():
        l = mk2l.get(r.mk_id)
        if l not in ok: continue
        for d, s in vt[r.vote_id].items():
            if d in Ds: S[(l, d, bn.get(vb.get(r.vote_id)))] += s * r.v
cells = collections.defaultdict(list)
for (l, d, nm), v in S.items():
    if v != 0: cells[(l, d)].append(np.sign(v))
L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)
tsp = pd.read_csv(f"{ROOT}/local/research/threshold_stability/pairs.csv", dtype={"d": str}).set_index(["letters", "d"])
gold = pd.read_csv(f"{ROOT}/local/research/gold_e2e/key_DO_NOT_SHOW.csv", dtype=str).merge(pd.read_csv(f"{ROOT}/local/research/gold_e2e/result.csv", dtype=str), on="id")
gold = gold[gold.q.isin(D)]
core = qf.core()
def cur(l, d):
    x = pos[l].get(d); return bool(x) and qr.is_clear(x[0], x[2], x[4])
def alt(l, d, alpha):
    x = pos[l].get(d); sg = cells.get((l, d), [])
    if not x or len(sg) < 2 or x[0] == 0: return False
    k = sum(1 for s in sg if s == np.sign(x[0])); return binom.sf(k - 1, len(sg), 0.5) < alpha
allc = [(l, D[q]) for l in ok for q in D if pos[l].get(D[q])]
for alpha in (0.05, 0.1, 0.2):
    a = {c: alt(*c, alpha) for c in allc}; c_ = {c: cur(*c) for c in allc}
    both = sum(a[c] and c_[c] for c in allc); only_a = sum(a[c] and not c_[c] for c in allc); only_c = sum(c_[c] and not a[c] for c in allc)
    def side(rule, l, q):
        d = D[q]; x = pos[l].get(d)
        if not x or not rule(l, d): return "unclear"
        return "agree" if x[0] * K[q] > 0 else "disagree"
    for nm, rule in (("current", cur), (f"alt α={alpha}", lambda l, d: alt(l, d, alpha))):
        if nm == "current" and alpha != 0.05: continue
        g = [(side(rule, r.list, r.q), r.side) for r in gold.itertuples()]
        stated = [(x, y) for x, y in g if x != "unclear"]
        clear_cells = [c for c in allc if rule(*c)]
        stab = [np.sign(tsp.P24[c]) == np.sign(tsp.P25[c]) for c in clear_cells if c in tsp.index]
        weak_core = sum(1 for l in ok for q in core if side(rule, l, q) == "unclear")
        vo = [c for c in allc if pos[c[0]][c[1]][3] == 0]
        p(f"{nm:12}: clear cells {len(clear_cells)}/{len(allc)} | vote-only clear {sum(rule(*c) for c in vo)}/{len(vo)} | no clear position in core {weak_core}/96 | "
          f"gold: stated {len(stated)}/{len(g)}, agree {sum(x == y for x, y in stated)} | clear cells same side K24 vs K25 {np.mean(stab):.0%} (n={len(stab)})")
    p(f"   agreement of the rules (α={alpha}): both clear {both}, only alt {only_a}, only current {only_c}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
