"""Pilot: can Jev tell a bill's direction on an issue-specific scale? Gold: local/research/direction/gold.csv.

Usage: python3 local/research/scripts/jev_direction.py [--with-text]
  --with-text adds the explanatory notes (data/bill_texts, see pipeline/bill_texts.py) to the state.
Writes local/research/output/direction_pilot[_text].jsonl and prints the evaluation.
"""
import asyncio, csv, json, os, sys
from typesafe_sdk import AsyncTypeSafeClient, Score
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "pipeline"))  # pipeline modules
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env, state_of

WITH_TEXT = "--with-text" in sys.argv
NOTES_CHARS = 3000  # explanatory notes are the argument for the bill; the start carries the intent

def state(bill):
    s = state_of(bill)
    if WITH_TEXT:
        p = os.path.join(ROOT, "data/bill_texts", f"{bill['bill_id']}.json")
        if os.path.exists(p):
            s["explanatory_notes_hebrew"] = json.load(open(p))["notes"][:NOTES_CHARS]
    return s

async def main():
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    gold = list(csv.DictReader(open(os.path.join(ROOT, "local/research/direction/gold.csv"))))
    bills = {b["bill_id"]: b for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))}
    load_env()
    sem, res = asyncio.Semaphore(12), []
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        async def one(g):
            ax = axes[g["axis"]]
            async with sem:
                r = await client.system_one(state=state(bills[int(g["bill_id"])]),
                                            questions={"dir": Score(instructions=ax["instructions"], criteria=ax["criteria"])})
            a = r.answers["dir"]
            res.append({**g, "score": a.score, "confidence": a.confidence, "tokens": r.usage.input_tokens})
        await asyncio.gather(*(one(g) for g in gold))
    with open(os.path.join(ROOT, "local/research/output/direction_pilot_text.jsonl" if WITH_TEXT else "local/research/output/direction_pilot.jsonl"), "w") as f:
        for r in res: f.write(json.dumps(r) + "\n")
    tok = sum(r["tokens"] for r in res)
    print(f"{len(res)} bills, {tok:,} tokens, ~${tok * USD_PER_INPUT_TOKEN:.4f}")
    side = lambda x: (x > 2) - (x < 2)  # -1 / 0 / +1 relative to the neutral middle level
    for axis in sorted({g["axis"] for g in gold}):
        rs = [r for r in res if r["axis"] == axis]
        mae = sum(abs(r["score"] - int(r["level"])) for r in rs) / len(rs)
        same = sum(side(round(r["score"])) == side(int(r["level"])) for r in rs)
        print(f"{axis:15s} n={len(rs):2d}  correct side {same}/{len(rs)}  mean abs error {mae:.2f}")
    bad = [r for r in res if side(round(r["score"])) != side(int(r["level"]))]
    print("\nwrong side:")
    for r in bad: print(f"  {r['axis']:14s} gold={r['level']} jev={r['score']:.2f} conf={r['confidence']:.2f} {r['note']}")

if __name__ == "__main__":
    asyncio.run(main())
