"""Check (2026-10-17, customer request after the Likud × q11 case): for every list × quiz statement, which part of the list's
position decides its side — sponsored bills (A) or private-bill votes (V) — and whether the side rests on votes for bills
where the quiz direction is only a secondary topic, or on a single vote.

Read-only: runs pipeline/positions.py with its output redirected to local/research/vote_sign_check/pos/ and decomposes
  P_list = mean over ex-MKs of P_mk,  P_mk = (A + 0.25 V) / (1[A] + 0.25 [V])           (SU 27.2-27.3)
  V_mk   = sum over the MK's votes of s*v / nV  -  centering (mean of the Knesset × direction + government-share term)
into A part + votes part + centering part. Nothing in the formula changes.

Usage: python3 local/research/scripts/check_vote_sign.py   -> local/research/vote_sign_check/{pairs.csv, votes.csv, summary.txt}
"""
import collections, json, os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/vote_sign_check")
os.makedirs(f"{OUT}/pos", exist_ok=True)
src = open(f"{ROOT}/pipeline/positions.py").read()
assert "OUT = f'{ROOT}/jef/positions'" in src
src = src.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {OUT + '/pos'!r}")
ns = {"__file__": f"{ROOT}/pipeline/positions.py", "__name__": "check_vote_sign"}
exec(compile(src, "positions.py", "exec"), ns)
T, V, pv, va, cm = ns["T"], ns["V"], ns["pv"], ns["va"], ns["cm"]
signed_topics, vote_label = ns["signed_topics"], ns["vote_label"]

data = json.load(open(f"{ROOT}/export/quiz_data.v1.json"))
st = data["statements"]
quiz_d = list(dict.fromkeys(s["d"] for s in st))
q_of = collections.defaultdict(list)
for s in st: q_of[s["d"]].append(s["q"])
lname = {L["id"]: L["name_en"] for L in data["lists"]}
shown = {L["id"] for L in data["lists"] if L["status"] != "not_evaluated"}

# role of the direction in each vote's label: main / secondary
vinfo = va.set_index("vote_id")
role = {}
for r in va.itertuples():
    lab = vote_label(r)
    if lab is None: continue
    main = signed_topics([lab[0]])
    for d in signed_topics(lab): role[(r.vote_id, d)] = "main" if d in main else "secondary"

# vote rows of MKs that have a V (same filter as positions.py: gov_share known)
rows = [(r.mk_id, r.knesset, d, s * r.v, r.vote_id) for r in pv.itertuples() for d, s in ns["vt"][r.vote_id].items() if d in quiz_d]
VR = pd.DataFrame(rows, columns=["mk_id", "knesset", "d", "c", "vote_id"])
VR = VR.merge(V[["mk_id", "knesset", "d"]], on=["mk_id", "knesset", "d"])
nVt = VR.groupby(["mk_id", "d"]).size().rename("nVt")
VR = VR.join(nVt, on=["mk_id", "d"])

Tq = T[T.d.isin(quiz_d)].set_index(["mk_id", "d"])
den = 1.0 * Tq.A.notna() + 0.25 * Tq.V.notna()
a_part = (Tq.A.fillna(0) / den).rename("a_part")
v_scale = (0.25 / den).rename("v_scale")
VR = VR.join(v_scale, on=["mk_id", "d"])
VR["contrib_mk"] = VR.v_scale * VR.c / VR.nVt               # this vote's share of P_mk
own = VR.groupby(["mk_id", "d"]).contrib_mk.sum()
v_part = (0.25 * Tq.V.fillna(0) / den)
cent = (v_part - own.reindex(v_part.index).fillna(0)).rename("cent")

mem = cm[["letters", "mk_id"]]
M = mem.merge(T[T.d.isin(quiz_d)][["mk_id", "d", "P", "nA", "nV"]], on="mk_id")
M = M.join(a_part, on=["mk_id", "d"]).join(cent, on=["mk_id", "d"])
M["votes"] = own.reindex(pd.MultiIndex.from_frame(M[["mk_id", "d"]])).fillna(0).values
n = M.groupby(["letters", "d"]).mk_id.transform("size")
for c in ("P", "a_part", "cent", "votes"): M[c + "_L"] = M[c] / n
LP = M.groupby(["letters", "d"]).agg(P=("P_L", "sum"), A=("a_part_L", "sum"), votes=("votes_L", "sum"), cent=("cent_L", "sum"),
                                     n_mk=("mk_id", "size"), nA=("nA", "sum"), nV=("nV", "sum")).reset_index()
LP = LP[LP.letters.isin(shown)]

# sanity: equal to the exported positions
exp = {(L["id"], d): x["P"] for L in data["lists"] for d, x in L["positions"].items()}
diff = max(abs(r.P - exp[(r.letters, r.d)]) for r in LP.itertuples())
assert diff < 1e-3, diff

# per list × direction × vote contributions to P_list
VR = VR.merge(mem, on="mk_id")
VR = VR.join(M.groupby(["letters", "d"]).size().rename("n_list"), on=["letters", "d"])
VR["contrib"] = VR.contrib_mk / VR.n_list
VL = VR.groupby(["letters", "d", "vote_id"]).agg(contrib=("contrib", "sum"), n_rows=("c", "size")).reset_index()
VL["role"] = [role.get((v, d), "?") for v, d in zip(VL.vote_id, VL.d)]
VL["bill_id"] = VL.vote_id.map(vinfo.bill_id)
VL["stage"] = VL.vote_id.map(vinfo.stage)
VL["date"] = VL.vote_id.map(vinfo.vote_date).dt.date
VL["bill_name"] = VL.vote_id.map(vinfo.bill_name)
VL = VL[VL.letters.isin(shown)]

EPS = 1e-9
sg = lambda x: 0 if abs(x) < EPS else (1 if x > 0 else -1)
out = []
for r in LP.itertuples():
    s = sg(r.P)
    v = VL[(VL.letters == r.letters) & (VL.d == r.d)]
    sec = v[v.role == "secondary"].contrib.sum()
    toward = v[np.sign(v.contrib) == s].sort_values("contrib", key=abs, ascending=False)
    top = toward.iloc[0] if len(toward) else None
    out.append(dict(
        letters=r.letters, list=lname[r.letters][:40], d=r.d, q="/".join(q_of[r.d]), n_mk=r.n_mk, nA=int(r.nA), nV=int(r.nV),
        P=r.P, A_part=r.A, votes_part=r.votes, cent_part=r.cent, votes_secondary=sec,
        side_by_votes=sg(r.A) != s,                                   # without votes the side would differ (or be 0)
        A_zero=abs(r.A) < EPS,                                        # sponsored bills say nothing (all one way)
        flips_without_secondary=sg(r.P - sec) != s,                   # side rests on votes where d is a secondary topic
        flips_without_top_vote=top is not None and sg(r.P - top.contrib) != s,
        top_vote=None if top is None else int(top.vote_id), top_vote_contrib=None if top is None else top.contrib,
        top_vote_role=None if top is None else top.role,
        top_vote_bill=None if top is None else str(top.bill_name)[:80]))
R = pd.DataFrame(out)
R.round(4).to_csv(f"{OUT}/pairs.csv", index=False)
VL.sort_values(["d", "letters", "contrib"]).round(5).to_csv(f"{OUT}/votes.csv", index=False)

# summary
L = []
def p(*a): L.append(" ".join(str(x) for x in a))
ok = R[R.n_mk >= 1]
p(f"list × quiz-direction pairs (lists shown in the quiz): {len(R)}; quiz directions {R.d.nunique()}; lists {R.letters.nunique()}")
p(f"sanity: max |P - exported P| = {diff:.2e}")
p(f"side decided by votes (without votes: other side or 0): {R.side_by_votes.sum()} ({R.side_by_votes.mean():.0%})")
p(f"  of them sponsored bills give exactly 0 (no own bills or all bills one way): {(R.side_by_votes & R.A_zero).sum()}")
p(f"side rests on votes where the direction is only a secondary topic: {R.flips_without_secondary.sum()} ({R.flips_without_secondary.mean():.0%})")
p(f"side rests on one single vote: {R.flips_without_top_vote.sum()} ({R.flips_without_top_vote.mean():.0%})")
p(f"  same, lists with n_mk >= 3: {R[R.n_mk >= 3].flips_without_top_vote.sum()} of {(R.n_mk >= 3).sum()}")
p("")
p("per statement: pairs | side by votes | rests on secondary-topic votes | rests on one vote")
for d in quiz_d:
    x = R[R.d == d]
    p(f"  q{'/'.join(q_of[d]):>6} d={d:>5}: {len(x):>2} | {x.side_by_votes.sum():>2} | {x.flips_without_secondary.sum():>2} | {x.flips_without_top_vote.sum():>2}")
p("")
p("votes that alone decide a side most often (vote, role, bill: n pairs):")
tv = R[R.flips_without_top_vote].groupby(["top_vote", "top_vote_role", "top_vote_bill", "d"]).size().sort_values(ascending=False)
for (v, ro, b, d), k in tv.head(25).items(): p(f"  {k:>2}  vote {v} d={d} {ro:9} {b}")
open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
