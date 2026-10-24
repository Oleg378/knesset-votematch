"""Stage 5 of the direction splits: the 24 basket directions (basket_split_input.py -> out_1..6.json by Opus, procedure of 2026-10-16).

Builds data/directions/split/plan5.json (same format as plan2–4: «parents» -> part keys, «new» -> definitions; a part that is the same
quantity as an existing direction («same_as») is a transfer: the existing direction id is the candidate, so its bills go there) and the
choice input for the Sonnet subagents that replace Jev (benchmark local/jef/directions/split/check/REVIEW.md, 2026-10-20: Sonnet 27/30
vs Jev 24/30): per bill name × basket — Hebrew title, first 3,000 characters of the notes (as Jev saw), the candidates with «+»/«−».
Unlike stages 2–4 the sign is asked per candidate: parts may be oriented against the basket (e.g. 366 → more oversight).
-> data/directions/split/plan5.json, local/research/basket_split/choice_K.json (CHUNK names each), choice_key.csv
"""
import csv, json, os, re, sys, collections, glob
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = f"{ROOT}/local/research/{os.environ.get('TAG', 'basket_split')}"
STAGE = int(os.environ.get("STAGE", 5))
CHUNK = int(os.environ.get("CHUNK", 90))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load()
D = {r["n"]: {"name": r["name_en"], "plus": r["plus"], "minus": r["minus"]} for r in csv.DictReader(open(f"{ROOT}/data/directions/DIRECTIONS_LIST.csv"))}
for k, v in lab["split_plan"]["new"].items(): D[k] = {"name": v["name_en"], "plus": v.get("plus_en", ""), "minus": v.get("minus_en", "")}
out = {}
for f in sorted(glob.glob(f"{B}/out_*.json")): out.update(json.load(open(f)))
plan = {"note": f"Stage {STAGE} (2026-10-20, [У]): split of the basket directions that pass the selection criteria (SHARED_UNDERSTANDING «Выпавшие "
        "законопроекты и направления без вопроса»; local/research/basket_split/). Procedure of 2026-10-16 (Opus proposes parts; a part that is "
        "an existing direction is a transfer); the choice is made by Sonnet subagents instead of Jev; sign asked per part.",
        "parents": {}, "new": {}, "transfers": {}}
cands = {}
for d, r in out.items():
    if r["decision"] != "split": continue
    r["subs"] = [x for x in r["subs"] if (x.get("same_as") or "").strip() != d]   # a part «same as» its own basket = the basket keeps those bills
    plan["parents"][d] = []; cands[d] = {}
    for s in r["subs"]:
        t = (s.get("same_as") or "").strip() or None
        if t and t not in D: print("unknown same_as", d, s["key"], t); t = None
        if t:
            plan["parents"][d].append(t); plan["transfers"][s["key"]] = t; cands[d][t] = D[t]
        else:
            plan["parents"][d].append(s["key"])
            plan["new"][s["key"]] = {k: s[k] for k in ("name_ru", "name_en", "plus_en", "minus_en")}
            cands[d][s["key"]] = {"name": s["name_en"], "plus": s["plus_en"], "minus": s["minus_en"]}
# a transfer target that is itself split (a basket of this stage, or a parent of stages 1–4) is replaced by its parts: otherwise the bill
# would land in a remainder, which gets no statement by rule
earlier = {p: subs for p, subs in lab["split_plan"]["parents"].items() if p not in json.load(open(f"{ROOT}/data/directions/split/plan.json"))["keep"]}
def parts(t, seen=()):
    subs = plan["parents"].get(t) or earlier.get(t)
    if not subs or t in seen: return [t]
    return [x for s in subs for x in parts(s, seen + (t,))]
for d in cands:
    exp = {}
    for k, v in cands[d].items():
        for x in (parts(k) if k in plan["transfers"].values() else [k]):
            if x in D or x in plan["new"]: exp[x] = D.get(x) or {"name": plan["new"][x]["name_en"], "plus": plan["new"][x]["plus_en"], "minus": plan["new"][x]["minus_en"]}
    cands[d] = exp
json.dump(plan, open(f"{ROOT}/data/directions/split/plan{STAGE}.json", "w"), ensure_ascii=False, indent=1)
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
def notes(b, n=3000):
    f = f"{ROOT}/raw/bill_texts/{b}.json"
    return (json.load(open(f)).get("notes") or "")[:n] if os.path.exists(f) else ""
items, key = [], []
for d in cands:
    inp = next(json.load(open(f))[d] for f in glob.glob(f"{B}/input_*.json") if d in json.load(open(f)))
    for x in inp["names"]:
        rep = max(x["bill_ids"], key=lambda b: len(notes(b)))
        iid = f"{d}:{rep}"
        items.append({"id": iid, "title": bname.get(int(rep)), "notes": notes(rep),
                      "parent": {"n": d, "name": D[d]["name"]},
                      "candidates": [{"n": k, **v} for k, v in cands[d].items()]})
        key.append({"id": iid, "parent": d, "bill_ids": " ".join(x["bill_ids"]), "role": x["role"], "parent_sign": x["sign"]})
for k in range(0, len(items), CHUNK):
    json.dump(items[k:k + CHUNK], open(f"{B}/choice_{k // CHUNK + 1}.json", "w"), ensure_ascii=False, indent=1)
with open(f"{B}/choice_key.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(key[0])); w.writeheader(); w.writerows(key)
print(len(plan["parents"]), "baskets split;", len(plan["new"]), "new parts;", len(plan["transfers"]), "transfers;",
      len(items), "names ->", -(-len(items) // CHUNK), "chunks")
