"""Impact of the relevance filter B (bills not about the statement's issue — Jev relevance < 0.2 — removed from authorship and
votes) on top of the formula fix, all 65 statements kept, K = 2. Customer request 2026-10-17.

Base = local/research/relevance_impact/pos_0 (new formula, no filter); filtered = local/research/relevance_impact/pos_0.2.
  1. sides «for / against» per list × statement: which flip, which become ~0, and which removed own bills caused it;
  2. rankings: the customer's pilot answers; 1,000 random full answer sets.
The filter itself was checked by Opus blind (local/research/opus_pilot/: 48 of 50 pairs agree at 0.2).

Usage: python3 local/research/scripts/filter_impact.py   -> local/research/filter_impact/summary.txt, sides.csv
"""
import collections, csv, json, os, random, sys
import duckdb, numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/filter_impact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels, quiz_match as qm

BASE, NEW, K = f"{ROOT}/research/relevance_impact/pos_0", f"{ROOT}/research/relevance_impact/pos_0.2", 2.0
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
per_d = collections.Counter(r["d"] for r in st)
for r in st: r["key_s"] = 1 if r["agree_key"] == "+" else -1; r["w"] = 1 / per_d[r["d"]]
cov = {r["letters"]: r for r in csv.DictReader(open(f"{ROOT}/jef/positions/list_coverage.csv"))}
shown = [l for l, c in cov.items() if c["status"] != "not_evaluated"]
short = {l: c["list_name"].split(",")[0].split("(")[0].split("–")[0].strip()[:22] for l, c in cov.items()}

def load(path):
    pos = collections.defaultdict(dict)
    for r in csv.DictReader(open(f"{path}/list_topic_positions.csv")):
        pos[r["letters"]][r["d"]] = (float(r["P"]), float(r["sum_nA"]) + 0.25 * float(r["sum_nV"]), int(r["n_mk"]),
                                     float(r["P_A"]), float(r["P_V"]), float(r["sum_nA"]), float(r["sum_nV"]))
    return pos
pb, pn = load(BASE), load(NEW)

# removed own bills per list × direction (authored by the list's ex-MKs, label carries d, relevance < 0.2)
lab = labels.load(relevance=False)["bill_lab"]
rel = {(int(r["bill_id"]), r["d"]): r["p"] for r in map(json.loads, open(labels.REL_FILE))}
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cm = cand[cand.match.isin(["exact", "manual"])]
mk2l = dict(zip(cm.mk_id.astype(int), cm.letters))
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
ini = con.sql("select distinct i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24, 25)").df()
bname = dict(con.sql("select bill_id, name from bills").fetchall())
removed = collections.defaultdict(collections.Counter)
for x, m in zip(ini.bill_id, ini.mk_id):
    if m in mk2l and x in lab:
        for d, s in labels.signed_topics(lab[x]).items():
            if rel.get((x, d), 1) < 0.2: removed[(mk2l[m], d)][(bname[x], s)] += 1

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)
def side(pos, l, r):
    x = pos.get(l, {}).get(r["d"])
    return None if not x else x[0] * x[1] / (x[1] + K) * r["key_s"]

rows = []
for r in st:
    for l in shown:
        a, b = side(pb, l, r), side(pn, l, r)
        if a is None and b is None: continue
        xb, xn = pb[l].get(r["d"]), pn[l].get(r["d"])
        rm = removed.get((l, r["d"]), collections.Counter())
        rows.append(dict(q=int(r["q"]), title=r["title_en"], letters=l, list=short[l], base=a, filtered=b,
                         nA_base=xb[5] if xb else 0, nA_new=xn[5] if xn else 0, nV_base=xb[6] if xb else 0, nV_new=xn[6] if xn else 0,
                         removed_bills="; ".join(f"{n} [{'+' if s > 0 else '−'}]×{c}" for (n, s), c in rm.most_common(3))))
S = pd.DataFrame(rows); S.to_csv(f"{OUT}/sides.csv", index=False)
both = S.dropna(subset=["base", "filtered"])
flip = both[np.sign(both.base) != np.sign(both.filtered)]
gone = S[S.base.notna() & S.filtered.isna()]
p(f"1. Sides: {len(S)} list × statement pairs; position lost (no data left) {len(gone)}; same side {len(both) - len(flip)}, flipped {len(flip)}")
p(f"   of the flips: both |p| < 0.05 (near zero) {int(((flip.base.abs() < .05) & (flip.filtered.abs() < .05)).sum())}; "
  f"own bills removed in the cell {int((flip.removed_bills != '').sum())}")
p(f"   median strength |p|: base {both.base.abs().median():.3f}, filtered {both.filtered.abs().median():.3f}")
p("\n   per list: flipped / lost / pairs")
for l in shown:
    q = S[S.letters == l]
    p(f"   {short[l]:22} {int(q.index.isin(flip.index).sum()):3} / {int(q.index.isin(gone.index).sum()):2} / {len(q)}")
p("\n   flips with |p| >= 0.05 on either side (+ for the statement, − against); removed own bills [their label sign] × MKs")
big = flip[(flip.base.abs() >= .05) | (flip.filtered.abs() >= .05)].sort_values(["q", "list"])
for x in big.itertuples():
    p(f"   q{x.q:<3} {x.title[:40]:40} {x.list:22} {x.base:+.2f} → {x.filtered:+.2f}  bills {int(x.nA_base)}→{int(x.nA_new)}, votes {int(x.nV_base)}→{int(x.nV_new)}")
    if x.removed_bills: p(f"        removed: {x.removed_bills}")
if len(gone):
    p("\n   positions lost: " + ", ".join(f"q{x.q} {x.list}" for x in gone.itertuples()))

def ranking(pos, ans):
    res = []
    for l in shown:
        c, cv = qm.score(st, ans, qm.list_vec(st, pos, l, K))
        if c == c and cv >= qm.MIN_COVERAGE: res.append((c, l))
    return [l for c, l in sorted(res, reverse=True)], {l: c for c, l in res}
pilot = {}
for row in csv.reader(open(f"{ROOT}/jef/quiz/pilot_answers_filled.csv")):
    if row and row[0].strip().isdigit():
        a = row[-1].strip(); pilot[row[0].strip()] = "dk" if a in ("нз", "") else int(a)
p("\n2. Rankings, pilot answers (local/jef/quiz/pilot_answers_filled.csv)")
p(f"   {'#':>2} {'formula only':28} {'formula + filter B':28}")
(ra, ca), (rb, cb) = ranking(pb, pilot), ranking(pn, pilot)
for i in range(max(len(ra), len(rb))):
    a = f"{short[ra[i]]} {ca[ra[i]]:+.2f}" if i < len(ra) else ""; b = f"{short[rb[i]]} {cb[rb[i]]:+.2f}" if i < len(rb) else ""
    p(f"   {i + 1:>2} {a:28} {b:28}")
rnd = random.Random(20261018); same1 = t3 = 0; N = 1000
for _ in range(N):
    ans = {r["q"]: rnd.choice([-2, -1, 0, 1, 2]) for r in st}
    a, b = ranking(pb, ans)[0], ranking(pn, ans)[0]
    same1 += a[:1] == b[:1]; t3 += len(set(a[:3]) & set(b[:3])) / 3
p(f"\n   {N} random full answer sets: same leader {same1 / N:.0%}, top-3 overlap {t3 / N:.0%}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
