"""Impact of the formula fix alone (SU 27.3, 2026-10-17: P = A + 0.25 V instead of (A + 0.25 V) / (1[A] + 0.25[V])), no relevance
filter, all 65 statements kept.

Old = production v1 (jef/positions, K = 2). New = local/research/relevance_impact/pos_0 (same code as pipeline/positions.py, filter off).
  1. K for the new positions by the same rule as quiz_match.py --calibrate (same synthetic users, same seed);
  2. sides «for / against» of each list on each statement (sign of p = P · e/(e + K) times the statement key): which flip and why;
  3. rankings: the customer's pilot answers; «a voter who answers exactly like list L» (old and new positions); 1,000 random
     full answer sets.

Usage: python3 local/research/scripts/formula_impact.py   -> local/research/formula_impact/ (summary.txt, sides.csv, flips.csv)
"""
import collections, csv, os, random, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/formula_impact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm

OLD, NEW = f"{ROOT}/jef/positions", f"{ROOT}/research/relevance_impact/pos_0"
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
per_d = collections.Counter(r["d"] for r in st)
for r in st: r["key_s"] = 1 if r["agree_key"] == "+" else -1; r["w"] = 1 / per_d[r["d"]]
cov = {r["letters"]: r for r in csv.DictReader(open(f"{OLD}/list_coverage.csv"))}
ev = [l for l, c in cov.items() if c["status"] == "ok"]
shown = [l for l, c in cov.items() if c["status"] != "not_evaluated"]
short = {l: c["list_name"].split(",")[0].split("(")[0].split("–")[0].strip()[:22] for l, c in cov.items()}

def load(path):
    pos = collections.defaultdict(dict)
    for r in csv.DictReader(open(f"{path}/list_topic_positions.csv")):
        pos[r["letters"]][r["d"]] = (float(r["P"]), float(r["sum_nA"]) + 0.25 * float(r["sum_nV"]), int(r["n_mk"]),
                                     float(r.get("P_A") or "nan"), float(r.get("P_V") or "nan"), float(r["sum_nA"]), float(r["sum_nV"]))
    return pos
pos_old, pos_new = load(OLD), load(NEW)

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)

# 1. K, same rule and code path as quiz_match.calibrate (seed 20261017)
def calibrate(pos):
    rnd = random.Random(20261017); out = []
    for k in (0, 2, 5, 10, 20, 50):
        vecs = {l: qm.list_vec(st, pos, l, k) for l in ev}
        rec = []
        for _ in range(40):
            for l in ev:
                ans = {}
                for r in st:
                    x = pos[l].get(r["d"])
                    if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
                    s = np.sign(x[0]) * r["key_s"] * (2 if abs(x[0]) > 0.5 else 1)
                    ans[r["q"]] = int(-s if rnd.random() < 0.2 else s)
                ranked = sorted(ev, key=lambda m: -np.nan_to_num(qm.score(st, ans, vecs[m])[0], nan=-9))
                rec.append(l in ranked[:3])
        first = collections.Counter()
        for _ in range(500):
            ans = {r["q"]: rnd.choice([-2, -1, 0, 1, 2]) for r in st}
            first[max(ev, key=lambda m: np.nan_to_num(qm.score(st, ans, vecs[m])[0], nan=-9))] += 1
        out.append((k, np.mean(rec), max(first.values()) / 500))
    return out
p("1. K (rule: among K with «persona in top 3» >= 0.97, the one with the smallest max share of first places at random answers)")
p("   K   persona top-3   max first-place share (fair = 1/12 = 0.083)")
cal = calibrate(pos_new)
for k, r, m in cal: p(f"   {k:<3} {r:13.3f}   {m:.3f}")
K_NEW = min((c for c in cal if c[1] >= 0.97), key=lambda c: c[2])[0]
p(f"   -> K = {K_NEW} (old: {qm.K:g})")

# 2. sides
def side(pos, l, r, k):
    x = pos.get(l, {}).get(r["d"])
    return None if not x else x[0] * x[1] / (x[1] + k) * r["key_s"]
rows = []
for r in st:
    for l in shown:
        a, b = side(pos_old, l, r, qm.K), side(pos_new, l, r, qm.K)   # same K: the formula effect only (the sign does not depend on K)
        if a is None and b is None: continue
        x = pos_new[l].get(r["d"])
        rows.append(dict(q=r["q"], title=r["title_en"], letters=l, list=short[l], old=a, new=b, n_mk=x[2] if x else 0,
                         from_bills=x[3] * r["key_s"] if x else None, from_votes=x[4] * r["key_s"] if x else None,
                         nA=x[5] if x else 0, nV=x[6] if x else 0))
flip = [x for x in rows if x["old"] and x["new"] and np.sign(x["old"]) != np.sign(x["new"])]
p(f"\n2. Sides «for / against»: {len(rows)} list × statement pairs; same side {len(rows) - len(flip)}, flipped {len(flip)}")
mo = np.median([abs(x["old"]) for x in rows]); mn = np.median([abs(x["new"]) for x in rows])
p(f"   median strength |p|: old {mo:.3f}, new {mn:.3f}")
def why(x):
    b, v = x["from_bills"], x["from_votes"]
    if x["nA"] == 0: return "no own bills: votes only, now at weight 0.25 — the old side came from the same votes"
    if abs(b) < 1e-9: return "own bills give 0 (all in one direction in that Knesset); votes decide, now at weight 0.25"
    if np.sign(b) == np.sign(x["new"]): return "own bills now outweigh the votes (before, MKs without bills had votes at full weight)"
    return "votes outweigh own bills"
for x in flip: x["why"] = why(x)
p("   flips by reason: " + "; ".join(f"{n} — {w}" for w, n in collections.Counter(x["why"] for x in flip).most_common()))
p("   flips with both |p| < 0.05 (both near zero): " + str(sum(abs(x["old"]) < 0.05 and abs(x["new"]) < 0.05 for x in flip)))
p("\n   per list: flipped / pairs")
for l in shown:
    n = sum(x["letters"] == l for x in rows); f = sum(x["letters"] == l for x in flip)
    p(f"   {short[l]:22} {f:3} / {n}")
p("\n   flipped pairs (side relative to the statement: + for, − against)")
p(f"   {'q':>3} {'statement':45} {'list':22} {'old':>6} {'new':>6} {'bills':>5} {'votes':>5}  reason")
for x in sorted(flip, key=lambda x: (int(x["q"]), x["list"])):
    p(f"   {x['q']:>3} {x['title'][:45]:45} {x['list']:22} {x['old']:+6.2f} {x['new']:+6.2f} {int(x['nA']):5} {int(x['nV']):5}  {x['why'].split(':')[0].split(';')[0]}")
with open(f"{OUT}/sides.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) + ["why"]); w.writeheader()
    for x in rows: w.writerow({**x, "why": x.get("why", "")})

# 3. rankings
def ranking(pos, k, ans):
    vecs = {l: qm.list_vec(st, pos, l, k) for l in shown}
    res = []
    for l in shown:
        c, cv = qm.score(st, ans, vecs[l])
        if c == c and cv >= qm.MIN_COVERAGE: res.append((c, l))
    return [l for c, l in sorted(res, reverse=True)], {l: c for c, l in res}
pilot = {}
for row in csv.reader(open(f"{ROOT}/jef/quiz/pilot_answers_filled.csv")):
    if row and row[0].strip().isdigit():
        a = row[-1].strip(); pilot[row[0].strip()] = "dk" if a in ("нз", "") else int(a)
p("\n3. Rankings\n   pilot answers (local/jef/quiz/pilot_answers_filled.csv):")
R3 = [ranking(pos_old, qm.K, pilot), ranking(pos_new, qm.K, pilot), ranking(pos_new, K_NEW, pilot)]
p(f"   {'#':>2} {'old, K=2':28} {'new formula, K=2':28} {'new formula, K=' + str(K_NEW):28}")
for i in range(max(len(r) for r, c in R3)):
    p(f"   {i + 1:>2} " + " ".join(f"{(short[r[i]] + ' ' + format(c[r[i]], '+.2f')) if i < len(r) else '':28}" for r, c in R3))
p("\n   a voter who answers every statement exactly like list L (side and strength of L's position): place of L")
p(f"   {'list':22} {'like old L: old/new':>20} {'like new L: old/new':>20}")
def like(pos, l):
    ans = {}
    for r in st:
        x = pos[l].get(r["d"])
        ans[r["q"]] = "dk" if not x or x[0] == 0 else int(np.sign(x[0]) * r["key_s"] * (2 if abs(x[0]) > 0.5 else 1))
    return ans
def place(r, l): return str(r.index(l) + 1) if l in r else "—"
for l in ev:
    a, b = like(pos_old, l), like(pos_new, l)
    p(f"   {short[l]:22} {place(ranking(pos_old, qm.K, a)[0], l) + ' / ' + place(ranking(pos_new, K_NEW, a)[0], l):>20} "
      f"{place(ranking(pos_old, qm.K, b)[0], l) + ' / ' + place(ranking(pos_new, K_NEW, b)[0], l):>20}")
N = 1000
for k in sorted({qm.K, K_NEW}, reverse=True):
    rnd = random.Random(20261018); same1 = t3 = 0
    for _ in range(N):
        ans = {r["q"]: rnd.choice([-2, -1, 0, 1, 2]) for r in st}
        a, b = ranking(pos_old, qm.K, ans)[0], ranking(pos_new, k, ans)[0]
        same1 += a[:1] == b[:1]; t3 += len(set(a[:3]) & set(b[:3])) / 3
    p(f"\n   {N} random full answer sets, old K=2 vs new formula K={k:g}: same leader {same1 / N:.0%}, top-3 overlap {t3 / N:.0%}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
