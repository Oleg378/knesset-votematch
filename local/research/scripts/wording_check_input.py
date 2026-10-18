"""Input for the Opus check after the label removals (customer, 2026-10-18):
  Part 1 — the 23 touched statements still in the quiz: does the title / statement still describe what the bills that now create
           the list spread share? (driving bills as in sec_audit_input.py, now after the removals; «new» = not seen by the audit)
  Part 2 — sides that come from votes: list × statement pairs with |P| >= CLOSE where the list's own bills give no side
           (|P_A| < CLOSE or the opposite sign); the voted bills that push the list most to its side (contribution to the list's
           vote part before the government-share residual), top 5 per pair.
  Part 3 — main labels in the 35 statements not audited: driving bills with a main label and share >= 0.10.
-> local/research/secondary_weight_v2/wording_input.md, wording_key.csv
"""
import csv, json, os, re, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
W = f"{ROOT}/local/research/secondary_weight_v2"
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "wording_check_input", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bill_lab, bi, pv, va, labels = ns["bill_lab"], ns["bi"], ns["pv"], ns["va"], ns["labels"]
plan = ns["SPLIT_PLAN"]["new"]
D = {r["n"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = {"name_en": v["name_en"], "plus": v.get("plus_en", ""), "minus": v.get("minus_en", "")}
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
cec = pd.read_csv(f"{ROOT}/manual/cec_lists_26.csv"); LN = dict(zip(cec.letters, cec.name_en))
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"])
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str})
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters))
MT["l"] = MT.mk_id.map(mk2l); MT = MT.dropna(subset=["l"])
bname = dict(zip(ns["va"].bill_id, ns["va"].bill_name))
import duckdb
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bname.update(dict(con.execute("select bill_id, name from bills").fetchall())); bkn = dict(con.execute("select bill_id, knesset from bills").fetchall())
SGN = {"+": 1, "−": -1, "-": -1}
rows = []
for b, (main, sec) in bill_lab.items():
    seen = set()
    for role, lst in (("main", main), ("secondary", sec)):
        for t in lst:
            d, s = str(t["n"]), SGN.get(t.get("sign"))
            if s and d not in seen: seen.add(d); rows.append((b, d, s, role))
LAB = pd.DataFrame(rows, columns=["bill_id", "d", "s", "role"]); X = bi.merge(LAB, on="bill_id")
ROLE = {(b, d): r for b, d, r in zip(LAB.bill_id, LAB.d, LAB.role)}
def notes(b, n):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    if not os.path.exists(f): return ""
    return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n]
def mains(b): return ", ".join(f"{t['n']} {D.get(str(t['n']), {}).get('name_en', '?')}" for t in bill_lab[int(b)][0]) if int(b) in bill_lab else ""
def P_of(d): return {l: LP.P[(l, d)] for l in OK if (l, d) in LP.index}
def drivers(d, cap=8):
    P = P_of(d); mu = np.mean(list(P.values())); ss = sum((v - mu) ** 2 for v in P.values())
    nL = MT[MT.d == d].groupby("l").size(); NA = MT[MT.d == d].set_index("mk_id").nA
    sh, by = {}, {}
    for r in X[X.d == d].itertuples():
        l = mk2l.get(r.mk_id)
        if l in P and r.mk_id in NA.index and NA[r.mk_id] > 0:
            c = r.s / (NA[r.mk_id] * nL[l]); sh[r.bill_id] = sh.get(r.bill_id, 0) + c * (P[l] - mu) / ss
            by.setdefault(r.bill_id, {}); by[r.bill_id][l] = by[r.bill_id].get(l, 0) + c
    top, acc, pos = [], 0, sum(v for v in sh.values() if v > 0)
    for b, v in sorted(sh.items(), key=lambda t: -t[1]):
        if v <= 0 or len(top) >= cap or acc >= 0.85 * pos: break
        top.append((b, v, by[b])); acc += v
    return top
inp = open(f"{W}/audit_statements.md").read()
seen = {blk.split(" ")[0]: set(re.findall(r"^- (\d+) \|", blk, flags=re.M)) for blk in re.split(r"^## q", inp, flags=re.M)[1:]}
rm = json.load(open(f"{ROOT}/jef/directions/labels/overrides.json"))["remove"]["items"]
AFF = sorted({i["q"] for i in rm if i["q"] in st}, key=int)
key = []
L = ["# Input", "", "Lists (ok): " + "; ".join(f"{l} = {LN.get(l)}" for l in OK), "",
     "P = position on the direction (> 0 = its «+» end); «share» = the bill's share of the between-list spread.", "",
     "# Part 1 — touched statements: does the wording still fit the bills that now separate the lists?", ""]
for q in AFF:
    s = st[q]; d = s["d"]; P = P_of(d)
    L += [f"## P1-q{q} — {s['title_en']}", f"Statement: {s['statement_en']}", f"Agree = {'+' if s['agree_key'] == '+' else '−'} end. Direction {d} «{D[d]['name_en']}». +: {D[d]['plus']} −: {D[d]['minus']}",
          "List P: " + " ".join(f"{l} {P[l]:+.2f}" for l in OK if l in P), "Driving bills now:"]
    for b, v, by in drivers(d):
        new = str(b) not in seen.get(q, set())
        L.append(f"- {b} | K{bkn.get(b)} | {bname.get(b)} | sign {LAB[(LAB.bill_id == b) & (LAB.d == d)].s.iloc[0]:+d} | {ROLE[(b, d)]} | share {v:.2f} | lists "
                 + " ".join(f"{l}{c:+.2f}" for l, c in by.items()) + f" | main topics: {mains(b)}" + (" | NEW" if new else ""))
        if new or ROLE[(b, d)] == "secondary": n = notes(b, 200); L.append(f"  notes: {n}") if n else None
    L.append(""); key.append(dict(id=f"P1-q{q}", part=1, q=q))
# ---- Part 2: votes ----
CLOSE = 0.2
vt = {r.vote_id: (r.bill_id, labels.signed_topics(ns["vote_label"](r)) if ns["vote_label"](r) is not None else {}) for r in va.itertuples()}
pvv = pv.assign(l=pv.mk_id.map(mk2l)).dropna(subset=["l"])
nV = MT.set_index(["mk_id", "d"]).nV
L += ["# Part 2 — sides that come from votes only", "",
      "The list's own bills give no side here; its side comes from its ex-MKs' votes on private bills (weight 0.25). Listed: the voted bills that push the list most toward its side (for = +1, against = −1 per MK vote, × the bill's sign on the direction). For each bill: is it about the statement's question?", ""]
n2 = 0
for q, s in sorted(st.items(), key=lambda t: int(t[0])):
    d = s["d"]
    for l in OK:
        if (l, d) not in LP.index: continue
        r = LP.loc[(l, d)]
        if abs(r.P) < CLOSE or (abs(r.P_A) >= CLOSE and np.sign(r.P_A) == np.sign(r.P)): continue
        sub = pvv[pvv.l == l]; con_ = {}
        for x in sub.itertuples():
            b, tp = vt[x.vote_id]
            if d in tp and (x.mk_id, d) in nV.index and nV[(x.mk_id, d)] > 0:
                con_[b] = con_.get(b, 0) + tp[d] * x.v / nV[(x.mk_id, d)]
        side = np.sign(r.P); top = sorted(con_.items(), key=lambda t: -t[1] * side)[:5]
        top = [(b, c) for b, c in top if c * side > 0]
        if not top: continue
        n2 += 1; pid = f"P2-{n2}"
        L += [f"## {pid}: list {l} ({LN.get(l)}) — q{q} {s['title_en']}", f"Statement: {s['statement_en']}",
              f"Agree = {'+' if s['agree_key'] == '+' else '−'} end of «{D[d]['name_en']}». List P {r.P:+.2f} (own bills {r.P_A:+.2f}, votes {r.P_V:+.2f}).", "Voted bills pushing to this side:"]
        for b, c in top:
            L.append(f"- {b} | K{bkn.get(b)} | {bname.get(b)} | push {c:+.2f} | main topics: {mains(b)}")
            n = notes(b, 160); L.append(f"  notes: {n}") if n else None
        L.append(""); key.append(dict(id=pid, part=2, q=q, list=l, bills=" ".join(str(b) for b, _ in top)))
# ---- Part 3: main labels, non-audited statements ----
L += ["# Part 3 — main labels in statements not audited before", "", "Each item: a bill whose MAIN topic is the statement's direction and that creates a large part of the spread. Is it about the statement's question?", ""]
n3 = 0
for q, s in sorted(st.items(), key=lambda t: int(t[0])):
    if q in seen: continue
    d = s["d"]
    for b, v, by in drivers(d):
        if ROLE[(b, d)] != "main" or v < 0.10: continue
        n3 += 1; pid = f"P3-{n3}"
        L += [f"## {pid}: q{q} {s['title_en']}", f"Statement: {s['statement_en']}", f"Direction «{D[d]['name_en']}» (+: {D[d]['plus']} −: {D[d]['minus']})",
              f"- {b} | K{bkn.get(b)} | {bname.get(b)} | sign {LAB[(LAB.bill_id == b) & (LAB.d == d)].s.iloc[0]:+d} | share {v:.2f} | main topics: {mains(b)}"]
        n = notes(b, 200); L.append(f"  notes: {n}") if n else None
        L.append(""); key.append(dict(id=pid, part=3, q=q, bills=str(b)))
open(f"{W}/wording_input.md", "w").write("\n".join(L) + "\n")
pd.DataFrame(key).to_csv(f"{W}/wording_key.csv", index=False)
print("part1", len(AFF), "part2", n2, "part3", n3, "size", len("\n".join(L)))
