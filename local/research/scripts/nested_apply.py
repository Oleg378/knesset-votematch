"""Nested themes (SHARED_UNDERSTANDING «Вложенные темы — глобальный аудит», [У] 2026-10-20): merge the blind meaning checks of the pairs
(nested_result_A/B.csv, third check nested_result_C.csv for disagreements and «borderline») and build the removals.

Decision per pair: different -> strategy 1 (the shared bills leave the broad theme), same -> strategy 2 (they leave the narrow theme);
two agreeing checks decide, otherwise the majority of three; three-way split or a borderline majority -> no change (the pair is listed).
All removals are computed on the ORIGINAL bill sets (not sequentially) and are per bill id × theme.

Usage: python3 nested_apply.py merge   -> nested_merged.csv, nested_items_C.md (pairs for the third check)
       python3 nested_apply.py final   -> nested_decision.csv, jef/directions/labels/nested_removals.json (read by pipeline/labels.py)
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
O = f"{ROOT}/local/research/theme_overlap"
STEP = sys.argv[1]
def res(x):
    f = f"{O}/nested_result_{x}.csv"
    if not os.path.exists(f): return {}
    out = {}
    for l in open(f).read().splitlines()[1:]:
        p = l.split(",", 2)
        if len(p) >= 2: out[p[0].strip()] = p[1].strip().strip('"')
    return out
K = pd.read_csv(f"{O}/nested_key.csv", dtype={"small_d": str, "big_d": str})
A, B, C = res("A"), res("B"), res("C")
K["vA"], K["vB"] = K.pid.map(A), K.pid.map(B)
sys.path.insert(0, f"{ROOT}/pipeline")
if STEP == "merge":
    K.to_csv(f"{O}/nested_merged.csv", index=False)
    print("A:", collections.Counter(A.values()), "B:", collections.Counter(B.values()), "missing", int(K.vA.isna().sum() + K.vB.isna().sum()))
    print("agree:", int((K.vA == K.vB).sum()), collections.Counter(K[K.vA == K.vB].vA))
    t = K[(K.vA != K.vB) | (K.vA == "borderline")]
    sec = dict(re.findall(r"## (P\d+)\n(.*?)(?=\n## |\Z)", open(f"{O}/nested_items.md").read(), re.S))
    open(f"{O}/nested_items_C.md", "w").write("# Pairs of themes\n\n" + "\n".join(f"## {p}\n{sec[p].strip()}\n" for p in t.pid))
    print("third check:", len(t))
elif STEP == "final":
    K["vC"] = K.pid.map(C)
    def dec(r):
        """«borderline» votes do not count; the majority of the decisive votes decides; a tie -> unresolved (no change)."""
        v = [x for x in (r.vA, r.vB, r.vC) if x in ("different", "same")]
        c = collections.Counter(v).most_common()
        if not c or (len(c) == 2 and c[0][1] == c[1][1]): return "unresolved"
        return c[0][0]
    K["decision"] = K.apply(dec, axis=1)
    K["strategy"] = K.decision.map({"different": 1, "same": 2})
    # rule (а), [У] 2026-10-20: strategy 2 only if the broad theme passes the selection (before the removals); otherwise strategy 1
    import quiz_select as QS0, labels as LB0
    _o = LB0.load; LB0.load = lambda *a, **k: _o(*a, **{**k, "nested": False})
    passing = {d for d, x in QS0.criteria().items() if x["base"]}; LB0.load = _o
    K["rule_a"] = (K.strategy == 2) & ~K.big_d.isin(passing)
    K.loc[K.rule_a, "strategy"] = 1
    K["basis"] = K.apply(lambda r: "two checks" if r.vA == r.vB and r.vA in ("different", "same") else ("third check alone" if r.vA == r.vB == "borderline" else "majority"), axis=1)
    K.to_csv(f"{O}/nested_decision.csv", index=False)
    print(K.decision.value_counts().to_dict(), "| strategy:", K.strategy.value_counts().to_dict(), "| moved to 1 by rule (а):", int(K.rule_a.sum()))
    # removals per bill id × theme, from the original sets (labels before this step)
    import labels as LB
    bl = LB.load(nested=False)["bill_lab"]
    con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
    base = lambda n: re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
    bn = {b: base(n) for b, n in con.execute("select bill_id, name from bills where knesset in (24, 25)").fetchall()}
    ids = collections.defaultdict(lambda: collections.defaultdict(set))   # theme -> name -> bill ids
    for b, lb in bl.items():
        if b in bn:
            for d in LB.signed_topics(lb): ids[d][bn[b]].add(b)
    rm = set()
    for r in K[K.strategy.notna()].itertuples():
        shared = set(ids[r.small_d]) & set(ids[r.big_d])
        loser = r.big_d if r.strategy == 1 else r.small_d
        for nm in shared:
            for b in ids[loser][nm]: rm.add((b, loser, r.pid))
    items = [dict(bill_id=str(b), d=d, pair=p) for b, d, p in sorted(rm)]
    json.dump({"_doc": "Nested themes, global audit (SHARED_UNDERSTANDING «Вложенные темы — глобальный аудит», [У] 2026-10-20): a bill's "
               "label on the theme that loses the double count is removed (strategy 1: the broad theme, 2: the narrow theme). Pairs: "
               "local/research/theme_overlap/nested_decision.csv. Applied by pipeline/labels.py after all other corrections.", "items": items},
              open(f"{ROOT}/jef/directions/labels/nested_removals.json", "w"), ensure_ascii=False, indent=1)
    print(len({(i['bill_id'], i['d']) for i in items}), "bill × theme labels removed;", len({i['d'] for i in items}), "themes touched")
