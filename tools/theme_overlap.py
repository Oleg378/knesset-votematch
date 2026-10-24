"""Global audit of links between themes (customer 2026-10-20): the 74 quiz themes and all themes that pass the selection criteria
without a statement. Data only, no agents.

Bills are counted by name without the year (a re-submission is one bill), as in the volume criterion. «Effective» bills are those
initiated by former MKs of the 2026 lists (the bills that move list positions through authorship).
Per pair of themes: shared bills, overlap = shared / size of the smaller theme, Jaccard, and the sign agreement on the shared bills
(same = the bill moves both themes the same way, opposite = a mirror). Per bill: in how many of these themes it counts.
-> local/research/theme_overlap/{themes.csv, pairs.csv, bills_multi.csv, SUMMARY.md}
"""
import csv, json, os, re, sys, collections, itertools
import duckdb, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/local/research/theme_overlap"; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB, quiz_select as QS
C = QS.criteria(); lab = LB.load(); bl = lab["bill_lab"]
st = {r["d"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements.csv")) if r["status"] == "ok"}
pl = json.load(open(f"{ROOT}/jef/directions/split/plan.json"))
rem = (set(pl["parents"]) - set(pl["keep"])) | {d for p in LB.later_plans() for d in p["parents"]}
TECH = {"107", "128", "236", "289", "339", "343", "346"}
def group(d):
    if d in st: return "quiz"
    if d in rem: return "remainder"
    if d in TECH: return "technical"
    return "passing, no statement"
themes = sorted(set(st) | {d for d, x in C.items() if x["base"]})
con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
bn = {b: base(n) for b, n in con.execute("select bill_id, name from bills").fetchall()}
cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); mks = set(cand[cand.match.isin(["exact", "manual"])].mk_id.astype(int))
eff_b = {b for b, m in con.execute("select bill_id, mk_id from bill_initiators where is_initiator").fetchall() if m in mks}
sign = collections.defaultdict(dict); eff = collections.defaultdict(set)   # theme -> {name: sign}
for b, lb in bl.items():
    for d, s in LB.signed_topics(lb).items():
        if d in themes:
            sign[d].setdefault(bn.get(b), s)
            if b in eff_b: eff[d].add(bn.get(b))
name = {d: (st[d]["title_en"] if d in st else C[d]["name"]) for d in themes}
T = [dict(d=d, q=("q" + st[d]["q"]) if d in st else "", group=group(d), name=name[d], bills=len(sign[d]), effective=len(eff[d])) for d in themes]
pd.DataFrame(T).to_csv(f"{OUT}/themes.csv", index=False)
P = []
for a, b in itertools.combinations(themes, 2):
    sh = set(sign[a]) & set(sign[b])
    if not sh: continue
    m = min(len(sign[a]), len(sign[b])); same = sum(sign[a][x] == sign[b][x] for x in sh)
    she = eff[a] & eff[b]; me = min(len(eff[a]), len(eff[b])) or 1
    P.append(dict(a=a, qa=("q" + st[a]["q"]) if a in st else "", ga=group(a), name_a=name[a], b=b, qb=("q" + st[b]["q"]) if b in st else "",
                  gb=group(b), name_b=name[b], shared=len(sh), overlap=round(len(sh) / m, 3), jaccard=round(len(sh) / len(set(sign[a]) | set(sign[b])), 3),
                  same_sign=same, opposite_sign=len(sh) - same, shared_eff=len(she), overlap_eff=round(len(she) / me, 3)))
P = pd.DataFrame(P).sort_values(["overlap", "shared"], ascending=False); P.to_csv(f"{OUT}/pairs.csv", index=False)
# per bill: number of themes among the audited ones (by group)
per = collections.defaultdict(set)
for d in themes:
    for x in sign[d]: per[x].add(d)
B = [dict(name=x, n_all=len(ds), n_quiz=sum(d in st for d in ds), themes=" ".join(sorted(ds))) for x, ds in per.items()]
pd.DataFrame(B).sort_values("n_all", ascending=False).to_csv(f"{OUT}/bills_multi.csv", index=False)
print(len(themes), "themes", collections.Counter(t["group"] for t in T), "|", len(P), "linked pairs")
