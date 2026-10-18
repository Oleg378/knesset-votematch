"""Input for the Opus audit «which bills drive the list spread, and do they fit the statement» (customer, 2026-10-18).

Statements: those whose authorship-based list order changes most when secondary labels are dropped: r over the ok lists between
P_A (all labels) and P_A from main topics only < 0.8 (or undefined), plus q5. Per statement: text, direction ends, the 12 ok lists' positions P (P_A, P_V), and the
driving bills: each bill's share of the between-list spread of P (via its contribution to the lists' authorship part
P_A = mean over list MKs of the MK's mean sign), top bills until 85 % of the positive share or 8 bills; with role, sign, the bill's main
topics, the sponsoring lists and the first 220 chars of the explanatory notes (secondary labels only).
Spot checks: pairs (list, statement) whose side changes under w = 0.5 «count» or w = 0.25 «mean» (local/research/secondary_weight_v2/flips.csv),
sampled; each with all bills of that list's ex-MKs on the direction. The new value is NOT shown (blind).
-> local/research/secondary_weight_v2/audit_input.md, spot_key.csv
"""
import csv, json, os, sys, random
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
OUT = f"{ROOT}/local/research/secondary_weight_v2"
QS = os.environ.get("QS", "").split(",") if os.environ.get("QS") else None   # wave 3 (2026-10-18): only these statements, no spot checks
if QS: OUT = f"{ROOT}/local/research/secondary_weight_v2/{os.environ.get('TAG', 'qs')}"; os.makedirs(OUT, exist_ok=True)
lab = LB.load(); bill_lab = lab["bill_lab"]; plan = lab["split_plan"]["new"]
D = {r["n"]: r for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in plan.items(): D[k] = {"name_en": v["name_en"], "plus": v.get("plus_en", ""), "minus": v.get("minus_en", "")}
st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
LN = dict(zip(cov.letters, cov.list_name))
cec = pd.read_csv(f"{ROOT}/manual/cec_lists_26.csv"); LN.update(dict(zip(cec.letters, cec.name_en)))
LP = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"])
MT = pd.read_csv(f"{ROOT}/jef/positions/mk_topic_positions.csv", dtype={"d": str})
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); cm = cand.drop_duplicates("mk_id"); mk2l = dict(zip(cm.mk_id, cm.letters))
MT["l"] = MT.mk_id.map(mk2l); MT = MT.dropna(subset=["l"])
nL = MT.groupby(["l", "d"]).size()                     # list MKs present on d (the list mean's denominator)
NA = MT.set_index(["mk_id", "d"]).nA
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
bi = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
spons = bi.groupby("bill_id").mk_id.apply(list).to_dict()
bname = dict(con.execute("select bill_id, name from bills").fetchall()); bkn = dict(con.execute("select bill_id, knesset from bills").fetchall())
by_dir = json.load(open(f"{ROOT}/export/quiz_bills.v2.json"))["by_direction"]

def notes(b, n=500):
    f = f"{ROOT}/data/bill_texts/{b}.json"
    if not os.path.exists(f): return ""
    t = json.load(open(f)).get("notes") or ""
    return " ".join(t.replace("דברי הסבר", "", 1).split())[:n]
def mains(b):
    return ", ".join(f"{t['n']}{t.get('sign','')} {D.get(str(t['n']),{}).get('name_en','?')}" for t in bill_lab[int(b)][0]) if int(b) in bill_lab else ""

def drivers(d):
    P = {l: LP.P.get((l, d)) for l in OK if (l, d) in LP.index}
    m = np.mean(list(P.values())); dev = {l: P[l] - m for l in P}; ss = sum(v * v for v in dev.values())
    rows = []
    for b, s, role in by_dir.get(d, []):
        c = {}
        for mk in spons.get(int(b), []):
            l = mk2l.get(mk)
            if l in P and (mk, d) in NA.index and NA[(mk, d)] > 0: c[l] = c.get(l, 0) + s / (NA[(mk, d)] * nL[(l, d)])
        sc = sum(c[l] * dev[l] for l in c) / ss if ss else 0
        if c: rows.append(dict(b=b, s=s, role=role, share=sc, lists=c))
    rows.sort(key=lambda r: -r["share"])
    out, acc, pos = [], 0, sum(r["share"] for r in rows if r["share"] > 0)
    for r in rows:
        if r["share"] <= 0 or len(out) >= 8 or acc >= 0.85 * pos: break
        out.append(r); acc += r["share"]
    pa = sum(LP.P_A.get((l, d), 0) * dev[l] for l in P) / ss if ss else 0
    return P, out, pa, sum(r["share"] for r in rows if r["role"] == "secondary")


def pa_main(d):
    mk_main = {}
    for b, sg, role in by_dir.get(d, []):
        if role != "main": continue
        for mk in spons.get(int(b), []): mk_main.setdefault(mk, []).append(sg)
    out = {}
    for l in OK:
        if (l, d) not in nL.index: continue
        mks = MT[(MT.l == l) & (MT.d == d)].mk_id
        out[l] = sum(np.mean(mk_main[m]) for m in mks if m in mk_main) / nL[(l, d)]
    return out
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
R = {}
for q, r in st.items():
    m = pa_main(r["d"]); ls = [l for l in m if (l, r["d"]) in LP.index]
    R[q] = corr([LP.P_A[(l, r["d"])] for l in ls], [m[l] for l in ls])
AUD = sorted([q for q in st if not R[q] >= 0.8] + (["5"] if R["5"] >= 0.8 else []), key=lambda q: (R[q] if R[q] == R[q] else -9))
if QS: AUD = QS
print("audit statements:", len(AUD))

L = ["# Audit input: bills that create the list spread", "",
     "Lists (ok): " + "; ".join(f"{l} = {LN.get(l)}" for l in OK), "",
     "Position P = A + 0.25 V (A: mean sign of the list's ex-MKs' sponsored bills; V: residual of their private-bill votes). P > 0 = the «+» end of the direction. «share» = the bill's share of the between-list spread of P (sum over all bills of the authorship part = «authorship share»).", ""]
for q in AUD:
    r = st[q]; d = r["d"]; P, dr, pa, sec = drivers(d)
    L += [f"## q{q} — {r['title_en']}", f"Statement: {r['statement_en']}", f"Agree means: {'+' if r['agree_key']=='+' else '−'} end of the direction.",
          f"Direction {d} «{D[d]['name_en']}». +: {D[d]['plus']} −: {D[d]['minus']}",
          f"r(P_A all labels, P_A main only) = {R[q]:.2f}; authorship share of the spread {pa:.2f}; of it from secondary labels {sec:.2f}",
          "List P: " + " ".join(f"{l} {P[l]:+.2f}" for l in OK if l in P), "", "Driving bills:"]
    for x in dr:
        L.append(f"- {x['b']} | K{bkn.get(int(x['b']))} | {bname.get(int(x['b']))} | sign {x['s']:+d} | {x['role']} | share {x['share']:.2f} | lists "
                 + " ".join(f"{l}{v:+.2f}" for l, v in x["lists"].items()) + f" | bill main topics: {mains(x['b'])}")
        n = notes(x["b"], 220) if x["role"] == "secondary" else "";  L.append(f"  notes: {n}") if n else None
    L.append("")
open(f"{OUT}/audit_statements.md", "w").write("\n".join(L) + "\n")

if QS: sys.exit(0)
# ---- spot checks (blind) ----
fl = pd.read_csv(f"{OUT}/flips.csv", dtype={"q": str})
fl = fl[((fl.w == 0.5) & (fl["mode"] == "count")) | ((fl.w == 0.25) & (fl["mode"] == "mean"))]
pairs = fl.drop_duplicates(["q", "list"])
random.seed(20261018)
idx = list(pairs.index); random.shuffle(idx)
pick, seen = [], {}
for i in idx:                                   # at most 2 per list, 1 per statement, 30 pairs
    r = pairs.loc[i]
    if seen.get(r["list"], 0) >= 2 or any(p["q"] == r["q"] for p in pick): continue
    pick.append(r.to_dict()); seen[r["list"]] = seen.get(r["list"], 0) + 1
    if len(pick) >= 30: break
S = ["# Spot checks: what is the list's side on the statement?", "",
     "For each pair: the statement, the list, and every bill sponsored by the list's ex-MKs (Knessets 24–25) on the statement's direction, with role (main / secondary topic of the bill) and sign (+1 raises the direction, −1 lowers it). V = residual of the list's private-bill votes on this direction (weight 0.25; ±0.5 is large).", ""]
key = []
for k, r in enumerate(pick, 1):
    q, l = r["q"], r["list"]; s = st[q]; d = s["d"]
    S += [f"## S{k}: list {l} ({LN.get(l)}) — q{q} {s['title_en']}", f"Statement: {s['statement_en']}",
          f"Agree means: {'+' if s['agree_key']=='+' else '−'} end of direction {d} «{D[d]['name_en']}». +: {D[d]['plus']} −: {D[d]['minus']}",
          f"List ex-MKs present on this direction: {nL.get((l, d), 0)}; V part (0.25·V): {LP.P_V.get((l, d), 0):+.2f}", "Bills:"]
    mks = set(MT[(MT.l == l) & (MT.d == d)].mk_id)
    nb = 0
    for b, sg, role in by_dir.get(d, []):
        who = [m for m in spons.get(int(b), []) if m in mks]
        if not who: continue
        nb += 1
        S.append(f"- {b} | K{bkn.get(int(b))} | {bname.get(int(b))} | sign {sg:+d} | {role} | by {len(who)} of the list's ex-MKs | bill main topics: {mains(b)}")
        n = notes(b, 160);  S.append(f"  notes: {n}") if n else None
    if not nb: S.append("- (no bills; only votes)")
    S.append("")
    key.append(dict(id=f"S{k}", q=q, list=l, d=d, prod=r["base"], prod_side=r["base_side"], alt_cfg=f"{r['w']} {r['mode']}"))
open(f"{OUT}/spot_checks.md", "w").write("\n".join(S) + "\n")
pd.DataFrame(key).to_csv(f"{OUT}/spot_key.csv", index=False)
print("spot pairs:", len(pick))
