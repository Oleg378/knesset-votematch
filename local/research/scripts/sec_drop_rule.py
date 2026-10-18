"""Rule test (customer, 2026-10-18): drop a SECONDARY label when the bill's main topic is a direction that has its own statement.
  R1 — the main topic itself has an ok statement;
  R2 — R1, or the main topic belongs to the same split family (number without the letter suffix, e.g. 277a ~ 277f) as a direction
       with an ok statement.
Measured against the Opus audit (local/research/secondary_weight_v2/audit_result.md): of the driving bills judged misfit / fit, how
many lose the label. Then the impact on the quiz as in sec_weight_impact.py (list sides, SD, core) and on the 24 blind spot checks.
-> local/research/secondary_weight_v2/drop_rule.txt
"""
import csv, os, re, json
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/secondary_weight_v2"
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "sec_drop_rule", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bill_lab, bi, pv, va, share, SGN = (ns[k] for k in ("bill_lab", "bi", "pv", "va", "share", "SGN"))
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
QD = {r["d"] for r in st}
fam = lambda d: (re.match(r"\d+", str(d)) or re.match(r".*", str(d))).group(0)
QF = {fam(d) for d in QD}

def entries(lab):          # [(d, s, role, mains)]
    mains = [str(t["n"]) for t in lab[0]]
    out, seen = [], set()
    for role, lst in (("main", lab[0]), ("sec", lab[1])):
        for t in lst:
            s = SGN.get(t.get("sign")); d = str(t["n"])
            if s and d not in seen: seen.add(d); out.append((d, s, role, mains))
    return out
def keep(rule, d, role, mains):
    if role == "main" or rule == "none": return True
    if rule == "R1": return not any(m in QD for m in mains)
    if rule == "R2": return not any(m in QD or fam(m) in QF for m in mains)
def vote_label(r):
    if r.vote_id in ns["pk_agent"]: return ns["pk_agent"][r.vote_id]
    if r.vote_id in ns["pk_whole"]: return ns["pk_whole"][r.vote_id]
    return bill_lab.get(r.bill_id)
AB = pd.DataFrame([(b, d, s, ro, tuple(m)) for b, lab in bill_lab.items() for d, s, ro, m in entries(lab)], columns=["bill_id", "d", "s", "role", "mains"])
VL = {r.vote_id: (entries(vote_label(r)) if vote_label(r) is not None else []) for r in va.itertuples()}
KEY = ["mk_id", "knesset", "d"]
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); cm = cand.drop_duplicates("mk_id"); mk2l = dict(zip(cm.mk_id, cm.letters))
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
gl = pd.read_csv(f"{ROOT}/jef/positions/government_layer_list.csv"); gl = gl[gl.knesset == 25]; GOV = dict(zip(gl.letters, gl.share_with_gov))

def list_pos(rule):
    ab = AB[[keep(rule, d, ro, m) for d, ro, m in zip(AB.d, AB.role, AB.mains)]]
    A = bi.merge(ab, on="bill_id").groupby(KEY).s.agg(["mean", "size"]).reset_index().rename(columns={"mean": "A", "size": "nA"})
    vrows = [(r.mk_id, r.knesset, d, s * r.v) for r in pv.itertuples() for d, s, ro, m in VL[r.vote_id] if keep(rule, d, ro, m)]
    V = pd.DataFrame(vrows, columns=KEY + ["c"]).groupby(KEY).c.agg(["mean", "size"]).reset_index().rename(columns={"mean": "pos", "size": "nV"})
    V = V.join(share, on=["mk_id", "knesset"]).dropna(subset=["gov_share"])
    g = V.groupby(["knesset", "d"]); mx, my = g.gov_share.transform("mean"), g.pos.transform("mean")
    c_ = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform("mean")
    v_ = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform("mean")
    V["V"] = V.pos - my - (c_ / v_.where(v_ > 1e-9)).fillna(0) * (V.gov_share - mx)
    def pool(df, val, n):
        g = df.assign(x=df[val] * df[n]).groupby(["mk_id", "d"]); return pd.DataFrame({val: g.x.sum() / g[n].sum(), n: g[n].sum()})
    T = pool(A, "A", "nA").join(pool(V, "V", "nV"), how="outer").reset_index()
    T["P"] = T.A.fillna(0) + 0.25 * T.V.fillna(0)
    T = T.assign(l=T.mk_id.map(mk2l)).dropna(subset=["l"])
    return T.groupby(["l", "d"]).P.mean(), len(AB) - len(ab)

lines = []
def p(*a): lines.append(" ".join(str(x) for x in a)); print(lines[-1], flush=True)

# ---- 1. against the audit ----
qd = {r["q"]: r["d"] for r in st}
inp = open(f"{OUT}/audit_statements.md").read(); res = open(f"{OUT}/audit_result.md").read()
mis = {}
for line in res.splitlines():
    m = re.match(r"\| q(\d+) \|", line)
    if m: mis[m.group(1)] = set(re.findall(r"\b(2\d{6})\b", line.split("|")[4]))
rows = []
for b in re.split(r"^## q", inp, flags=re.M)[1:]:
    q = b.split(" ")[0]
    for bid, role, sh in re.findall(r"^- (\d+) \|.*?\| (main|secondary) \| share ([\d.]+)", b, flags=re.M):
        mains = [str(t["n"]) for t in bill_lab[int(bid)][0]]
        rows.append(dict(q=q, bill=bid, role=role, share=float(sh), misfit=bid in mis.get(q, ()),
                         R1=not keep("R1", qd[q], "sec" if role == "secondary" else "main", mains),
                         R2=not keep("R2", qd[q], "sec" if role == "secondary" else "main", mains)))
au = pd.DataFrame(rows)
p("1. Against the Opus audit: driving bills of 48 statements")
p(f"   misfit bills {int(au.misfit.sum())} (share sum {au[au.misfit].share.sum():.2f}), of them main labels {int((au.misfit & (au.role=='main')).sum())}; fit bills {int((~au.misfit).sum())}")
for R in ("R1", "R2"):
    mc, fc = au[au.misfit & au[R]], au[~au.misfit & au[R]]
    p(f"   {R}: drops {len(mc)} of {int(au.misfit.sum())} misfit bills (share {mc.share.sum():.2f} of {au[au.misfit].share.sum():.2f}); "
      f"drops {len(fc)} of {int((~au.misfit).sum())} fit bills (share {fc.share.sum():.2f}): " + ", ".join(f"q{r.q}:{r.bill}" for r in fc.itertuples()))
    left = au[au.misfit & ~au[R]]
    p(f"      misfits left: {len(left)} (share {left.share.sum():.2f}); statements still with misfit share >= 0.15: "
      + ", ".join(f"q{q}({s:.2f})" for q, s in left.groupby("q").share.sum().items() if s >= 0.15))

# ---- 2. quiz impact ----
CLOSE = 0.2
side = lambda x: "none" if abs(x) < CLOSE else ("+" if x > 0 else "−")
LPs = {}
for R in ("none", "R1", "R2"): LPs[R] = list_pos(R)
def vals(R, d): return {l: LPs[R][0].get((l, d)) for l in OK if (l, d) in LPs[R][0].index}
def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
def core(R, n=8):
    rows = []
    for s in st:
        v = vals(R, s["d"])
        if len(v) < 2: continue
        x = list(v.values()); rows.append((-np.std(x) * len(v) / len(OK), int(s["q"]), s, abs(corr(x, [GOV[l] for l in v])) >= 0.8))
    out, dirs, ng = [], set(), 0
    for _, _, s, og in sorted(rows, key=lambda t: (t[0], t[1])):
        if len(out) >= n: break
        if s["d"] in dirs or (og and ng >= n // 2): continue
        vq = vals(R, s["d"])
        if any(abs(corr(*zip(*[(vq[l], vals(R, o["d"])[l]) for l in vq if l in vals(R, o["d"])]))) >= 0.8 for o in out): continue
        out.append(s); dirs.add(s["d"]); ng += og
    return [s["q"] for s in out]
p("\n2. Quiz impact (83 statements × 12 lists)")
p(f"   {'rule':5} {'labels dropped':>14} {'side changed':>12} {'+/− swap':>9} {'stmts changed':>13} {'SD<0.25':>8} {'median SD':>9}  core")
for R in ("none", "R1", "R2"):
    ch = sw = 0; stc = set(); sds = []
    for s in st:
        b, x = vals("none", s["d"]), vals(R, s["d"])
        if len(x) >= 2: sds.append(np.std(list(x.values())))
        for l in OK:
            sb, sx = side(b.get(l, 0)), side(x.get(l, 0))
            if sb != sx: ch += 1; stc.add(s["q"]); sw += {sb, sx} == {"+", "−"}
    p(f"   {R:5} {LPs[R][1]:14} {ch:12} {sw:9} {len(stc):13} {sum(v < 0.25 for v in sds):8} {np.median(sds):9.2f}  " + ",".join(core(R)))
p("   SD per statement that falls below 0.25: " + "; ".join(
    f"{R}: " + ", ".join(f"q{s['q']} {np.std(list(vals('none', s['d']).values())):.2f}→{np.std(list(vals(R, s['d']).values())):.2f}"
                         for s in st if len(vals(R, s['d'])) >= 2 and np.std(list(vals(R, s['d']).values())) < 0.25) for R in ("R1", "R2")))

# ---- 3. spot checks ----
K = {r["q"]: r["agree_key"] for r in st}
m = pd.read_csv(f"{OUT}/spot_key.csv", dtype={"q": str}).merge(pd.read_csv(f"{OUT}/spot_result.csv"), on="id")
truth = ["none" if r.side == "unclear" else ("+" if (r.side == "agree") == (K[r.q] == "+") else "−") for r in m.itertuples()]
p("\n3. Spot checks (24 blind pairs; Opus side): matches")
for R in ("none", "R1", "R2"):
    got = [side(LPs[R][0].get((r.list, r.d), 0)) for r in m.itertuples()]
    ok_ = [g == t for g, t in zip(got, truth)]
    hm = [o for o, c in zip(ok_, m.confidence) if c != "low"]
    p(f"   {R:5} all {sum(ok_)}/24, high+medium {sum(hm)}/{len(hm)}")

# ---- 4. q5 ----
p("\n4. q5 (164) list positions")
for R in ("none", "R1", "R2"):
    v = vals(R, "164"); p(f"   {R:5} SD {np.std(list(v.values())):.2f} | " + " ".join(f"{l}{v[l]:+.2f}" for l in OK if l in v))
open(f"{OUT}/drop_rule.txt", "w").write("\n".join(lines) + "\n")
