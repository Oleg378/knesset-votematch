"""Modeling (2026-10-17, customer request; nothing in the product changes): variants of the position formula against the
problems found by check_vote_sign.py.

  base  as in production (pipeline/positions.py): P_mk = (A + 0.25 V) / (1[A] + 0.25 [V]); list = mean of ex-MKs;
        e = sum_nA + 0.25 sum_nV
  v1    votes count only for the MAIN topics of a bill (secondary topics still count for authorship)
  v2    a MK's vote position shrunk by its number of votes: V * nV / (nV + 2)
  v3    e does not count authorship in a Knesset × direction where all bills point one way (A = 0 for everyone there)
  v4a   P_mk = A + 0.25 V, missing component = 0 (the model the weights were fitted on: local/research/positions_test/test_weights.py)
  v4b   list = mean of ex-MKs weighted by their evidence nA + 0.25 nV (the agent's first proposal for problem 4)
and combinations. For each variant: how many list × statement sides are fragile (decided by votes / by secondary-topic
votes / by one vote), how many sides flip vs base, how the rankings of the golden answer sets change, how many quiz
directions would fail the spread criterion (SD >= 0.3, which was set on the base scale).

Usage: python3 local/research/scripts/model_vote_variants.py  -> local/research/vote_variants/{summary.txt, pairs_<variant>.csv, pos_<variant>/}
"""
import collections, json, os, shutil, statistics, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/vote_variants")
os.makedirs(f"{OUT}/pos_run", exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
assert "OUT = f'{ROOT}/jef/positions'" in src
src = src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {OUT + '/pos_run'!r}")
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "model_vote_variants"}
exec(compile(src, "positions.py", "exec"), ns)
va, pv, cm, share = ns["va"], ns["pv"], ns["cm"], ns["share"]
A0, bi, ab = ns["A"], ns["bi"], pd.DataFrame(ns["arows"], columns=["bill_id", "d", "s"])
signed_topics, vote_label = ns["signed_topics"], ns["vote_label"]
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import quiz_match as qm

data = json.load(open(f"{ROOT}/export/quiz_data.v1.json"))
quiz_d = list(dict.fromkeys(s["d"] for s in data["statements"]))
shown = {L["id"] for L in data["lists"] if L["status"] != "not_evaluated"}
golden = json.load(open(f"{ROOT}/export/golden.v1.json"))["cases"]
EPS = 1e-9
sg = lambda x: 0 if abs(x) < EPS else (1 if x > 0 else -1)

# ---- vote topics: all / main only; role of each (vote, direction)
topics_all, topics_main, role = {}, {}, {}
for r in va.itertuples():
    lab = vote_label(r)
    if lab is None: topics_all[r.vote_id] = topics_main[r.vote_id] = {}; continue
    t, m = signed_topics(lab), signed_topics([lab[0]])
    topics_all[r.vote_id], topics_main[r.vote_id] = t, m
    for d in t: role[(r.vote_id, d)] = "main" if d in m else "secondary"

def votes(main_only):
    """Same as positions.py «V», with the chosen topics. Returns V per MK × Knesset × direction and the vote rows."""
    vt = topics_main if main_only else topics_all
    rows = pd.DataFrame([(r.mk_id, r.knesset, d, s * r.v, r.vote_id) for r in pv.itertuples() for d, s in vt[r.vote_id].items()],
                        columns=["mk_id", "knesset", "d", "c", "vote_id"])
    V = rows.groupby(["mk_id", "knesset", "d"]).c.agg(["mean", "size"]).reset_index().rename(columns={"mean": "pos", "size": "nV"})
    V = V.join(share, on=["mk_id", "knesset"]).dropna(subset=["gov_share"])
    grp = V.groupby(["knesset", "d"])
    mx, my = grp.gov_share.transform("mean"), grp.pos.transform("mean")
    cov = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform("mean")
    var = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform("mean")
    beta = (cov / var.where(var > 1e-9)).fillna(0)
    V["V"] = V.pos - my - beta * (V.gov_share - mx)
    rows = rows[rows.d.isin(quiz_d)].merge(V[["mk_id", "knesset", "d"]], on=["mk_id", "knesset", "d"])
    return V, rows

# ---- authorship informative? (Knesset × direction with bills of both signs)
signs = bi.merge(ab, on="bill_id").groupby(["knesset", "d"]).s.nunique()
A0 = A0.join((signs > 1).rename("inf"), on=["knesset", "d"])
A0["nA_inf"] = A0.nA * A0.inf

def pool(df, val, n):
    g = df.assign(w=df[val] * df[n]).groupby(["mk_id", "d"])
    return pd.DataFrame({val: g.w.sum() / g[n].sum(), n: g[n].sum()})

VOTES = {False: votes(False), True: votes(True)}

def run(name, main_only=False, shrink_v=0.0, inf_e=False, combine="avg", listw="equal"):
    V, vrows = VOTES[main_only]
    T = pool(A0, "A", "nA").join(A0.groupby(["mk_id", "d"]).nA_inf.sum()).join(pool(V, "V", "nV"), how="outer").reset_index()
    T = T[T.d.isin(quiz_d)].copy()
    T[["nA", "nV", "nA_inf"]] = T[["nA", "nV", "nA_inf"]].fillna(0)
    s = T.nV / (T.nV + shrink_v) if shrink_v else 1.0
    if combine == "avg":
        den = 1.0 * T.A.notna() + 0.25 * T.V.notna()
        T["a_w"], T["v_w"] = 1 / den, 0.25 / den * s
    else:
        T["a_w"], T["v_w"] = 1.0, 0.25 * s
    T["P"] = T.a_w * T.A.fillna(0) + T.v_w * T.V.fillna(0)
    M = cm[["letters", "mk_id"]].merge(T, on="mk_id")
    M = M[M.letters.isin(shown)].copy()
    M["omega"] = 1.0 if listw == "equal" else (M.nA + 0.25 * M.nV)
    M["omega"] = M.omega / M.groupby(["letters", "d"]).omega.transform("sum")
    M["A_L"] = M.omega * M.a_w * M.A.fillna(0)
    M["P_L"] = M.omega * M.P
    LP = M.groupby(["letters", "d"]).agg(P=("P_L", "sum"), A=("A_L", "sum"), n_mk=("mk_id", "size"), nA=("nA", "sum"),
                                         nA_inf=("nA_inf", "sum"), nV=("nV", "sum")).reset_index()
    LP["e"] = (LP.nA_inf if inf_e else LP.nA) + 0.25 * LP.nV
    # vote contributions to the list position
    nvt = vrows.groupby(["mk_id", "d"]).size().rename("nVt")
    vr = vrows.join(nvt, on=["mk_id", "d"]).merge(M[["letters", "mk_id", "d", "omega", "v_w"]], on=["mk_id", "d"])
    vr["contrib"] = vr.omega * vr.v_w * vr.c / vr.nVt
    VL = vr.groupby(["letters", "d", "vote_id"]).contrib.sum().reset_index()
    VL["sec"] = [role.get((v, d)) == "secondary" for v, d in zip(VL.vote_id, VL.d)]
    g = {k: x for k, x in VL.groupby(["letters", "d"])}
    fl = []
    for r in LP.itertuples():
        s_ = sg(r.P); x = g.get((r.letters, r.d))
        if x is None: fl.append((sg(r.A) != s_, False, False)); continue
        sec = x[x.sec].contrib.sum()
        tw = x[np.sign(x.contrib) == s_].contrib
        top = tw.loc[tw.abs().idxmax()] if len(tw) else 0.0
        fl.append((sg(r.A) != s_, sg(r.P - sec) != s_ if sec else False, sg(r.P - top) != s_ if len(tw) else False))
    LP[["by_votes", "on_secondary", "on_one_vote"]] = pd.DataFrame(fl, index=LP.index)
    # files for quiz_match (positions + coverage as in production)
    d_ = f"{OUT}/pos_{name}"; os.makedirs(d_, exist_ok=True)
    LP.assign(sum_nA=LP.e - 0.25 * LP.nV, sum_nV=LP.nV, direction="")[["letters", "d", "direction", "P", "n_mk", "sum_nA", "sum_nV"]] \
        .to_csv(f"{d_}/list_topic_positions.csv", index=False)
    for f in ("list_coverage.csv", "government_layer_list.csv"): shutil.copy(f"{ROOT}/jef/positions/{f}", d_)
    LP.round(4).to_csv(f"{OUT}/pairs_{name}.csv", index=False)
    return LP

def rankings(name):
    qm.POS = f"{OUT}/pos_{name}"
    out = []
    for c in golden:
        rows = qm.match(c["answers"], mult=c["mult"])
        ranked = [(r["letters"], r["closeness"]) for r in rows if r["closeness"] is not None and r["closeness"] == r["closeness"]
                  and r["coverage"] >= qm.MIN_COVERAGE]
        out.append(ranked)
    return out

def kendall(a, b):
    common = [x for x in a if x in b]
    pa, pb = {x: i for i, x in enumerate(a)}, {x: i for i, x in enumerate(b)}
    n = c = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            x, y = common[i], common[j]; n += 1
            c += 1 if (pa[x] - pa[y]) * (pb[x] - pb[y]) > 0 else -1
    return c / n if n else float("nan")

def select(LP):
    cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv")
    ok = set(cov[cov.status == "ok"].letters)
    x = LP[LP.letters.isin(ok) & (LP.n_mk >= 3)]
    g = x.groupby("d").agg(lists=("P", "size"), sd=("P", lambda p: statistics.pstdev(p) if len(p) > 1 else 0.0), nA=("nA", "sum"))
    g = g.reindex(quiz_d)
    return g, g[(g.lists >= 8) & (g.sd >= 0.3) & (g.nA >= 30)].index

VARIANTS = [("base", {}), ("v1", dict(main_only=True)), ("v2", dict(shrink_v=2.0)), ("v3", dict(inf_e=True)),
            ("v1+v3", dict(main_only=True, inf_e=True)), ("v1+v2+v3", dict(main_only=True, shrink_v=2.0, inf_e=True)),
            ("v4a", dict(combine="sum")), ("v4b", dict(listw="evidence")), ("v1+v3+v4a", dict(main_only=True, inf_e=True, combine="sum"))]

L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1])
res, R = {}, {}
for name, kw in VARIANTS:
    res[name] = run(name, **kw); R[name] = rankings(name)

base = res["base"]
exp = {(Li["id"], d): x["P"] for Li in data["lists"] for d, x in Li["positions"].items()}
p(f"sanity: base vs exported P, max diff {max(abs(r.P - exp[(r.letters, r.d)]) for r in base.itertuples()):.1e}; "
  f"base rankings == golden: {all([x for x, _ in R['base'][i]] == [r['id'] for r in c['ranking'] if r['ranked']] for i, c in enumerate(golden))}")
cases = [i for i, c in enumerate(golden) if len(R["base"][i]) >= 3]
pilot = [i for i, c in enumerate(golden) if c["name"] == "pilot"][0]
lname = {Li["id"]: Li["name_en"].split(",")[0].split("(")[0].strip()[:18] for Li in data["lists"]}
p(f"\nanswer sets compared: {len(cases)} golden cases with >= 3 ranked lists (pilot, pilot + trade-offs, adaptive, random)")
p(f"\n{'variant':11} {'pairs':>5} {'by votes':>8} {'2nd-topic':>9} {'one vote':>8} {'any':>5} {'side flip':>9} "
  f"{'top1 same':>9} {'top3 ovl':>8} {'tau':>5} {'|dC|':>5} {'fail SD':>7}")
gb, passed_b = select(base)
for name, _ in VARIANTS:
    x = res[name]
    m = x.merge(base[["letters", "d", "P"]], on=["letters", "d"], suffixes=("", "_b"))
    flip = sum(sg(a) != sg(b) for a, b in zip(m.P, m.P_b))
    any3 = (x.by_votes | x.on_secondary | x.on_one_vote).sum()
    t1 = np.mean([R[name][i][0][0] == R["base"][i][0][0] for i in cases])
    t3 = np.mean([len({a for a, _ in R[name][i][:3]} & {a for a, _ in R["base"][i][:3]}) / 3 for i in cases])
    tau = np.mean([kendall([a for a, _ in R[name][i]], [a for a, _ in R["base"][i]]) for i in cases])
    dc = np.mean([abs(dict(R[name][i])[a] - c) for i in cases for a, c in R["base"][i] if a in dict(R[name][i])])
    g, passed = select(x)
    p(f"{name:11} {len(x):5} {x.by_votes.sum():8} {x.on_secondary.sum():9} {x.on_one_vote.sum():8} {any3:5} {flip:9} "
      f"{t1:9.0%} {t3:8.0%} {tau:5.2f} {dc:5.2f} {len(quiz_d) - len(passed):7}")
p("\nfail SD = quiz directions that would not pass «>= 8 lists, SD >= 0.3, nA >= 30» (base: "
  f"{len(quiz_d) - len(passed_b)}); the SD threshold was set on the base scale, so it is not comparable for v2/v4a.")
p("\npilot top-5 per variant:")
for name, _ in VARIANTS:
    p(f"  {name:11} " + " · ".join(f"{lname[a]} {c:+.2f}" for a, c in R[name][pilot][:5]))
p("\nq11 (direction 276), list positions P (shrunk p = P·e/(e+2)):")
for name in ("base", "v1", "v3", "v1+v3", "v4a", "v1+v3+v4a"):
    x = res[name][res[name].d == "276"].set_index("letters")
    p(f"  {name:10} " + " ".join(f"{l}:{x.P[l]:+.2f}({x.P[l] * x.e[l] / (x.e[l] + 2):+.2f})" for l in ("מחל", "שס", "רק", "אמת", "ודם", "עם") if l in x.index))
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
