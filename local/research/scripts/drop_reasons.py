"""Why a statement drops after the relevance filter (B: votes + authorship, threshold 0.2), 2026-10-17. Two different problems:
  wording — most bills of the direction are not about the statement's issue (relevance < 0.2): the statement is narrower than
            the topic the data covers;
  data    — on the bills that are about the issue the lists do not differ more than chance, or there are too few of them.
Per statement: share of relevant (bill × direction) pairs, volume before/after (sum_nA over the counted lists), spread vs
chance before/after (local/research/sd_threshold/directions.csv).
Usage: python3 local/research/scripts/drop_reasons.py -> local/research/sd_threshold/drop_reasons.csv
"""
import csv, json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
rel = pd.DataFrame(map(json.loads, open(f"{ROOT}/jef/directions/relevance/relevance_q2.jsonl")))
R = pd.read_csv(f"{ROOT}/research/sd_threshold/directions.csv", dtype={"d": str})
st = [r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"]
g = rel.groupby("d").agg(pairs=("p", "size"), rel_share=("p", lambda v: (v >= 0.2).mean()))
a = R[R.variant == "new, no filter"].set_index("d"); b = R[R.variant == "B both 0.2"].set_index("d")
out = []
for r in st:
    d = r["d"]
    out.append(dict(q=r["q"], title=r["title_en"], d=d, pairs=g.pairs.get(d), rel_share=round(g.rel_share.get(d), 2),
        nA_before=a.nA[d], nA_after=b.nA[d], lists_after=b.n[d], sd_before=a.sd[d], chance_before=a.chance95[d], sd_after=b.sd[d],
        chance_after=b.chance95[d], pass_before=bool(a.above_chance[d]), pass_after=bool(b.above_chance[d])))
O = pd.DataFrame(out); O.to_csv(f"{ROOT}/research/sd_threshold/drop_reasons.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(O.sort_values(["pass_after", "rel_share"]).to_string(index=False))
