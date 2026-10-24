"""Test run: score bills on the 375 approved directions with Jev (jef). Two stages, one request each per bill:
  1. applicability: one yes/no question per direction ("does the bill change this quantity?");
  2. side: for directions with applicability >= APPLIES, a 3-level scale (− / no change / +) with the direction's own «+» and «−».
State: Hebrew title + explanatory notes (first NOTES_CHARS). Directions are passed as written (Russian).

Usage: python3 pipeline/labeling/jev_directions_test.py sample N   -> local/jef/directions/jev_test/bills.json
       python3 pipeline/labeling/jev_directions_test.py run        -> local/jef/directions/jev_test/out.json   (test 1: 374 directions, Russian)
       python3 pipeline/labeling/jev_directions_test.py run2       -> local/jef/directions/jev_test2/out.json  (test 2: 255 final directions, English,
                                                            plus one question whether the bill moves something outside the list)
       python3 pipeline/labeling/jev_directions_test.py pool3 N    -> ids of N fresh candidate bills (outside the discovery sample) for test 3
       python3 pipeline/labeling/jev_directions_test.py sample3 N  -> local/jef/directions/jev_test3/bills.json (first N candidates with notes)
       python3 pipeline/labeling/jev_directions_test.py run3       -> local/jef/directions/jev_test3/out.json  (255 directions; side asked from 0.3)
       pool4 / sample4 / run4 — the same for test 4 (government bills only) in local/jef/directions/jev_test4/
       pool5 N / sample5 N / run5 — test 5: N government + N private fresh bills in local/jef/directions/jev_test5/
       pool6 N / sample6 N / run6 — test 6, the same, excluding the pools of tests 3-5 (and 7: pool7 / sample7 / run7)
"""
import asyncio, csv, json, os, random, sys
import duckdb
from typesafe_sdk import AsyncTypeSafeClient, Noul, Score
from jef_run import ROOT, USD_PER_INPUT_TOKEN, BILL_TYPE_EN, load_env

D = os.path.join(ROOT, "jef/directions")
OUT = os.path.join(D, "jev_test")
NOTES_CHARS, APPLIES, CHUNK = 3000, 0.5, 50

def directions():
    """The approved list: merge v4 groups with the manual decisions applied (merge/manual_decisions.json)."""
    groups = json.load(open(os.path.join(D, "merge/out.json")))["groups"]
    dec = json.load(open(os.path.join(D, "merge/manual_decisions.json")))
    gone = {d["group"] for d in dec}
    out = [{"n": i, "name": g["name"], "plus": g["plus"], "minus": g["minus"]} for i, g in enumerate(groups, 1) if i not in gone]
    for d in dec:
        if d.get("new_direction"):
            new = next(t for b in d["bills"].values() for t in b if str(t.get("target", "")).startswith("new:"))
            out.append({"n": f"new{d['group']}", "name": d["new_direction"], "plus": new["plus"], "minus": new["minus"]})
    return out

def sample(n):
    """n bills from the discovery sample with notes, by type in sample proportions, fixed seed."""
    order = list(csv.DictReader(open(os.path.join(D, "order.csv"))))
    with_notes = [r for r in order if json.load(open(os.path.join(ROOT, f"data/bill_texts/{r['bill_id']}.json")))["notes"]]
    rnd = random.Random(20261013)
    gov = [r for r in with_notes if r["bill_type"] != "פרטית"]
    pick = rnd.sample(gov, max(1, n * len(gov) // len(with_notes)))
    pick += rnd.sample([r for r in with_notes if r["bill_type"] == "פרטית"], n - len(pick))
    os.makedirs(OUT, exist_ok=True)
    json.dump([{k: r[k] for k in ("bill_id", "knesset", "bill_type", "name")} for r in pick], open(os.path.join(OUT, "bills.json"), "w"),
              ensure_ascii=False, indent=1)
    print(len(pick), "bills")

T3 = os.path.join(D, "jev_test3")
GOV_ONLY = False

def pool3(n):
    """Fresh bills: not in the discovery sample, all types, knessets 24-25, fixed seed. Prints ids for bill_texts.py."""
    seen = {r["bill_id"] for r in csv.DictReader(open(os.path.join(D, "order.csv")))}
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    rows = [r for r in con.sql("select bill_id, knesset, bill_type, name from bills order by bill_id").fetchall() if str(r[0]) not in seen and (not GOV_ONLY or r[2] == "ממשלתית")]
    for r in random.Random(20261014).sample(rows, n): print(r[0])

def pool5(n):
    """Test 5: n government and n private fresh bills, also excluding the candidate pools of tests 3 and 4."""
    seen = {r["bill_id"] for r in csv.DictReader(open(os.path.join(D, "order.csv")))}
    for t in ("jev_test3", "jev_test4", "jev_test5", "jev_test6", "jev_test7"):
        if os.path.exists(os.path.join(D, t, "pool.txt")) and t != os.path.basename(T3):
            seen |= set(open(os.path.join(D, t, "pool.txt")).read().split())
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    rows = [r for r in con.sql("select bill_id, knesset, bill_type, name from bills order by bill_id").fetchall() if str(r[0]) not in seen]
    rnd = random.Random({"jev_test5": 20261016, "jev_test6": 20261017}.get(os.path.basename(T3), 20261018))
    for t in ("ממשלתית", "פרטית"):
        for r in rnd.sample([r for r in rows if r[2] == t], n): print(r[0])

def sample5(n):
    """n bills with notes of each type (government, private) from pool.txt, in pool order."""
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    pick, cnt = [], {}
    for i in open(os.path.join(T3, "pool.txt")).read().split():
        p = os.path.join(ROOT, f"data/bill_texts/{i}.json")
        if not (os.path.exists(p) and json.load(open(p))["notes"]): continue
        bid, k, t, name = con.sql(f"select bill_id, knesset, bill_type, name from bills where bill_id={i}").fetchone()
        if cnt.get(t, 0) < n:
            pick.append({"bill_id": str(bid), "knesset": k, "bill_type": t, "name": name}); cnt[t] = cnt.get(t, 0) + 1
    json.dump(pick, open(os.path.join(T3, "bills.json"), "w"), ensure_ascii=False, indent=1)
    print(len(pick), "bills", cnt)

def sample3(n):
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    ids = [int(x) for x in open(os.path.join(T3, "pool.txt")).read().split()]
    pick = []
    for i in ids:
        p = os.path.join(ROOT, f"data/bill_texts/{i}.json")
        if os.path.exists(p) and json.load(open(p))["notes"]:
            bid, k, t, name = con.sql(f"select bill_id, knesset, bill_type, name from bills where bill_id={i}").fetchone()
            pick.append({"bill_id": str(bid), "knesset": k, "bill_type": t, "name": name})
        if len(pick) == n: break
    json.dump(pick, open(os.path.join(T3, "bills.json"), "w"), ensure_ascii=False, indent=1)
    print(len(pick), "bills")

def state(b):
    notes = json.load(open(os.path.join(ROOT, f"data/bill_texts/{b['bill_id']}.json")))["notes"][:NOTES_CHARS]
    return {"bill_title_hebrew": b["name"], "bill_type": BILL_TYPE_EN.get(b["bill_type"], b["bill_type"]),
            "explanatory_notes_hebrew": notes}

def q_applies(d):
    return Noul(instructions=f"Does this Israeli bill change the following quantity (increase or decrease it)? Quantity: «{d['name']}». "
                             f"«+» means: {d['plus']}. «−» means: {d['minus']}. Answer yes only if what the bill itself does moves this quantity, "
                             f"not merely if it touches a related subject.")

def q_side(d):
    return Score(instructions=f"Which way does this Israeli bill move the quantity «{d['name']}»?",
                 criteria=[f"−: {d['minus']}", "Neither: the bill does not move this quantity either way", f"+: {d['plus']}"])

async def ask(client, st, qs):
    """Jev request(s) for one bill; questions are sent in chunks of CHUNK."""
    ans, tok, keys = {}, 0, list(qs)
    for i in range(0, len(keys), CHUNK):
        r = await client.system_one(state=st, questions={k: qs[k] for k in keys[i:i + CHUNK]})
        ans.update(r.answers); tok += r.usage.input_tokens
    return ans, tok

def directions_final():
    """The final list (merge3/directions_final.json): English names with «+» and «−»."""
    return [{"n": d["key"], "name": d["name_en"], "plus": d["plus_en"], "minus": d["minus_en"]}
            for d in json.load(open(os.path.join(D, "merge3/directions_final.json")))]

def q_outside(dirs):
    return Noul(instructions="Below is a list of quantities. Does this Israeli bill substantially change some quantity that is NOT on the list "
                             "(not even as a close variant)? Answer yes only for a real effect of the bill that no listed quantity covers.\n"
                             + "\n".join(f"- {d['name']}" for d in dirs.values()))

async def run(final=False, test3=False):
    load_env()
    dirs = {str(d["n"]): d for d in (directions_final() if final else directions())}
    bills = json.load(open(os.path.join(T3 if test3 else OUT, "bills.json")))
    out_dir = T3 if test3 else (os.path.join(D, "jev_test2") if final else OUT)
    applies_min = 0.3 if test3 else APPLIES
    os.makedirs(out_dir, exist_ok=True)
    res, total = [], 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        for b in bills:
            st = state(b)
            qs = {f"d{k}": q_applies(d) for k, d in dirs.items()}
            if final and not test3: qs["outside"] = q_outside(dirs)
            a1, t1 = await ask(client, st, qs)
            outside = a1.pop("outside").noul if "outside" in a1 else None
            applies = {k[1:]: a.noul for k, a in a1.items()}
            hit = [k for k, p in applies.items() if p >= applies_min]
            a2, t2 = await ask(client, st, {f"d{k}": q_side(dirs[k]) for k in hit}) if hit else ({}, 0)
            side = {k[1:]: {"score": a.score, "confidence": a.confidence, "p": a.probabilities} for k, a in a2.items()}
            res.append({"bill_id": b["bill_id"], "applies": applies, "side": side, "outside": outside, "tokens": t1 + t2})
            total += t1 + t2
            print(b["bill_id"], len(hit), "applicable", t1 + t2, "tokens", file=sys.stderr, flush=True)
    json.dump(res, open(os.path.join(out_dir, "out.json"), "w"), ensure_ascii=False)
    print(f"{total:,} tokens, ~${total * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)

if __name__ == "__main__":
    if sys.argv[1][-1] in "567":
        T3 = os.path.join(D, "jev_test" + sys.argv[1][-1]); os.makedirs(T3, exist_ok=True)
        sys.argv[1] = sys.argv[1][:-1] + "5"
        if sys.argv[1] == "pool5": pool5(int(sys.argv[2])); sys.exit()
        if sys.argv[1] == "sample5": sample5(int(sys.argv[2])); sys.exit()
        sys.argv[1] = "run3"
    if sys.argv[1].endswith("4"):
        T3, GOV_ONLY = os.path.join(D, "jev_test4"), True
        os.makedirs(T3, exist_ok=True)
        sys.argv[1] = sys.argv[1][:-1] + "3"
    if sys.argv[1] == "sample": sample(int(sys.argv[2]))
    elif sys.argv[1] == "pool3": pool3(int(sys.argv[2]))
    elif sys.argv[1] == "sample3": sample3(int(sys.argv[2]))
    else: asyncio.run(run(final=sys.argv[1] in ("run2", "run3"), test3=sys.argv[1] == "run3"))
