"""Nested themes (SHARED_UNDERSTANDING «Вложенные темы — глобальный аудит», [У] 2026-10-20): merge the blind meaning checks of the pairs
(nested_result_A/B.csv, third check nested_result_C.csv for disagreements and «borderline») and build the removals.

Decision per pair: different -> strategy 1 (the shared bills leave the broad theme), same -> strategy 2 (they leave the narrow theme);
two agreeing checks decide, otherwise the majority of three; three-way split or a borderline majority -> no change (the pair is listed).
All removals are computed on the ORIGINAL bill sets (not sequentially) and are per bill id × theme.

Usage: python3 nested_apply.py merge   -> nested_merged.csv, nested_items_C.md (pairs for the third check)
       python3 nested_apply.py final   -> nested_decision.csv, nested_removals.computed.json (APPLY=1 writes data/directions/labels/nested_removals.json,
                                          read by pipeline/labels.py). Do not re-apply: the removals were computed on the labels of 2026-10-20
                                          (before stages 6–8 and the new-theme label checks); the applied file is the source of truth.
"""
import csv, json, os, re, sys, collections
import pandas as pd, duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        """Two agreeing decisive checks decide; otherwise the third check (forced choice) decides — v1 fix 2026-10-20: a tie used to be
        left unresolved although the third check was asked precisely to break it."""
        if r.vA == r.vB and r.vA in ("different", "same"): return r.vA
        return r.vC if r.vC in ("different", "same") else "unresolved"
    K["decision"] = K.apply(dec, axis=1)
    K["strategy"] = K.decision.map({"different": 1, "same": 2})
    # rule (а), [У] 2026-10-20: strategy 2 only if the broad theme passes the selection (before the removals); otherwise strategy 1
    import quiz_select as QS0, labels as LB0
    _o = LB0.load; LB0.load = lambda *a, **k: _o(*a, **{**k, "nested": False})
    pl0 = json.load(open(f"{ROOT}/data/directions/split/plan.json"))
    rem0 = (set(pl0["parents"]) - set(pl0["keep"])) | {d for p in LB0.later_plans() for d in p["parents"]}
    tech0 = {"107", "128", "236", "289", "339", "343", "346"}
    # «passes» = can carry a statement: remainders of split themes and technical themes get none by rule, so they count as failing
    # frozen: the selection BEFORE any nested removal (positions on disk change once the removals are applied)
    passing = set(json.load(open(f"{O}/passing_before.json"))) - rem0 - tech0; LB0.load = _o
    K["rule_a"] = (K.strategy == 2) & ~K.big_d.isin(passing)
    K.loc[K.rule_a, "strategy"] = 1
    # customer decisions per pair override everything above (nested_customer.csv)
    cf = f"{O}/nested_customer.csv"
    K["customer"] = False
    if os.path.exists(cf):
        for r in csv.DictReader(open(cf)):
            K.loc[K.pid == r["pid"], ["strategy", "customer"]] = [int(r["strategy"]), True]
    K["basis"] = K.apply(lambda r: "two checks" if r.vA == r.vB and r.vA in ("different", "same") else "third check", axis=1)
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
              open(f"{ROOT}/data/directions/labels/nested_removals.json" if os.environ.get("APPLY") == "1" else f"{O}/nested_removals.computed.json", "w"), ensure_ascii=False, indent=1)
    print(len({(i['bill_id'], i['d']) for i in items}), "bill × theme labels removed;", len({i['d'] for i in items}), "themes touched")
