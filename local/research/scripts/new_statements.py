"""Point «new statements» (2026-10-18, [У] «делай сразу все»): directions that pass the selection criteria but have no statement.

Excluded: remainders of split directions, directions whose statements were removed by a decision (unsuitable, technical, split
and audit decisions of 2026-10-17/18), and passing stage-2 parts left out as duplicates (169b = q2, 151a = q33, 90b = q45).
For each direction: definition (+/−), the bills with the most weight in the list positions (weight = candidates who initiated it
+ 0.25 × their votes; same bill name grouped; sign of the label), and the list positions (P, new formula).

Usage: python3 local/research/scripts/new_statements.py   -> local/research/new_statements/input.md, dirs.json
"""
import collections, csv, json, os, sys
import duckdb, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/new_statements"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels, quiz_select as qs
import jev_directions_test as j

DUPS = {"169b": "q2", "151a": "q33", "90b": "q45"}
C = qs.criteria()
st = list(csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")))
okd = {r["d"] for r in st if r["status"] == "ok"}
decided = {r["d"] for r in st if r["d"] and r["status"] != "ok"}
plan = json.load(open(f"{ROOT}/jef/directions/split/plan.json")); plan2 = json.load(open(f"{ROOT}/jef/directions/split/plan2.json"))
rem = (set(plan["parents"]) - set(plan["keep"])) | {d for p in labels.later_plans() for d in p["parents"]}
ds = sorted((d for d, x in C.items() if x["base"] and d not in okd | decided | rem | set(DUPS)), key=lambda d: -C[d]["sd"])
if os.environ.get("DIRS"): ds = os.environ["DIRS"].split(",")   # only these directions (2026-10-18: threshold 30 → 25)
if os.environ.get("TAG"): OUT = os.path.join(ROOT, f"local/research/new_statements_{os.environ['TAG']}"); os.makedirs(OUT, exist_ok=True)

defs = {str(d["n"]): (d["name"], d["plus"], d["minus"]) for d in j.directions_final()}
for p in [plan] + labels.later_plans():
    for k, v in p["new"].items(): defs[k] = (v["name_en"], v["plus_en"], v["minus_en"])
lab = labels.load(relevance=False)["bill_lab"]
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cm = cand[cand.match.isin(["exact", "manual"])]
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); okl = set(cov[cov.status == "ok"].letters)
mks = set(cm[cm.letters.isin(set(cov[cov.status != "not_evaluated"].letters))].mk_id.astype(int))
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bills = con.sql("select bill_id, name from bills where knesset in (24, 25)").df().set_index("bill_id")
ini = con.sql("select distinct bill_id, mk_id from bill_initiators where is_initiator").df()
ini = ini[ini.mk_id.isin(mks) & ini.bill_id.isin(bills.index)]
votes = con.sql("""select a.bill_id, r.mk_id from vote_roster r join vote_attrs a using(vote_id) join bills b using(bill_id)
    where a.kind='bill' and a.stage in ('preliminary','first','second','third') and b.bill_type='פרטית' and r.result in ('for','against')""").df()
votes = votes[votes.mk_id.isin(mks)]
na, nv = collections.Counter(ini.bill_id), collections.Counter(votes.bill_id)
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str})
LP = LP[LP.letters.isin(okl) & (LP.n_mk >= 3)]
short = lambda s: s.split(",")[0].split("(")[0].split("–")[0].strip()[:18]

L = []
for i, d in enumerate(ds, 1):
    name, plus, minus = defs.get(d, (C[d]["name"], "", ""))
    agg = collections.defaultdict(lambda: [0.0, 0, 0, set()])
    for x, l in lab.items():
        if x not in bills.index: continue
        s = labels.signed_topics(l).get(d)
        if not s or (na[x] + nv[x]) == 0: continue
        a = agg[bills.name[x]]; a[0] += na[x] + 0.25 * nv[x]; a[1] += na[x]; a[2] += nv[x]; a[3].add("+" if s > 0 else "−")
    top = sorted(agg.items(), key=lambda kv: -kv[1][0])[:12]
    x = LP[LP.d == d].sort_values("P")
    pos = ", ".join(f"{short(r.list_name)} {r.P:+.2f}" for r in x.itertuples())
    L.append(f"## {i}. {d} — {name} (SD {C[d]['sd']:.2f}, r_gov {C[d]['r']:+.2f}, authorships {C[d]['nA']})")
    L.append(f"+: {plus}\n−: {minus}\nLists (P, − … +): {pos}")
    for nm, a in top: L.append(f"- [{'/'.join(sorted(a[3]))}] {a[0]:.1f} (init {a[1]}, votes {a[2]}) {nm}")
    L.append("")
open(f"{OUT}/input.md", "w").write("\n".join(L)); json.dump(ds, open(f"{OUT}/dirs.json", "w"))
print(len(ds), "directions ->", f"{OUT}/input.md")
