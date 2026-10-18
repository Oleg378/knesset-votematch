"""Direction on issue-specific scales for every bill whose Jev issue has an axis (local/research/direction/axes.json).

Usage: python3 local/research/scripts/jev_direction_all.py run     # -> local/research/output/direction_all.jsonl (resumable)
       python3 local/research/scripts/jev_direction_all.py text    # second signal: title + explanatory notes for every bill with notes
                                                    #    -> local/research/output/direction_text.jsonl
       python3 local/research/scripts/jev_direction_all.py check   # agreement with how the blocs voted (Knesset 25), final answers
       python3 local/research/scripts/jev_direction_all.py redo AXIS ...  # forget rows of rewritten scales, then `run` again
       python3 local/research/scripts/jev_direction_all.py sync    # after a new issue run: forget rows whose issue changed
       python3 local/research/scripts/jev_direction_all.py relevance  # applicability gate (Q21) -> local/research/output/direction_relevance.jsonl
Final answer per bill: the uniform two-signal rule (local/docs/archive/decision_registry_2026-10-12.md Q17), the same for every issue:
  both signals on the same side -> that side, reliability "high"
  one side + one unclear       -> that side, reliability "medium"
  opposite sides               -> "disputed" (manual review, never used automatically)
  both unclear                 -> "unclear"
A signal is "unclear" when its score is within 0.5 of the scale middle (1.5..2.5).
On local/research/direction/gold.csv: 56/61 decided, 54/56 correct, 3 disputed, 2 unclear.
"""
import asyncio, collections, json, os, re, sys
from typesafe_sdk import AsyncTypeSafeClient, Noul, Score
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "pipeline"))  # pipeline modules
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env, state_of

OUT = os.path.join(ROOT, "local/research/output/direction_all.jsonl")
OUT_TEXT = os.path.join(ROOT, "local/research/output/direction_text.jsonl")
OUT_REL = os.path.join(ROOT, "local/research/output/direction_relevance.jsonl")
RELEVANCE_MIN = 0.5  # Q21: direction is used only when the bill actually bears on the scale's dispute
NOTES_CHARS = 3000

def side(score):
    return 0 if abs(score - 2) < 0.5 else (1 if score > 2 else -1)

def combine(title, text, relevance=None):
    """Uniform two-signal rule (Q17) behind the applicability gate (Q21). `text` may be None (no notes)."""
    if relevance is not None and relevance < RELEVANCE_MIN:
        return {**title, "title_score": title["score"], "text_score": text["score"] if text else None,
                "relevance": relevance, "side": 0, "status": "not_applicable", "reliability": None}
    a, x = side(title["score"]), side(text["score"]) if text else 0
    if a and x and a != x:
        status, final, rel = "disputed", 0, None
    elif a or x:
        final = a or x
        status, rel = "decided", ("high" if a and x else "medium")
    else:
        status, final, rel = "unclear", 0, None
    return {**title, "title_score": title["score"], "text_score": text["score"] if text else None,
            "relevance": relevance, "side": final, "status": status, "reliability": rel}

def sync():
    """After the issue labels change: drop direction rows (title and text signals) whose bill now has a different
    issue or is no longer eligible, so `run` and `text` re-score only what changed."""
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    cur = {r["bill_id"]: r for r in map(json.loads, open(os.path.join(ROOT, "local/research/output/issues_all.jsonl")))}
    ok = lambda r: (r["bill_id"] in cur and cur[r["bill_id"]]["choice"] == r["issue"]
                    and cur[r["bill_id"]]["confidence"] >= MIN_ISSUE_CONFIDENCE and r["issue"] in axes["issue_axis"])
    for path in (OUT, OUT_TEXT, OUT_REL):
        if not os.path.exists(path): continue
        rows = [json.loads(l) for l in open(path)]
        keep = [r for r in rows if ok(r)]
        with open(path, "w") as f:
            for r in keep: f.write(json.dumps(r) + "\n")
        print(f"{os.path.basename(path)}: kept {len(keep)}, dropped {len(rows) - len(keep)}", file=sys.stderr)

def redo(axis_names):
    """Drop title-only rows for these issue axes so `run` re-scores them (after a scale was rewritten)."""
    rows = [json.loads(l) for l in open(OUT)]
    keep = [r for r in rows if r.get("issue_axis", r["axis"]) not in axis_names and r["axis"] not in axis_names]
    with open(OUT, "w") as f:
        for r in keep: f.write(json.dumps(r) + "\n")
    print(f"dropped {len(rows) - len(keep)} rows", file=sys.stderr)

FORMAL_PART = re.compile(r"\s*(תיקון\s*(מס'?\s*)?\d+\S*|הוראת שעה|תיקון)\s*(והוראת שעה)?\s*")

def no_content(title, has_notes):
    """Q22: a formal title ("... (תיקון מס' 36)") and no explanatory notes: nothing says what the bill does."""
    inner = re.findall(r"\(([^)]*)\)", title)
    return (not has_notes) and bool(inner) and all(FORMAL_PART.fullmatch(x) for x in inner)

def final_rows():
    title = {r["bill_id"]: r for r in map(json.loads, open(OUT))}
    text = {r["bill_id"]: r for r in map(json.loads, open(OUT_TEXT))} if os.path.exists(OUT_TEXT) else {}
    rel = {r["bill_id"]: r["relevance"] for r in map(json.loads, open(OUT_REL))} if os.path.exists(OUT_REL) else {}
    names = {b["bill_id"]: b["state"].split("\n")[0] for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))}
    rows = []
    for b, t in title.items():
        r = combine(t, text.get(b), rel.get(b))
        p = os.path.join(ROOT, "data/bill_texts", f"{b}.json")
        has_notes = os.path.exists(p) and bool(json.load(open(p))["notes"])
        if r["status"] in ("decided", "disputed", "unclear") and no_content(names[b], has_notes):
            r = {**r, "side": 0, "status": "no_content", "reliability": None}
        rows.append(r)
    return rows

async def relevance():
    """Applicability gate (Q21): one yes/no question per bill, same wording for every scale, on title + notes."""
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    bills = {b["bill_id"]: b for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))}
    done = {json.loads(l)["bill_id"] for l in open(OUT_REL)} if os.path.exists(OUT_REL) else set()
    todo = [r for r in map(json.loads, open(OUT)) if r["bill_id"] not in done]
    print(f"to check applicability: {len(todo)}", file=sys.stderr)
    load_env()
    sem, lock, tok = asyncio.Semaphore(16), asyncio.Lock(), 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(OUT_REL, "a") as out:
            async def one(r):
                nonlocal tok
                ax = r.get("issue_axis", r["axis"])
                st = state_of(bills[r["bill_id"]])
                p = os.path.join(ROOT, "data/bill_texts", f"{r['bill_id']}.json")
                notes = json.load(open(p))["notes"][:NOTES_CHARS] if os.path.exists(p) else ""
                if notes: st["explanatory_notes_hebrew"] = notes
                q = Noul(instructions=f"Does the Israeli bill in `bill_title_hebrew` actually bear on {axes[ax]['topic']}? "
                                      f"Answer yes only if what the bill does is part of that dispute, not merely a related subject.")
                async with sem:
                    resp = await client.system_one(state=st, questions={"rel": q})
                async with lock:
                    out.write(json.dumps({"bill_id": r["bill_id"], "issue": r["issue"], "issue_axis": ax, "relevance": resp.answers["rel"].noul,
                                          "with_notes": bool(notes), "model": resp.model}) + "\n")
                    tok += resp.usage.input_tokens
            await asyncio.gather(*(one(r) for r in todo))
    print(f"{tok:,} tokens, ~${tok * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)

async def rescore_with_text():
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    bills = {b["bill_id"]: b for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))}
    done = {json.loads(l)["bill_id"] for l in open(OUT_TEXT)} if os.path.exists(OUT_TEXT) else set()
    todo = []
    for r in map(json.loads, open(OUT)):
        if r["bill_id"] in done: continue
        p = os.path.join(ROOT, "data/bill_texts", f"{r['bill_id']}.json")
        notes = json.load(open(p))["notes"] if os.path.exists(p) else ""
        if notes: todo.append((r, notes[:NOTES_CHARS]))
    print(f"to re-score with text: {len(todo)}", file=sys.stderr)
    load_env()
    sem, lock, tok = asyncio.Semaphore(16), asyncio.Lock(), 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(OUT_TEXT, "a") as out:
            async def one(r, notes):
                nonlocal tok
                st = {**state_of(bills[r["bill_id"]]), "explanatory_notes_hebrew": notes}
                qs, resolve = questions_for(axes, r.get("issue_axis", r["axis"]))
                async with sem:
                    resp = await client.system_one(state=st, questions=qs)
                score, conf, used = resolve(resp.answers)
                async with lock:
                    out.write(json.dumps({**r, "axis": used, "score": score, "confidence": conf, "model": resp.model,
                                          "title_score": r["score"], "title_confidence": r["confidence"], "with_text": True}) + "\n")
                    tok += resp.usage.input_tokens
            await asyncio.gather(*(one(r, n) for r, n in todo))
    print(f"{tok:,} tokens, ~${tok * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)
MIN_ISSUE_CONFIDENCE = 0.5

def questions_for(axes, axis):
    """Questions to send and a resolver answers -> (score, confidence, axis actually used).
    A `split` axis asks a yes/no selector plus both scales in one request (speculative fan-out) and keeps one."""
    ax = axes[axis]
    if "split" in ax:
        sp = ax["split"]
        qs = {"sel": Noul(instructions=sp["selector"]), "yes": question(axes, sp["if_yes"]), "no": question(axes, sp["if_no"])}
        def resolve(ans):
            key, sub = ("yes", sp["if_yes"]) if ans["sel"].noul >= 0.5 else ("no", sp["if_no"])
            return ans[key].score, ans[key].confidence, sub
        return qs, resolve
    return {"dir": question(axes, axis)}, lambda ans: (ans["dir"].score, ans["dir"].confidence, axis)

def question(axes, axis):
    ax = axes[axis]
    if "criteria" in ax:
        return Score(instructions=ax["instructions"], criteria=ax["criteria"])
    lo, hi = ax["poles"]
    return Score(instructions=f"Assume the Israeli bill in `bill_title_hebrew` concerns {ax['topic']}. Which way does it push?",
                 criteria=[f"Strongly: {lo}", f"Somewhat: {lo}", "Neutral, procedural, or no clear direction on this question",
                           f"Somewhat: {hi}", f"Strongly: {hi}"])

async def run():
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    issues = {r["bill_id"]: r for r in map(json.loads, open(os.path.join(ROOT, "local/research/output/issues_all.jsonl")))}
    bills = {b["bill_id"]: b for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))}
    done = {json.loads(l)["bill_id"] for l in open(OUT)} if os.path.exists(OUT) else set()
    todo = [(b, axes["issue_axis"][r["choice"]]) for b, r in issues.items()
            if r["choice"] in axes["issue_axis"] and r["confidence"] >= MIN_ISSUE_CONFIDENCE and b not in done]
    print(f"to score: {len(todo)} (done: {len(done)})", file=sys.stderr)
    load_env()
    sem, lock, tok = asyncio.Semaphore(16), asyncio.Lock(), 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(OUT, "a") as out:
            async def one(b, axis):
                nonlocal tok
                qs, resolve = questions_for(axes, axis)
                async with sem:
                    r = await client.system_one(state=state_of(bills[b]), questions=qs)
                score, conf, used = resolve(r.answers)
                async with lock:
                    out.write(json.dumps({"bill_id": b, "issue": issues[b]["choice"], "axis": used, "issue_axis": axis,
                                          "score": score, "confidence": conf, "model": r.model}) + "\n")
                    tok += r.usage.input_tokens
            await asyncio.gather(*(one(b, ax) for b, ax in todo))
    print(f"{tok:,} tokens, ~${tok * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)

def check():
    """For Knesset-25 bills with a contested vote: does the direction score line up with coalition-minus-opposition support?"""
    import duckdb
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    sup = dict(con.sql("""
        WITH v AS (SELECT a.bill_id, a.vote_id, row_number() OVER (PARTITION BY a.bill_id ORDER BY
                     CASE a.stage WHEN 'third' THEN 4 WHEN 'second' THEN 3 WHEN 'first' THEN 2 ELSE 1 END DESC, a.vote_date DESC) rn
                   FROM vote_attrs a WHERE a.kind = 'bill' AND a.knesset = 25 AND a.split_pattern NOT IN ('consensus','no_blocs','one_bloc_only'))
        SELECT v.bill_id,
               max(CASE WHEN b.bloc='coalition' THEN b.n_for::DOUBLE/nullif(b.n_for+b.n_against,0) END)
             - max(CASE WHEN b.bloc='opposition' THEN b.n_for::DOUBLE/nullif(b.n_for+b.n_against,0) END)
        FROM v JOIN bloc_vote b USING (vote_id) WHERE v.rn = 1 GROUP BY 1""").fetchall())
    rows = final_rows()
    by = collections.defaultdict(list)
    for r in rows:
        s = sup.get(r["bill_id"])
        if s is not None and r["status"] == "decided":
            by[r["axis"]].append((r["side"], s))
    st = collections.Counter(r["status"] for r in rows); rel = collections.Counter(r["reliability"] for r in rows if r["reliability"])
    print(f"bills: {len(rows)} | {dict(st)} | reliability {dict(rel)}")
    print(f"decided bills with a contested K25 vote: {sum(len(v) for v in by.values())}")
    print("axis | n | share where (direction>0) == (coalition supported more than opposition)")
    for axis, ps in sorted(by.items(), key=lambda x: -len(x[1])):
        agree = sum((d > 0) == (s > 0) for d, s in ps)
        print(f"  {axis:22s} {len(ps):4d}  {agree / len(ps):5.0%}")

if __name__ == "__main__":
    if sys.argv[1] == "sync":  # after re-running issues: python3 local/research/scripts/jev_direction_all.py sync, then run, then text
        sync()
    elif sys.argv[1] == "redo":  # python3 local/research/scripts/jev_direction_all.py redo AXIS [AXIS ...], then `run`
        redo(set(sys.argv[2:]))
    else:
        {"run": lambda: asyncio.run(run()), "text": lambda: asyncio.run(rescore_with_text()),
         "relevance": lambda: asyncio.run(relevance()), "check": check}[sys.argv[1]]()
