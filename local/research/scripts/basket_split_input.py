"""Split of the basket directions that pass the selection criteria (SHARED_UNDERSTANDING «Выпавшие законопроекты и направления без вопроса»,
[У] 2026-10-20) — the procedure of the 18 heterogeneous quiz directions (2026-10-16, jef/directions/split/SPLIT.md), same input: for each
direction its names, «+»/«−» and ALL bills labeled with it (effective labels, pipeline/labels.py). Bills are grouped by name without the year
(the volume rule counts names since 2026-10-18). A name that fell out of the quiz carries the checkers' reason (what it is about).
-> local/research/basket_split/input_K.json (K = 1..PARTS, directions balanced by size), catalog.md (current directions, for «same_as»)
"""
import csv, json, os, re, sys, collections, shutil
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/basket_split"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
BASKETS = "133 149 15 162 211 240 248 256 260 280 285 290 32 349 354 358 366 40 50 64 8 88 96 99".split()
PARTS = int(os.environ.get("PARTS", 6))
lab = LB.load(); bl = lab["bill_lab"]
D = {r["n"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
reason = {}
for it in csv.DictReader(open(f"{ROOT}/local/research/dropped_bills/items.csv")): reason[it["name"]] = it["reasons"]
dirs = {}
for d in BASKETS:
    g = collections.defaultdict(list)
    for b, (main, sec) in bl.items():
        for role, lst in (("main", main), ("secondary", sec)):
            for t in lst:
                if str(t["n"]) == d and LB.SGN.get(t.get("sign")): g[base(bname.get(b))].append((str(b), role, t["sign"]))
    items = []
    for nm, xs in g.items():
        x = dict(bill_ids=[b for b, _, _ in xs], role=xs[0][1], sign=xs[0][2], title=nm)
        if nm in reason: x["fell_out_of_quiz_reason"] = reason[nm]
        items.append(x)
    dirs[d] = dict(name_en=D[d]["name_en"], plus=D[d]["plus"], minus=D[d]["minus"], names=items)
order = sorted(dirs, key=lambda d: -len(dirs[d]["names"])); parts = [[] for _ in range(PARTS)]; size = [0] * PARTS
for d in order:
    k = size.index(min(size)); parts[k].append(d); size[k] += len(dirs[d]["names"])
for k, ds in enumerate(parts, 1):
    json.dump({d: dirs[d] for d in ds}, open(f"{OUT}/input_{k}.json", "w"), ensure_ascii=False, indent=1)
shutil.copy(f"{ROOT}/local/research/dropped_bills/catalog.md", f"{OUT}/catalog.md")
print({k + 1: (ds, size[k]) for k, ds in enumerate(parts)})
