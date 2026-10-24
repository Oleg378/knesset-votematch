"""Sign check on the full explanatory notes (customer rule 2026-10-19, docs/LABEL_CHECK.md step 3): a proposed sign change is
confirmed only by a blind check that sees the notes up to 3,000 characters — as much as Jev saw when it labeled the bill.

Input: a CSV with columns q (empty for a direction without a statement), d, rep (representative bill_id), name, kind (flip / control) — e.g. rows of a label check's merged1.csv.
Usage: python3 tools/flip_check.py <in.csv> <out_dir>  -> <out_dir>/flip_items.md, flip_key.csv
"""
import csv, json, os, sys, random
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
N = 3000   # pipeline/jev_label.py: Hebrew title + first 3,000 characters of the notes
plan = LB.load()["split_plan"]["new"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements.csv"))}
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
def notes(b):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:N] if os.path.exists(f) else ""
k = pd.read_csv(sys.argv[1], dtype=str).sample(frac=1, random_state=19).reset_index(drop=True)
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
k["sid"] = [f"S{i+1}" for i in range(len(k))]
L = ["# Items: which way does the bill move the direction?", ""]
for _, g in k.iterrows():
    n, pl, mi = D[g["d"]]
    L += [f"## {g['sid']}"] + ([f"Statement (q{g['q']}): {st[g['q']]['statement_en']}"] if isinstance(g["q"], str) and g["q"] else []) + [f"Direction «{n}» — +: {pl} −: {mi}",
          f"Bill: {bname.get(int(g['rep']))}", f"Explanatory notes: {notes(g['rep'])}", ""]
open(f"{out}/flip_items.md", "w").write("\n".join(L) + "\n"); k.to_csv(f"{out}/flip_key.csv", index=False)
print(k[["sid", "kind", "rep"]].to_string())
