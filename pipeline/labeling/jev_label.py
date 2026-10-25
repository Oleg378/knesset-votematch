"""Mass labeling of bills with the current scheme (local/jef/directions/jev_roles/CURRENT_SCHEME.md) on 255 directions.

Per bill (Hebrew title + first 3,000 characters of the explanatory notes):
  1. applicability: yes/no per direction -> applies; candidates: applies >= 0.3;
  2. side scale (− / no movement / +) for candidates;
  3. role scale (Not affected / Minor / Secondary / Main) for candidates;
  4. main-aim choice over candidates;
  selection: main #1 = top choice, main #2 if >= 0.5 of #1; secondary: applies >= 0.7 and role Main/Secondary, by applies, up to 5;
  sign: side < 0.7 "−", > 1.3 "+"; in between: increase / decrease questions, the side with p >= 0.5 and higher, else unknown.

Usage: python3 pipeline/labeling/jev_label.py BATCH            -> data/directions/labels/batch_BATCH.jsonl (resumable)
       python3 pipeline/labeling/jev_label.py ids BATCH        -> bill ids of the batch (for bill_texts.py --file)
Order: labels/full_order.csv — the 1,500 bills of the discovery sample first, then all other bills shuffled (seed 20261013).
Batch N = positions (N-1)*1000+1 .. N*1000. Texts must be downloaded first (bill_texts.py, Israeli IP).
"""
import asyncio, csv, json, os, sys
import duckdb
from typesafe_sdk import AsyncTypeSafeClient, Noul
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env
import jev_directions_test as j
import jev_roles as r

D = os.path.join(ROOT, "data/directions")
OUT = os.path.join(D, "labels")
BATCH = 1000

def full_order():
    """All bills in a fixed order: the 1,500 of the discovery sample first (order.csv), then the rest shuffled (seed 20261013).
    Written once to labels/full_order.csv so that batches never change."""
    path = os.path.join(OUT, "full_order.csv")
    if not os.path.exists(path):
        import random
        first = list(csv.DictReader(open(os.path.join(D, "order.csv"))))
        seen = {x["bill_id"] for x in first}
        con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
        rest = [{"bill_id": str(b), "knesset": str(k), "bill_type": t}
                for b, k, t in con.sql("select bill_id, knesset, bill_type from bills order by bill_id").fetchall() if str(b) not in seen]
        random.Random(20261013).shuffle(rest)
        os.makedirs(OUT, exist_ok=True)
        with open(path, "w") as f:
            w = csv.DictWriter(f, fieldnames=["bill_id", "knesset", "bill_type"]); w.writeheader()
            for x in first + rest: w.writerow({k: x[k] for k in ("bill_id", "knesset", "bill_type")})
    return list(csv.DictReader(open(path)))

def bills_of(batch):
    order = full_order()
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    names = dict(con.sql("select bill_id::varchar, name from bills").fetchall())
    part = order[(batch - 1) * BATCH: batch * BATCH]
    return [{"bill_id": x["bill_id"], "bill_type": x["bill_type"], "knesset": x["knesset"], "name": names[x["bill_id"]]} for x in part]

def state(b):
    p = os.path.join(ROOT, f"raw/bill_texts/{b['bill_id']}.json")
    notes = json.load(open(p))["notes"][:j.NOTES_CHARS] if os.path.exists(p) else ""
    return {"bill_title_hebrew": b["name"], "bill_type": j.BILL_TYPE_EN.get(b["bill_type"], b["bill_type"]),
            "explanatory_notes_hebrew": notes}, bool(notes)

async def label(client, b, dirs):
    st, has_notes = state(b)
    tok = 0
    a, t = await j.ask(client, st, {f"d{k}": j.q_applies(d) for k, d in dirs.items()}); tok += t
    applies = {k[1:]: v.noul for k, v in a.items()}
    cand = sorted((k for k, p in applies.items() if p >= 0.3), key=lambda k: -applies[k])
    if not cand:
        return {"bill_id": b["bill_id"], "has_notes": has_notes, "main": [], "secondary": [], "applies": applies, "tokens": tok}
    cb = {"cand": cand}
    q1, _ = r.iter1(cb, dirs); q2, _ = r.iter2(cb, dirs)
    qs = {**{f"s{k}": j.q_side(dirs[k]) for k in cand}, **q1, **q2}
    a, t = await j.ask(client, st, qs); tok += t
    side = {k[1:]: v.score for k, v in a.items() if k.startswith("s")}
    role = {}
    for k, v in a.items():
        if k.startswith("d"):
            pr = {str(l): p for l, p in v.probabilities.items()}
            role[k[1:]] = max(pr, key=pr.get)
    choice = {k[1:]: p for k, p in a["main"].probabilities.items()}
    o = sorted(choice, key=lambda k: -choice[k])
    main = o[:1] + [k for k in o[1:2] if choice[k] >= 0.5 * choice[o[0]]]
    sec = [k for k in cand if k not in main and applies[k] >= 0.7 and role.get(k) in ("2", "3")][:5]
    sign, fix = {}, {}
    for k in main + sec:
        s = "−" if side[k] < 0.7 else ("+" if side[k] > 1.3 else None)
        if s is None:
            d = dirs[k]
            a, t = await j.ask(client, st, {
                "inc": Noul(instructions=f"Does this Israeli bill increase, expand or strengthen «{d['name']}»? («+» means: {d['plus']})"),
                "dec": Noul(instructions=f"Does this Israeli bill reduce, cut, weaken or abolish «{d['name']}»? («−» means: {d['minus']})")})
            tok += t
            pi, pd = a["inc"].noul, a["dec"].noul
            s = "+" if pi >= 0.5 and pi > pd else ("−" if pd >= 0.5 and pd > pi else None)
            fix[k] = [round(pi, 3), round(pd, 3)]
        sign[k] = s
    return {"bill_id": b["bill_id"], "has_notes": has_notes,
            "main": [{"n": k, "sign": sign[k], "p_choice": round(choice[k], 3)} for k in main],
            "secondary": [{"n": k, "sign": sign[k], "applies": round(applies[k], 3)} for k in sec],
            "applies": {k: round(p, 3) for k, p in applies.items()}, "side": {k: round(v, 3) for k, v in side.items()},
            "role": role, "choice": {k: round(v, 3) for k, v in choice.items()}, "sign_fix": fix, "tokens": tok}

async def main(batch):
    load_env()
    dirs = {str(d["n"]): d for d in j.directions_final()}
    bills = bills_of(batch)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"batch_{batch:02d}.jsonl")
    done = {json.loads(l)["bill_id"] for l in open(path)} if os.path.exists(path) else set()
    todo = [b for b in bills if b["bill_id"] not in done]
    print(f"batch {batch}: {len(bills)} bills, {len(done)} done, {len(todo)} to label", file=sys.stderr, flush=True)
    sem, lock, stats = asyncio.Semaphore(8), asyncio.Lock(), {"n": 0, "tok": 0, "err": 0}
    stop = asyncio.Event()
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(path, "a") as out:
            async def one(b):
                if stop.is_set(): return
                async with sem:
                    if stop.is_set(): return
                    try:
                        rec = await label(client, b, dirs)
                    except Exception as e:
                        async with lock:
                            stats["err"] += 1
                            print(f"error {b['bill_id']}: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr, flush=True)
                            if stats["err"] >= 5: stop.set()
                        return
                async with lock:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
                    stats["n"] += 1; stats["tok"] += rec["tokens"]
                    if stats["n"] % 100 == 0 or stats["n"] == len(todo):
                        print(f"{stats['n']}/{len(todo)}  tokens={stats['tok']:,}  ~${stats['tok'] * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr, flush=True)
            await asyncio.gather(*(one(b) for b in todo))
    print(json.dumps({"labeled": stats["n"], "errors": stats["err"], "tokens": stats["tok"],
                      "usd": round(stats["tok"] * USD_PER_INPUT_TOKEN, 3), "stopped": stop.is_set()}))

if __name__ == "__main__":
    if sys.argv[1] == "ids":
        for b in bills_of(int(sys.argv[2])): print(b["bill_id"])
    else:
        asyncio.run(main(int(sys.argv[1])))
