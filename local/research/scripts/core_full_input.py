"""Audit №2 К2 (customer 2026-10-18): check EVERY bill behind the 8 core statements (not a sample). Bills are grouped by name without
the year (a re-submitted bill is judged once). Blind: the checker sees the statement, the direction and the bill, not our label or
sign. -> items_{1,2,3}.md, key.csv
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/core_full"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv"))}
core = json.load(open(f"{ROOT}/export/quiz_core.v2.json"))["core"]
bd = json.load(open(f"{ROOT}/export/quiz_bills.v2.json"))
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
def notes(b, n=260):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
groups = []
for q in core:
    d = st[q]["d"]; g = collections.defaultdict(list)
    for b, s, role in bd["by_direction"].get(d, []): g[base(bname.get(int(b)))].append((b, s, role))
    for nm, bs in g.items(): groups.append(dict(q=q, d=d, name=nm, bills=" ".join(b for b, _, _ in bs), sign="+" if bs[0][1] > 0 else "−", role=bs[0][2], rep=bs[0][0]))
print(len(groups), "groups")
parts = [groups[i::3] for i in range(3)]; key = []
for k, part in enumerate(parts, 1):
    L = ["# Items: is the bill about the statement's question, and which way?", ""]
    for i, g in enumerate(part, 1):
        gid = f"F{k}-{i}"; g["id"] = gid; key.append(g); s = st[g["q"]]; n, pl, mi = D[g["d"]]
        L += [f"## {gid}", f"Statement (q{g['q']}): {s['statement_en']}", f"Direction «{n}» — +: {pl} −: {mi}",
              f"Bill: {bname.get(int(g['rep']))}", f"Notes: {notes(g['rep'])}", ""]
    open(f"{OUT}/items_{k}.md", "w").write("\n".join(L) + "\n")
pd.DataFrame(key).to_csv(f"{OUT}/key.csv", index=False)
print([len(p) for p in parts])
