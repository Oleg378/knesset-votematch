"""Second, independent check of the label removals proposed by the Opus audit (customer, 2026-10-18).
Proposed removals = misfit bills of audit_result.md on the statement's direction, extended to resubmissions (same name without the
year, same direction) and, for q5, the two Keren Kayemeth LeIsrael Law repeal bills (not among the audited driving bills).
Controls = driving bills the audit judged fit (same statements, up to one per proposed removal), so the checker cannot tell which
items are proposed. Order shuffled.
-> local/research/secondary_weight_v2/check2_items.md, check2_key.csv
"""
import csv, json, os, re, random, sys
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
OUT = os.environ.get("DIR") or f"{ROOT}/local/research/secondary_weight_v2"   # DIR: wave folder (wave 3, 2026-10-18)
lab = LB.load(); bill_lab = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = {"name_en": v["name_en"], "plus": v.get("plus_en", ""), "minus": v.get("minus_en", "")}
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
by_dir = json.load(open(f"{ROOT}/export/quiz_bills.v2.json"))["by_direction"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall()); bkn = dict(con.execute("select bill_id, knesset from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", (n or "")).strip()
res = open(f"{OUT}/audit_result.md").read(); inp = open(f"{OUT}/audit_statements.md").read()
prop, fit = {}, {}
for line in res.splitlines():
    m = re.match(r"\| q(\d+) \|", line)
    if m: prop[m.group(1)] = set(re.findall(r"\b(2\d{6})\b", line.split("|")[4]))
for b in re.split(r"^## q", inp, flags=re.M)[1:]:
    q = b.split(" ")[0]
    fit[q] = [x for x in re.findall(r"^- (\d+) \|", b, flags=re.M) if x not in prop.get(q, ())]
if "5" in prop and not os.environ.get("DIR"): prop["5"] |= {"2196279", "2168492"}   # wave 1 only
items = []
for q, bills in prop.items():
    d = st[q]["d"]; ondir = {str(b): (s, role) for b, s, role in by_dir.get(d, [])}
    names = {base(bname.get(int(b))) for b in bills}
    ext = {b for b in ondir if base(bname.get(int(b))) in names}
    for b in sorted(bills | ext):
        if b in ondir: items.append(dict(q=q, d=d, bill=b, kind="proposed" if b in bills else "proposed_resubmission"))
    for b in fit.get(q, [])[:len(bills)]:
        items.append(dict(q=q, d=d, bill=b, kind="control"))
random.seed(20261018); random.shuffle(items)
def notes(b, n=300):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    if not os.path.exists(f): return ""
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n]
L = ["# Items: is the bill about the statement's question?", ""]
for i, it in enumerate(items, 1):
    s, d, b = st[it["q"]], it["d"], it["bill"]
    sign, role = next((x[1], x[2]) for x in by_dir[d] if str(x[0]) == b)
    mains = ", ".join(f"{t['n']} {D.get(str(t['n']), {}).get('name_en', '?')}" for t in bill_lab[int(b)][0])
    it.update(id=f"I{i}", role=role, sign=sign)
    L += [f"## I{i}", f"Statement (q{it['q']}): {s['statement_en']}",
          f"Direction «{D[d]['name_en']}» (+: {D[d]['plus']} −: {D[d]['minus']}); the bill is labeled {'+' if sign > 0 else '−'} on it.",
          f"Bill {b}, K{bkn.get(int(b))}: {bname.get(int(b))}", f"Bill's main topics: {mains}", f"Notes: {notes(b)}", ""]
open(f"{OUT}/check2_items.md", "w").write("\n".join(L) + "\n")
with open(f"{OUT}/check2_key.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=["id", "q", "d", "bill", "kind", "role", "sign"]); w.writeheader(); w.writerows(items)
from collections import Counter
print(len(items), Counter(i["kind"] for i in items), "size", len("\n".join(L)))
