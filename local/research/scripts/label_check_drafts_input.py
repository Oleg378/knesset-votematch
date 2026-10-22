"""Label check (docs/LABEL_CHECK.md, step 1) for themes that get NEW statements (new-statement procedure, round 2+, 2026-10-20): every bill
of the theme against the draft text after the standard audit (rewrite -> the audit's text, keep -> the draft). Same material as
core_full_input.py (blind: statement, direction, bill, notes 260 chars; our label and sign not shown), grouped by name without the year,
bills taken from the effective labels (pipeline/labels.py), not from the export. Steps 2–4: label_check_step.py <TAG> merge1|merge2|apply.

Env: DRAFTS=a.json,b.json  AUDIT=out_1.jsonl,out_2.jsonl  TAG=<name>  PARTS=<n>  [SKIP=d1,d2 — themes not checked now (e.g. split by audit)]
-> local/research/label_check_q<TAG>/items_K.md, key.csv, texts.json (the checked texts)
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TAG = os.environ["TAG"]; OUT = f"{ROOT}/local/research/label_check_q{TAG}"; os.makedirs(OUT, exist_ok=True)
PARTS = int(os.environ.get("PARTS", 4)); SKIP = set(filter(None, os.environ.get("SKIP", "").split(",")))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
lab = LB.load(); bl = lab["bill_lab"]
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in lab["split_plan"]["new"].items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
aud = {}
for f in filter(None, os.environ.get("AUDIT", "").split(",")):
    for l in open(f):
        if l.strip(): o = json.loads(l); aud[o["d"]] = o
texts = {}
for f in os.environ["DRAFTS"].split(","):
    for x in json.load(open(f)):
        d = x["d"]
        if x.get("no_statement") or d in SKIP: continue
        a = aud.get(d, {}); t, k = x["statement_en"], x["key"]
        if a.get("verdict") == "split": continue
        if a.get("verdict") == "rewrite" and a["statements"] and a["statements"][0].get("new_statement_en"):
            t = a["statements"][0]["new_statement_en"]; k = a["statements"][0].get("new_agree_key") or k
        texts[d] = dict(d=d, title_en=x["title_en"], statement_en=t, key=k.replace("-", "−"))
json.dump(texts, open(f"{OUT}/texts.json", "w"), ensure_ascii=False, indent=1)
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
def notes(b, n=260):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
groups = []
for d, t in texts.items():
    g = collections.defaultdict(list)
    for b, (main, sec) in bl.items():
        for role, lst in (("main", main), ("secondary", sec)):
            for x in lst:
                if str(x["n"]) == d and LB.SGN.get(x.get("sign")): g[base(bname.get(b))].append((str(b), x["sign"], role))
    for nm, bs in g.items():
        groups.append(dict(q="n" + d, d=d, name=nm, bills=" ".join(b for b, _, _ in bs), sign=bs[0][1], role=bs[0][2], rep=bs[0][0]))
parts = [groups[i::PARTS] for i in range(PARTS)]; key = []
for k, part in enumerate(parts, 1):
    L = ["# Items: is the bill about the statement's question, and which way?", ""]
    for i, g in enumerate(part, 1):
        gid = f"F{k}-{i}"; g["id"] = gid; key.append(g); t = texts[g["d"]]; n, pl, mi = D[g["d"]]
        L += [f"## {gid}", f"Statement: {t['statement_en']}", f"Direction «{n}» — +: {pl} −: {mi}",
              f"Bill: {bname.get(int(g['rep']))}", f"Notes: {notes(g['rep'])}", ""]
    open(f"{OUT}/items_{k}.md", "w").write("\n".join(L) + "\n")
pd.DataFrame(key).to_csv(f"{OUT}/key.csv", index=False)
print(len(texts), "themes,", len(groups), "groups ->", [len(p) for p in parts])
