"""Relevance of a labeled bill to the quiz statement(s) of its direction (customer decision 2026-10-17, after the Likud × q11
case: the side of a list was set by votes on bills that carry the direction but are not about the statement — e.g. denial of
rights to people involved in terrorism counted as «less state support for pension savings»).

Per bill × quiz direction (the bill carries the direction in its labels; Knessets 24–25): one yes/no question with the same
input as the mass labeling (Hebrew title + first 3,000 characters of the notes): is the bill about the issue of the quiz
statement(s) of this direction? The answer probability is stored; the threshold and what it filters (votes only, or also
authorship) are decided after the pilot.

Usage: python3 pipeline/labeling/jev_relevance.py --pilot     -> jef/directions/relevance/pilot_<QV>.jsonl (8 known cases, 30 random voted
                                                        pairs, 42 random pairs of any kind; gold labels: pilot_gold.csv)
       python3 pipeline/labeling/jev_relevance.py [--votes] [N] -> jef/directions/relevance/relevance.jsonl (resumable; --votes: only pairs
                                                        with private-bill votes; N = first N pairs)
"""
import asyncio, csv, json, os, random, sys
import duckdb
from typesafe_sdk import AsyncTypeSafeClient, Noul
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j
import jev_label as jl
import labels

OUT_DIR = os.path.join(ROOT, "jef/directions/relevance")
STOP_USD = 0.8
# pilot: pairs found in the check of 2026-10-17 (local/research/vote_sign_check/) with the agent's expected answer
KNOWN = [("2158413", "276", "no"), ("2158413", "275", "no"), ("2158413", "277a", "yes"), ("2159538", "314", "no"),
         ("2197029", "314", "no"), ("2219182", "314", "yes"), ("2196011", "159", "yes"), ("2198959", "277c", "yes")]

def statements():
    by_d = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "jef/quiz/statements.csv"))):
        if r["status"] == "ok": by_d.setdefault(r["d"], []).append((r["title_en"], r["statement_en"]))
    return by_d

def pairs(by_d):
    lab = labels.load(relevance=False)
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    info = {b: (n, t, k) for b, n, t, k in con.sql("select bill_id, name, bill_type, knesset from bills").fetchall()}
    voted = {b for (b,) in con.sql("""select distinct a.bill_id from vote_attrs a join bills b using(bill_id)
        where a.kind='bill' and a.stage in ('preliminary','first','second','third') and b.bill_type='פרטית'""").fetchall()}
    res = []
    for b, l in sorted(lab["bill_lab"].items()):
        if b not in info or info[b][2] not in (24, 25): continue
        for d in labels.signed_topics(l):
            if d in by_d:
                n, t, _ = info[b]
                res.append({"bill_id": str(b), "name": n, "bill_type": t, "d": d, "voted": b in voted})
    return res

# the current question (2026-10-17): in the pilot of the first question (pilot_q1.jsonl) Jev judged the statement's «even if» clause rather
# than its topic (demolition of terrorists' homes vs «tighten counter-terrorism measures, even if …»: 0.48)
QV = "q2"
def question(sts):
    topics = " / ".join(f"«{t}»" for t, _ in sts)
    texts = " ".join(f"«{s}»" for _, s in sts)
    return Noul(instructions=f"A voter quiz has a question on the topic {topics}. Voters are asked whether they agree with: {texts} "
                "Is this Israeli bill about that topic — does what the bill itself does move policy on this issue one way or the other? "
                "Judge only the issue: the bill does not have to match the statement's wording, its direction or its «even if» clause. "
                "Answer no if the bill is about a different issue and only touches a nearby subject.")

async def one(client, p, sts):
    st, has_notes = jl.state(p)
    a, tok = await j.ask(client, st, {"rel": question(sts)})
    return {"bill_id": p["bill_id"], "d": p["d"], "voted": p["voted"], "p": round(a["rel"].noul, 4), "has_notes": has_notes,
            "tokens": tok}

async def main(pilot, votes_only, limit):
    load_env()
    os.makedirs(OUT_DIR, exist_ok=True)
    by_d = statements()
    allp = pairs(by_d)
    if pilot:
        out = os.path.join(OUT_DIR, f"pilot_{QV}.jsonl")
        idx = {(p["bill_id"], p["d"]): p for p in allp}
        known = [dict(idx[(b, d)], expected=e) for b, d, e in KNOWN if (b, d) in idx]
        kset = {(b, d) for b, d, _ in KNOWN}
        rest = [p for p in allp if p["voted"] and (p["bill_id"], p["d"]) not in kset]
        first = random.Random(20261017).sample(rest, 30)            # the 30 random pairs of pilot q1
        seen = kset | {(p["bill_id"], p["d"]) for p in first}
        more = random.Random(20261018).sample([p for p in allp if (p["bill_id"], p["d"]) not in seen], 42)   # any pair (authorship too)
        todo = known + first + more
    else:
        out = os.path.join(OUT_DIR, f"relevance_{QV}.jsonl")
        todo = [p for p in allp if p["voted"] or not votes_only][:limit]
    done = {(json.loads(l)["bill_id"], json.loads(l)["d"]) for l in open(out)} if os.path.exists(out) else set()
    todo = [p for p in todo if (p["bill_id"], p["d"]) not in done]
    print(f"{len(todo)} pairs to check", file=sys.stderr, flush=True)
    sem, lock, stats = asyncio.Semaphore(8), asyncio.Lock(), {"n": 0, "tok": 0, "err": 0}
    stop = asyncio.Event()
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(out, "a") as f:
            async def run(p):
                if stop.is_set(): return
                async with sem:
                    if stop.is_set(): return
                    try: rec = await one(client, p, by_d[p["d"]])
                    except Exception as e:
                        async with lock:
                            stats["err"] += 1; print(f"error {p['bill_id']}: {e}"[:200], file=sys.stderr, flush=True)
                            if stats["err"] >= 5: stop.set()
                        return
                if "expected" in p: rec["expected"] = p["expected"]
                async with lock:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                    stats["n"] += 1; stats["tok"] += rec["tokens"]
                    if stats["tok"] * USD_PER_INPUT_TOKEN >= STOP_USD: stop.set()
                    if stats["n"] % 200 == 0: print(f"{stats['n']}  ~${stats['tok'] * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr, flush=True)
            await asyncio.gather(*(run(p) for p in todo))
    print(json.dumps({"checked": stats["n"], "errors": stats["err"], "usd": round(stats["tok"] * USD_PER_INPUT_TOKEN, 4),
                      "stopped": stop.is_set(), "pairs_total": len(allp), "pairs_voted": sum(p["voted"] for p in allp)}))

if __name__ == "__main__":
    args = sys.argv[1:]
    pilot, votes_only = "--pilot" in args, "--votes" in args
    rest = [a for a in args if not a.startswith("--")]
    asyncio.run(main(pilot, votes_only, int(rest[0]) if rest else None))
