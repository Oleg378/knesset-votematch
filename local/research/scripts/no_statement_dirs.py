"""Directions that pass the selection criteria (quiz_select.py) but have no statement — together with the bills dropped from the quiz
(customer 2026-10-20: one task). For each direction: selection numbers, why it has no statement by the rules already in force, overlap with
the quiz, and how many dropped bills it would bring back.

Existing patterns checked (no new rule):
  remainder  — what is left of a split direction gets no statement ([У] 2026-10-17, quiz_select.py);
  history    — the direction had a statement that was removed / found unsuitable (statements_v4.csv status, «change»);
  duplicate  — most of its bills are already in the topic of another statement ([У] 2026-10-20, LABEL_CHECK.md «Дополнения»: 165b, 77b,
               277g2, 69a, 80b) — here: share of its bill names that carry a label on a direction with a statement;
  dropped    — how many of the 611 dropped bills carry its label, and how many dropped names both blind groupings put into it.
-> local/research/dropped_bills/no_statement.csv
"""
import csv, json, os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/dropped_bills"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB, quiz_select as QS
import duckdb
C = QS.criteria(); lab = LB.load(); bl = lab["bill_lab"]
st = list(csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")))
quiz = {r["d"]: r["q"] for r in st if r["status"] == "ok"}
hist = collections.defaultdict(list)
for r in st:
    if r["status"] != "ok": hist[r["d"]].append(f"q{r['q']} {r['status']}: {r['change'].strip()[:160]}")
plan = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
remainder = (set(plan["parents"]) - set(plan["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
bn = {b: base(n) for b, n in con.execute("select bill_id, name from bills").fetchall()}
names = collections.defaultdict(set); inq = collections.defaultdict(set); withq = collections.defaultdict(collections.Counter)
for b, lb in bl.items():
    t = LB.signed_topics(lb); qd = [d for d in t if d in quiz]
    for d in t:
        names[d].add(bn.get(b))
        if any(x != d for x in qd): inq[d].add(bn.get(b))
        for x in qd:
            if x != d: withq[d][x] += 1
items = list(csv.DictReader(open(f"{OUT}/items.csv")))
drop_lab = collections.Counter(d for it in items for d in it["other"].split())
cat = {}
for X in "AB":
    o = json.load(open(f"{OUT}/{X}/out.json"))
    cat[X] = {i: t.get("catalog") for t in o["themes"] for i in t["members"]}
agree = collections.Counter(cat["A"][i["id"]] for i in items if cat["A"].get(i["id"]) and cat["A"].get(i["id"]) == cat["B"].get(i["id"]))
rows = []
for d, x in C.items():
    if not x["base"] or d in quiz: continue
    top = ", ".join(f"q{quiz[q]}:{n}" for q, n in withq[d].most_common(3))
    rows.append(dict(d=d, name=x["name"], lists=x["lists"], sd=round(x["sd"], 2), names_sel=x["nA"], names_all=len(names[d]), gov=int(x["gov"]),
                     remainder=int(d in remainder), history=" || ".join(hist.get(d, [])),
                     in_quiz_share=round(len(inq[d]) / max(len(names[d]), 1), 2), top_quiz=top,
                     dropped_bills=drop_lab.get(d, 0), dropped_names_agents=agree.get(d, 0)))
rows.sort(key=lambda r: (-r["dropped_bills"], r["d"]))
with open(f"{OUT}/no_statement.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "passing directions without a statement;", sum(r["remainder"] for r in rows), "remainders;",
      sum(bool(r["history"]) for r in rows), "with a removed/unsuitable statement")
