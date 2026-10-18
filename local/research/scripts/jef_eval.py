"""Score jef topic predictions against the hand-labelled gold set.

Usage: python3 local/research/scripts/jef_eval.py local/research/output/results.jsonl
Expected line format (see local/docs/jef-task.md):
  {"bill_id": 2201200, "topic": {"judiciary": 0.91, "governance": 0.05, ...}, "value_laden": 0.88}
"""
import collections, csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main(path):
    gold = {int(r["bill_id"]): r for r in csv.DictReader(open(os.path.join(ROOT, "local/research/gold/gold.csv")))}
    pred = {}
    for line in open(path):
        r = json.loads(line)
        if r["bill_id"] in gold:
            top = max(r["topic"], key=r["topic"].get)
            pred[r["bill_id"]] = (top, r["topic"][top])
    missing = set(gold) - set(pred)
    n = len(pred)
    exact = sum(pred[b][0] == gold[b]["topic"] for b in pred)
    lenient = sum(pred[b][0] in (gold[b]["topic"], gold[b]["secondary_topic"]) for b in pred)
    print(f"gold bills scored: {n} (missing in output: {len(missing)})")
    print(f"top-1 accuracy: {exact / n:.1%}   counting secondary topic as correct: {lenient / n:.1%}")

    # Confidence routing: how accurate are confident answers, and how many bills would go to manual review.
    print("\nconfidence >= t | share of bills kept | accuracy on kept")
    for t in (0.3, 0.5, 0.6, 0.7, 0.8, 0.9):
        kept = [b for b in pred if pred[b][1] >= t]
        if kept:
            acc = sum(pred[b][0] in (gold[b]["topic"], gold[b]["secondary_topic"]) for b in kept) / len(kept)
            print(f"  {t:.1f}            | {len(kept) / n:6.1%}             | {acc:.1%}")

    print("\nper topic: recall (gold n) | most common wrong prediction")
    by_topic = collections.defaultdict(list)
    for b in pred: by_topic[gold[b]["topic"]].append(pred[b][0])
    for topic, ps in sorted(by_topic.items(), key=lambda x: -len(x[1])):
        wrong = collections.Counter(p for p in ps if p != topic).most_common(1)
        print(f"  {topic:26s} {ps.count(topic) / len(ps):5.0%} ({len(ps):2d}) | {wrong[0][0] + ' x' + str(wrong[0][1]) if wrong else ''}")

if __name__ == "__main__":
    main(sys.argv[1])
