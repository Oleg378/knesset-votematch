"""Add check (SHARED_UNDERSTANDING «Дубль по смыслу», variant (б), [У] 2026-10-20; approved to run 2026-10-21): bills of a theme that
duplicates an existing statement by meaning (step 2 of the new-statement procedure) and are not yet in that statement's theme are checked
against the statement's text; a label on the statement's direction is ADDED where two independent blind checks say «about» with the same
sign (overrides.json «add», the rule of 2026-10-18). Also the 8 candidates of the dropped-bills analysis (dropped_bills/RESULT.md).
Blind material as in the label check (statement, direction, bill, notes 260 chars), grouped by name without the year.
-> local/research/add_check/items_K.md, key.csv
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TAG = os.environ.get("TAG"); OUT = f"{ROOT}/local/research/add_check" + (f"_{TAG}" if TAG else ""); os.makedirs(OUT, exist_ok=True)
PARTS = int(os.environ.get("PARTS", 11))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in lab["split_plan"]["new"].items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
R = f"{ROOT}/local/research"
dups = {}
for r in ("2", "3"):
    for i, cat, a, b in json.load(open(f"{R}/new_statements_round{r}/check_merged.json")):
        if cat.startswith("dup"): dups[i] = cat.split()[1].lstrip("q")
for f in (f"{R}/new_statements_round2/check_C.csv", f"{R}/new_statements_round3/check_C.csv"):
    for row in csv.DictReader(open(f)):
        if row["duplicate"].strip().lower() != "none": dups.setdefault(row["id"].strip(), row["duplicate"].strip().lstrip("q"))
dups["163p1"] = "33"   # round 4, both checks
if os.environ.get("DUPS"):   # only these theme:statement pairs (e.g. round 5), no dropped-bills candidates
    dups = dict(x.split(":") for x in os.environ["DUPS"].split(","))
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
def notes(b, n=260):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
groups = {}   # (q, name) -> dict
for d, q in dups.items():
    if q not in st: continue   # target statement removed
    T = st[q]["d"]
    for b, lb in bl.items():
        t = LB.signed_topics(lb)
        if d in t and T not in t:
            g = groups.setdefault((q, base(bname.get(b))), dict(q=q, d=T, src=d, bills=[]))
            g["bills"].append(str(b))
# dropped-bills candidates (dropped_bills/RESULT.md): item -> target statement
items = {r["id"]: r for r in csv.DictReader(open(f"{R}/dropped_bills/items.csv"))}
for iid, q in ({} if os.environ.get("DUPS") else {"B161": "20", "B244": "20", "B316": "20", "B226": "12", "B227": "78", "B327": "101", "B358": "9", "B372": "49"}).items():
    if q not in st: continue
    T = st[q]["d"]
    bs = [b for b in items[iid]["bills"].split() if int(b) in bl and T not in LB.signed_topics(bl[int(b)])]
    if bs: groups.setdefault((q, items[iid]["name"]), dict(q=q, d=T, src="dropped:" + iid, bills=[]))["bills"] += bs
G = [dict(g, name=k[1], bills=" ".join(sorted(set(g["bills"]))), rep=g["bills"][0], role="secondary") for k, g in groups.items()]
parts = [G[i::PARTS] for i in range(PARTS)]; key = []
for k, part in enumerate(parts, 1):
    L = ["# Items: is the bill about the statement's question, and which way?", ""]
    for i, g in enumerate(part, 1):
        gid = f"F{k}-{i}"; g["id"] = gid; key.append(g); s = st[g["q"]]; n, pl, mi = D[g["d"]]
        L += [f"## {gid}", f"Statement: {s['statement_en']}", f"Direction «{n}» — +: {pl} −: {mi}",
              f"Bill: {bname.get(int(g['rep']))}", f"Notes: {notes(g['rep'])}", ""]
    open(f"{OUT}/items_{k}.md", "w").write("\n".join(L) + "\n")
pd.DataFrame(key).to_csv(f"{OUT}/key.csv", index=False)
print(len(dups), "duplicate themes;", len(G), "groups ->", [len(p) for p in parts])
