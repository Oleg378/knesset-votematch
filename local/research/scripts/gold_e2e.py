"""End-to-end gold set (customer, 2026-10-18): is the quiz's side of a list on a statement right?
Sample: 40 (list, statement) pairs over the 12 ok lists, stratified by the quiz's strength |p|: >= 0.5, 0.2–0.5, < 0.2
(at most 2 pairs per statement). For each pair the judge (Opus, blind: no positions, no label signs or roles) gets the statement
and the raw record of the list's former MKs on its topic: bills they sponsored that carry the topic (name, Knesset, sponsors from the
list, notes excerpt) and their votes on private bills that carry it (for / against counts). The judge says agree / disagree /
unclear. The quiz's side: p × key >= CLOSE agree, <= −CLOSE disagree, else unclear (CLOSE 0.2, K = 0).
Limitation: the material is the bills our labels attach to the topic, so a bill the labels missed is not tested (recall).
Usage: python3 local/research/scripts/gold_e2e.py build | score   -> local/research/gold_e2e/
"""
import collections, csv, json, os, random, sys
import numpy as np, pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/gold_e2e"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB, quiz_match as qm
CLOSE = 0.2
def build():
    st, pos, cov = qm.load(); ok = [l for l, c in cov.items() if c["status"] == "ok"]
    S = {r["q"]: r for r in st}
    vec = {l: qm.list_vec(st, pos, l, qm.K) for l in ok}
    key = {r["q"]: 1 if r["agree_key"] in ("+",) else -1 for r in st}
    cands = []
    for l in ok:
        for q, p in vec[l].items():
            a = abs(p); band = "strong" if a >= 0.5 else "medium" if a >= CLOSE else "weak"
            cands.append((l, q, p, band))
    rnd = random.Random(20261018); rnd.shuffle(cands)
    want = {"strong": 16, "medium": 14, "weak": 10}; per_list = collections.Counter(); per_q = collections.Counter(); pick = []
    quota_list = {l: 0 for l in ok}
    for band, n in want.items():
        got = 0
        for l, q, p, b in sorted(cands, key=lambda c: (quota_list[c[0]], rnd.random())):
            if b != band or got >= n or per_q[q] >= 2 or any(x[0] == l and x[1] == q for x in pick): continue
            if quota_list[l] >= 4: continue
            pick.append((l, q, p, b)); per_q[q] += 1; quota_list[l] += 1; got += 1
    lab = LB.load()["bill_lab"]
    con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
    bname = dict(con.execute("select bill_id, name from bills").fetchall()); bkn = dict(con.execute("select bill_id, knesset from bills").fetchall())
    ini = con.execute("select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
    votes = con.execute("""select a.bill_id, r.mk_id, r.result from vote_roster r join vote_attrs a using(vote_id) join bills b using(bill_id)
        where a.kind='bill' and a.stage in ('preliminary','first','second','third') and b.bill_type='פרטית' and r.result in ('for','against')""").df()
    cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cand = cand[cand.match.isin(["exact", "manual"])].copy(); cand["mk_id"] = cand.mk_id.astype(int)
    names = pd.read_csv(f"{ROOT}/manual/mk_names_en.csv") if os.path.exists(f"{ROOT}/manual/mk_names_en.csv") else None
    cec = pd.read_csv(f"{ROOT}/manual/cec_lists_26.csv"); LN = dict(zip(cec.letters, cec.name_en))
    dset = {}
    for b, (m, s) in lab.items():
        for t in m + s:
            if t.get("sign") in ("+", "−", "-"): dset.setdefault(str(t["n"]), set()).add(b)
    def notes(b, n=220):
        f = f"{ROOT}/data/bill_texts/{b}.json"
        return " ".join((json.load(open(f)).get("notes") or "").replace("דברי הסבר", "", 1).split())[:n] if os.path.exists(f) else ""
    L = ["# Gold set: what is each list's side on the statement?", "",
         "For each pair: the statement, the list, and the record of the list's candidates who were MKs in Knessets 24–25 on the topic: bills they sponsored and their votes on private bills. Decide from substance whether the list, by this record, agrees or disagrees with the statement, or the record does not show a side (unclear). Bills not about the statement's question should be ignored.", ""]
    key_rows = []
    for i, (l, q, p, b) in enumerate(pick, 1):
        s = S[q]; d = s["d"]; mks = set(cand[cand.letters == l].mk_id)
        bills = dset.get(d, set())
        sp = ini[ini.bill_id.isin(bills) & ini.mk_id.isin(mks)].groupby("bill_id").mk_id.nunique().sort_values(ascending=False)
        vv = votes[votes.bill_id.isin(bills) & votes.mk_id.isin(mks)].groupby(["bill_id", "result"]).size().unstack(fill_value=0)
        if len(vv): vv = vv.assign(n=vv.sum(1)).sort_values("n", ascending=False)
        L += [f"## G{i}: list {LN.get(l, l)} — {s['title_en']}", f"Statement: {s['statement_en']}",
              f"The list has {len(mks)} former MKs among its candidates.", f"Bills sponsored by them on this topic ({len(sp)}; up to 25 shown):"]
        for bid, n in sp.head(25).items():
            L.append(f"- {bid} | K{bkn.get(bid)} | {bname.get(bid)} | sponsored by {n} of the list's former MKs")
            t = notes(bid); L.append(f"  notes: {t}") if t else None
        if not len(sp): L.append("- none")
        L.append(f"Their votes on private bills on this topic ({len(vv)} bills; up to 15 with the most votes):")
        for bid, r in vv.head(15).iterrows():
            L.append(f"- {bid} | K{bkn.get(bid)} | {bname.get(bid)} | for {int(r.get('for', 0))}, against {int(r.get('against', 0))}")
        if not len(vv): L.append("- none")
        L.append("")
        qs = "agree" if p * key[q] >= CLOSE else "disagree" if p * key[q] <= -CLOSE else "unclear"
        key_rows.append(dict(id=f"G{i}", list=l, q=q, p=round(p, 3), band=b, quiz_side=qs, n_bills=len(sp), n_voted=len(vv)))
    open(f"{OUT}/items.md", "w").write("\n".join(L) + "\n")
    pd.DataFrame(key_rows).to_csv(f"{OUT}/key_DO_NOT_SHOW.csv", index=False)
    print(len(pick), collections.Counter(x[3] for x in pick), "size", len("\n".join(L)))
def score():
    k = pd.read_csv(f"{OUT}/key_DO_NOT_SHOW.csv", dtype=str); r = pd.read_csv(f"{OUT}/result.csv", dtype=str)
    m = k.merge(r, on="id"); m["match"] = m.quiz_side == m.side
    print(pd.crosstab(m.quiz_side, m.side, margins=True)); print("\nagreement by band:"); print(m.groupby("band").match.agg(["mean", "size"]))
    print("\nexcluding judge low confidence:", m[m.confidence != "low"].match.mean().round(2), len(m[m.confidence != "low"]))
    print("\nopposite sides (agree <-> disagree):"); print(m[(m.quiz_side != m.side) & (m.quiz_side != "unclear") & (m.side != "unclear")][["id", "list", "q", "p", "quiz_side", "side", "confidence", "reason"]].to_string())
    m.to_csv(f"{OUT}/scored.csv", index=False)
{"build": build, "score": score}[sys.argv[1]]()
