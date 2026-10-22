"""Terminal quiz (no UI yet): start -> core questions -> clarifying questions -> trade-off questions -> leaderboard
(-> more questions) -> list details -> leaderboard.

Same computation as pipeline/quiz_match.py and pipeline/quiz_report.py (docs/TECHNICAL.md):
  - question order [У] 2026-10-18 (pipeline/quiz_flow.py, parameters in quiz_flow.FLOW): the core statements (the same for
    everyone), then clarifying ones chosen one at a time from the answers so far, then trade-offs; «m» on the results screen
    asks more clarifying questions; --all asks every statement in file order (the old flow);
  - regular questions: the quiz statements in English (jef/quiz/statements_v4.csv, title_en / statement_en), answers
    2 / 1 / 0 / -1 / -2 / ? (don't know); [У] 2026-10-17: the product language is English, bill names stay in Hebrew;
  - trade-off questions [У 2026-10-16]: up to 5, asked one at a time, each only if it can change the top 5; the chosen statement
    gets weight ×2, «=» (equally) changes nothing; every next pair is searched with the weights already chosen;
  - leaderboard: all lists by closeness with notes; lists below the coverage threshold and lists without ex-MKs below
    ([У] 2026-10-17: the government layer is not shown, so it does not bias the reader);
  - list details: why it fits (statements that added points) and why not (that took points); any statement opens all bills
    of the list's ex-MKs on its direction, split into «same way as your answer» and «the opposite way».
The session (answers, trade-offs, weights) is saved to jef/quiz/sessions/<time>.json.

Usage: python3 pipeline/quiz_cli.py                                   core + clarifying + trade-offs
       python3 pipeline/quiz_cli.py --all                             every statement (old flow)
       python3 pipeline/quiz_cli.py --answers local/jef/quiz/pilot_answers_filled.csv   prefill regular answers (pilot sheet or session json)
"""
import argparse, datetime, json, os, re, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quiz_match as qm
import quiz_report as qr
import quiz_flow as qf

W = 100
SHOW = 5   # statements per section in list details before «a» (all)

def say(s=""):
    print("\n".join(textwrap.fill(x, W) if x else "" for x in s.split("\n")))

def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print(); sys.exit(0)

def parse_answer(s):
    s = s.lower().replace("−", "-").replace("+", "")
    if s in ("?", "dk", "нз"): return "dk"
    if re.fullmatch(r"-?[0-2]", s): return int(s)
    return None

def regular(ctx, ans):
    st = ctx["st"]
    say("\nAnswer each statement: 2 — strongly agree, 1 — agree, 0 — neutral, -1 — disagree,\n"
        "-2 — strongly disagree, ? — don't know. Enter — skip, < — back, q — finish answering.")
    i = 0
    while i < len(st):
        q = st[i]
        if q["q"] in ans: i += 1; continue
        say(f"\n[{i + 1}/{len(st)}] {q['title_en']}\n{q['statement_en']}")
        s = ask("Your answer: ")
        if s == "<":
            i = max(0, i - 1); ans.pop(st[i]["q"], None); continue
        if s.lower() in ("q", "й"): break
        if s == "": i += 1; continue
        a = parse_answer(s)
        if a is None: say("Enter 2, 1, 0, -1, -2 or ?."); continue
        ans[q["q"]] = a; i += 1
    return ans

def ask_one(q, n, total):
    say(f"\n[{n}{'/' + str(total) if total else ''}] {q['title_en']}\n{q['statement_en']}")
    while True:
        s = ask("Your answer: ")
        if s == "<" or s.lower() in ("q", "й") or s == "": return s.lower()
        a = parse_answer(s)
        if a is not None: return a
        say("Enter 2, 1, 0, -1, -2 or ?.")

def flow(ctx, ans, shown, until, fctx):
    """Core statements, then clarifying ones: until="rule" — until quiz_flow.should_stop (fixed number or stopping rule, FLOW),
    until=None — until the pool ends («answer more»). shown: statements already shown, in order (answered or skipped).
    Back («<») removes the last shown statement and its answer; the next one is then recomputed."""
    say("\nAnswer each statement: 2 — strongly agree, 1 — agree, 0 — neutral, -1 — disagree, -2 — strongly disagree,\n"
        "? — don't know. Enter — skip, < — back, q — finish answering.")
    core = fctx["core"]
    fixed = qf.FLOW["stop_gap"] is None
    total = len(core) + qf.FLOW["clarify"] if until == "rule" and fixed else None
    while True:
        rest = [q for q in core if q not in shown and q not in ans]
        if rest: nq = rest[0]
        elif until == "rule" and qf.should_stop(ans, len(shown), qf.FLOW): return
        else:
            nq = qf.next_clarify(ans, list(shown) + [q for q in ans if q not in shown], ctx=fctx["ctx"])   # in order shown (area rule)
            if nq is None: say("\nNo more questions."); return
        a = ask_one(ctx["title"][nq], len(shown) + 1, total)
        if a == "<":
            if shown: ans.pop(shown.pop(), None)
            continue
        if a in ("q", "й"): return
        shown.append(nq)
        if a != "": ans[nq] = a

def exchange(ctx, ans, mult, done):
    """Trade-off questions one at a time; done = [(qa, qb, list, choice)]."""
    used = {x for d in done for x in d[:2]}
    lists = {d[2] for d in done}
    if len(done) >= qf.FLOW["trade"]: return
    first = True
    while len(done) < qf.FLOW["trade"]:
        pairs = qm.tradeoffs(ans, mult, exclude=used, skip_lists=lists)
        if not pairs: break
        qa, qb, L = pairs[0]
        if first:
            say("\nTrade-off questions. In each, suppose you could only choose between two sides: the first agrees with you on "
                "statement A but not on B; the second, the other way round. Which matters more to you? Answer: A, B or = (equally).")
            first = False
        A, B = ctx["title"][qa], ctx["title"][qb]
        say(f"\nTrade-off {len(done) + 1}\nA. “{A['statement_en']}” — your answer: {qr.ANS[ans[qa]]}.\n"
            f"B. “{B['statement_en']}” — your answer: {qr.ANS[ans[qb]]}.")
        while True:
            s = ask("A / B / = : ").upper().replace("А", "A").replace("Б", "B")
            if s in ("A", "B", "="): break
            say("Enter A, B or =.")
        if s == "A": mult[qa] = mult.get(qa, 1) * qm.TRADE_W
        elif s == "B": mult[qb] = mult.get(qb, 1) * qm.TRADE_W
        done.append((qa, qb, L, s)); used |= {qa, qb}; lists.add(L)
    if first: say("\nNo trade-off questions: none of them would change your top five.")

def leaderboard(ctx, ans, mult):
    ranking = qm.match(ans, mult=mult)
    ranked = [r for r in ranking if r["ranked"]]
    low = [r for r in ranking if r["closeness"] is not None and r not in ranked]
    none = [r for r in ranking if r["closeness"] is None]
    say("\n" + "=" * W + "\nRESULT: all lists by closeness to your answers (from −1 to +1)\n"
        f"Based on {sum(1 for v in ans.values() if v != 'dk')} answers ({len(ctx['st'])} statements in the quiz)"
        f"{', including trade-offs' if mult else ''}.\n")
    print(f"{'#':>3}  {'List':60} {'Closeness':>9}  Note")
    rows = ranked + low
    for i, r in enumerate(rows, 1):
        if low and r is low[0]: print("     Not ranked:")
        print(f"{i:>3}  {r['list'][:60]:60} {r['closeness']:+9.2f}  {r['note']}")
    say(f"\nNo record in the Knesset ({len(none)}): " + "; ".join(r["list"] for r in none) + ".")
    return rows

def details(ctx, r, ans, mult):
    L = r["letters"]
    rows = qr.contributions(ctx, L, ans, mult)
    plus = [x for x in rows if x[0] > 0]
    minus = [x for x in rows[::-1] if x[0] < 0]
    full = False
    while True:
        say("\n" + "=" * W + f"\n{r['list']} — closeness {r['closeness']:+.2f}" + (f"\n{r['note'].capitalize()}." if r["note"] else ""))
        items = []
        for head, part in ((f"WHY IT FITS — {len(plus)} matches", plus),
                           (f"WHY IT DOESN'T FIT — {len(minus)} mismatches", minus)):
            say(f"\n{head}")
            for x in (part if full else part[:SHOW]):
                c, q, a, u, p = x
                items.append(x)
                lines, _ = qr.explain(ctx, L, q, a, p, c, mult)
                print(f"\n {len(items):>2}. {q['title_en']}")
                for ln in lines: print(textwrap.fill(ln, W, initial_indent="     ", subsequent_indent="     "))
            if not full and len(part) > SHOW: print(f"\n     … {len(part) - SHOW} more (a — show all)")
        s = ask("\nNumber — bills behind a statement, a — all statements, Enter — back to results: ").lower()
        if s == "": return
        if s in ("a", "в"): full = not full; continue
        if not s.isdigit() or not 1 <= int(s) <= len(items): continue
        c, q, a, u, p = items[int(s) - 1]
        lines, ev = qr.explain(ctx, L, q, a, p, c, mult)
        say("\n" + q["title_en"]); [print(textwrap.fill(ln, W)) for ln in lines]
        for head, flag in (("Your way", True), ("The other way", False)):
            part = [e for e in ev if e[6] == flag]
            say(f"\n{head} ({len(part)}):")
            for _, _, b, sg, role, authors, same in part: print(qr.bill_line(ctx, q, b, sg, role, authors, same, link=False))
            if not part: print("- none")
        ask("\nEnter — back to the list: ")

def load_answers(f):
    if f.endswith(".json"):
        x = json.load(open(f))
        return {k: v for k, v in x.get("answers", x).items()}, x.get("mult", {}), [tuple(t) for t in x.get("tradeoffs", [])]
    return qr.read_answers(f), {}, []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", help="pilot sheet (.csv) or a saved session (.json) to prefill answers")
    ap.add_argument("--no-save", action="store_true", help="do not save the session (test runs)")
    ap.add_argument("--all", action="store_true", help="ask every statement in file order (the old flow)")
    args = ap.parse_args()
    ctx = qr.context()
    ans, mult, done = load_answers(args.answers) if args.answers else ({}, {}, [])
    say("Knesset election quiz, 27.10.2026.\nThe lists' positions come only from what their candidates who are former MKs did "
        "in the Knesset in 2021–2026: which bills they sponsored and how they voted. New faces on the lists are not visible.")
    if ask("\nEnter — start, q — quit: ").lower() in ("q", "й"): return
    fctx = None
    if args.all: regular(ctx, ans)
    else:
        c = qf._ctx(); fctx = {"ctx": c, "core": qf.core(ctx=c)}; shown = []
        flow(ctx, ans, shown, "rule", fctx)
    if not any(v != "dk" for v in ans.values()): say("No answers — nothing to compute."); return
    exchange(ctx, ans, mult, done)
    path = None
    if not args.no_save:
        os.makedirs(os.path.join(qm.Q, "sessions"), exist_ok=True)
        path = os.path.join(qm.Q, "sessions", datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
        json.dump({"answers": ans, "tradeoffs": done, "mult": mult}, open(path, "w"), ensure_ascii=False, indent=1)
    while True:
        rows = leaderboard(ctx, ans, mult)
        if path: say(f"\nAnswers saved: {os.path.relpath(path, qm.ROOT)}")
        s = ask("List number — details" + (", m — answer more questions" if fctx else "") + ", q — quit: ").lower()
        if s in ("q", "й"): return
        if s in ("m", "ь") and fctx:
            flow(ctx, ans, shown, None, fctx)
            if path: json.dump({"answers": ans, "tradeoffs": done, "mult": mult}, open(path, "w"), ensure_ascii=False, indent=1)
            continue
        if s.isdigit() and 1 <= int(s) <= len(rows): details(ctx, rows[int(s) - 1], ans, mult)

if __name__ == "__main__":
    main()
