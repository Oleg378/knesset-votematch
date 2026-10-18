"""Scheme v2 = CURRENT_SCHEME.md plus three hypotheses (approved for testing 2026-10-13):
  (a) technical filter: a yes/no question whether the bill changes anything of substance; if not (p < 0.5), no topics;
  (b) sign fix: for a selected topic whose side score is in the middle (0.7-1.3), two yes/no questions — does the bill
      increase / decrease the quantity; the sign is the side with p >= 0.5 and higher than the other, else unknown;
  (c) direction 244 narrowed to land-use and building planning (merge3/directions_final.json; v1 kept as .v1.json).
Run on all 50 bills with expert gold (jev_test3, jev_test4, jev_test5). Baseline: the current scheme on the saved answers.

Usage: python3 local/research/scripts/jev_scheme2.py            -> local/jef/directions/jev_roles/scheme2.json + metrics
       python3 local/research/scripts/jev_scheme2.py --reworded -> scheme3.json: also re-asks applicability and side for the 32 directions
                                                    reworded in rename/proposals.json (approved 2026-10-13)
       python3 local/research/scripts/jev_scheme2.py --softened -> scheme4.json: accepted scheme (no substance filter), 149/4/2 softened
       python3 local/research/scripts/jev_scheme2.py --fresh6   -> scheme_test6.json: accepted scheme on test 6 (fresh bills); --fresh7 likewise
"""
import asyncio, json, os
from typesafe_sdk import AsyncTypeSafeClient, Noul
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "pipeline"))  # pipeline modules
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j
import jev_roles as r

D = os.path.join(ROOT, "jef/directions")
OUT = os.path.join(D, "jev_roles")
TESTS = ["jev_test3", "jev_test4", "jev_test5"]
MID = (0.7, 1.3)

def gold_of(e):
    roles = {str(v["n"]): {"not_applicable": "none", "borderline": "borderline"}.get(v["verdict"], v.get("role") or "none") for v in e["verdicts"]}
    roles.update({str(d["n"]): d["role"] for d in e["my_directions"]})
    signs = {str(d["n"]): d["sign"] for d in e["my_directions"] + e.get("missed", [])}
    return roles, signs

def load_all():
    bills = []
    for t in TESTS:
        meta = {b["bill_id"]: b for b in json.load(open(os.path.join(D, t, "bills.json")))}
        jev = {x["bill_id"]: x for x in json.load(open(os.path.join(D, t, "out.json")))}
        for e in json.load(open(os.path.join(D, t, "review_out.json")))["bills"]:
            bid = str(e["bill_id"]); roles, signs = gold_of(e)
            bills.append({"bill_id": bid, "test": t, "type": meta[bid]["bill_type"], "state": j.state(meta[bid]),
                          "applies": dict(jev[bid]["applies"]), "side": {k: v["score"] for k, v in jev[bid]["side"].items()},
                          "gold": roles, "gold_sign": signs})
    return bills

def baseline_rows():
    """The current scheme on the saved answers of iterations 1 and 2 (dev, holdout, fresh)."""
    rows = []
    for sub, files in (("", ("iter_1.json", "iter_2.json")), ("", ("iter_1_holdout.json", "iter_2_holdout.json")),
                       ("fresh", ("iter_1_holdout.json", "iter_2_holdout.json"))):
        i1 = {x["bill_id"]: x["detail"] for x in json.load(open(os.path.join(OUT, sub, files[0])))["rows"]}
        for x in json.load(open(os.path.join(OUT, sub, files[1])))["rows"]:
            rows.append({"bill_id": x["bill_id"], "i1": i1[x["bill_id"]], "choice": {k: v["p_choice"] for k, v in x["detail"].items()}})
    return {x["bill_id"]: x for x in rows}

def select(b, choice, i1, technical_p=None):
    if technical_p is not None and technical_p < 0.5:
        return [], []
    o = sorted(choice, key=lambda k: -choice[k])
    main = o[:1] + [k for k in o[1:2] if choice[k] >= 0.5 * choice[o[0]]]
    cand = sorted((k for k, p in b["applies"].items() if p >= 0.3), key=lambda k: -b["applies"][k])
    sec = [k for k in cand if k not in main and b["applies"][k] >= 0.7 and i1.get(k, {}).get("top") in ("2", "3")][:5]
    return main, sec

def sign_of(score):
    return "−" if score < MID[0] else ("+" if score > MID[1] else None)

def metrics(rows, bills):
    by = {b["bill_id"]: b for b in bills}
    m = r.metrics([{"main": x["main"], "sec": x["sec"], "gold": by[x["bill_id"]]["gold"]} for x in rows])
    with_main = [x for x in rows if any(v == "primary" for v in by[x["bill_id"]]["gold"].values())]
    no_main = [x for x in rows if x not in with_main]
    m["bills_with_gold_main"] = len(with_main)
    m["correct_main_where_gold_has_one"] = sum(any(by[x["bill_id"]]["gold"].get(k) == "primary" for k in x["main"]) for x in with_main)
    m["bills_without_gold_main"] = len(no_main)
    m["no_topics_where_gold_has_no_main"] = sum(not x["main"] for x in no_main)
    m["no_topics_where_gold_has_main"] = sum(not x["main"] for x in with_main)
    ok = wrong = unknown = 0
    for x in rows:
        gs = by[x["bill_id"]]["gold_sign"]
        for k in x["main"] + x["sec"]:
            if k not in gs: continue
            s = x["sign"].get(k)
            if s is None: unknown += 1
            elif s == gs[k]: ok += 1
            else: wrong += 1
    m["sign_correct"], m["sign_wrong"], m["sign_unknown"] = ok, wrong, unknown
    m["false_244"] = sum(("244" in x["main"] + x["sec"]) and by[x["bill_id"]]["gold"].get("244", "none") == "none" for x in rows)
    return m

async def main():
    load_env()
    dirs = {str(d["n"]): d for d in j.directions_final()}
    bills = load_all()
    base = baseline_rows() if WITH_BASELINE else {}
    base_rows = []
    for b in bills if WITH_BASELINE else []:
        x = base[b["bill_id"]]
        mn, sc = select(b, x["choice"], x["i1"])
        base_rows.append({"bill_id": b["bill_id"], "main": mn, "sec": sc, "sign": {k: sign_of(b["side"][k]) for k in mn + sc}})
    rows, tok = [], 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        for b in bills:
            # (c) direction 244 (and, with --reworded, the reworded directions) re-asked with the new definitions
            a, t = await j.ask(client, b["state"], {f"d{k}": j.q_applies(dirs[k]) for k in REASK}) if REASK else ({}, 0); tok += t
            for k in REASK: b["applies"][k] = a[f"d{k}"].noul
            b["applies"].setdefault("244", 0)
            need = [k for k in REASK if b["applies"][k] >= 0.3]
            if need:
                a, t = await j.ask(client, b["state"], {f"d{k}": j.q_side(dirs[k]) for k in need}); tok += t
                for k in need: b["side"][k] = a[f"d{k}"].score
            cb = {**b, "cand": sorted((k for k, p in b["applies"].items() if p >= 0.3), key=lambda k: -b["applies"][k])}
            # role scale and main-aim choice on the (possibly changed) candidates
            q1, _ = r.iter1(cb, dirs); q2, _ = r.iter2(cb, dirs)
            qs = {**q1, **q2}
            if USE_SUBSTANCE: qs["substance"] = Noul(instructions="Does this Israeli bill change anything of substance — rights, duties, powers, "
                  "money, prohibitions or who is covered? Answer no if it is only technical, procedural or editorial: renumbering, rounding, "
                  "fixing references or wording, renaming, or moving a provision without changing what it does.")
            ans, t = await j.ask(client, b["state"], qs); tok += t
            i1 = {}
            for k, v in ans.items():
                if k.startswith("d"):
                    pr = {str(l): p for l, p in v.probabilities.items()}
                    i1[k[1:]] = {"top": max(pr, key=pr.get)}
            choice = {k[1:]: p for k, p in ans["main"].probabilities.items()}
            subst = ans["substance"].noul if USE_SUBSTANCE else None
            mn, sc = select(b, choice, i1, subst)
            # (b) sign fix for topics with a middle side score
            sign, fix = {}, {}
            for k in mn + sc:
                s = sign_of(b["side"][k])
                if s is None:
                    d = dirs[k]
                    a, t = await j.ask(client, b["state"], {
                        "inc": Noul(instructions=f"Does this Israeli bill increase, expand or strengthen «{d['name']}»? («+» means: {d['plus']})"),
                        "dec": Noul(instructions=f"Does this Israeli bill reduce, cut, weaken or abolish «{d['name']}»? («−» means: {d['minus']})")})
                    tok += t
                    pi, pd = a["inc"].noul, a["dec"].noul
                    s = "+" if pi >= 0.5 and pi > pd else ("−" if pd >= 0.5 and pd > pi else None)
                    fix[k] = {"p_inc": round(pi, 3), "p_dec": round(pd, 3)}
                sign[k] = s
            rows.append({"bill_id": b["bill_id"], "test": b["test"], "type": b["type"], "substance": subst,
                         "main": mn, "sec": sc, "sign": sign, "sign_fix": fix, "applies_244": round(b["applies"]["244"], 3),
                         "applies_reasked": {k: round(b["applies"][k], 3) for k in REASK}})
    old244 = {x["bill_id"]: x for t in TESTS for x in json.load(open(os.path.join(D, t, "out.json")))}
    if "244" not in REASK: old244 = {}
    res = {"baseline": metrics(base_rows, load_all()) if WITH_BASELINE else None, "scheme2": metrics(rows, bills), "tokens": tok,
           "usd": round(tok * USD_PER_INPUT_TOKEN, 4), "rows": rows, "baseline_rows": base_rows,
           "applies_244_old": {k: round(v["applies"]["244"], 3) for k, v in old244.items()}}
    json.dump(res, open(os.path.join(OUT, NAME), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("baseline", "scheme2", "usd")}, ensure_ascii=False, indent=1))

REASK, NAME, USE_SUBSTANCE, WITH_BASELINE = ["244"], "scheme2.json", True, True
if __name__ == "__main__":
    import sys
    if "--reworded" in sys.argv:
        REASK = ["244"] + [p[0] for p in json.load(open(os.path.join(D, "rename/proposals.json")))]
        NAME = "scheme3.json"
    if "--softened" in sys.argv:   # accepted scheme: no substance filter (a); 149, 4, 2 softened
        REASK = ["244"] + [p[0] for p in json.load(open(os.path.join(D, "rename/proposals.json")))]
        NAME, USE_SUBSTANCE = "scheme4.json", False
    for t in ("6", "7"):
        if f"--fresh{t}" in sys.argv:   # tests 6, 7: fresh bills, applicability already asked with the current list
            TESTS, REASK, NAME, USE_SUBSTANCE, WITH_BASELINE = [f"jev_test{t}"], [], f"scheme_test{t}.json", False, False
    asyncio.run(main())
