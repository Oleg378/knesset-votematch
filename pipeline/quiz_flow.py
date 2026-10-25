"""Order of questions: core -> clarifying -> trade-offs (customer's idea, 2026-10-18 [У]; selection rules [У] 2026-10-21 after the
customer's pilot in chat — research in local/research/flow_models/REPORT.md).

The quiz does not ask every statement. It asks
  1. CORE      — the same N statements for everyone: markers of the main axes of the list × statement matrix, weighted by
                 interest, from different areas and not two of one «same question for the voter» group;
  2. CLARIFY   — statements chosen one at a time after each answer: the one that best separates the current leader from the
                 lists close behind it («contending pair»), among statements on which the compared lists stand on both sides;
  3. TRADE     — up to N trade-off questions (quiz_match.tradeoffs, unchanged).
After that the user may answer more (MORE: clarifying questions continue until the pool is exhausted).
Matching itself is unchanged (quiz_match.match): closeness is computed over whatever was answered.

All parameters are in FLOW (now 8 + 7 + up to 5 trade-offs). The export carries FLOW, so the web reads the same numbers.
Statement metadata (data/quiz/statement_meta.csv, one row per statement; new statements get theirs in the new-statements procedure):
  interest   1–5, how much an ordinary voter cares (mean of two blind agent ratings; used only for the ORDER of questions);
  area       one of 13 broad areas (two blind agent runs + tie-break);
  sim_group  statements that feel like one question to a voter (pairs on which two blind groupings agree); empty = none.

Definitions (lists = evaluated lists, status ok; p = the list's position on the statement's direction, quiz_match.list_vec):
  axes          SVD of the lists × statements matrix (missing positions = 0, columns centred); loading L[k][q] of statement q on
                axis k (unit rows); purity = L[k][q]² / Σ_k L[k][q]² over the first `core_axes` axes;
  core score    L[k][q]² × purity × (interest / 5) ** interest_alpha, per axis; slots per axis `core_slots`, asked interleaved;
  core filters  (same as before) two-sided among clear positions, one statement per direction, at most core_gov_share of the
                core on the government axis; (new) interest >= core_min_interest, at most core_area_cap per area, no two of one
                sim_group, |r| of list values < core_r_max with a statement already chosen;
  clarifying    leader = first ranked list with status ok; contenders = the next ranked ok lists (at most clarify_top − 1)
                whose closeness is within pair_gap of the leader's, else the runner-up alone;
                score(q) = Σ_contenders |p_leader − p_contender| / (gap + pair_eps) × (interest / 5) ** interest_alpha over
                candidates with a leader position; ties -> lower statement number;
  candidates    not shown yet; minus any statement in the sim_group of a shown one; minus (if possible) the area of the previous
                question and |r| >= near_dup_r with a shown one; minus (if possible) statements on which the top clarify_top
                ranked lists do not have clear positions on both sides (the core's two-sided rule, applied locally);
                before any ranking exists: the largest SD of p over all evaluated lists.

Usage: python3 pipeline/quiz_flow.py            print the core and, for a demo, the first clarifying question after it
"""
import csv, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quiz_match as qm
from quiz_report import is_clear   # «clear position»: one rule for explanations and the core / clarifying filters

META = os.path.join(qm.Q, "statement_meta.csv")

FLOW = {
    "core": 8,            # [У] 2026-10-18: 8 core + 7 clarifying (local/research/scripts/flow_core_clar.py)
    "clarify": 7,
    "trade": 5,           # at most; asked only if it can change the top 5 (quiz_match.tradeoffs)
    # core [У] 2026-10-21 (local/research/flow_models/REPORT.md, «K2c + A + F»)
    "core_axes": 4,           # axes of the SVD used for loadings and purity
    "core_slots": [4, 3, 1],  # core statements per axis (axis 1, 2, 3)
    "core_r_max": 0.8,        # core statements must not repeat each other's list order
    "core_gov_share": 0.5,    # [У] 2026-10-18: at most half of the core on the government axis
    "gov_r": 0.8,             # as quiz_select.GOV_R
    "core_min_interest": 3,   # interest floor for the core
    "core_area_cap": 1,       # at most one core statement per area
    "core_one_sided": False,  # [У] 2026-10-18 (external audit К2): one-sided statements are not in the core
    "interest_alpha": 2,      # interest weight: score × (interest / 5) ** alpha, core and clarifying
    # clarifying [У] 2026-10-21 («U3 + C + I2 + S + F»)
    "clarify_top": 4,         # lists compared: the leader and up to clarify_top − 1 contenders; the two-sided filter uses the top clarify_top
    "pair_gap": 0.1,          # a list is a contender if its closeness is within pair_gap of the leader's
    "pair_eps": 0.05,         # weight of a contender = 1 / (gap + pair_eps)
    "near_dup_r": 0.9,        # a candidate with |r| >= near_dup_r to a shown statement is skipped (if anything else is left)
    "same_area_in_row": False,   # the previous question's area is skipped (if anything else is left)
    "sim_groups": True,       # no two statements of one sim_group among the shown ones
    # stopping rule (2026-10-18; off): with stop_gap set, clarifying questions go on until the leader's closeness exceeds the
    # second list's by stop_gap (after at least min_questions), or max_questions are asked; with stop_gap None the fixed number is used.
    "stop_gap": None,
    "min_questions": 10,
    "max_questions": 30,
}

def load_meta():
    if not os.path.exists(META): return {}
    return {r["q"]: {"interest": float(r["interest"]), "area": r["area"], "sim_group": r["sim_group"]} for r in csv.DictReader(open(META))}

def _ctx(k=qm.K, flow=FLOW):
    """Everything the selectors need, computed once: positions, clear flags, axes, pairwise |r|, metadata."""
    st, pos, cov = qm.load()
    ok = [l for l, c in cov.items() if c["status"] == "ok"]
    vec = {l: qm.list_vec(st, pos, l, k) for l, c in cov.items() if c["status"] != "not_evaluated"}   # ranked lists incl. warning
    gov = {r["letters"]: float(r["share_with_gov"]) for r in csv.DictReader(open(os.path.join(qm.POS, "government_layer_list.csv")))
           if r["knesset"] == "25"}
    meta = load_meta()
    qs = [r["q"] for r in st]; qi = {q: i for i, q in enumerate(qs)}
    P = np.full((len(ok), len(qs)), np.nan); clear = np.zeros(P.shape, bool)
    for i, l in enumerate(ok):
        for j, r in enumerate(st):
            x = pos.get(l, {}).get(r["d"])
            if x: P[i, j] = vec[l][r["q"]]; clear[i, j] = is_clear(x[0], x[2], x[4])
    has = ~np.isnan(P); P0 = np.where(has, P, 0.0)
    Mc = P0 - P0.mean(0)
    axes = np.linalg.svd(Mc, full_matrices=False)[2][:flow["core_axes"]]
    g = np.array([gov[l] for l in ok])
    two_sided = np.zeros(len(qs), bool); on_gov = np.zeros(len(qs), bool)
    for j in range(len(qs)):
        c = P[clear[:, j], j]
        two_sided[j] = len(c) > 0 and (c > 0).any() and (c < 0).any()
        m = has[:, j]
        on_gov[j] = m.sum() >= 3 and np.std(P[m, j]) > 0 and abs(np.corrcoef(P[m, j], g[m])[0, 1]) >= flow["gov_r"]
    R = np.zeros((len(qs), len(qs)))
    for a in range(len(qs)):
        for b in range(a + 1, len(qs)):
            m = has[:, a] & has[:, b]
            if m.sum() >= 3 and np.std(P[m, a]) > 0 and np.std(P[m, b]) > 0:
                R[a, b] = R[b, a] = abs(np.corrcoef(P[m, a], P[m, b])[0, 1])
    return {"st": st, "ok": ok, "vec": vec, "gov": gov, "meta": meta, "qs": qs, "qi": qi, "P": P, "has": has, "clear": clear,
            "axes": axes, "two_sided": two_sided, "on_gov": on_gov, "R": R, "d": [r["d"] for r in st], "ok_i": {l: i for i, l in enumerate(ok)}}

def _interest(ctx, q, default=3.0):
    return ctx["meta"].get(q, {}).get("interest", default)

def _iw(ctx, q, flow):
    return (_interest(ctx, q) / 5) ** flow["interest_alpha"] if flow["interest_alpha"] and ctx["meta"] else 1.0

def _same_group(ctx, q1, q2):
    m = ctx["meta"]; g = m.get(q1, {}).get("sim_group")
    return bool(g) and g == m.get(q2, {}).get("sim_group")

def core(flow=FLOW, ctx=None):
    """The core statements, in the order they are asked (axes interleaved: axis 1, axis 2, axis 3, axis 1, ...)."""
    ctx = ctx or _ctx(flow=flow)
    qs, L = ctx["qs"], ctx["axes"]
    pur = L ** 2 / (L ** 2).sum(0, keepdims=True).clip(1e-9)
    iw = np.array([_iw(ctx, q, flow) for q in qs])
    chosen, ngov, per_axis = [], 0, []
    cap_gov = int(flow["core"] * flow["core_gov_share"])
    def ok(j):
        q = qs[j]
        if not flow["core_one_sided"] and not ctx["two_sided"][j]: return False
        if ctx["has"][:, j].sum() < 2: return False
        if ctx["d"][j] in {ctx["d"][c] for c in chosen}: return False
        if ctx["meta"] and _interest(ctx, q, 5) < flow["core_min_interest"]: return False
        if flow["core_area_cap"] and ctx["meta"]:
            area = ctx["meta"].get(q, {}).get("area")
            if sum(ctx["meta"].get(qs[c], {}).get("area") == area for c in chosen) >= flow["core_area_cap"]: return False
        if flow["sim_groups"] and any(_same_group(ctx, q, qs[c]) for c in chosen): return False
        if ctx["on_gov"][j] and ngov >= cap_gov: return False
        if any(ctx["R"][j, c] >= flow["core_r_max"] for c in chosen): return False
        return True
    for k, slots in enumerate(flow["core_slots"]):
        score = L[k] ** 2 * pur[k] * iw
        taken = []
        for j in np.argsort(-score):
            if len(taken) >= slots: break
            if not ok(j): continue
            chosen.append(j); taken.append(j); ngov += bool(ctx["on_gov"][j])
        per_axis.append(taken)
    out = []
    while any(per_axis):
        for taken in per_axis:
            if taken: out.append(taken.pop(0))
    return [qs[j] for j in out[:flow["core"]]]

def should_stop(answers, n_asked, flow=FLOW, mult=None):
    """True when no more clarifying questions are needed. n_asked: core + clarifying statements shown so far."""
    if flow["stop_gap"] is None: return n_asked >= flow["core"] + flow["clarify"]
    if n_asked >= flow["max_questions"]: return True
    if n_asked < flow["min_questions"]: return False
    rows = [r for r in qm.match(answers, mult=mult) if r["closeness"] is not None and r["closeness"] == r["closeness"]
            and r["coverage"] >= qm.MIN_COVERAGE]
    return len(rows) > 1 and rows[0]["closeness"] - rows[1]["closeness"] >= flow["stop_gap"]

def _ranked(answers, mult):
    """Ranked lists in order with their closeness (quiz_match.match: the same rule as the results screen)."""
    return [(r["letters"], r["closeness"]) for r in qm.match(answers, mult=mult) if r["ranked"]]

def next_clarify(answers, asked, flow=FLOW, mult=None, ctx=None):
    """The next clarifying statement, or None when the pool is exhausted.
    asked: statements already shown (answered or skipped), in the order shown — a list; a set works too, but then the rule
    «not the previous question's area» cannot apply (no order)."""
    ctx = ctx or _ctx(flow=flow)
    qs, qi, P, has, clear, meta = ctx["qs"], ctx["qi"], ctx["P"], ctx["has"], ctx["clear"], ctx["meta"]
    shown = list(asked) if not isinstance(asked, (set, frozenset)) else sorted(asked, key=int)
    shown_i = [qi[q] for q in shown if q in qi]
    cand = [j for j in range(len(qs)) if qs[j] not in asked]
    if flow["sim_groups"] and meta:
        cand = [j for j in cand if not any(_same_group(ctx, qs[j], qs[c]) for c in shown_i)] or cand
    if shown_i and meta:   # not the previous question's area, and no near-duplicate of a shown statement; relaxed if nothing is left
        last = meta.get(shown[-1], {}).get("area") if not isinstance(asked, (set, frozenset)) and not flow["same_area_in_row"] else None
        far = lambda j: all(ctx["R"][j, c] < flow["near_dup_r"] for c in shown_i)
        c1 = [j for j in cand if meta.get(qs[j], {}).get("area") != last and far(j)]
        cand = c1 or [j for j in cand if meta.get(qs[j], {}).get("area") != last] or cand
    ranked = _ranked(answers, mult) if any(v != "dk" for v in answers.values()) else []
    top = [l for l, _ in ranked[:flow["clarify_top"]] if l in ctx["ok_i"]]
    if len(top) >= 2:   # two-sided among the compared lists (the core's rule, applied locally); relaxed if nothing is left
        rows = [ctx["ok_i"][l] for l in top]
        c2 = [j for j in cand if (lambda c: bool(c) and any(x > 0 for x in c) and any(x < 0 for x in c))([P[i, j] for i in rows if clear[i, j]])]
        cand = c2 or cand
    if not cand: return None
    ok_ranked = [(l, c) for l, c in ranked if l in ctx["ok_i"]]
    score = np.full(len(qs), -np.inf)
    if len(ok_ranked) >= 2:   # contending pair
        (lead, c0), rest = ok_ranked[0], ok_ranked[1:flow["clarify_top"]]
        cont = [(l, c) for l, c in rest if c0 - c < flow["pair_gap"]] or rest[:1]
        li = ctx["ok_i"][lead]
        for j in cand:
            if not has[li, j]: continue
            s = sum(abs(P[li, j] - P[ctx["ok_i"][l], j]) / (c0 - c + flow["pair_eps"]) for l, c in cont if has[ctx["ok_i"][l], j])
            if s > 0: score[j] = s
    else:   # no ranking yet: the statement on which all evaluated lists differ most
        for j in cand:
            v = P[has[:, j], j]
            if len(v) >= 2: score[j] = float(np.std(v))
    for j in cand:
        if np.isfinite(score[j]) and score[j] > 0: score[j] *= _iw(ctx, qs[j], flow)
    best = max(cand, key=lambda j: (score[j], -int(qs[j])))
    return qs[best] if np.isfinite(score[best]) else None

if __name__ == "__main__":
    ctx = _ctx()
    title = {r["q"]: r["title_en"] for r in ctx["st"]}
    c = core(ctx=ctx)
    print(f"FLOW {FLOW}\ncore ({len(c)}): " + "; ".join(f"q{q} {title[q]}" for q in c))
    nq = next_clarify({}, list(c), ctx=ctx)
    print(f"first clarifying question with no answers yet (all lists compared): q{nq} {title.get(nq)}")
