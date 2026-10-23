"""Measurement for the methodology page (customer 2026-10-24): how often a label on a statement theme is right — the bill is about
the statement's question (main or secondary role alike) and the sign is right. Uniform random sample of labels that feed the
positions (export/quiz_bills.json by_direction, after every check and the nested removals), seed 2026. Blind items: the checker
sees the statement, the direction definition, the bill's name and notes — not our sign or role. -> items_1.md, items_2.md, key.csv
"""
import csv, json, os, random, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.dirname(os.path.abspath(__file__))
import duckdb
N = int(os.environ.get("N", 100)); random.seed(2026)
bd = json.load(open(f"{ROOT}/export/quiz_bills.json")); qd = json.load(open(f"{ROOT}/export/quiz_data.json"))
st = {s["d"]: s for s in qd["statements"]}; D = qd["directions"]
labels = [(d, b, s, role) for d, refs in bd["by_direction"].items() if d in st for b, s, role in refs]
print(len(labels), "labels on statement themes")
sample = random.sample(labels, N)
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname = dict(con.execute("select bill_id, name from bills").fetchall())
def notes(b, n=700):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
parts = [sample[:N // 2], sample[N // 2:]]; key = []
for k, part in enumerate(parts, 1):
    L = ["# Items: is the bill about the statement's question, and which way?", ""]
    for i, (d, b, s, role) in enumerate(part, 1):
        gid = f"A{k}-{i}"; q = st[d]; dr = D[d]
        key.append(dict(id=gid, q=q["q"], d=d, bill=b, sign="+" if s > 0 else "−", role=role, name=bname.get(int(b), "")))
        L += [f"## {gid}", f"Statement: {q['statement_en']}", f"Direction «{dr['name_en']}» — +: {dr['plus_en']} −: {dr['minus_en']}",
              f"Bill: {bname.get(int(b), '')}", f"Notes: {notes(b)}", ""]
    open(f"{OUT}/items_{k}.md", "w").write("\n".join(L) + "\n")
with open(f"{OUT}/key.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=list(key[0])); w.writeheader(); w.writerows(key)
print([len(p) for p in parts], "with notes:", sum(1 for r in key if notes(r["bill"])))
