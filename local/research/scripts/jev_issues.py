"""Classify bills into the bottom-up issue catalogue (local/manual/issue_defs.json) with Jev.

Usage:
  python3 local/research/scripts/jev_issues.py run  [--limit N]   # labelled pool (local/manual/issue_labels.csv) -> local/research/output/issues_pool.jsonl
  python3 local/research/scripts/jev_issues.py run --all          # every bill -> local/research/output/issues_all.jsonl
  python3 local/research/scripts/jev_issues.py run --all --redo-uncertain 0.5  # re-ask bills that got none_of_these or confidence < 0.5
  python3 local/research/scripts/jev_issues.py eval [--all]       # compare with the hand labels (--all: use the full run's answers for the pool bills)
"""
import argparse, asyncio, collections, csv, json, os, sys
from typesafe_sdk import AsyncTypeSafeClient, Choice
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "pipeline"))  # pipeline modules
from jef_run import ROOT, USD_PER_INPUT_TOKEN, load_env, state_of

OUT = os.path.join(ROOT, "local/research/output/issues_pool.jsonl")
OUT_ALL = os.path.join(ROOT, "local/research/output/issues_all.jsonl")

def issue_question():
    defs = json.load(open(os.path.join(ROOT, "local/manual/issue_defs.json")))
    criteria = {d["id"]: d["description"] for d in defs}
    criteria["none_of_these"] = "None of the listed issues fits this bill"
    q = Choice(instructions="Which specific policy issue is the Israeli bill in `bill_title_hebrew` about?", criteria=criteria)
    return q, {d["issue_ru"]: d["id"] for d in defs}

async def run(bills, q, concurrency, out_path):
    sem, lock, tokens = asyncio.Semaphore(concurrency), asyncio.Lock(), 0
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(out_path, "a") as out:
            async def one(b):
                nonlocal tokens
                async with sem:
                    r = await client.system_one(state=state_of(b), questions={"issue": q})
                a = r.answers["issue"]
                async with lock:
                    out.write(json.dumps({"bill_id": b["bill_id"], "model": r.model, "input_tokens": r.usage.input_tokens,
                                          "choice": a.choice, "confidence": a.confidence,
                                          "top5": sorted(a.probabilities.items(), key=lambda kv: -kv[1])[:5]}) + "\n")
                    tokens += r.usage.input_tokens
            await asyncio.gather(*(one(b) for b in bills))
    print(f"{len(bills)} bills, {tokens:,} input tokens, ~${tokens * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)

def evaluate(ru2id, source=None):
    gold = {int(r["bill_id"]): ru2id[r["issue"]] for r in csv.DictReader(open(os.path.join(ROOT, "local/manual/issue_labels.csv")))}
    pred = {r["bill_id"]: r for r in map(json.loads, open(source or OUT))}
    ids = [b for b in gold if b in pred]
    top1 = sum(pred[b]["choice"] == gold[b] for b in ids)
    top3 = sum(gold[b] in [k for k, _ in pred[b]["top5"][:3]] for b in ids)
    print(f"scored {len(ids)} | top-1 {top1 / len(ids):.1%} | top-3 {top3 / len(ids):.1%} | none_of_these chosen: {sum(pred[b]['choice'] == 'none_of_these' for b in ids)}")
    print("\nconfidence >= t | kept | top-1 on kept")
    for t in (0.0, 0.3, 0.5, 0.7, 0.8, 0.9):
        k = [b for b in ids if pred[b]["confidence"] >= t]
        print(f"  {t:.1f}  {len(k) / len(ids):6.1%}  {sum(pred[b]['choice'] == gold[b] for b in k) / max(len(k), 1):.1%}")
    by = collections.defaultdict(list)
    for b in ids: by[gold[b]].append(pred[b]["choice"])
    print("\nissue recall (n) | most frequent confusion")
    for issue, ps in sorted(by.items(), key=lambda x: sum(p == x[0] for p in x[1]) / len(x[1])):
        wrong = collections.Counter(p for p in ps if p != issue).most_common(1)
        print(f"  {issue:32s} {sum(p == issue for p in ps) / len(ps):5.0%} ({len(ps):2d}) {wrong[0] if wrong else ''}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["run", "eval"])
    ap.add_argument("--limit", type=int); ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--all", action="store_true", help="classify every bill, not only the labelled pool")
    ap.add_argument("--redo-uncertain", type=float, help="with --all: re-ask none_of_these and answers below this confidence (after the catalogue grows)")
    a = ap.parse_args()
    q, ru2id = issue_question()
    if a.cmd == "eval": return evaluate(ru2id, OUT_ALL if a.all else None)
    out = OUT_ALL if a.all else OUT
    labelled = {int(r["bill_id"]) for r in csv.DictReader(open(os.path.join(ROOT, "local/manual/issue_labels.csv")))}
    prev = [json.loads(l) for l in open(out)] if os.path.exists(out) else []
    if a.redo_uncertain is not None:
        keep = [r for r in prev if r["choice"] != "none_of_these" and r["confidence"] >= a.redo_uncertain]
        with open(out, "w") as f:  # drop the rows being re-asked; the rest stay as they are
            for r in keep: f.write(json.dumps(r) + "\n")
        prev = keep
    done = {r["bill_id"] for r in prev}
    bills = [b for b in map(json.loads, open(os.path.join(ROOT, "local/research/input/bills.jsonl")))
             if (a.all or b["bill_id"] in labelled) and b["bill_id"] not in done][: a.limit]
    print(f"to classify: {len(bills)} (done: {len(done)})", file=sys.stderr)
    load_env()
    asyncio.run(run(bills, q, a.concurrency, out))

if __name__ == "__main__":
    main()
