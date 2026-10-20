"""Bills that fell out of the quiz entirely (LABEL_CHECK_PROGRESS «Следующий шаг», customer 2026-10-20: all removal sources, 611 bills).

A bill is dropped when overrides.json «remove» took at least one of its labels and no label on a direction with a statement (status ok)
is left. Bills are grouped by name without the year (a re-submitted bill is one item). The grouping agents see: the bill name, the start
of the explanatory note, why the label was removed (what the checkers said the bill is about), and a catalog of the current directions.
-> local/research/dropped_bills/{items.csv, items.md, catalog.md}
"""
import csv, json, os, re, sys, collections
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/dropped_bills"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in lab["split_plan"]["new"].items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
quiz = {r["d"]: r["q"] for r in st}
ov = json.load(open(f"{ROOT}/jef/directions/labels/overrides.json"))
rm = collections.defaultdict(list)
for r in ov["remove"]["items"]: rm[str(r["bill_id"])].append(r)
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
def notes(b, n=int(os.environ.get("NOTES", 160))):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""

dropped = [b for b in rm if int(b) in bl and not set(LB.signed_topics(bl[int(b)])) & set(quiz)]
g = collections.defaultdict(list)
for b in sorted(dropped, key=int): g[base(bname.get(int(b)))].append(b)
items = []
for i, (nm, bs) in enumerate(sorted(g.items(), key=lambda x: int(x[1][0])), 1):
    rs = [r for b in bs for r in rm[b]]
    reasons = list(dict.fromkeys(r.get("reason", "").strip() for r in rs if r.get("reason")))
    rep = max(bs, key=lambda b: len(notes(b)))
    other = sorted({d for b in bs for d in LB.signed_topics(bl[int(b)])})
    items.append(dict(id=f"B{i}", name=nm, bills=" ".join(bs), rep=rep, removed_from=" ".join(sorted({f"q{r['q']}/{r['d']}" for r in rs})),
                      reasons=" | ".join(reasons), other=" ".join(other)))
with open(f"{OUT}/items.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(items[0])); w.writeheader(); w.writerows(items)
L = ["# Bills that fell out of the quiz", ""]
for it in items:
    L += [f"## {it['id']}", f"Bill: {bname.get(int(it['rep']))}", f"Notes: {notes(it['rep'])}", f"Checkers' reason: {it['reasons']}", ""]
open(f"{OUT}/items.md", "w").write("\n".join(L) + "\n")
used = sorted({d for lb in bl.values() for d in LB.signed_topics(lb)} | set(quiz), key=lambda d: (int(re.search(r"\d+", d).group()), d))
C = ["# Catalog of current directions", "", "Format: id — name. +: … −: …", ""]
C += [f"- {d} — {D[d][0]}. +: {D[d][1]} −: {D[d][2]}" for d in used if d in D]
open(f"{OUT}/catalog.md", "w").write("\n".join(C) + "\n")
print(len(dropped), "bills,", len(items), "names,", sum(not it["reasons"] for it in items), "without a reason;", len(used), "directions in catalog")
