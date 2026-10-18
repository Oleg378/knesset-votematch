"""Weight of secondary topics on the CURRENT formula (A not centered, K = 0), customer request 2026-10-18.

Two definitions of «weight w of a secondary topic» in an MK's mean:
  mean  — weighted mean Σ w·s / Σ w  (as in the 2026-10-17 test). An MK whose only bills on a direction are secondary keeps ±1
          for any w > 0 (q5: the Joint Arab List is −1 at every w > 0).
  count — Σ w·s / n (n = all the MK's bills / votes on the direction). A secondary-only author gets ±w.
For w in 0, .25, .5, .75, 1 and both definitions:
  1. cross-Knesset prediction (24→25, 25→24; targets «equal» = all labels, «main» = main topics only), MK and list level;
  2. impact on the quiz (83 statements, 12 ok lists): list side changes (+ / − / no clear position, CLOSE 0.2), SD, statements
     below SD 0.25, the core (quiz_flow rule).
Writes local/research/secondary_weight_v2/{summary.txt, flips.csv, list_pos.csv}. Production (w = 1, mean) is checked against
jef/positions/list_topic_positions.csv.
"""
import csv, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/secondary_weight_v2"); os.makedirs(OUT, exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "sec_weight_impact", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
bill_lab, bi, pv, va, share, SGN = (ns[k] for k in ("bill_lab", "bi", "pv", "va", "share", "SGN"))

def roles(lab):
    out = {}
    for role, lst in (("main", lab[0]), ("sec", lab[1])):
        for t in lst:
            s = SGN.get(t.get("sign"))
            if s and str(t["n"]) not in out: out[str(t["n"])] = (s, role)
    return out
def vote_label(r):
    if r.vote_id in ns["pk_agent"]: return ns["pk_agent"][r.vote_id]
    if r.vote_id in ns["pk_whole"]: return ns["pk_whole"][r.vote_id]
    return bill_lab.get(r.bill_id)
ab = pd.DataFrame([(b, d, s, r) for b, lab in bill_lab.items() for d, (s, r) in roles(lab).items()], columns=["bill_id", "d", "s", "role"])
AU = bi.merge(ab, on="bill_id")
vt = {r.vote_id: (roles(vote_label(r)) if vote_label(r) is not None else {}) for r in va.itertuples()}
VO = pd.DataFrame([(r.mk_id, r.knesset, d, s * r.v, ro) for r in pv.itertuples() for d, (s, ro) in vt[r.vote_id].items()],
                  columns=["mk_id", "knesset", "d", "c", "role"])
KEY = ["mk_id", "knesset", "d"]

def position(w, mode):
    a = AU.assign(w=np.where(AU.role == "main", 1.0, w)); a = a[a.w > 0]
    A = a.assign(ws=a.w * a.s).groupby(KEY).agg(S=("ws", "sum"), N=("w", "sum"), nA=("s", "size")).reset_index()
    A["A"] = A.S / (A.N if mode == "mean" else A.nA)
    v = VO.assign(w=np.where(VO.role == "main", 1.0, w)); v = v[v.w > 0]
    V = v.assign(wc=v.w * v.c).groupby(KEY).agg(S=("wc", "sum"), N=("w", "sum"), nV=("c", "size")).reset_index()
    V["pos"] = V.S / (V.N if mode == "mean" else V.nV)
    V = V.join(share, on=["mk_id", "knesset"]).dropna(subset=["gov_share"])
    g = V.groupby(["knesset", "d"]); mx, my = g.gov_share.transform("mean"), g.pos.transform("mean")
    cov = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform("mean")
    var = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform("mean")
    V["V"] = V.pos - my - (cov / var.where(var > 1e-9)).fillna(0) * (V.gov_share - mx)
    return A, V

def pooled(A, V):   # as positions.py: pool Knessets weighted by counts; P = A + 0.25 V
    def pool(df, val, n):
        g = df.assign(x=df[val] * df[n]).groupby(["mk_id", "d"])
        return pd.DataFrame({val: g.x.sum() / g[n].sum(), n: g[n].sum()})
    T = pool(A, "A", "nA").join(pool(V, "V", "nV"), how="outer").reset_index()
    T["P"] = T.A.fillna(0) + 0.25 * T.V.fillna(0)
    return T

def per_knesset(A, V):
    T = A.set_index(KEY)[["A", "nA"]].join(V.set_index(KEY)[["V", "nV"]], how="outer")
    T[["nA", "nV"]] = T[["nA", "nV"]].fillna(0)
    T["P"] = T.A.fillna(0) + 0.25 * T.V.fillna(0)
    return T

cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy()
cand["mk_id"] = cand.mk_id.astype(int); cm = cand.drop_duplicates("mk_id"); mk2l = dict(zip(cm.mk_id, cm.letters))
cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); OK = list(cov[cov.status == "ok"].letters)
gl = pd.read_csv(f"{ROOT}/jef/positions/government_layer_list.csv"); gl = gl[gl.knesset == 25]; GOV = dict(zip(gl.letters, gl.share_with_gov))
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
quiz = {r["d"] for r in st}

WS = [0, 0.25, 0.5, 0.75, 1.0]; MODES = ["mean", "count"]
CONF = [(1.0, "mean")] + [(w, m) for m in MODES for w in WS if (w, m) != (1.0, "mean") and not (w in (0, 1.0) and m == "count")]
raw = {c: position(*c) for c in CONF}

def list_pos(T):
    L = T.assign(l=T.mk_id.map(mk2l)).dropna(subset=["l"])
    return L.groupby(["l", "d"]).P.mean()
LP = {c: list_pos(pooled(*raw[c])) for c in CONF}

lines = []
def p(*a): lines.append(" ".join(str(x) for x in a)); print(lines[-1], flush=True)
prod = pd.read_csv(f"{ROOT}/jef/positions/list_topic_positions.csv", dtype={"d": str}).set_index(["letters", "d"]).P
j = pd.concat([LP[(1.0, "mean")], prod], axis=1, keys=["sim", "prod"]).dropna()
p(f"check: w=1 mean vs production list positions: {len(j)} cells, max |diff| {np.abs(j.sim - j['prod']).max():.4f}\n")

def corr(a, b): return np.corrcoef(a, b)[0, 1] if len(a) > 2 and np.std(a) > 0 and np.std(b) > 0 else np.nan
both = set(pd.concat([per_knesset(*raw[(1.0, 'mean')]).reset_index()]).groupby("mk_id").knesset.nunique().loc[lambda s: s == 2].index)
PK = {c: per_knesset(*raw[c]) for c in CONF}
targets = {"equal": PK[(1.0, "mean")], "main": PK[(0, "mean")]}
p("1. Cross-Knesset prediction, quiz directions (mean of 24→25 and 25→24); r MK / r list")
p(f"   {'config':14}" + "".join(f"{'target '+t:>22}" for t in targets))
for c in CONF:
    row = []
    for tname, T in targets.items():
        rs, rl = [], []
        for tr, te in ((24, 25), (25, 24)):
            t = T.reset_index(); t = t[(t.knesset == te) & t.mk_id.isin(both) & ((t.nA + t.nV) >= 3) & t.d.isin(quiz)]
            x = PK[c].reset_index(); x = x[x.knesset == tr].set_index(["mk_id", "d"]).P
            pr = x.reindex(pd.MultiIndex.from_arrays([t.mk_id, t.d])).fillna(0).values
            rs.append(corr(pr, t.P.values))
            df = pd.DataFrame({"l": t.mk_id.map(mk2l).values, "d": t.d.values, "pred": pr, "t": t.P.values}).dropna(subset=["l"])
            g = df.groupby(["l", "d"]).agg(pred=("pred", "mean"), t=("t", "mean"), n=("t", "size")); g = g[g.n >= 2]
            rl.append(corr(g.pred.values, g.t.values))
        row.append(f"{np.mean(rs):.3f} / {np.mean(rl):.3f}")
    p(f"   w={c[0]:<4} {c[1]:6}" + "".join(f"{x:>22}" for x in row))

# ---- quiz impact ----
CLOSE = 0.2
def side(x): return "none" if abs(x) < CLOSE else ("+" if x > 0 else "−")
def vals(c, d): return {l: LP[c].get((l, d)) for l in OK if (l, d) in LP[c].index}
def r_(x, y): return corr(np.array(x), np.array(y))
def core(c, n=8, rmax=0.8, share=0.5, gov_r=0.8):
    rows = []
    for s in st:
        v = vals(c, s["d"])
        if len(v) < 2: continue
        x = list(v.values()); sep = np.std(x) * len(v) / len(OK)
        g = abs(r_(x, [GOV[l] for l in v]))
        rows.append((-sep, int(s["q"]), s, g >= gov_r))
    out, dirs, ng = [], set(), 0
    for _, _, s, og in sorted(rows, key=lambda t: (t[0], t[1])):
        if len(out) >= n: break
        if s["d"] in dirs or (og and ng >= int(n * share)): continue
        vq = vals(c, s["d"])
        if any(abs(r_(*zip(*[(vq[l], vals(c, o["d"])[l]) for l in vq if l in vals(c, o["d"])]))) >= rmax for o in out): continue
        out.append(s); dirs.add(s["d"]); ng += og
    return [s["q"] for s in out]

base = (1.0, "mean"); flips = []
p("\n2. Quiz impact vs production (w=1 mean): 83 statements × 12 ok lists = list-statement pairs")
p(f"   {'config':14} {'side changed':>12} {'+/− swap':>9} {'to/from none':>12} {'stmt with change':>16} {'SD<0.25':>8} {'median SD':>9}  core")
for c in CONF:
    ch = sw = nn = 0; stc = set(); sds = []
    for s in st:
        b, x = vals(base, s["d"]), vals(c, s["d"])
        if len(x) >= 2: sds.append(np.std(list(x.values())))
        for l in OK:
            sb, sx = side(b.get(l, 0)), side(x.get(l, 0))
            if sb != sx:
                ch += 1; stc.add(s["q"]); sw += ({sb, sx} == {"+", "−"}); nn += ({sb, sx} != {"+", "−"})
                if c != base: flips.append(dict(w=c[0], mode=c[1], q=s["q"], title=s["title_en"], d=s["d"], list=l, base=round(b.get(l, 0), 3), new=round(x.get(l, 0), 3), base_side=sb, new_side=sx))
    p(f"   w={c[0]:<4} {c[1]:6} {ch:12} {sw:9} {nn:12} {len(stc):16} {sum(1 for v in sds if v < 0.25):8} {np.median(sds):9.2f}  " + ",".join(core(c)))
pd.DataFrame(flips).to_csv(f"{OUT}/flips.csv", index=False)
pd.concat({f"{c[0]}_{c[1]}": LP[c] for c in CONF}, axis=1).to_csv(f"{OUT}/list_pos.csv")
# q5 detail
p("\n3. q5 (direction 164), list positions by config")
for c in CONF:
    v = vals(c, "164"); p(f"   w={c[0]:<4} {c[1]:6} SD {np.std(list(v.values())):.2f} | " + " ".join(f"{l}{v[l]:+.2f}" for l in OK if l in v))
open(f"{OUT}/summary.txt", "w").write("\n".join(lines) + "\n")
