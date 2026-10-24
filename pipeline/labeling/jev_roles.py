"""Experiment: can Jev pick the 1-2 main directions of a bill and up to 5 secondary ones?
Gold: expert roles (primary / secondary / tertiary; not applicable; borderline) for the 40 bills of jev_test3 and jev_test4.
Candidates: directions with applies >= 0.3 in the existing Jev runs. Dev half: 10 private + 10 government; holdout: the rest.

Usage: python3 pipeline/labeling/jev_roles.py run ITER [--holdout]   -> local/jef/directions/jev_roles/iter_ITER[_holdout].json + metrics
       python3 pipeline/labeling/jev_roles.py recompute ITER SRC [--holdout]  -> iteration ITER from the saved answers of SRC (same prompt, new rule)
       --fresh: test 5 (local/jef/directions/jev_test5, results in jev_roles/fresh/): run 1, run 2, recompute current 2
Each iteration is a function PROMPTS[ITER] -> (questions for one bill, selection rule). Documented in local/jef/directions/jev_roles/EXPERIMENT.md.
"""
import asyncio, json, os, random, sys
from typesafe_sdk import AsyncTypeSafeClient, Score, Choice, Noul
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j

D = os.path.join(ROOT, "data/directions")
OUT = os.path.join(D, "jev_roles")
TESTS = ["jev_test3", "jev_test4"]
FRESH = False   # test 5: fresh bills, checked once with the fixed scheme (CURRENT_SCHEME.md)

def load():
    """Bills with state, candidates and gold roles; split into dev and holdout (fixed seed).
    With FRESH (test 5): only the fresh bills, all of them in the 'holdout' role."""
    dirs = {str(d["n"]): d for d in j.directions_final()}
    bills = []
    for t in TESTS:
        meta = {b["bill_id"]: b for b in json.load(open(os.path.join(D, t, "bills.json")))}
        jev = {r["bill_id"]: r for r in json.load(open(os.path.join(D, t, "out.json")))}
        for e in json.load(open(os.path.join(D, t, "review_out.json")))["bills"]:
            bid = str(e["bill_id"])
            gold = {str(v["n"]): {"not_applicable": "none", "borderline": "borderline"}.get(v["verdict"], v.get("role") or "none")
                    for v in e["verdicts"]}
            gold.update({str(d["n"]): d["role"] for d in e["my_directions"]})
            cand = sorted((k for k, p in jev[bid]["applies"].items() if p >= 0.3), key=lambda k: -jev[bid]["applies"][k])
            bills.append({"bill_id": bid, "test": t, "state": j.state(meta[bid]), "cand": cand,
                          "applies": jev[bid]["applies"], "gold": gold})
    if FRESH: return dirs, bills, set()
    rnd = random.Random(20261015)
    dev = []
    for t in TESTS:
        dev += rnd.sample([b["bill_id"] for b in bills if b["test"] == t], 10)
    return dirs, bills, set(dev)

# ---- iterations -------------------------------------------------------------------------------------------------
ROLES = ["Not affected: the bill does not change this quantity",
         "Minor: a weak or indirect side effect of the bill",
         "Secondary: a noticeable side effect, but not what the bill is for",
         "Main: changing this quantity is the purpose of the bill"]

def iter1(b, dirs):
    """One role scale (0-3) per candidate. Rule: rank by P(main); top-1 is main; the 2nd is main too if its most likely
    level is 'Main'. Secondary: next candidates whose most likely level is Secondary or Main, up to 5."""
    qs = {f"d{k}": Score(instructions=f"What role does the quantity «{dirs[k]['name']}» play in this Israeli bill? "
                                      f"«+» means: {dirs[k]['plus']}. «−» means: {dirs[k]['minus']}.", criteria=ROLES) for k in b["cand"]}
    def select(ans):
        prob = {k[1:]: {str(l): p for l, p in a.probabilities.items()} for k, a in ans.items()}
        pm = {k: p.get("3", 0) for k, p in prob.items()}
        top = {k: max(p, key=p.get) for k, p in prob.items()}
        order = sorted(pm, key=lambda k: -pm[k])
        main = order[:1] + [k for k in order[1:2] if top[k] == "3"]
        sec = [k for k in order if k not in main and top[k] in ("2", "3")][:5]
        return main, sec, {k: {"p_main": round(pm[k], 3), "top": top[k]} for k in pm}
    return qs, select

_iter1 = None
SUFFIX = ""   # "_holdout" when working on the holdout half
def iter1_detail(bid):
    """Role-scale answers of iteration 1 (dev), reused so that only the main-topic question changes."""
    global _iter1
    if _iter1 is None:
        _iter1 = {r["bill_id"]: r["detail"] for r in json.load(open(os.path.join(OUT, f"iter_1{SUFFIX}.json")))["rows"]}
    return _iter1[bid]

def iter2(b, dirs, ratio=0.5):
    """One choice question over all candidates: which quantity is the main purpose of the bill? Probabilities compete.
    Main: the top choice, plus the second if its probability >= ratio * the top one. Secondary: as in iteration 1
    (role-scale answers of iteration 1 reused), excluding the mains."""
    crit = {f"D{k}": f"{dirs[k]['name']} («+»: {dirs[k]['plus']} «−»: {dirs[k]['minus']})" for k in b["cand"]}
    qs = {"main": Choice(instructions="Which of these quantities does this Israeli bill mainly aim to change? Choose the one whose change "
                                      "is the purpose of the bill, not a side effect.", criteria=crit)}
    def select(ans):
        pr = {k[1:]: p for k, p in ans["main"].probabilities.items()}
        order = sorted(pr, key=lambda k: -pr[k])
        main = order[:1] + [k for k in order[1:2] if pr[k] >= ratio * pr[order[0]]]
        det = iter1_detail(b["bill_id"])
        sec = [k for k in sorted(det, key=lambda k: -det[k]["p_main"]) if k not in main and det[k]["top"] in ("2", "3")][:5]
        return main, sec, {k: {"p_choice": round(pr[k], 3)} for k in order}
    return qs, select

def iter3(b, dirs):
    """Iteration 2 with ratio 0.3 for the second main topic."""
    return iter2(b, dirs, ratio=0.3)

def iter4(b, dirs, ratio=0.3, sec_min=0.8):
    """Mains as in iteration 3. Secondary: candidates other than the mains with applies >= sec_min, by applies, up to 5."""
    qs, select3 = iter2(b, dirs, ratio)
    def select(ans):
        main, _, detail = select3(ans)
        sec = [k for k in b["cand"] if k not in main and b["applies"][k] >= sec_min][:5]
        return main, sec, detail
    return qs, select

def iter5(b, dirs, ratio=0.3):
    """Mains as in iteration 3. Secondary: candidates other than the mains with applies >= 0.8, or 0.6 <= applies < 0.8
    and the iteration-1 role scale puts them at Main or Secondary; by applies, up to 5."""
    qs, select3 = iter2(b, dirs, ratio)
    def select(ans):
        main, _, detail = select3(ans)
        det = iter1_detail(b["bill_id"])
        sec = [k for k in b["cand"] if k not in main and (b["applies"][k] >= 0.8 or
               (b["applies"][k] >= 0.6 and det[k]["top"] in ("2", "3")))][:5]
        return main, sec, detail
    return qs, select

_iter3 = None
def iter3_main(bid):
    """Main topics chosen in iteration 3 (same half), so that only the secondary question changes."""
    global _iter3
    if _iter3 is None:
        _iter3 = {r["bill_id"]: r["main"] for r in json.load(open(os.path.join(OUT, f"iter_3{SUFFIX}.json")))["rows"]}
    return _iter3[bid]

def iter6(b, dirs, cut=0.5):
    """Idea 1: secondary topics anchored to the main aim. Mains: as in iteration 3. For every other candidate, a yes/no
    question: the bill's main aim is to change M; do its own provisions also directly change Y? Secondary: yes-probability
    >= cut, by that probability, up to 5."""
    main = iter3_main(b["bill_id"])
    aim = "; ".join(f"«{dirs[k]['name']}» («+»: {dirs[k]['plus']})" for k in main)
    qs = {f"d{k}": Noul(instructions=f"The main aim of this Israeli bill is to change: {aim}. Besides that, do the bill's own provisions "
                                     f"also directly change «{dirs[k]['name']}» («+»: {dirs[k]['plus']} «−»: {dirs[k]['minus']})? "
                                     f"Answer yes only if a provision of the bill itself changes this quantity; answer no if it is "
                                     f"merely a related subject, a motive, or the background of the bill.")
          for k in b["cand"] if k not in main}
    def select(ans):
        py = {k[1:]: a.noul for k, a in ans.items()}
        sec = [k for k in sorted(py, key=lambda k: -py[k]) if py[k] >= cut][:5]
        return main, sec, {k: {"p_yes": round(v, 3)} for k, v in py.items()}
    return qs, select

def iter7(b, dirs):
    """Idea 2: secondary topics by one competing choice. Mains: as in iteration 3. One choice question over the other
    candidates plus «none of these»: which of these quantities do the bill's own provisions also change? Secondary: every
    option whose probability is at least that of «none», by probability, up to 5. No tuned parameters."""
    main = iter3_main(b["bill_id"])
    crit = {f"D{k}": f"{dirs[k]['name']} («+»: {dirs[k]['plus']} «−»: {dirs[k]['minus']})" for k in b["cand"] if k not in main}
    crit["NONE"] = "None of these: the bill's provisions change none of the listed quantities"
    qs = {"sec": Choice(instructions="Apart from its main aim, which of these quantities do this Israeli bill's own provisions also change? "
                                     "Choose the one most clearly changed by the bill.", criteria=crit)}
    def select(ans):
        pr = {k: p for k, p in ans["sec"].probabilities.items()}
        none = pr.pop("NONE", 0)
        sec = [k[1:] for k in sorted(pr, key=lambda k: -pr[k]) if pr[k] >= none][:5]
        return main, sec, {k[1:]: {"p_choice": round(v, 3)} for k, v in pr.items()} | {"NONE": {"p_choice": round(none, 3)}}
    return qs, select

def current(b, dirs):
    """The fixed scheme of CURRENT_SCHEME.md: mains by the choice question (ratio 0.5); secondary: applies >= 0.7 and the
    role scale's most likely level Main or Secondary, by applies, up to 5. Built from the saved answers of iterations 1 and 2."""
    qs, select2 = iter2(b, dirs, ratio=0.5)
    def select(ans):
        main, _, detail = select2(ans)
        det = iter1_detail(b["bill_id"])
        sec = [k for k in b["cand"] if k not in main and b["applies"][k] >= 0.7 and det[k]["top"] in ("2", "3")][:5]
        return main, sec, detail
    return qs, select

PROMPTS = {"1": iter1, "2": iter2, "3": iter3, "4": iter4, "5": iter5, "6": iter6, "7": iter7, "current": current}

def recompute(it, src):
    """Same prompt as iteration `src`, only the selection rule differs: rebuild the result from the saved answers (no Jev calls)."""
    dirs, bills, dev = load()
    by = {b["bill_id"]: b for b in bills}
    old = json.load(open(os.path.join(OUT, f"iter_{src}{SUFFIX}.json")))
    rows = []
    for r in old["rows"]:
        _, select = PROMPTS[it](by[r["bill_id"]], dirs)
        class A: pass
        a = A(); a.probabilities = {"D" + k: v["p_choice"] for k, v in r["detail"].items()}
        main, sec, detail = select({"main": a})
        rows.append({**r, "main": main, "sec": sec, "detail": detail})
    m = metrics(rows); m["tokens"], m["usd"], m["recomputed_from"] = 0, 0, src
    json.dump({"iteration": it, "holdout": bool(SUFFIX), "metrics": m, "rows": rows},
              open(os.path.join(OUT, f"iter_{it}{SUFFIX}.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(m, ensure_ascii=False, indent=1))

# ---- run and metrics --------------------------------------------------------------------------------------------
def metrics(rows):
    m = {"bills": len(rows), "main_selected": 0, "main_correct": 0, "gold_main": 0, "gold_main_found": 0,
         "bills_with_correct_main": 0, "secondary_selected": 0, "secondary_by_gold_role": {}}
    for r in rows:
        g = r["gold"]
        gm = {k for k, v in g.items() if v == "primary"}
        m["main_selected"] += len(r["main"]); m["main_correct"] += sum(k in gm for k in r["main"])
        m["gold_main"] += len(gm); m["gold_main_found"] += sum(k in r["main"] for k in gm)
        m["bills_with_correct_main"] += any(k in gm for k in r["main"])
        m["secondary_selected"] += len(r["sec"])
        gs = {k for k, v in g.items() if v == "secondary"}
        m["gold_secondary"] = m.get("gold_secondary", 0) + len(gs)
        m["gold_secondary_found"] = m.get("gold_secondary_found", 0) + sum(k in r["sec"] for k in gs)
        for k in r["sec"]:
            role = g.get(k, "unrated")
            m["secondary_by_gold_role"][role] = m["secondary_by_gold_role"].get(role, 0) + 1
    m["main_precision"] = round(m["main_correct"] / max(1, m["main_selected"]), 2)
    m["main_recall"] = round(m["gold_main_found"] / max(1, m["gold_main"]), 2)
    m["share_bills_with_correct_main"] = round(m["bills_with_correct_main"] / max(1, m["bills"]), 2)
    m["secondary_recall"] = round(m.get("gold_secondary_found", 0) / max(1, m.get("gold_secondary", 0)), 2)
    m["secondary_not_applicable_share"] = round(m["secondary_by_gold_role"].get("none", 0) / max(1, m["secondary_selected"]), 2)
    return m

async def run(it, holdout):
    global SUFFIX
    SUFFIX = "_holdout" if holdout else ""
    load_env()
    dirs, bills, dev = load()
    todo = [b for b in bills if (b["bill_id"] in dev) != holdout]
    rows, tok = [], 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        for b in todo:
            qs, select = PROMPTS[it](b, dirs)
            ans, t = await j.ask(client, b["state"], qs)
            tok += t
            main, sec, detail = select(ans)
            rows.append({"bill_id": b["bill_id"], "test": b["test"], "main": main, "sec": sec, "detail": detail, "gold": b["gold"]})
    m = metrics(rows)
    m["tokens"], m["usd"] = tok, round(tok * USD_PER_INPUT_TOKEN, 4)
    os.makedirs(OUT, exist_ok=True)
    name = f"iter_{it}{'_holdout' if holdout else ''}.json"
    json.dump({"iteration": it, "holdout": holdout, "metrics": m, "rows": rows}, open(os.path.join(OUT, name), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(m, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    if "--fresh" in sys.argv:
        FRESH, TESTS, OUT = True, ["jev_test5"], os.path.join(D, "jev_roles/fresh")
        sys.argv.append("--holdout")
    if "--holdout" in sys.argv: SUFFIX = "_holdout"
    if sys.argv[1] == "recompute": recompute(sys.argv[2], sys.argv[3])
    else: asyncio.run(run(sys.argv[2], "--holdout" in sys.argv))
