"""Explained quiz result: for each list — closeness, then each answered statement with the list's position and the bills behind it.

For every 2026 list (evaluated ones, ranked as in quiz_match.py) and every answered statement where the list has a position:
  - the user's stance (agree / disagree on the statement), the list's position and whether they match;
  - the evidence: bills on the statement's direction authored by the list's ex-MKs (main or secondary topic, signed), each marked
    as pushing the same way as the user's answer or the opposite way, with a link to the Knesset site; plus how many of their
    votes on private bills on this direction there are (votes enter the position with weight 0.25).
Labels are the mass labels with the split of heterogeneous directions applied (as in pipeline/positions.py).

Usage: python3 pipeline/quiz_report.py local/jef/quiz/pilot_answers_filled.csv  ->  jef/quiz/report_<file name>.md
"""
import csv, glob, json, os, re, sys, collections
import duckdb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quiz_match as qm
import labels as L

ROOT, LAB = qm.ROOT, os.path.join(qm.ROOT, "jef/directions/labels")
SGN = {"+": 1, "−": -1, "-": -1}
LINK = "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid={}"
TOP, PER = 10, 5   # [У] 2026-10-17: топ-10 списков, у каждого «почему подходит» и «почему не подходит»
CLOSE = 0.1   # [О] п. 6: |p| below this — «close to the average MK»; test: local/research/scripts/threshold_stability.py
EPS = 1e-9
ANS = {2: "strongly agree", 1: "somewhat agree", 0: "neutral", -1: "somewhat disagree", -2: "strongly disagree"}   # [У] 2026-10-17: product language is English

def labels():
    lab = {}
    for f in sorted(glob.glob(f"{LAB}/batch_*.jsonl")):
        for l in open(f):
            x = json.loads(l)
            lab[x["bill_id"]] = {"main": [dict(m) for m in x["main"]], "sec": [dict(m) for m in x["secondary"]]}
    for l in open(f"{LAB}/split_choice.jsonl"):
        r = json.loads(l)
        if r["bill_id"] not in lab or not r["assigned"]: continue
        k = "main" if r["role"] == "main" else "sec"
        lab[r["bill_id"]][k] = [t for t in lab[r["bill_id"]][k] if t["n"] != r["parent"]]
        have = {t["n"] for t in lab[r["bill_id"]]["main"] + lab[r["bill_id"]]["sec"]}
        for a in r["assigned"]:
            if a["n"] not in have: lab[r["bill_id"]][k].append({"n": a["n"], "sign": a["sign"]})
    for b, v in json.load(open(f"{LAB}/overrides.json")).get("labels", {}).items():   # point corrections of resonant laws
        if b in lab: lab[b] = {"main": v["main"], "sec": v["secondary"]}
    tech = set()
    for v in json.load(open(f"{LAB}/overrides.json"))["technical"].values(): tech |= set(v["bill_ids"])
    drop = L.irrelevant()   # SU 27.3, 2026-10-17: bills not about the issue of the direction's quiz statements (as in positions.py)
    for b, v in lab.items():
        for k in ("main", "sec"): v[k] = [t for t in v[k] if (b, str(t["n"])) not in drop]
    return {b: v for b, v in lab.items() if b not in tech}

def tradeoff_text(A, aa, B, ab):
    """A trade-off question on the original quiz statements: the side that answers A as the user did and B the opposite way."""
    return (f"Suppose you could only choose between two sides. The first agrees with you on statement A but not on B; "
            f"the second, the other way round. Which matters more to you?\n"
            f"A. “{A['statement_en']}” — your answer: {ANS[aa]}.\n"
            f"B. “{B['statement_en']}” — your answer: {ANS[ab]}.\n"
            f"Answer: A, B or = (equally).")

def read_answers(f):
    ans = {}
    for row in csv.reader(open(f)):
        if not row or not row[0].strip().isdigit(): continue
        a = row[3].strip().lower().replace("−", "-") if len(row) > 3 else ""
        if a in ("нз", "dk", "?"): ans[row[0].strip()] = "dk"
        elif re.fullmatch(r"-?[0-2]", a): ans[row[0].strip()] = int(a)
    return ans

def context():
    """Everything the explanations need: statements, positions, labels, bills, authors, candidates."""
    st, pos, cov = qm.load()
    lab = labels()
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    info = {str(b): (n, k) for b, n, k in con.sql("select bill_id, name, knesset from bills").fetchall()}
    init = collections.defaultdict(set)
    for b, m in con.sql("select bill_id::varchar, mk_id::varchar from bill_initiators where is_initiator").fetchall(): init[b].add(m)
    # [У] 2026-10-17: sponsors' names transliterated to English (manual/mk_names_en.csv; not an official source)
    name_en = {r["mk_id"]: r["name_en"] for r in csv.DictReader(open(os.path.join(ROOT, "manual/mk_names_en.csv")))}
    cand = collections.defaultdict(dict)   # list -> mk_id -> (position, name)
    for r in csv.DictReader(open(os.path.join(ROOT, "manual/candidate_mk_26.csv"))):
        if r["match"] in ("exact", "manual"): cand[r["letters"]][r["mk_id"]] = (int(r["position"]), name_en.get(r["mk_id"], r["mk_name"]))
    by_d = collections.defaultdict(list)   # direction -> [(bill, sign, role)]
    for b, v in lab.items():
        for role, ms in (("main", v["main"]), ("secondary", v["sec"])):
            for m in ms:
                if m["sign"] in SGN: by_d[m["n"]].append((b, SGN[m["sign"]], role))
    nv = {(r["letters"], r["d"]): int(r["sum_nV"]) for r in csv.DictReader(open(os.path.join(qm.POS, "list_topic_positions.csv")))}
    dir_en = {d["key"]: d["name_en"] for d in json.load(open(os.path.join(ROOT, "jef/directions/merge3/directions_final.json")))}
    dir_en.update({k: v["name_en"] for k, v in json.load(open(os.path.join(ROOT, "jef/directions/split/plan.json")))["new"].items()})
    return dict(st=st, pos=pos, cov=cov, info=info, init=init, cand=cand, by_d=by_d, nv=nv, dir_en=dir_en,
                title={r["q"]: r for r in st})

def contributions(ctx, L, ans, mult=None):
    """Per answered statement: (contribution to closeness numerator, statement, answer, u, list value), largest first."""
    lv = qm.list_vec(ctx["st"], ctx["pos"], L, qm.K)
    rows = []
    for q in ctx["st"]:
        a = ans.get(q["q"])
        if a in (None, "dk") or a == 0 or q["q"] not in lv: continue
        u = a / 2 * q["key_s"]
        rows.append((q["w"] * (mult or {}).get(q["q"], 1) * u * lv[q["q"]], q, a, u, lv[q["q"]]))
    return sorted(rows, key=lambda x: -x[0])

def evidence(ctx, L, q, u, contrib):
    """Bills on the statement's direction authored by the list's ex-MKs: (relevant first, best position, bill, sign, role,
    authors, same way as the user's answer)."""
    ev = []
    for b, s, role in ctx["by_d"].get(q["d"], []):
        authors = [ctx["cand"][L][m] for m in ctx["init"][b] if m in ctx["cand"][L]]
        if not authors: continue
        same = (s * (1 if u > 0 else -1)) > 0
        ev.append((not same if contrib < 0 else same, min(a_[0] for a_ in authors), b, s, role, authors, same))
    return sorted(ev, key=lambda x: (not x[0], x[1]))

def bill_line(ctx, q, b, s, role, authors, same, link=True):
    name = f"[{ctx['info'][b][0]}]({LINK.format(b)})" if link else f"{ctx['info'][b][0]} — {LINK.format(b)}"
    return (f"- {'✓' if same else '✗'} {name} — Knesset {ctx['info'][b][1]}, {role} topic, "
            f"{'raises' if s > 0 else 'lowers'} “{ctx['dir_en'].get(q['d'], q['d'])}”; sponsored by: "
            + ", ".join(f"{nm} (#{p_} on the list)" for p_, nm in sorted(authors)[:2]))

def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"

def explain(ctx, L, q, a, p, contrib, mult=None):
    """[У] 2026-10-17: one explained statement in plain words — the statement as shown in the quiz, the user's answer, the
    list's side (by sign; «close to the average MK» when |p| < CLOSE, п. 6), the basis (the list's ex-MKs' bills split by
    direction and their votes) and one caveat: the side comes from votes when the list's own bills give nothing or the other
    side (п. 7); otherwise, when the bill counts look opposite to the verdict, positions are relative to the average MK."""
    ev = evidence(ctx, L, q, a / 2 * q["key_s"], contrib)
    n_same = sum(1 for e in ev if e[6]); n_opp = len(ev) - n_same
    nvotes = ctx["nv"].get((L, q["d"]), 0)
    close = abs(p) < CLOSE
    side = ("close to the average MK on this statement" if close else
            "for this statement" if p * q["key_s"] > 0 else "against this statement")
    lines = [f"“{q['statement_en']}”",
             f"Your answer: {ANS[a]}. The list is {side}.",
             (f"Basis: {plural(len(ev), 'bill')} sponsored by the list's former MKs — {n_same} your way, {n_opp} the other way; "
              f"{plural(nvotes, 'vote')} on private bills on this topic." if ev else
              f"Basis: no bills of their own on this topic, only {plural(nvotes, 'vote')} on private bills.")]
    if (mult or {}).get(q["q"], 1) != 1: lines.append("Weight ×2: you chose this topic in a trade-off question.")
    P, P_A = ctx["pos"][L][q["d"]][0], ctx["pos"][L][q["d"]][3]
    by_votes = bool(ev) and (abs(P_A) <= EPS or (P_A > 0) != (P > 0))   # own bills give nothing or the other side
    if close: pass
    elif by_votes:
        lines.append("The list's side comes from how its former MKs voted on private bills, not from the bills they sponsored.")
    elif ev and contrib > 0 and n_opp > n_same:
        lines.append("The list has more bills of its own the other way, but other MKs sponsored such bills even more often: "
                     "positions are measured relative to the average MK.")
    elif ev and contrib < 0 and n_same > n_opp:
        lines.append("The list has more bills of its own your way, but other MKs sponsored such bills even more often: "
                     "positions are measured relative to the average MK.")
    return lines, ev

def main(f):
    ctx = context()
    st, title, nv = ctx["st"], ctx["title"], ctx["nv"]
    ans = read_answers(f)
    # trade-off questions [У 2026-10-16]: sheet tradeoffs_<file>.csv; if it is filled, its answers re-weight the statements
    tf = os.path.join(os.path.dirname(os.path.abspath(f)), "tradeoffs_" + os.path.basename(f))
    mult = qm.read_tradeoffs(tf) if os.path.exists(tf) else {}
    if not os.path.exists(tf):
        with open(tf, "w", newline="") as fo:
            w = csv.writer(fo)
            w.writerow(["#", "Topic A", "Topic B", "Answer (A / B / =)", "Question"])
            for i, (qa, qb, _) in enumerate(qm.tradeoffs(ans), 1):   # built on the statements exactly as shown in the quiz
                A, B = title[qa], title[qb]
                w.writerow([i, f"{qa}. {A['title_en']}", f"{qb}. {B['title_en']}", "", tradeoff_text(A, ans[qa], B, ans[qb])])
    ranking = qm.match(ans, mult=mult)
    out = [f"# Quiz result with explanations", "",
           f"_Answers file: `{os.path.basename(f)}`. Answered: {sum(1 for v in ans.values() if v != 'dk')}, “don't know”: "
           f"{sum(1 for v in ans.values() if v == 'dk')}. Trade-off questions: "
           f"{'applied, ' + ', '.join(f'#{q} ×{m:g}' for q, m in mult.items()) if mult else ('not filled in — `' + os.path.basename(tf) + '`')}. "
           f"How closeness is computed — `docs/QUIZ_MATCHING.md`._", "",
           "## Result", "", "| Rank | List | Closeness | Note |", "|---|---|---|---|"]
    place = 0
    for r in ranking:
        if r["closeness"] is None: continue
        ranked = r["coverage"] >= qm.MIN_COVERAGE
        place += ranked
        out.append(f"| {place if ranked else '—'} | {r['list']} | {r['closeness']:+.2f} | {r['note']} |")
    ne = [r["list"] for r in ranking if r["closeness"] is None]
    out += ["", f"**No record in the Knesset ({len(ne)}):** " + "; ".join(ne) + ".", "",
            "How to read the breakdown below:",
            "- “your answer” — your position on the statement;",
            "- “the list is for / against the statement” — whether its former MKs pushed that side more or less than the average MK;",
            "- “✓ / ✗” next to a bill — whether it moves things the same way as your answer or the opposite way.", ""]
    shown = [r for r in ranking if r["closeness"] is not None and r["coverage"] >= qm.MIN_COVERAGE][:TOP]
    for place_, r in enumerate(shown, 1):
        L = r["letters"]
        rows = contributions(ctx, L, ans, mult)
        out += [f"## {place_}. {r['list']} — closeness {r['closeness']:+.2f}", "",
                *([r["note"], ""] if r["note"] else [])]
        for head, part in (("Why it fits — what added points", [x for x in rows if x[0] > 0][:PER]),
                           ("Why it doesn't fit — what took points away", [x for x in rows[::-1] if x[0] < 0][:PER])):
            out += [f"### {head}", ""]
            for contrib, q, a, u, p in part:
                lines, ev = explain(ctx, L, q, a, p, contrib, mult)
                out.append(f"**{q['title_en']}**  ")
                out += [x + "  " for x in lines]
                line = lambda *e: bill_line(ctx, q, *e)
                for _, _, b, s, role, authors, same in ev[:3]: out.append(line(b, s, role, authors, same))
                if len(ev) > 3:   # [У] 2026-10-16: the full split of what went «+» and «−», so mixed directions are visible
                    out += ["", "<details><summary>All bills on this topic</summary>", ""]
                    for head_, flag in (("Your way", True), ("The other way", False)):
                        part_ = [e for e in ev if e[6] == flag]
                        out.append(f"**{head_} ({len(part_)}):**")
                        out += [line(b, s, role, authors, same) for _, _, b, s, role, authors, same in part_] or ["- none"]
                        out.append("")
                    out.append("</details>")
                out.append("")
    path = os.path.join(qm.Q, "report_" + os.path.splitext(os.path.basename(f))[0] + ".md")
    open(path, "w").write("\n".join(out) + "\n")
    print(path)

if __name__ == "__main__":
    main(sys.argv[1])
