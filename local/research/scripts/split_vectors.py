"""Point 1, split block (2026-10-17): if the 15 directions are split as the Opus statement audit proposes, do the list positions of
the parts differ from each other, and do they repeat another quiz statement?

Bills are assigned to parts by the audit's own row lists (local/research/statement_audit/AUDIT.md «строки [...]» over the bill
tables in input_*.md); a bill of the direction outside every part goes to «rest». Not the Jev split: an estimate before spending.
Positions: pipeline/positions.py as is (P = A + 0.25 V), run on a copy with the remapped labels, outputs to OUT only.
Comparison: lists with status ok and >= 3 ex-MKs on both; Pearson r of P, and the share of lists on the same side.

Usage: python3 local/research/scripts/split_vectors.py   -> local/research/split_vectors/ (summary.txt, list_positions.csv)
"""
import collections, csv, glob, io, os, re, sys, contextlib
import numpy as np, pandas as pd, duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AUD = os.path.join(ROOT, "local/research/statement_audit")
OUT = os.path.join(ROOT, "local/research/split_vectors"); os.makedirs(OUT, exist_ok=True)

# ---- audit parts -> bill ids
tabs = {}
for f in sorted(glob.glob(f"{AUD}/input_*.md")):
    cur = None
    for l in open(f):
        m = re.match(r"## Direction (\S+) ", l)
        if m: cur = m.group(1); tabs[cur] = {}
        m = re.match(r"\| (\d+) \| (.*?) \| [\d.]+ \| \d+ \| \d+ \|", l)
        if m and cur: tabs[cur][int(m.group(1))] = m.group(2).strip()
parts, d = collections.defaultdict(dict), None
for l in open(f"{AUD}/AUDIT.md"):
    m = re.match(r"### .* — направление (\S+)", l)
    if m: d = m.group(1)
    m = re.match(r"- \*\*Часть «(.*?)»\*\* \(.?; строки \[(.*?)\]\)", l)
    if m and d: parts[d][m.group(1)] = [tabs[d][int(x)] for x in m.group(2).split(",") if x.strip()]
con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
by_name = collections.defaultdict(list)
for b, n in con.sql("select bill_id, name from bills").fetchall(): by_name[re.sub(r"\s+", " ", n).strip()].append(int(b))
PART = {}   # (bill_id, d) -> [part keys]
KEY = {}    # part key -> (d, part name)
for d, ps in parts.items():
    for i, (name, titles) in enumerate(ps.items(), 1):
        k = f"{d}#{i}"; KEY[k] = (d, name)
        for t in titles:
            for b in by_name.get(re.sub(r"\s+", " ", t).strip(), []): PART.setdefault((b, d), []).append(k)
for d in parts: KEY[f"{d}#rest"] = (d, "rest")

def remap(bill_lab):
    out = {}
    for b, (main, sec) in bill_lab.items():
        def f(lst):
            r = []
            for t in lst:
                d = str(t["n"])
                if d in parts: r += [{**t, "n": k} for k in PART.get((b, d), [f"{d}#rest"])]
                else: r.append(t)
            return r
        out[b] = (f(main), f(sec))
    return out

# ---- run pipeline/positions.py on the remapped labels, writing to OUT
src = open(os.path.join(ROOT, "pipeline/positions.py")).read()
src = src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {OUT!r}")
src = src.replace("signed_topics = labels.signed_topics", "signed_topics = labels.signed_topics\nbill_lab = REMAP(bill_lab)\ndname.update(NAMES)")
assert "REMAP(bill_lab)" in src and repr(OUT) in src
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "positions_split", "exec"), {"__file__": os.path.join(ROOT, "pipeline/positions.py"), "__name__": "positions_split", "REMAP": remap, "NAMES": {k: f"{d}: {n}" for k, (d, n) in KEY.items()}})

# ---- compare
LP = pd.read_csv(f"{OUT}/list_topic_positions.csv", dtype={"d": str})
ok = set(pd.read_csv(f"{OUT}/list_coverage.csv").query("status == 'ok'").letters)
LP = LP[LP.letters.isin(ok) & (LP.n_mk >= 3)]
M = LP.pivot(index="letters", columns="d", values="P")
nA = LP.groupby("d").sum_nA.sum()
SD = LP.groupby("d").P.std(ddof=0)
NL = LP.groupby("d").size()
st = [r for r in csv.DictReader(open(os.path.join(ROOT, "jef/quiz/statements_v4.csv"))) if r["status"] == "ok"]
qd = {r["d"]: r for r in st}

def cmp(a, b):
    x = M[[a, b]].dropna()
    if len(x) < 3 or x[a].std() == 0 or x[b].std() == 0: return float("nan"), 0, len(x)
    return float(np.corrcoef(x[a], x[b])[0, 1]), int((np.sign(x[a]) == np.sign(x[b])).sum()), len(x)

L = []
p = L.append
p("Split as the audit proposes: list positions of the parts (P = A + 0.25 V; lists ok with >= 3 ex-MKs)")
p("r — correlation of list positions on the direction; «same side» — lists with the same sign; criteria: lists >= 8, SD >= 0.3, nA >= 30\n")
for d in parts:
    ks = [k for k in KEY if KEY[k][0] == d and k in M.columns]
    p(f"== {d} (now q{', q'.join(r['q'] for r in st if r['d'] == d)})")
    for k in ks:
        crit = "pass" if NL.get(k, 0) >= 8 and SD.get(k, 0) >= 0.3 and nA.get(k, 0) >= 30 else "fail"
        p(f"   {k:8} {KEY[k][1][:58]:58} lists {NL.get(k, 0):2}  SD {SD.get(k, 0):.2f}  nA {int(nA.get(k, 0)):4}  {crit}")
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            r, s, n = cmp(a, b)
            p(f"   r({a}, {b}) = {r:+.2f}; same side {s}/{n}")
    for k in ks:
        if KEY[k][1] == "rest": continue
        best = sorted(((abs(cmp(k, o)[0]), o) for o in qd if o in M.columns and o != d and not np.isnan(cmp(k, o)[0])), reverse=True)[:2]
        p(f"   closest other quiz statements to {k}: " + "; ".join(f"q{qd[o]['q']} ({o}) r={cmp(k, o)[0]:+.2f}, same side {cmp(k, o)[1]}/{cmp(k, o)[2]}" for _, o in best))
    p("")
for a, b in [("309#2", "183#2")]:
    r, s, n = cmp(a, b); p(f"two «Family reunification» parts: r({a}, {b}) = {r:+.2f}; same side {s}/{n}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
M.round(4).to_csv(f"{OUT}/list_positions.csv")
