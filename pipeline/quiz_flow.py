"""Order of questions: core -> clarifying -> trade-offs (customer's idea, 2026-10-18 [У]; the selection rules below are [А]).

The quiz no longer asks every statement. It asks
  1. CORE      — the same N statements for everyone, chosen from the data: the ones that separate the evaluated lists most,
                 from different topics (not near-duplicates of each other) and at most half on the government axis;
  2. CLARIFY   — N statements chosen one at a time after each answer: the one on which the lists closest to the user so far
                 differ most;
  3. TRADE     — up to N trade-off questions (quiz_match.tradeoffs, unchanged).
After that the user may answer more (MORE: clarifying questions continue until the pool is exhausted).
Matching itself is unchanged (quiz_match.match): closeness is computed over whatever was answered.

All parameters are in FLOW; e.g. 8 + 4 + 2 is FLOW = {**FLOW, "core": 8, "clarify": 4, "trade": 2}. The export carries FLOW,
so the web reads the same numbers.

Definitions (lists = evaluated lists, status ok; p = list position on the statement's direction after shrinkage, quiz_match):
  separation(q)  = population SD of p over the lists that have a position on q × (share of lists that have one);
  redundancy     = |r| between the list values of two statements (lists with both); a candidate is skipped if |r| >= CORE_R_MAX
                   with a statement already in the core;
  government axis = |r| between p and the list's share of votes with the government in K25 >= GOV_R (as in quiz_select.py);
  clarifying     = among statements not asked yet, the max SD of p over the top CLARIFY_TOP lists of the current ranking
                   (lists with a position; at least 2); ties -> lower statement number. Before any ranking exists, all lists.

Usage: python3 pipeline/quiz_flow.py            print the core and, for a demo, the first clarifying question after it
"""
import csv, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quiz_match as qm

FLOW = {
    "core": 5,            # [У] 2026-10-18: 5 + 5 + 5
    "clarify": 5,
    "trade": 5,           # at most; asked only if it can change the top 5 (quiz_match.tradeoffs)
    "core_r_max": 0.8,    # [А] core statements must not repeat each other's list order
    "core_gov_share": 0.5,   # [У] 2026-10-18: at most half of the core on the government axis (5 -> 2, 6 -> 3)
    "gov_r": 0.8,         # as quiz_select.GOV_R
    "clarify_top": 4,     # [А] lists compared when choosing the next clarifying question
}

def _ctx(k=qm.K):
    st, pos, cov = qm.load()
    ok = [l for l, c in cov.items() if c["status"] == "ok"]
    vec = {l: qm.list_vec(st, pos, l, k) for l, c in cov.items() if c["status"] != "not_evaluated"}   # ranked lists incl. warning
    gov = {r["letters"]: float(r["share_with_gov"]) for r in csv.DictReader(open(os.path.join(qm.POS, "government_layer_list.csv")))
           if r["knesset"] == "25"}
    return st, ok, vec, gov

def _vals(vec, lists, q):
    return [(l, vec[l][q]) for l in lists if q in vec[l]]

def _r(x, y):
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0: return 0.0
    return float(np.corrcoef(x, y)[0, 1])

def core(flow=FLOW, ctx=None):
    """The core statements, in the order they are asked (most separating first)."""
    st, ok, vec, gov = ctx or _ctx()
    rows = []
    for r in st:
        v = _vals(vec, ok, r["q"])
        if len(v) < 2: continue
        p = [x for _, x in v]
        sep = float(np.std(p)) * len(v) / len(ok)
        g = abs(_r(p, [gov[l] for l, _ in v]))
        rows.append((-sep, int(r["q"]), r["q"], r["d"], g >= flow["gov_r"]))
    out, dirs, ngov = [], set(), 0
    for _, _, q, d, on_gov in sorted(rows):
        if len(out) >= flow["core"]: break
        if d in dirs or (on_gov and ngov >= int(flow["core"] * flow["core_gov_share"])): continue
        vq = dict(_vals(vec, ok, q))
        if any(abs(_r(*zip(*[(vq[l], vec[l][c]) for l in vq if c in vec[l]]))) >= flow["core_r_max"]
               for c in out if sum(1 for l in vq if c in vec[l]) >= 3):
            continue
        out.append(q); dirs.add(d); ngov += on_gov
    return out

def next_clarify(answers, asked, flow=FLOW, mult=None, ctx=None):
    """The next clarifying statement, or None when the pool is exhausted. asked: statements already shown (answered or skipped)."""
    st, ok, vec, _ = ctx or _ctx()
    top = qm.ranked_top(answers, flow["clarify_top"], mult) if any(v != "dk" for v in answers.values()) else []
    lists = top if len(top) >= 2 else ok
    best = None
    for r in st:
        if r["q"] in asked: continue
        p = [x for _, x in _vals(vec, lists, r["q"])]
        if len(p) < 2: continue
        key = (-float(np.std(p)), int(r["q"]))
        if best is None or key < best[0]: best = (key, r["q"])
    return best[1] if best else None

if __name__ == "__main__":
    ctx = _ctx()
    title = {r["q"]: r["title_en"] for r in ctx[0]}
    c = core(ctx=ctx)
    print(f"FLOW {FLOW}\ncore ({len(c)}): " + "; ".join(f"q{q} {title[q]}" for q in c))
    nq = next_clarify({}, set(c), ctx=ctx)
    print(f"first clarifying question with no answers yet (all lists compared): q{nq} {title.get(nq)}")
