"""Wave 2 of label removals (customer, 2026-10-18): candidates from the wording / votes / main-label check (wording_result.csv):
Part 1 misfit bills, Part 2 voted bills judged not_about, Part 3 main labels judged not_about — each on the statement's direction,
extended to resubmissions (same name without the year, same direction). Controls: bills the same check judged about, same statements,
up to one per candidate. Blind, shuffled. Same item format as relabel_check_input.py (wave 1).
-> local/research/secondary_weight_v2/check3_items.md, check3_key.csv
"""
import csv, json, os, re, random, sys
import duckdb, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
W = f"{ROOT}/local/research/secondary_weight_v2"
lab = LB.load(); bill_lab = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = {"name_en": v["name_en"], "plus": v.get("plus_en", ""), "minus": v.get("minus_en", "")}
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
SGN = {"+": 1, "−": -1, "-": -1}
ondir = {}
for b, (m, s) in bill_lab.items():
    for role, lst in (("main", m), ("secondary", s)):
        for t in lst:
            if t.get("sign") in SGN: ondir.setdefault(str(t["n"]), {}).setdefault(str(b), (SGN[t["sign"]], role))
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = {str(k): v for k, v in con.execute("select bill_id, name from bills").fetchall()}; bkn = {str(k): v for k, v in con.execute("select bill_id, knesset from bills").fetchall()}
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", (n or "")).strip()
r = pd.read_csv(f"{W}/wording_result.csv", dtype=str); key = pd.read_csv(f"{W}/wording_key.csv", dtype=str).set_index("id")
cand, ctrl = {}, {}
for x in r.itertuples():
    q = x.id.split("-q")[1] if x.id.startswith("P1-") else key.q[x.id]
    if x.id.startswith("P1-"):
        if "misfit" in x.verdict: [cand.setdefault(q, set()).add(b) for b in re.findall(r"\b(\d{7})\b", str(x.detail))]
    elif re.fullmatch(r"\d+", str(x.item)):
        (cand if x.verdict == "not_about" else ctrl if x.verdict == "about" else {}).setdefault(q, set()).add(x.item)
inp = open(f"{W}/wording_input.md").read()                     # Part 1 controls: driving bills not flagged
for blk in re.split(r"^## P1-q", inp, flags=re.M)[1:]:
    q = blk.split(" ")[0]
    for b in re.findall(r"^- (\d+) \|", blk, flags=re.M):
        if b not in cand.get(q, set()): ctrl.setdefault(q, set()).add(b)
items = []
for q, bills in cand.items():
    d = st[q]["d"]; od = ondir.get(d, {})
    names = {base(bname.get(b)) for b in bills}
    ext = {b for b in od if base(bname.get(b)) in names}
    for b in sorted((bills & set(od)) | ext): items.append(dict(q=q, d=d, bill=b, kind="proposed" if b in bills else "proposed_resubmission"))
    for b in sorted(ctrl.get(q, set()) - bills - ext)[:len(bills)]:
        if b in od: items.append(dict(q=q, d=d, bill=b, kind="control"))
random.seed(20261019); random.shuffle(items)
def notes(b, n=300):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    if not os.path.exists(f): return ""
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n]
L = ["# Items: is the bill about the statement's question?", ""]
for i, it in enumerate(items, 1):
    s, d, b = st[it["q"]], it["d"], it["bill"]; sign, role = ondir[d][b]
    mains = ", ".join(f"{t['n']} {D.get(str(t['n']), {}).get('name_en', '?')}" for t in bill_lab[int(b)][0])
    it.update(id=f"I{i}", role=role, sign=sign)
    L += [f"## I{i}", f"Statement (q{it['q']}): {s['statement_en']}",
          f"Direction «{D[d]['name_en']}» (+: {D[d]['plus']} −: {D[d]['minus']}); the bill is labeled {'+' if sign > 0 else '−'} on it.",
          f"Bill {b}, K{bkn.get(b)}: {bname.get(b)}", f"Bill's main topics: {mains}", f"Notes: {notes(b)}", ""]
open(f"{W}/check3_items.md", "w").write("\n".join(L) + "\n")
with open(f"{W}/check3_key.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=["id", "q", "d", "bill", "kind", "role", "sign"]); w.writeheader(); w.writerows(items)
from collections import Counter
print(len(items), Counter(i["kind"] for i in items), "statements", len(cand), "size", len("\n".join(L)))
