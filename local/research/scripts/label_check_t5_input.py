"""Label check of the bills that stage 5 (basket split, 2026-10-20) moved into directions WITH a statement: every bill in a quiz topic is
checked (docs/LABEL_CHECK.md), and these are new there. Same material as core_full_input.py (blind: statement, direction, bill, notes
260 chars; our label and sign are not shown), grouped by name without the year. Steps 2–4 then run with label_check_step.py t5 …
(SRC env for the source tag). -> local/research/label_check_qt5/items_1.md, key.csv
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STAGE = int(os.environ.get("STAGE", 5))
OUT = f"{ROOT}/local/research/label_check_qt{STAGE}"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]; bl4 = LB.load(stages=STAGE - 1)["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = {r["d"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
def notes(b, n=260):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
g = collections.defaultdict(list)
for b, (main, sec) in bl.items():
    old = set(LB.signed_topics(bl4.get(b, ([], []))))
    for role, lst in (("main", main), ("secondary", sec)):
        for t in lst:
            d = str(t["n"])
            if d in st and d not in old and LB.SGN.get(t.get("sign")): g[(d, base(bname.get(b)))].append((str(b), t["sign"], role))
L = ["# Items: is the bill about the statement's question, and which way?", ""]; key = []
for i, ((d, nm), bs) in enumerate(sorted(g.items()), 1):
    s = st[d]; n, pl, mi = D[d]; gid = f"F1-{i}"; rep = bs[0][0]
    key.append(dict(q=s["q"], d=d, name=nm, bills=" ".join(b for b, _, _ in bs), sign=bs[0][1], role=bs[0][2], rep=rep, id=gid))
    L += [f"## {gid}", f"Statement (q{s['q']}): {s['statement_en']}", f"Direction «{n}» — +: {pl} −: {mi}", f"Bill: {bname.get(int(rep))}", f"Notes: {notes(rep)}", ""]
open(f"{OUT}/items_1.md", "w").write("\n".join(L) + "\n"); pd.DataFrame(key).to_csv(f"{OUT}/key.csv", index=False)
print(len(key), "groups;", collections.Counter(k["q"] for k in key))
