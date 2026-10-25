"""Stage 5: Sonnet choices (basket_choice_run.py -> choice_out_K.json) -> data/directions/labels/split5_choice.jsonl, the format of
split2–4_choice.jsonl read by pipeline/labels.py (LATER). One line per bill × basket: every bill of a grouped name gets the choice of its
representative. «assigned» empty -> the bill stays in the basket (remainder). Signs are Sonnet's per part (normalized to «−»).
"""
import csv, glob, json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not (os.environ.get("TAG") and os.environ.get("STAGE")):   # never run by accident: a run rewrites data/directions/split/ and labels/
    raise SystemExit("usage: TAG=<local/research dir> STAGE=<N> python3 tools/basket_choice_apply.py   (see .claude/skills/split-themes/SKILL.md)")
B = f"{ROOT}/local/research/{os.environ['TAG']}"
key = {r["id"]: r for r in csv.DictReader(open(f"{B}/choice_key.csv"))}
ch = {}
for f in glob.glob(f"{B}/choice_out_[0-9]*.json"):
    if ".bad" in f: continue
    for x in json.load(open(f))["items"]: ch[x["id"]] = x
miss = [i for i in key if i not in ch]
if miss: raise SystemExit(f"{len(miss)} names without a choice, e.g. {miss[:3]}")
n = collections.Counter()
with open(f"{ROOT}/data/directions/labels/split{os.environ['STAGE']}_choice.jsonl", "w") as f:
    for i, k in key.items():
        subs = [{"n": s["n"], "sign": s["sign"].replace("-", "−"), "role": k["role"]} for s in ch[i]["subs"] if s.get("sign") in ("+", "-", "−")]
        n["assigned" if subs else "remainder"] += 1
        for b in k["bill_ids"].split():
            f.write(json.dumps({"bill_id": b, "parent": k["parent"], "role": k["role"], "parent_sign": k["parent_sign"],
                                "assigned": subs, "note": ch[i].get("note", "")}, ensure_ascii=False) + "\n")
print(dict(n))
