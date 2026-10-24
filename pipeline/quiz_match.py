"""Quiz matching: user answers -> closeness to 2026 lists (decision of the customer, 2026-10-17; docs/TECHNICAL.md).

Answer scale: 2 полностью согласен, 1 скорее согласен, 0 нейтрально, -1 скорее не согласен, -2 полностью не согласен,
"dk" не знаю (skipped). User value on a statement u = answer/2 × key (key «+» = +1, «−» = −1).
List value p = the list's position P on the statement's direction (data/positions/list_topic_positions.csv), shrunk toward 0:
p = P × e/(e + K), e = sum_nA + 0.25·(sum_nV + sum_nO + sum_nG) (the evidence behind P, same weights as the position); K = 0: p = P.
Weight w = 1, or 1/2 for each statement of an a/b pair on the same direction.
Closeness = cosine over statements the user answered and the list has a position on:
  Σ w·u·p / sqrt(Σ w·u²) / sqrt(Σ w·p²); with the share of answered weight covered by the list.
Output: lists sorted by closeness; evaluated lists (status ok / warning) with the number of ex-MKs behind the position;
lists without ex-MKs are listed as «нет данных о работе в Кнессете».

Usage: python3 pipeline/quiz_match.py local/jef/quiz/pilot_answers_filled.csv   filled pilot sheet: № (statement q), Тема, Утверждение, Ответ
                                                                   (2 / 1 / 0 / -1 / -2 / нз; empty = не отвечено)
       python3 pipeline/quiz_match.py answers.json                  {"<№>": 2 | 1 | 0 | -1 | -2 | "dk"}
       python3 pipeline/quiz_match.py --calibrate         choose K on synthetic users (writes local/research/match_calibration.txt; decided K = 0)
"""
import csv, json, os, random, re, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texts as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "data/quiz")
POS = os.path.join(ROOT, "data/positions")
MIN_COVERAGE = 0.5   # [А]
MIN_EX_MKS = 2       # [У] 2026-10-18 (Р3, external audit С3): a list resting on one former MK is shown, but not ranked
MAX_TRADE, TRADE_TOP, TRADE_W = 5, 5, 2.0   # [У] 2026-10-16: trade-off questions (Wahl-O-Mat / StemWijzer convention: ×2)
K = 0.0   # [У] 2026-10-18: no shrinkage — persona recovery (local/research/scripts/k_persona.py) and the cross-Knesset weight test both
          # are best at 0; the random-answer «first places» criterion is dropped (it measures list clusters, not K)

def load():
    st = [r for r in csv.DictReader(open(os.path.join(Q, "statements.csv"))) if r["status"] == "ok"]
    per_d = collections.Counter(r["d"] for r in st)
    for r in st:
        r["key_s"] = 1 if r["agree_key"] == "+" else -1
        r["w"] = 1 / per_d[r["d"]]
    pos = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(POS, "list_topic_positions.csv"))):
        e = float(r["sum_nA"]) + 0.25 * (float(r["sum_nV"]) + float(r.get("sum_nO") or 0) + float(r.get("sum_nG") or 0))   # O: other camp's bills (2026-10-18); G: own camp's government bills (2026-10-22)
        pos[r["letters"]][r["d"]] = (float(r["P"]), e, int(r["n_mk"]), float(r["P_A"]), int(r.get("n_names") or 0))   # P_A: own bills; n_names: distinct bills
    cov = {r["letters"]: r for r in csv.DictReader(open(os.path.join(POS, "list_coverage.csv")))}
    return st, pos, cov

def list_vec(st, pos, letters, k):
    v = {}
    for r in st:
        x = pos.get(letters, {}).get(r["d"])
        if x: v[r["q"]] = x[0] if k == 0 else x[0] * x[1] / (x[1] + k)
    return v

def score(st, answers, lv, mult=None):
    num = uu = pp = wa = wc = 0.0
    for r in st:
        a = answers.get(r["q"])
        if a is None or a == "dk": continue
        u = a / 2 * r["key_s"]; w = r["w"] * (mult or {}).get(r["q"], 1); wa += w
        if r["q"] not in lv: continue
        p = lv[r["q"]]; wc += w
        num += w * u * p; uu += w * u * u; pp += w * p * p
    cos = num / np.sqrt(uu * pp) if uu > 0 and pp > 0 else float("nan")
    return cos, (wc / wa if wa else 0.0)

def few_mks_note(N, n):
    """The note of a list with status warning (fewer than 3 former MKs in its top ten), by its number of former MKs."""
    return N["oneMk"] if n == 1 else N["twoMks"] if n == 2 else N["fewInTopTen"]

def match(answers, k=K, mult=None):
    st, pos, cov = load()
    N = T.load()["notes"]   # user-facing notes: export/quiz_texts.json (export/WEB_CONTRACT.md §7), the same templates as the web
    rows = []
    for letters, c in cov.items():
        if c["status"] == "not_evaluated":
            rows.append({"letters": letters, "list": c["list_name"], "status": c["status"], "closeness": None, "coverage": 0,
                         "ex_mks": 0, "note": N["noRecord"]}); continue
        cos, cv = score(st, answers, list_vec(st, pos, letters, k), mult)
        rows.append({"letters": letters, "list": c["list_name"], "status": c["status"], "closeness": cos, "coverage": cv,
                     "ex_mks": int(c["ex_mks"]), "note": few_mks_note(N, int(c["ex_mks"])) if c["status"] == "warning" else ""})
    for r in rows:   # [А] a list whose positions cover less than half of the answered weight is not ranked with the others
        if r["closeness"] is not None and r["coverage"] < MIN_COVERAGE:
            r["note"] = (r["note"] + N["join"] if r["note"] else "") + T.fill(N["lowCoverage"], pct=f"{r['coverage']:.0%}")
    for r in rows: r["ranked"] = is_ranked(r)
    rows.sort(key=lambda r: (not r["ranked"], r["closeness"] is None, -(r["closeness"] if r["ranked"] else 0)))
    return rows

def is_ranked(r):
    """One rule for every place that ranks lists: a closeness exists, the list's positions cover >= MIN_COVERAGE of the answers,
    and the list has >= MIN_EX_MKS former MKs."""
    return (r["closeness"] is not None and r["closeness"] == r["closeness"] and r["coverage"] >= MIN_COVERAGE
            and r["ex_mks"] >= MIN_EX_MKS)

def ranked_top(answers, n, mult=None):
    return [r["letters"] for r in match(answers, mult=mult) if r["ranked"]][:n]

def tradeoffs(answers, mult=None, exclude=(), skip_lists=()):
    """[У] 2026-10-16. Trade-off questions: at most MAX_TRADE, each only if it can change the top TRADE_TOP.
    For each list in the current top (in rank order) the pair is: the statement that added it the most points (the list is with
    the user) vs the one that took the most (the list is against the user); next-best statements are tried if the best pair
    cannot change the top. One pair per list. A pair is asked if doubling either side's weight changes the order of the top TRADE_TOP.
    The answer «A важнее» / «Б важнее» multiplies that statement's weight by TRADE_W for all lists; «одинаково» changes nothing."""
    st, pos, _ = load()
    mult = dict(mult or {})
    base = ranked_top(answers, TRADE_TOP, mult)
    used, out = set(exclude), []   # exclude: statements already used in earlier trade-off questions
    for L in base:
        if L in skip_lists: continue   # one question per list: lists already asked about are not asked again
        lv = list_vec(st, pos, L, K)
        rows = []
        for r in st:
            a = answers.get(r["q"])
            if a in (None, "dk", 0) or r["q"] not in lv: continue
            rows.append((r["w"] * a / 2 * r["key_s"] * lv[r["q"]], r["q"]))
        plus = [q for c, q in sorted(rows, reverse=True) if c > 0 and q not in used][:3]
        minus = [q for c, q in sorted(rows) if c < 0 and q not in used][:3]
        for qa in plus:
            hit = None
            for qb in minus:
                if any(ranked_top(answers, TRADE_TOP, {**mult, q: mult.get(q, 1) * TRADE_W}) != base for q in (qa, qb)):
                    hit = qb; break
            if hit:
                out.append((qa, hit, L)); used |= {qa, hit}; break
        if len(out) >= MAX_TRADE: break
    return out

def read_tradeoffs(f):
    """Filled trade-off sheet: №, A, Б, Ответ (А / Б / =) -> weight multipliers."""
    mult = {}
    for row in csv.reader(open(f)):
        if len(row) < 4 or not row[0].strip().isdigit(): continue
        a = row[3].strip().upper().replace("A", "А").replace("B", "Б")
        qa, qb = row[1].split(".")[0].strip(), row[2].split(".")[0].strip()
        if a == "А": mult[qa] = mult.get(qa, 1) * TRADE_W
        elif a == "Б": mult[qb] = mult.get(qb, 1) * TRADE_W
    return mult

def calibrate():
    """K is chosen on synthetic users. (1) Persona recovery: a user who answers like list L (sign of L's raw position,
    strength by |P|, 20% of answers flipped, 20% «не знаю») — how often is L in the top 3. (2) Neutrality: users with random
    answers — the largest share of first places taken by one list (should be close to 1/12)."""
    st, pos, cov = load()
    ev = [l for l, c in cov.items() if c["status"] == "ok"]
    rnd = random.Random(20261017)
    out = []
    for k in (0, 2, 5, 10, 20, 50):
        vecs = {l: list_vec(st, pos, l, k) for l in ev}
        rec = []
        for _ in range(40):
            for l in ev:
                ans = {}
                for r in st:
                    x = pos[l].get(r["d"])
                    if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
                    s = np.sign(x[0]) * r["key_s"] * (2 if abs(x[0]) > 0.5 else 1)
                    ans[r["q"]] = int(-s if rnd.random() < 0.2 else s)
                ranked = sorted(ev, key=lambda m: -np.nan_to_num(score(st, ans, vecs[m])[0], nan=-9))
                rec.append(l in ranked[:3])
        first = collections.Counter()
        for _ in range(500):
            ans = {r["q"]: rnd.choice([-2, -1, 0, 1, 2]) for r in st}
            first[max(ev, key=lambda m: np.nan_to_num(score(st, ans, vecs[m])[0], nan=-9))] += 1
        out.append((k, np.mean(rec), max(first.values()) / 500, first.most_common(3)))
    lines = ["K | персона в топ-3 | макс. доля первых мест при случайных ответах | лидеры"]
    lines += [f"{k} | {r:.3f} | {m:.3f} | {f}" for k, r, m, f in out]
    os.makedirs(os.path.join(ROOT, "local/research"), exist_ok=True)
    open(os.path.join(ROOT, "local/research/match_calibration.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    if sys.argv[1] == "--calibrate": calibrate()
    else:
        f = sys.argv[1]
        if f.endswith(".csv"):
            answers = {}
            for row in csv.reader(open(f)):
                if not row or not row[0].strip().isdigit(): continue
                a = row[3].strip().lower().replace("−", "-") if len(row) > 3 else ""
                if a in ("нз", "dk", "?"): answers[row[0].strip()] = "dk"
                elif re.fullmatch(r"-?[0-2]", a): answers[row[0].strip()] = int(a)
        else:
            answers = json.load(open(f))
        print(f"ответов: {sum(1 for v in answers.values() if v not in (None, 'dk'))}, «не знаю»: {sum(1 for v in answers.values() if v == 'dk')}")
        for r in match(answers):
            c = "—" if r["closeness"] is None else f"{r['closeness']:+.2f}"
            print(f"{c:>6}  {r['list'][:55]:55}  бывших депутатов {r['ex_mks']:2}  покрытие {r['coverage']:.0%}  {r['note']}")
