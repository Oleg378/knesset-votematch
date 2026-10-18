"""Р8 (customer 2026-10-18, external audit С7/С11): symmetric label check for the core statements.
Per core statement: (a) 12 random bills that carry its direction (sponsored by 2026 candidates who are ex-MKs), stratified by sign;
(b) 8 random candidate bills that do NOT carry it but carry one of the 3 directions most often labeled together with it (possible
misses). The checker sees neither the current labels nor which group an item is from. -> items.md, key.csv
"""
import collections, csv, json, os, random, sys
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/r8_labels"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
core = json.load(open(f"{ROOT}/export/quiz_core.v2.json"))["core"]
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); mks = set(cand[cand.match.isin(["exact", "manual"])].mk_id.astype(int))
spons = set(b for b, m in con.execute("select bill_id, mk_id from bill_initiators where is_initiator").fetchall() if m in mks)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
lab_d = collections.defaultdict(dict); co = collections.defaultdict(collections.Counter)
for b, (m, s) in bl.items():
    ds = {str(t["n"]): (t.get("sign"), "main" if t in m else "secondary") for t in m + s if t.get("sign") in ("+", "−", "-")}
    for d, x in ds.items(): lab_d[d][b] = x
    for d in ds:
        for e in ds:
            if e != d: co[d][e] += 1
def notes(b, n=350):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
rnd = random.Random(20261019); items = []
for q in core:
    d = st[q]["d"]; on = [b for b in lab_d[d] if b in spons]
    plus = [b for b in on if lab_d[d][b][0] == "+"]; minus = [b for b in on if lab_d[d][b][0] != "+"]
    k_m = min(len(minus), max(3, round(12 * len(minus) / max(1, len(on)))))
    pick = rnd.sample(minus, k_m) + rnd.sample(plus, min(len(plus), 12 - k_m))
    nb = [e for e, _ in co[d].most_common(3)]
    pool = sorted({b for e in nb for b in lab_d[e] if b in spons and b not in lab_d[d]})
    miss = rnd.sample(pool, min(8, len(pool)))
    for b in pick: items.append(dict(q=q, d=d, bill=b, group="labeled", sign=lab_d[d][b][0], role=lab_d[d][b][1]))
    for b in miss: items.append(dict(q=q, d=d, bill=b, group="candidate", sign="", role=""))
rnd.shuffle(items)
L = ["# Items: is the bill about the statement's question, and which way?", ""]
for i, it in enumerate(items, 1):
    s, d, b = st[it["q"]], it["d"], it["bill"]
    mains = ", ".join(D.get(str(t["n"]), ("?",))[0] for t in bl[b][0])
    it["id"] = f"R{i}"
    L += [f"## R{i}", f"Statement (q{it['q']}): {s['statement_en']}",
          f"Direction «{D[d][0]}» — +: {D[d][1]} −: {D[d][2]}",
          f"Bill {b}: {bname.get(b)}", f"Bill's main topics: {mains}", f"Notes: {notes(b)}", ""]
open(f"{OUT}/items.md", "w").write("\n".join(L) + "\n")
pd.DataFrame(items).to_csv(f"{OUT}/key.csv", index=False)
print(len(items), collections.Counter(i["group"] for i in items), "size", len("\n".join(L)))
