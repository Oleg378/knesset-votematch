"""Classify bills with TypeSafe Jev ("jef") using local/research/questions.json.

Usage:
  python3 pipeline/labeling/jef_run.py --dry-run          # print one request, no API call
  python3 pipeline/labeling/jef_run.py --gold             # pilot: the 200 gold bills
  python3 pipeline/labeling/jef_run.py --all              # all 11,768 bills
Options: --out PATH (default local/research/output/results.jsonl), --limit N, --concurrency N.

API key: TYPESAFE_API_KEY from the environment or from .env in the repo root (git-ignored).
Re-running resumes: bills already present in the output file are skipped.
Pricing (docs.typesafe.ai/models, jev-1.13): $0.042 per million input tokens, output free.
"""
import argparse, asyncio, csv, json, os, sys
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline'), os.path.join(ROOT, 'pipeline/fetch')]   # labels.py, bill_texts.py
USD_PER_INPUT_TOKEN = 0.042 / 1_000_000
BILL_TYPE_EN = {"ממשלתית": "government bill", "פרטית": "private member's bill", "ועדה": "committee bill"}

def load_env():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def build_questions(spec):
    qs = {}
    for q in spec["questions"]:
        if q["type"] == "choice":
            qs[q["id"]] = Choice(instructions=q["question"], criteria=q["options"])
        elif q["type"] == "noul":
            qs[q["id"]] = Noul(instructions=q["question"])
    return qs

def state_of(bill):
    # Named fields help the model; the title stays in the original Hebrew.
    return {"bill_title_hebrew": bill["state"], "knesset_term": bill["knesset"],
            "bill_type": BILL_TYPE_EN.get(bill["bill_type"], bill["bill_type"])}

async def run(bills, questions, version, out_path, concurrency):
    sem, done, tokens = asyncio.Semaphore(concurrency), 0, 0
    lock = asyncio.Lock()
    async with AsyncTypeSafeClient(model="jev-latest") as client:
        with open(out_path, "a") as out:
            async def one(bill):
                nonlocal done, tokens
                async with sem:
                    r = await client.system_one(state=state_of(bill), questions=questions)
                rec = {"bill_id": bill["bill_id"], "model": r.model, "questions_version": version,
                       "input_tokens": r.usage.input_tokens}
                for qid, a in r.answers.items():
                    if a.type == "choice":
                        rec[qid] = a.probabilities
                        rec[qid + "_confidence"] = a.confidence
                    elif a.type == "noul":
                        rec[qid] = a.noul
                async with lock:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
                    done += 1; tokens += r.usage.input_tokens
                    if done % 200 == 0 or done == len(bills):
                        print(f"{done}/{len(bills)}  tokens={tokens:,}  ~${tokens * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)
            await asyncio.gather(*(one(b) for b in bills))
    return tokens

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--gold", action="store_true"); g.add_argument("--all", action="store_true"); g.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "local/research/output/results.jsonl"))
    ap.add_argument("--limit", type=int); ap.add_argument("--concurrency", type=int, default=16)
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "local/research/questions.json")))
    questions = build_questions(spec)
    bills = [json.loads(l) for l in open(os.path.join(ROOT, "local/research/input/bills.jsonl"))]
    if a.dry_run:
        print(json.dumps({"state": state_of(bills[0]), "model": "jev-latest",
                          "questions": {k: v.model_dump(exclude_none=True) if hasattr(v, "model_dump") else str(v) for k, v in questions.items()}},
                         ensure_ascii=False, indent=1, default=str))
        return
    if a.gold:
        gold = {int(r["bill_id"]) for r in csv.DictReader(open(os.path.join(ROOT, "local/research/gold/gold.csv")))}
        bills = [b for b in bills if b["bill_id"] in gold]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    seen = {json.loads(l)["bill_id"] for l in open(a.out)} if os.path.exists(a.out) else set()
    bills = [b for b in bills if b["bill_id"] not in seen][: a.limit]
    print(f"to classify: {len(bills)} (already done: {len(seen)})", file=sys.stderr)
    if not bills: return
    load_env()
    if not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("TYPESAFE_API_KEY is not set: put it into .env in the repo root (see local/docs/jef-task.md)")
    tokens = asyncio.run(run(bills, questions, spec["version"], a.out, a.concurrency))
    print(f"done: {tokens:,} input tokens, ~${tokens * USD_PER_INPUT_TOKEN:.3f}", file=sys.stderr)

if __name__ == "__main__":
    main()
