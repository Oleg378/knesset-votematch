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
import texts as T

ROOT, LAB = qm.ROOT, os.path.join(qm.ROOT, "jef/directions/labels")
SGN = {"+": 1, "−": -1, "-": -1}
LINK = "https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid={}"
TOP, PER = 10, 5   # [У] 2026-10-17: топ-10 списков, у каждого «почему подходит» и «почему не подходит»
CLOSE = 0.2   # [У] 2026-10-18 (after external audit №2): |p| below this — «shows no clear position». With the O signal the side of
              # positions >= 0.2 agrees between K24 and K25 in 79 % of pairs, below 0.2 in 35 % (threshold_stability.py). 0.3 was dropped:
              # it is above the ceiling of the O signal (0.25), so a stance expressed only by votes could never be clear (audit №2, К1).
MIN_CLEAR_MKS, MIN_CLEAR_BILLS = 2, 2   # [У] 2026-10-18 (audit №2, С2): a clear position also needs >= 2 former MKs and >= 2 distinct
                                        # bills (sponsored or voted, by name) behind it — one MK or one bill is not a position

def is_clear(p, n_mk, n_names):
    """One rule for «the list has a clear position» — explanations and the core filter."""
    return abs(p) >= CLOSE and n_mk >= MIN_CLEAR_MKS and n_names >= MIN_CLEAR_BILLS
EPS = 1e-9
TX = T.load()   # user-facing texts: export/quiz_texts.json (export/WEB_CONTRACT.md §7), the same templates as the web
ANS = {int(k): v for k, v in TX["answers"].items()}   # [У] 2026-10-18: the same words as the UI buttons

def labels():
    """The production labels (pipeline/labels.py: both split stages, point overrides, technical bills out, relevance filter as
    configured there) in the shape used here: bill id (str) -> {"main": [...], "sec": [...]}."""
    return {str(b): {"main": [dict(t) for t in m], "sec": [dict(t) for t in s_]} for b, (m, s_) in L.load()["bill_lab"].items()}

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
    nv, no, ng = {}, {}, {}
    for r in csv.DictReader(open(os.path.join(qm.POS, "list_topic_positions.csv"))):
        nv[(r["letters"], r["d"])] = int(r["sum_nV"]); no[(r["letters"], r["d"])] = int(r.get("sum_nO") or 0); ng[(r["letters"], r["d"])] = int(r.get("sum_nG") or 0)
    dir_en = {d["key"]: d["name_en"] for d in json.load(open(os.path.join(ROOT, "jef/directions/merge3/directions_final.json")))}
    for p in [json.load(open(os.path.join(ROOT, "jef/directions/split/plan.json")))] + L.later_plans():   # all split stages (labels.LATER)
        dir_en.update({k: v["name_en"] for k, v in p["new"].items()})
    return dict(st=st, pos=pos, cov=cov, info=info, init=init, cand=cand, by_d=by_d, nv=nv, no=no, ng=ng, dir_en=dir_en,
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

def explain(ctx, L, q, a, p, contrib, mult=None):
    """[У] 2026-10-17: one explained statement in plain words — the statement as shown in the quiz, the user's answer, the
    list's side (by sign; «has no clear position» when |p| < CLOSE, п. 6), the basis (the list's ex-MKs' bills split by
    direction and their votes) and one caveat: the side comes from votes when the list's own bills give nothing or the other
    side (п. 7). [У] 2026-10-18: the caveat «positions are relative to the average MK» is gone — authorship is no longer centered."""
    ev = evidence(ctx, L, q, a / 2 * q["key_s"], contrib)
    n_same = sum(1 for e in ev if e[6]); n_opp = len(ev) - n_same
    nvotes = ctx["nv"].get((L, q["d"]), 0); nother = ctx["no"].get((L, q["d"]), 0); ngov = ctx["ng"].get((L, q["d"]), 0)
    x = ctx["pos"][L][q["d"]]
    close = not is_clear(p, x[2], x[4])
    toward = not close and p * q["key_s"] > 0
    # [У] 2026-10-18 (Р4а, external audit К2): say what was measured — what the list's former MKs pushed for with their bills and
    # votes — not that the list accepts the statement, whose «even if» price the data does not measure.
    E = TX["explain"]
    side = E["sideNoClear"] if close else E["sideFor"] if toward else E["sideAgainst"]
    # [У] 2026-10-22: G — votes on the coalition's own government bills (named only when the list has any)
    votes = T.fill(E["votes"], votes=nvotes, other=nother, gov=T.fill(E["votesGov"], gov=ngov) if ngov else "")
    lines = [T.fill(E["quote"], text=q["statement_en"]),
             T.fill(E["answer"], answer=ANS[a], side=side),
             (T.fill(E["basis"], bills=len(ev), same=n_same, opp=n_opp, votes=votes) if ev
              else T.fill(E["basisVotesOnly"], votes=votes))]
    if (mult or {}).get(q["q"], 1) != 1: lines.append(E["weight"])
    P, P_A = ctx["pos"][L][q["d"]][0], ctx["pos"][L][q["d"]][3]
    by_votes = bool(ev) and (abs(P_A) <= EPS or (P_A > 0) != (P > 0))   # own bills give nothing or the other side
    if close: pass
    elif by_votes:
        lines.append(E["caveatByVotes"])
    if toward:
        lines.append(E["caveatPrice"])
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
           f"How closeness is computed — `docs/TECHNICAL.md`._", "",
           "## Result", "", "| Rank | List | Closeness | Note |", "|---|---|---|---|"]
    place = 0
    for r in ranking:
        if r["closeness"] is None: continue
        ranked = r["ranked"]
        place += ranked
        out.append(f"| {place if ranked else '—'} | {r['list']} | {r['closeness']:+.2f} | {r['note']} |")
    ne = [r["list"] for r in ranking if r["closeness"] is None]
    out += ["", f"**No record in the Knesset ({len(ne)}):** " + "; ".join(ne) + ".", "",
            "How to read the breakdown below:",
            "- “your answer” — your position on the statement;",
            "- “the list is for / against the statement” — which side its former MKs pushed with the bills they sponsored and, with less weight, their votes;",
            "- “✓ / ✗” next to a bill — whether it moves things the same way as your answer or the opposite way.", ""]
    shown = [r for r in ranking if r["ranked"]][:TOP]
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
