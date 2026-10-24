"""Export for the web quiz: the only link between pipeline/ and web/ (CLAUDE.md «Data contract»).

Writes to export/ (three files loaded in order, see export/WEB_CONTRACT.md «Loading»):
  quiz_core.json         the core statements and the flow numbers — enough to start answering;
  quiz_data.json         everything for matching: params, all statements, directions, lists with positions;
  quiz_bills.json        what only the list details need: bills, sponsors, bills by direction, the lists' votes;
  quiz_data.schema.json  JSON Schema of the three merged (validated here before writing);
  golden.json            golden test cases: answers (+ trade-off weights) -> what pipeline/quiz_match.py and
                            pipeline/quiz_report.py compute. The TypeScript port must reproduce them (web/ Vitest);
  stats.json             the numbers the documents quote (statements, lists by status, bills, former MKs, directions, file sizes
                            in KB) — make check I9 compares the documents with it.
Read, not written: quiz_texts.json — the user-facing texts, edited by hand (pipeline/texts.py, export/WEB_CONTRACT.md §7); the
explanation lines and notes in golden.json are rendered from its templates.
When the formula or the structure changes, the schema and the golden cases are regenerated and the contract (export/WEB_CONTRACT.md)
and the web tests are updated in the same step — the files the live site reads never change silently.

Nothing is computed here that the quiz scripts do not already compute: the positions come from pipeline/positions.py
(data/positions/), the statements and their English text from data/quiz/statements.csv, the labels as in quiz_report.py.

Usage: python3 pipeline/export.py        (or: make data)
"""
import collections, csv, datetime, json, math, os, random, subprocess, sys
import jsonschema
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quiz_match as qm
import quiz_report as qr
import quiz_flow as qf
import quiz_select as qs

ROOT = qm.ROOT
OUT = os.path.join(ROOT, "export")

def num(x):
    """JSON has no NaN: a closeness that cannot be computed is null."""
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else x

def source_commit():
    """HEAD, with «+dirty» if the inputs differ from it (external audit 2026-10-18, minor 4): uncommitted changes in the code
    (pipeline/), the data (data/ except the generated data/positions/) or manual/ mean the export does not come from that commit."""
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout
    dirty = [l[3:] for l in git("status", "--porcelain").splitlines() if l[3:].startswith(("pipeline/", "data/", "manual/")) and not l[3:].startswith("data/positions/")]
    if dirty: print(f"warning: export built from a working tree with uncommitted inputs: {dirty[:5]}", file=sys.stderr)
    return git("rev-parse", "--short", "HEAD").strip() + ("+dirty" if dirty else "")

def fetched():
    """The day the Knesset bill tables were last downloaded (pipeline/fetch/fetch_bills.py writes raw/bills/bill.json): the date the
    site shows as the data's date (customer 2026-10-24), not the day of this export."""
    return datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, "raw/bills/bill.json"))).isoformat()

def build_data(ctx):
    st, pos, cov = ctx["st"], ctx["pos"], ctx["cov"]
    quiz_d = list(dict.fromkeys(r["d"] for r in st))
    plan = {**json.load(open(os.path.join(ROOT, "data/directions/split/plan.json")))["new"],
            **{k: v for p in qr.L.later_plans() for k, v in p["new"].items()}}   # all later split stages (labels.LATER)
    final = {d["key"]: d for d in json.load(open(os.path.join(ROOT, "data/directions/merge3/directions_final.json")))}
    def ddesc(d):
        x = plan.get(d) or final[d]
        return {"name_en": x["name_en"], "plus_en": x["plus_en"], "minus_en": x["minus_en"]}
    nv = ctx["nv"]
    meta = qf.load_meta()
    lists = []
    for L, c in cov.items():   # order of data/positions/list_coverage.csv: the tie order of the ranking
        P = {}
        for d in quiz_d:
            x = pos.get(L, {}).get(d)
            if x: P[d] = {"P": x[0], "P_bills": x[3], "e": x[1], "n_mk": x[2], "n_votes": nv.get((L, d), 0), "n_other": ctx["no"].get((L, d), 0), "n_gov": ctx["ng"].get((L, d), 0), "n_names": x[4]}
        lists.append({"id": L, "name_en": c["list_name"], "status": c["status"], "ex_mks": int(c["ex_mks"]), "positions": P})
    # [У] 2026-10-22 (external audit №3 п. 1.4): which component party of the 2026 list each former MK comes from (Central Elections
    # Committee candidate list, manual/candidate_mk_26.csv «party»; English names manual/party_names_en.csv). Empty on the CEC page
    # = the list itself. lists[].composition summarises it for «Based on N former MKs: 17 from Yesh Atid, 2 from …».
    party_en = {r["party_he"]: r["party_en"] for r in csv.DictReader(open(os.path.join(ROOT, "manual/party_names_en.csv")))}
    mk_party = {int(r["mk_id"]): party_en.get(r["party"], r["party"]) or None for r in csv.DictReader(open(os.path.join(ROOT, "manual/candidate_mk_26.csv")))
                if r["match"] in ("exact", "manual")}
    cand_list, mks = {}, {}
    for L, ms in ctx["cand"].items():
        for m, (p, name) in ms.items():
            cand_list[m] = L
            mks[m] = {"name_en": name, "list": L, "list_position": p, "party_en": mk_party.get(int(m))}
    for l in lists:
        c = collections.Counter(mks[m]["party_en"] or l["name_en"].split(",")[0].strip() for m, x in mks.items() if x["list"] == l["id"])
        l["composition"] = [{"party_en": k, "ex_mks": n} for k, n in c.most_common()]
    by_direction = {d: [[b, s, role] for b, s, role in ctx["by_d"].get(d, [])] for d in quiz_d}
    # [У] 2026-10-19: how the list's former MKs voted on each bill of a quiz direction (data/positions/list_topic_votes.csv):
    # votes[list][direction] = [[bill, sign (+1 raises / −1 lowers the direction), camp («own» / «other»), for, against], ...];
    # «own» covers both V (private bills of the MK's camp) and, since 2026-10-22, G (the coalition's own government bills).
    votes = {}
    for r in csv.DictReader(open(os.path.join(qm.POS, "list_topic_votes.csv"))):
        if r["d"] in by_direction and cov.get(r["letters"], {}).get("status") != "not_evaluated":
            votes.setdefault(r["letters"], {}).setdefault(r["d"], []).append([r["bill_id"], int(r["sign"]), r["camp"], int(r["for"]), int(r["against"])])
    bill_ids = {b for v in by_direction.values() for b, _, _ in v} | {r[0] for dd in votes.values() for rows in dd.values() for r in rows}
    bills = {}
    for b in sorted(bill_ids, key=int):
        name, k = ctx["info"][b]
        bills[b] = {"name_he": name, "knesset": k,   # no url and no summary_en (DATA_REQUESTS #2); link = params.BILL_URL
                    "sponsors": sorted(m for m in ctx["init"][b] if m in cand_list)}
    return {
        "generated": datetime.date.today().isoformat(),
        "source_commit": source_commit(),
        "fetched": fetched(),
        "params": {"K": qm.K, "MIN_COVERAGE": qm.MIN_COVERAGE, "MIN_EX_MKS": qm.MIN_EX_MKS, "MAX_TRADE": qm.MAX_TRADE, "TRADE_TOP": qm.TRADE_TOP,
                   "TRADE_W": qm.TRADE_W, "TRADE_CANDIDATES": 3, "VOTE_WEIGHT": 0.25, "CLOSE": qr.CLOSE, "MIN_CLEAR_MKS": qr.MIN_CLEAR_MKS, "MIN_CLEAR_BILLS": qr.MIN_CLEAR_BILLS,
                   "BILL_URL": qr.LINK.replace("{}", "{id}"),
                   # selection of themes (quiz_select.py) — shown on the methodology page (quiz_texts.json placeholders)
                   "SELECT_MIN_LISTS": qs.MIN_LISTS, "SELECT_MIN_MKS": qs.MIN_MKS, "SELECT_MIN_SPREAD": qs.MIN_SD, "SELECT_MIN_NAMES": qs.MIN_NAMES},
        "flow": dict(qf.FLOW),
        "core": qf.core(),
        # interest / area / sim_group [У] 2026-10-21: metadata for the ORDER of questions only (data/quiz/statement_meta.csv)
        "statements": [{"q": r["q"], "title_en": r["title_en"], "statement_en": r["statement_en"], "key": r["key_s"],
                        "d": r["d"], "w": r["w"], "interest": meta[r["q"]]["interest"], "area": meta[r["q"]]["area"],
                        "sim_group": meta[r["q"]]["sim_group"] or None} for r in st],
        "directions": {d: ddesc(d) for d in quiz_d},
        "lists": lists,
        "mks": dict(sorted(mks.items(), key=lambda x: int(x[0]))),
        "by_direction": by_direction,
        "votes": votes,
        "bills": bills,
    }

# ---------------- golden test cases ----------------

def case(ctx, name, answers, mult=None, exclude=(), skip_lists=()):
    mult = mult or {}
    rows = qm.match(answers, mult=mult)
    ranking = [{"id": r["letters"], "closeness": num(r["closeness"]), "coverage": r["coverage"], "note": r["note"],
                "ranked": r["ranked"]}
               for r in rows]
    out = {"name": name, "answers": answers, "mult": mult, "ranking": ranking,
           "tradeoffs": {"exclude": list(exclude), "skip_lists": list(skip_lists),
                         "pairs": [list(t) for t in qm.tradeoffs(answers, mult, exclude=exclude, skip_lists=skip_lists)]},
           "details": []}
    for r in [x for x in ranking if x["ranked"]][:2] + [x for x in ranking if not x["ranked"] and x["closeness"] is not None][:1]:
        L = r["id"]
        items = []
        for c, q, a, u, p in qr.contributions(ctx, L, answers, mult):
            lines, ev = qr.explain(ctx, L, q, a, p, c, mult)
            items.append({"q": q["q"], "contribution": c, "p": p, "lines": lines,
                          "evidence": [{"bill": b, "sign": s, "role": role, "same": same, "authors": [[p_, nm] for p_, nm in sorted(authors)]}
                                       for _, _, b, s, role, authors, same in ev]})
        out["details"].append({"id": L, "items": items})
    return out

def flow_case(ctx, name, full):
    """Question order for a user whose answers to every statement would be `full`: core, then each clarifying statement chosen
    from the answers given so far (quiz_flow.next_clarify), the trade-off pairs at the end, and the ranking."""
    fctx = qf._ctx(); asked = qf.core(ctx=fctx); ans = {q: full[q] for q in asked if q in full}; steps = []
    while not qf.should_stop(ans, len(asked)):
        q = qf.next_clarify(ans, asked, ctx=fctx)
        if q is None: break
        asked.append(q)
        if q in full: ans[q] = full[q]
        steps.append(q)
    out = case(ctx, name, ans)
    out["flow"] = {"core": asked[:len(asked) - len(steps)], "clarifying": steps}
    return out

def full_answers(qs):
    """A synthetic full answer set (no real person's answers in the contract) with at least two trade-off pairs."""
    for seed in range(20261019, 20262019):
        rnd = random.Random(seed)
        ans = {q: rnd.choice([-2, -1, 0, 1, 2, "dk"]) for q in qs}
        if len(qm.tradeoffs(ans)) >= 2: return ans
    raise RuntimeError("no synthetic answer set with two trade-off pairs")

def golden(ctx):
    """The golden cases as a dict (nothing written): main() writes it to export/golden.json, make check I10 compares with it."""
    st = ctx["st"]
    qs = [r["q"] for r in st]
    full = full_answers(qs)
    t = qm.tradeoffs(full)
    cases = [case(ctx, "full", full), case(ctx, "full + trade-offs", full, {t[0][0]: qm.TRADE_W, t[1][1]: qm.TRADE_W})]
    cases.append(case(ctx, "full, adaptive step 2", full, {t[0][0]: qm.TRADE_W}, exclude=t[0][:2], skip_lists=[t[0][2]]))
    rnd = random.Random(20261017)
    for i in range(20):
        n = rnd.choice([3, 10, 30, len(qs)])
        ans = {q: rnd.choice([-2, -1, 0, 1, 2, "dk"]) for q in rnd.sample(qs, n)}
        mult = {q: qm.TRADE_W for q in rnd.sample(list(ans), min(2, len(ans)))} if i % 3 == 0 else {}
        cases.append(case(ctx, f"random {i}", ans, mult))
    cases += [case(ctx, "no answers", {}), case(ctx, "all don't know", {q: "dk" for q in qs}),
              case(ctx, "all neutral", {q: 0 for q in qs}), case(ctx, "one answer", {qs[0]: 2}),
              case(ctx, "rare topic only", {"71": -2, "66": 1})]
    for i in range(6):   # question order: synthetic users answering every statement at random (no real person's answers)
        rnd2 = random.Random(20261018 + i)
        cases.append(flow_case(ctx, f"flow {i}", {q: rnd2.choice([-2, -1, 1, 2, "dk"]) for q in qs}))
    return {"tolerance": 1e-9, "cases": cases}

def stats(data):
    """The numbers the documents quote, from the data just exported (file sizes: raw bytes / 1000, rounded)."""
    st = collections.Counter(l["status"] for l in data["lists"])
    size = lambda n: round(os.path.getsize(os.path.join(OUT, n)) / 1e3)
    return {"generated": data["generated"], "source_commit": data["source_commit"],
            "statements": len(data["statements"]),
            "lists": {"total": len(data["lists"]), "evaluated": st["ok"], "warning": st["warning"], "no_record": st["not_evaluated"]},
            "bills": len(data["bills"]), "mks": len(data["mks"]), "directions": len(data["directions"]),
            "files": {n: size(n) for n in ("quiz_core.json", "quiz_data.json", "quiz_bills.json", "quiz_texts.json")}}

def main():
    ctx = qr.context()
    data = build_data(ctx)
    schema = json.load(open(os.path.join(OUT, "quiz_data.schema.json")))
    jsonschema.validate(data, schema)
    os.makedirs(OUT, exist_ok=True)
    # [У] 2026-10-18: three files loaded in order, so the start page and the first questions never wait for the bills
    head = {k: data[k] for k in ("generated", "source_commit")}
    parts = {"core": {**head, "flow": data["flow"], "core": data["core"],
                      "statements": [s for s in data["statements"] if s["q"] in data["core"]]},
             "data": {**head, **{k: data[k] for k in ("fetched", "params", "flow", "core", "statements", "directions", "lists")}},
             "bills": {**head, **{k: data[k] for k in ("mks", "by_direction", "votes", "bills")}}}
    for name, part in parts.items():
        json.dump(part, open(os.path.join(OUT, f"quiz_{name}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    g = golden(ctx)
    json.dump(g, open(os.path.join(OUT, "golden.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "stats.json"), "w") as f:
        json.dump(stats(data), f, ensure_ascii=False, indent=1); f.write("\n")
    sz = {n: os.path.getsize(os.path.join(OUT, f"quiz_{n}.json")) / 1e3 for n in parts}
    print(f"{len(data['statements'])} statements, {len(data['lists'])} lists, {len(data['bills'])} bills; files (KB): "
          + ", ".join(f"quiz_{n}.json {v:.0f}" for n, v in sz.items()) + f"; golden.json: {len(g['cases'])} cases")

if __name__ == "__main__":
    main()
