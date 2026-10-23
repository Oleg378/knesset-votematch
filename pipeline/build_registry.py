"""Theme registry (customer 2026-10-21, docs variant 3): one row per theme that has a recorded decision, so that every theme passing the
selection either carries a statement or a reason why not (pipeline/check_invariants.py enforces it).

Built once from the decision records of 2026-10-15 … 2026-10-21 (statements.csv, split plans, the new-statement procedure, the
nested-theme audit); from now on the registry is the place where such decisions are written (by hand or by the procedure scripts),
and this builder is not re-run over it. Statuses:
  quiz            — the theme carries statement q
  duplicate       — duplicates statement q by meaning (its bills were checked for adding to q's theme)
  split           — split into parts (the theme itself is a remainder: no statement by rule)
  basket          — bills about unrelated subjects and no part reaches 5 names: no statement
  technical       — no honest question for a voter
  no_statement    — the draft step found no honest statement
  dropped_dup     — a drafted statement dropped in the final duplicate check (another statement asks the same)
  pending         — in the new-statement procedure now
-> jef/directions/registry.csv  (d, status, q, reason, source, date)
"""
import csv, glob, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline")); import labels as LB
R = f"{ROOT}/local/research"
rows = {}
def put(d, status, q="", reason="", source="", date=""):
    rows.setdefault(str(d), dict(d=str(d), status=status, q=q, reason=reason, source=source, date=date))
for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements.csv")):
    if r["status"] == "ok": rows[r["d"]] = dict(d=r["d"], status="quiz", q=r["q"], reason=r["title_en"], source="jef/quiz/statements.csv", date="")
pl = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
for p in sorted(set(pl["parents"]) - set(pl["keep"])): put(p, "split", source="jef/directions/split/plan.json", date="2026-10-16")
for k, (_, f, _) in enumerate(LB.LATER, 2):
    for p in json.load(open(f"{ROOT}/jef/directions/split/{f}"))["parents"]: put(p, "split", source=f"jef/directions/split/{f}")
for d in ("107", "128", "236", "289", "339", "343", "346"): put(d, "technical", reason="statement audit 2026-10-15/17", source="TECHNICAL.md §7")
for d, q in {"24": "42", "239": "60", "353": "52", "46": "62", "317": "9", "89": "64", "163": "33", "114a": "75", "112": "75", "196": "74",
             "344": "81", "29": "93", "103a": "64", "296a": "13", "161a": "19", "69a": "63", "80b": "47", "165b": "10", "77b": "45",
             "169b": "2", "151a": "33", "90b": "45", "211s2": "15", "96s4": "45", "8s4": "93"}.items():
    put(d, "duplicate", q=q, reason="decided 2026-10-17/18/20 (earlier rounds)", source="SHARED_UNDERSTANDING")
for r in ("2", "3", "5"):
    f = f"{R}/new_statements_round{r}/check_merged.json"
    if not os.path.exists(f): continue
    third = {}
    cf = f"{R}/new_statements_round{r}/check_C.csv"
    if os.path.exists(cf):
        for x in csv.DictReader(open(cf)): third[x["id"].strip()] = x
    for i, cat, a, b in json.load(open(f)):
        if cat == "disagree" and i in third:
            x = third[i]; votes = [a, b, (x["duplicate"].strip().lower(), x["technical"].strip().lower(), x["basket"].strip().lower())]
            dup = [v[0] for v in votes if v[0] != "none"]
            if len(dup) >= 2 and dup[0] == dup[1]: cat = "dup " + dup[0]
            elif sum(v[2] == "yes" for v in votes) >= 2: cat = "basket"
            elif sum(v[1] == "yes" for v in votes) >= 2: cat = "technical"
            else: cat = "clean"
        src = f"local/research/new_statements_round{r}/ (step 2)"
        if cat.startswith("dup"): put(i, "duplicate", q=cat.split()[1].lstrip("q"), reason="step 2: same question for voters", source=src, date="2026-10-20/21")
        elif cat == "technical": put(i, "technical", reason="step 2", source=src, date="2026-10-20/21")
        elif cat == "basket" and r == "5": put(i, "basket", reason="step 2 basket; split agent found no part ≥ 5 names", source=src, date="2026-10-21")
put("163p1", "duplicate", q="33", reason="step 2 (round 4)", source="local/research/new_statements_round4/", date="2026-10-21")
for f in glob.glob(f"{R}/basket_split2/out_*.json"):
    for d, r in json.load(open(f)).items():
        if r["decision"] == "technical": put(d, "technical", reason="basket split round 2: " + r.get("reason", "")[:80], source="local/research/basket_split2/", date="2026-10-20")
for d in ("196", "103c", "116b", "122s4", "8s4", "34s2", "88s2", "24"):
    put(d, "dropped_dup", reason="final duplicate check 2026-10-21: another statement asks the same", source="local/research/new_statements_round2/dups_*.csv", date="2026-10-21")
put("113", "no_statement", reason="one law carries the weight; no honest statement", source="local/research/new_statements_round2/drafts_1.json", date="2026-10-20")
for d in ("276", "292", "342", "240s3"): put(d, "pending", reason="new-statement procedure, round 5", source="local/research/new_statements_round5/", date="2026-10-21")
with open(f"{ROOT}/jef/directions/registry.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["d", "status", "q", "reason", "source", "date"]); w.writeheader()
    w.writerows(sorted(rows.values(), key=lambda r: (r["status"], r["d"])))
print(len(rows), "themes;", {s: sum(r["status"] == s for r in rows.values()) for s in sorted({r["status"] for r in rows.values()})})
