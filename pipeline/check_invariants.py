"""Invariants of the quiz data (customer 2026-10-21, after the cycle «dropped bills → new themes → new statements»). Run after every stage
that changes labels, themes or statements, and before every release: `make check`. Exit code 1 on any FAIL.

  I1  every statement's theme passes the selection (pipeline/quiz_select.py)          — a failing statement is removed (customer rule)
  I2  one theme — one statement
  I3  no statement on a remainder of a split theme or on a technical theme
  I4  every theme that passes the selection and has no statement has a decision in jef/directions/registry.csv
      (duplicate / split / basket / technical / no_statement / dropped_dup); «pending» is a WARN
  I5  no two statement themes nested: the smaller shares < 50 % of its bills (by name, ≥ 5 shared) with the other
  I6  every bill label on a statement theme was label-checked (jef/directions/labels/label_check_coverage.csv; a check under the theme
      a part was split from counts)
  I7  the export holds exactly the current statements (ids, texts, keys)
  I8  export/quiz_methodology.json (the texts of the methodology page, edited by hand) validates against
      export/quiz_methodology.schema.json (generated from web/src/methodology.ts: structure, allowed placeholders)
"""
import csv, json, os, re, sys, itertools, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels as LB, quiz_select as QS
import duckdb
fails, warns = [], []
def fail(code, msg): fails.append(f"FAIL {code}: {msg}")
def warn(code, msg): warns.append(f"WARN {code}: {msg}")

C = QS.criteria()
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements.csv")) if r["status"] == "ok"]
by_d = collections.defaultdict(list)
for r in st: by_d[r["d"]].append(r)
reg = {r["d"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/registry.csv"))}
lab = LB.load(); bl = lab["bill_lab"]
pl = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
rem = (set(pl["parents"]) - set(pl["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
tech = {d for d, r in reg.items() if r["status"] == "technical"}

for r in st:                                                                       # I1
    x = C.get(r["d"]) or {}
    if not x.get("base"): fail("I1", f"q{r['q']} «{r['title_en']}» ({r['d']}): lists {x.get('lists')}, SD {x.get('sd', 0):.2f}, names {x.get('nA')}")
for d, rs in by_d.items():                                                         # I2
    if len(rs) > 1: fail("I2", f"theme {d} has {len(rs)} statements: " + ", ".join("q" + r["q"] for r in rs))
for r in st:                                                                       # I3
    if r["d"] in rem: fail("I3", f"q{r['q']} on remainder {r['d']}")
    if r["d"] in tech: fail("I3", f"q{r['q']} on technical theme {r['d']}")
OK = {"duplicate", "split", "basket", "technical", "no_statement", "dropped_dup"}
for d, x in C.items():                                                             # I4
    if not x["base"] or d in by_d or d in rem: continue
    s = (reg.get(d) or {}).get("status")
    if s == "pending": warn("I4", f"{d} «{x['name'][:50]}» is in the procedure (pending)")
    elif s not in OK: fail("I4", f"{d} «{x['name'][:50]}» passes the selection, has no statement and no registry decision")
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)                     # I5
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
bn = {b: base(n) for b, n in con.execute("select bill_id, name from bills where knesset in (24, 25)").fetchall()}
nm = collections.defaultdict(set)
for b, lb in bl.items():
    if b in bn:
        for d in LB.signed_topics(lb):
            if d in by_d: nm[d].add(bn[b])
for a, b in itertools.combinations(by_d, 2):
    s = nm[a] & nm[b]; m = min(len(nm[a]), len(nm[b]))
    if m and len(s) >= 5 and len(s) / m >= 0.5:
        fail("I5", f"q{by_d[a][0]['q']} ({a}, {len(nm[a])}) and q{by_d[b][0]['q']} ({b}, {len(nm[b])}) share {len(s)} — {len(s)/m:.0%} of the smaller")
cov = {(r["bill_id"], r["d"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/labels/label_check_coverage.csv"))}   # I6
parent = {}
for p, subs in lab["split_plan"]["parents"].items():
    for s in subs: parent.setdefault(s, p)
def lineage(d):
    out = [d]
    while d in parent and parent[d] not in out: d = parent[d]; out.append(d)
    return out
un = collections.Counter()
for b, lb in bl.items():
    for d in LB.signed_topics(lb):
        if d in by_d and not any((str(b), x) in cov for x in lineage(d)): un[d] += 1
for d, n in un.items(): fail("I6", f"q{by_d[d][0]['q']} ({d}): {n} bill labels never label-checked")
ex = {s["q"]: s for s in json.load(open(f"{ROOT}/export/quiz_data.json"))["statements"]}   # I7
cur = {r["q"]: r for r in st}
for q in set(ex) ^ set(cur): fail("I7", f"q{q} is {'only in the export' if q in ex else 'not in the export'} (run make data)")
for q in set(ex) & set(cur):
    if ex[q]["statement_en"] != cur[q]["statement_en"] or int(ex[q]["key"]) != (1 if cur[q]["agree_key"] == "+" else -1): fail("I7", f"q{q}: export text or key differs (run make data)")

print(f"{len(st)} statements, {len(C)} themes with positions, {len(reg)} registry rows")
for l in fails + warns: print(l)
try:                                                                               # I8
    import jsonschema
    jsonschema.validate(json.load(open(f"{ROOT}/export/quiz_methodology.json")), json.load(open(f"{ROOT}/export/quiz_methodology.schema.json")))
except jsonschema.ValidationError as e:
    fail("I8", f"export/quiz_methodology.json: {e.message[:200]} at {'/'.join(map(str, e.absolute_path))}")
print("OK" if not fails else f"{len(fails)} FAIL, {len(warns)} WARN")
sys.exit(1 if fails else 0)
