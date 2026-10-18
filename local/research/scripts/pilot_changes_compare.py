"""Compare blind agents A and B on the multi-change pilot (SU п. 23–26).

Usage: python3 local/research/scripts/pilot_changes_compare.py   -> prints stats, writes local/research/pilot_changes/compare.md (side-by-side table)
Object matching is left to a human reading the table; here only counts and action sets are compared.
"""
import collections, csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, "local/research/pilot_changes")
names = {r["bill_id"]: r for r in csv.DictReader(open(os.path.join(P, "sample.csv")))}

def load(x):
    rows = {}
    for line in open(os.path.join(P, f"blind/{x}/pass1.jsonl")):
        line = line.strip()
        if line: r = json.loads(line); rows[str(r["bill_id"])] = r
    return rows

A, B = load("A"), load("B")
ids = [i for i in names if i in A and i in B]
same_n = sum(len(A[i]["changes"]) == len(B[i]["changes"]) for i in ids)
acts = {x: collections.Counter(c["action"] for r in R.values() for c in r["changes"]) for x, R in (("A", A), ("B", B))}
same_actset = sum(collections.Counter(c["action"] for c in A[i]["changes"]) == collections.Counter(c["action"] for c in B[i]["changes"]) for i in ids)
print(f"bills: A {len(A)}, B {len(B)}, both {len(ids)}")
print(f"changes: A {sum(len(r['changes']) for r in A.values())}, B {sum(len(r['changes']) for r in B.values())}")
print(f"same number of changes: {same_n}/{len(ids)}; same multiset of actions: {same_actset}/{len(ids)}")
for x in "AB": print(x, dict(acts[x]))

with open(os.path.join(P, "compare.md"), "w") as f:
    f.write("# Пилот «список изменений»: A и B рядом\n\n")
    for i in ids:
        f.write(f"## {i} — {names[i]['name']}\n\n")
        for x, R in (("A", A), ("B", B)):
            f.write(f"**{x}** ({R[i]['status']}):\n\n")
            for k, c in enumerate(R[i]["changes"]):
                note = f" — {c['action_note']}" if c.get("action_note") else ""
                f.write(f"{k}. {c['object_ru']} → **{c['action']}**{note}\n")
            if R[i].get("difficulties"): f.write(f"\n_Трудности: {R[i]['difficulties']}_\n")
            f.write("\n")
for x in "AB":
    p = os.path.join(P, f"blind/{x}/pass2.json")
    if os.path.exists(p):
        t = json.load(open(p))
        print(f"{x} pass2: {len(t['topics'])} topics, sizes {sorted((len(z['members']) for z in t['topics']), reverse=True)[:15]}, technical {len(t['technical'])}")
