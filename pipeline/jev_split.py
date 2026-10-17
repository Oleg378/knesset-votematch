"""Split of heterogeneous quiz directions (PROGRESS «План», approved 2026-10-16): relabel only the bills that carry one of
the split directions, with the candidates from jef/directions/split/plan.json — the new sub-directions of that direction and
the existing directions its bills may be transferred to.

Per bill × split direction d (same input as the mass labeling: Hebrew title + first 3,000 characters of the notes):
  applicability (yes/no) and side (− / neither / +) for each candidate of d;
  a candidate is assigned when applies >= 0.7 (the secondary-topic threshold of CURRENT_SCHEME.md) and inherits the role of d
  (main or secondary); its sign follows the current scheme (side < 0.7 «−», > 1.3 «+», else increase/decrease questions);
  if no candidate is assigned, the bill stays in d (leftover).

Stages 2 and 3 (--stage2 / --stage3, 2026-10-18 [У]): directions split by the audits of the statements (jef/directions/split/plan2.json, plan3.json). The bills are taken
from the effective labels (pipeline/labels.py after stage 1 and the overrides); one choice question per bill × direction, as in
--choice; every sub-direction keeps the parent's orientation, so the bill keeps the parent's sign (no sign questions).
-> jef/directions/labels/split2_choice.jsonl, split3_choice.jsonl.

Usage: python3 pipeline/jev_split.py [N]            -> jef/directions/labels/split_relabel.jsonl (resumable; N = first N pairs only)
       python3 pipeline/jev_split.py --choice [N]   -> split_choice.jsonl: variant (a), approved 2026-10-16. The bill already
         belongs to the parent direction, so one choice question picks which candidate describes it best (plus «none of these»);
         assigned: the top choice unless it is «none», and the second if its probability >= 0.5 of the top (the main-topic rule
         of CURRENT_SCHEME.md); sign by the side score from split_relabel.jsonl, middle scores re-asked (increase/decrease).
"""
import asyncio, glob, json, os, sys
import duckdb
from typesafe_sdk import AsyncTypeSafeClient, Noul, Choice
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j
import jev_label as jl

SPLIT = os.path.join(ROOT, "jef/directions/split")
OUT = os.path.join(ROOT, "jef/directions/labels/split_relabel.jsonl")
ASSIGN, STOP_USD = 0.7, 1.6

def candidates(plan, dirs):
    """parent direction -> {candidate key: {n, name, plus, minus}}"""
    new = {k: {"n": k, "name": v["name_en"], "plus": v["plus_en"], "minus": v["minus_en"]} for k, v in plan["new"].items()}
    out = {}
    for parent, subs in plan["parents"].items():
        if parent in plan["keep"]: continue
        c = {}
        for s in subs:
            if s in new: c[s] = new[s]
            for t in plan["transfers"].get(s, []): c[t] = dirs[t]
        if c: out[parent] = c
    return out

def pairs(cands):
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    info = {str(b): (n, t) for b, n, t in con.sql("select bill_id, name, bill_type from bills").fetchall()}
    res = []
    for f in sorted(glob.glob(os.path.join(ROOT, "jef/directions/labels/batch_*.jsonl"))):
        for l in open(f):
            x = json.loads(l)
            for role, ms in (("main", x["main"]), ("secondary", x["secondary"])):
                for m in ms:
                    if m["n"] in cands:
                        n, t = info[x["bill_id"]]
                        res.append({"bill_id": x["bill_id"], "name": n, "bill_type": t, "parent": m["n"], "role": role, "parent_sign": m["sign"]})
    return res

async def one(client, p, cand):
    st, _ = jl.state(p)
    tok = 0
    a, t = await j.ask(client, st, {**{f"a{k}": j.q_applies(d) for k, d in cand.items()}, **{f"s{k}": j.q_side(d) for k, d in cand.items()}}); tok += t
    applies = {k: a[f"a{k}"].noul for k in cand}
    side = {k: a[f"s{k}"].score for k in cand}
    assigned = []
    for k in sorted(cand, key=lambda k: -applies[k]):
        if applies[k] < ASSIGN: continue
        s = "−" if side[k] < 0.7 else ("+" if side[k] > 1.3 else None)
        if s is None:
            d = cand[k]
            b, t = await j.ask(client, st, {
                "inc": Noul(instructions=f"Does this Israeli bill increase, expand or strengthen «{d['name']}»? («+» means: {d['plus']})"),
                "dec": Noul(instructions=f"Does this Israeli bill reduce, cut, weaken or abolish «{d['name']}»? («−» means: {d['minus']})")})
            tok += t
            pi, pd = b["inc"].noul, b["dec"].noul
            s = "+" if pi >= 0.5 and pi > pd else ("−" if pd >= 0.5 and pd > pi else None)
        assigned.append({"n": k, "sign": s, "role": p["role"], "applies": round(applies[k], 3)})
    return {"bill_id": p["bill_id"], "parent": p["parent"], "role": p["role"], "parent_sign": p["parent_sign"],
            "assigned": assigned, "applies": {k: round(v, 3) for k, v in applies.items()},
            "side": {k: round(v, 3) for k, v in side.items()}, "tokens": tok}

async def sign_of(client, st, d, score):
    s = "−" if score < 0.7 else ("+" if score > 1.3 else None)
    if s is not None: return s, 0
    b, t = await j.ask(client, st, {
        "inc": Noul(instructions=f"Does this Israeli bill increase, expand or strengthen «{d['name']}»? («+» means: {d['plus']})"),
        "dec": Noul(instructions=f"Does this Israeli bill reduce, cut, weaken or abolish «{d['name']}»? («−» means: {d['minus']})")})
    pi, pd = b["inc"].noul, b["dec"].noul
    return ("+" if pi >= 0.5 and pi > pd else ("−" if pd >= 0.5 and pd > pi else None)), t

PRIOR = {}

async def one_choice(client, p, cand):
    st, _ = jl.state(p)
    crit = {f"D{k}": f"{d['name']} («+»: {d['plus']} «−»: {d['minus']})" for k, d in cand.items()}
    crit["Dnone"] = "None of these: the bill is about something else"
    a, tok = await j.ask(client, st, {"pick": Choice(instructions="This Israeli bill was classified under a broad topic. Which of these "
                                       "narrower quantities does the bill itself change? Choose the one that best describes what the bill does.",
                                       criteria=crit)})
    pr = {k[1:]: v for k, v in a["pick"].probabilities.items()}
    order = sorted(pr, key=lambda k: -pr[k])
    pick = [] if order[0] == "none" else order[:1] + [k for k in order[1:2] if k != "none" and pr[k] >= 0.5 * pr[order[0]]]
    prior = PRIOR.get((p["bill_id"], p["parent"]), {}).get("side", {})
    assigned = []
    for k in pick:
        s, t = await sign_of(client, st, cand[k], prior.get(k, 1.0)); tok += t
        assigned.append({"n": k, "sign": s, "role": p["role"], "p_choice": round(pr[k], 3)})
    return {"bill_id": p["bill_id"], "parent": p["parent"], "role": p["role"], "parent_sign": p["parent_sign"],
            "assigned": assigned, "choice": {k: round(v, 3) for k, v in pr.items()}, "tokens": tok}

async def one_stage2(client, p, cand):
    st, _ = jl.state(p)
    crit = {f"D{k}": f"{d['name']} («+»: {d['plus']} «−»: {d['minus']})" for k, d in cand.items()}
    crit["Dnone"] = "None of these: the bill is about something else"
    a, tok = await j.ask(client, st, {"pick": Choice(instructions="This Israeli bill was classified under a broad topic. Which of these "
                                       "narrower quantities does the bill itself change? Choose the one that best describes what the bill does.",
                                       criteria=crit)})
    pr = {k[1:]: v for k, v in a["pick"].probabilities.items()}
    order = sorted(pr, key=lambda k: -pr[k])
    pick = [] if order[0] == "none" else order[:1] + [k for k in order[1:2] if k != "none" and pr[k] >= 0.5 * pr[order[0]]]
    assigned = [{"n": k, "sign": p["parent_sign"], "role": p["role"], "p_choice": round(pr[k], 3)} for k in pick]
    return {"bill_id": p["bill_id"], "parent": p["parent"], "role": p["role"], "parent_sign": p["parent_sign"],
            "assigned": assigned, "choice": {k: round(v, 3) for k, v in pr.items()}, "tokens": tok}

def pairs_stage2(plan):
    import labels
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    info = {str(b): (n, t) for b, n, t in con.sql("select bill_id, name, bill_type from bills").fetchall()}
    res = []
    for b, (main, sec) in labels.load(relevance=False, stages=STAGE - 1)["bill_lab"].items():
        for role, ms in (("main", main), ("secondary", sec)):
            for m in ms:
                if str(m["n"]) in plan["parents"] and m.get("sign") in ("+", "−", "-"):
                    n, t = info[str(b)]
                    res.append({"bill_id": str(b), "name": n, "bill_type": t, "parent": str(m["n"]), "role": role, "parent_sign": m["sign"]})
    return res

async def main(limit):
    load_env()
    if STAGE:
        plan = json.load(open(os.path.join(SPLIT, f"plan{STAGE}.json")))
        cands = {par: {k: {"n": k, "name": plan["new"][k]["name_en"], "plus": plan["new"][k]["plus_en"], "minus": plan["new"][k]["minus_en"]}
                       for k in subs} for par, subs in plan["parents"].items()}
        return await label(pairs_stage2(plan)[:limit], cands, one_stage2)
    plan = json.load(open(os.path.join(SPLIT, "plan.json")))
    dirs = {str(d["n"]): d for d in j.directions_final()}
    cands = candidates(plan, dirs)
    if CHOICE:
        for l in open(OUT_A): r = json.loads(l); PRIOR[(r["bill_id"], r["parent"])] = r
    return await label(pairs(cands)[:limit], cands, one_choice if CHOICE else one)

async def label(todo, cands, fn):
    done = {(json.loads(l)["bill_id"], json.loads(l)["parent"]) for l in open(OUT)} if os.path.exists(OUT) else set()
    todo = [p for p in todo if (p["bill_id"], p["parent"]) not in done]
    print(f"{len(todo)} pairs to label", file=sys.stderr, flush=True)
    sem, lock, stats = asyncio.Semaphore(8), asyncio.Lock(), {"n": 0, "tok": 0, "err": 0}
    stop = asyncio.Event()
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(OUT, "a") as out:
            async def run(p):
                if stop.is_set(): return
                async with sem:
                    if stop.is_set(): return
                    try: rec = await fn(client, p, cands[p["parent"]])
                    except Exception as e:
                        async with lock:
                            stats["err"] += 1; print(f"error {p['bill_id']}: {e}"[:200], file=sys.stderr, flush=True)
                            if stats["err"] >= 5: stop.set()
                        return
                async with lock:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
                    stats["n"] += 1; stats["tok"] += rec["tokens"]
                    if stats["tok"] * USD_PER_INPUT_TOKEN >= STOP_USD: stop.set()
                    if stats["n"] % 100 == 0: print(f"{stats['n']}  ~${stats['tok'] * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr, flush=True)
            await asyncio.gather(*(run(p) for p in todo))
    print(json.dumps({"labeled": stats["n"], "errors": stats["err"], "usd": round(stats["tok"] * USD_PER_INPUT_TOKEN, 4), "stopped": stop.is_set()}))

OUT_A = OUT
CHOICE, STAGE = False, 0
if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("--stage2", "--stage3"):
        STAGE = int(args[0][-1]); OUT, args = OUT.replace("split_relabel", f"split{STAGE}_choice"), args[1:]
        STOP_USD = 0.30   # [У] 2026-10-18: estimate ≈ $0.22 for 1,328 pairs
    if args and args[0] == "--choice":
        CHOICE, OUT, args = True, OUT.replace("split_relabel", "split_choice"), args[1:]
    asyncio.run(main(int(args[0]) if args else None))
