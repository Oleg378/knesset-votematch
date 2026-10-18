"""Customer Р1 (2026-10-18, external audit К1): a signal «voted against the bills of the other camp».
O (per MK × direction): mean of topic sign × vote (for +1 / against −1) over the MK's votes on bills of the OTHER camp — government
bills are the coalition's; a private bill belongs to the camp of the majority of its initiators on the vote date (faction in government
by ministers, + Ra'am K24 by behaviour, Р2 X = 0.9). All four stages, outside the transition windows; not residualised (the point is
to keep «the opposition voted against the coalition's judicial bills»). Knessets pooled by count, list = mean over ex-MKs with O.
Checks: (1) stability of list O between K24 and K25 (camps swapped between the Knessets, so a stable O is ideology, not camp);
(2) P' = A + 0.25 V + w·O for w = 0 / 0.25 / 0.5 / 1: weak cells in the core, archetypes, gold set (40 pairs), random first places.
-> stdout, local/research/other_camp/summary.txt
"""
import collections, csv, json, os, random, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/other_camp"; os.makedirs(OUT, exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
cut = "# ======================= pool Knessets, topic position ======================="
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "other_camp", "print": lambda *a, **k: None}
exec(compile(src.split(cut)[0], "positions.py", "exec"), ns)
g = ns; ro, va, fm, INGOV, labels = g["ro"], g["va"], g["fm"], g["INGOV"], g["labels"]
# Р2: Ra'am K24 in the coalition by behaviour
raam = ro[(ro.faction_id == 973) & (ro.knesset == 24)].vote_date.unique()
INGOV |= {(973, pd.Timestamp(d)) for d in raam}
ro["gov_side"] = [(int(f), d) in INGOV if pd.notna(f) else False for f, d in zip(ro.faction_id, ro.vote_date)]
con = g["con"]
ini = con.execute("select bill_id, mk_id from bill_initiators where is_initiator").df()
inis = ini.groupby("bill_id").mk_id.apply(list).to_dict()
fmd = {m: q for m, q in fm.groupby("mk_id")}
def faction_at(m, d):
    q = fmd.get(m)
    if q is None: return None
    x = q[(q.df <= d) & (q.dt > d)]
    return int(x.sort_values("df").faction_id.iloc[-1]) if len(x) else None
camp = {}
for r in va.itertuples():
    if r.bill_type == "ממשלתית": camp[r.vote_id] = "gov"; continue
    if r.bill_type != "פרטית": continue
    fs = [faction_at(m, r.vote_date) for m in inis.get(r.bill_id, [])]
    s = [(f, r.vote_date) in INGOV for f in fs if f is not None]
    if s: camp[r.vote_id] = "gov" if np.mean(s) > 0.5 else "opp"
vt = {r.vote_id: labels.signed_topics(g["vote_label"](r)) if g["vote_label"](r) is not None else {} for r in va.itertuples()}
rv = ro.dropna(subset=["v"]); rv = rv[~rv.trans & rv.vote_id.isin(camp.keys())].copy()
rv["mkcamp"] = np.where(rv.gov_side, "gov", "opp"); rv["bcamp"] = rv.vote_id.map(camp)
rv = rv[rv.mkcamp != rv.bcamp]
rows = [(r.mk_id, r.knesset, d, s * r.v) for r in rv.itertuples() for d, s in vt[r.vote_id].items()]
O = pd.DataFrame(rows, columns=["mk_id", "knesset", "d", "c"]).groupby(["mk_id", "knesset", "d"]).c.agg(["mean", "size"]).reset_index()
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy(); cand["mk_id"] = cand.mk_id.astype(int)
mk2l = dict(zip(cand.drop_duplicates("mk_id").mk_id, cand.drop_duplicates("mk_id").letters)); O["l"] = O.mk_id.map(mk2l); O = O.dropna(subset=["l"])
sys.path.insert(0, f"{ROOT}/pipeline"); import quiz_match as qm, quiz_report as qr
st, pos, cov = qm.load(); ok = [l for l, c in cov.items() if c["status"] == "ok"]; ranked = [l for l, c in cov.items() if c["status"] in ("ok", "warning")]
D = {r["q"]: r["d"] for r in st}; Ds = set(D.values())
L = []
def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1], flush=True)
# (1) stability between Knessets, lists × quiz directions
lk = O[O.d.isin(Ds) & O.l.isin(ok)].groupby(["l", "knesset", "d"]).agg(O=("mean", "mean"), n=("size", "sum")).reset_index()
w = lk.pivot_table(index=["l", "d"], columns="knesset", values="O").dropna()
p(f"(1) list O, K24 vs K25 on quiz directions: r = {np.corrcoef(w[24], w[25])[0, 1]:.2f} over {len(w)} list×direction cells; same sign {np.mean(np.sign(w[24]) == np.sign(w[25])):.0%}")
nb = lk.groupby(["l", "d"]).n.sum(); p(f"    votes behind O per list×direction: median {nb.median():.0f}")
pooled = O.assign(x=O["mean"] * O["size"]).groupby(["mk_id", "d"]).agg(x=("x", "sum"), n=("size", "sum"))
pooled["O"] = pooled.x / pooled.n; pooled = pooled.reset_index(); pooled["l"] = pooled.mk_id.map(mk2l)
LO = pooled.groupby(["l", "d"]).O.mean()
p(f"    lists with O on quiz directions: {LO.reset_index().query('d in @Ds').l.nunique()}")
# (2) variants
key = pd.read_csv(f"{ROOT}/local/research/gold_e2e/key_DO_NOT_SHOW.csv", dtype=str).merge(pd.read_csv(f"{ROOT}/local/research/gold_e2e/result.csv", dtype=str), on="id")
K = {r["q"]: r["key_s"] for r in st}
anti = {"1": 2, "24": -2, "61": -2, "62": -2, "63": -2, "64": 2, "74": 2, "105": 2}; pro = {q: -a for q, a in anti.items()}
core = json.load(open(f"{ROOT}/export/quiz_core.v2.json"))["core"]
name = {l: cov[l]["list_name"][:22] for l in cov}
for wO in (0, 0.25, 0.5, 1.0):
    vec = {}
    for l in ranked:
        v = {}
        for r in st:
            x = pos.get(l, {}).get(r["d"]); o = LO.get((l, r["d"]))
            if x is None and o is None: continue
            v[r["q"]] = (x[0] if x else 0.0) + wO * (o if o == o and o is not None else 0.0)
        vec[l] = v
    weak = sum(1 for l in ok for q in core if abs(vec[l].get(q, 0)) < qr.CLOSE)
    def rank(ans):
        out = []
        for l in ranked:
            c, cv = qm.score(st, ans, vec[l])
            if c == c and cv >= qm.MIN_COVERAGE: out.append((c, l))
        return [l for c, l in sorted(out, reverse=True)]
    side = lambda x: "agree" if x >= qr.CLOSE else "disagree" if x <= -qr.CLOSE else "unclear"
    gs = [side(vec[r.list].get(r.q, 0) * K[r.q]) == r.side for r in key.itertuples()]
    stated = [(side(vec[r.list].get(r.q, 0) * K[r.q]), r.side) for r in key.itertuples()]
    st_ok = [a == b for a, b in stated if a != "unclear"]
    rnd = random.Random(1); first = collections.Counter()
    for _ in range(800):
        rr = rank({x["q"]: rnd.choice([-2, -1, 1, 2]) for x in st})
        if rr: first[rr[0]] += 1
    p(f"\n(2) w_O = {wO}: core cells with no clear position {weak}/96; gold set: agree with the judge {sum(gs)}/40, where the quiz states a side {sum(st_ok)}/{len(st_ok)}")
    p("    anti reform: " + " > ".join(name[l] for l in rank(anti)[:4]))
    p("    pro reform:  " + " > ".join(name[l] for l in rank(pro)[:4]))
    p("    random first places: " + ", ".join(f"{name[l]} {n / 800:.2f}" for l, n in first.most_common(4)))
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
