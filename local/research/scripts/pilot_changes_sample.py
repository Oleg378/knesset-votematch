"""Pilot sample for the multi-change markup (SU п. 23–26): 40 private bills, stratified.

Frame: all private bills of Knessets 24–25 (government and committee bills have notes only in PDF booklets — separate step).
Strata: Knesset 24 / 25 = 20 / 20; with and without a plenum vote about equal; at most 2 bills per old topic;
hard cases: 5 "disputed" in the old layer, 3 formal titles without notes.

Usage: python3 local/research/scripts/pilot_changes_sample.py pick    -> local/research/pilot_changes/ids.txt (then: python3 pipeline/bill_texts.py --file local/research/pilot_changes/ids.txt)
       python3 local/research/scripts/pilot_changes_sample.py build   -> local/research/pilot_changes/sample.csv (hidden fields), blind/input.jsonl (title + notes only)
"""
import csv, json, os, random, sys
import duckdb
sys.path.insert(0, os.path.dirname(__file__))
from jev_direction_all import final_rows

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/pilot_changes")
NOTES_CHARS = 4000
rng = random.Random(20261012)

con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
bills = {r[0]: dict(bill_id=r[0], knesset=r[1], name=r[2], bill_type=r[3], has_vote=r[4]) for r in con.sql(
    "select b.bill_id, b.knesset, b.name, b.bill_type, exists(select 1 from votes v where v.bill_id = b.bill_id) from bills b").fetchall()}
topic = {r["bill_id"]: r["choice"] for r in map(json.loads, open(os.path.join(ROOT, "local/research/output/issues_all.jsonl")))}
status = {r["bill_id"]: r["status"] for r in final_rows()}

def text(b):
    p = os.path.join(ROOT, "data/bill_texts", f"{b}.json")
    return json.load(open(p)) if os.path.exists(p) else None

for b in bills.values():
    b.update(topic=topic.get(b["bill_id"]), old_status=status.get(b["bill_id"]))

picked, per_topic, per_k, per_vote = [], {}, {24: 0, 25: 0}, {True: 0, False: 0}

def ok(b):
    return (b["bill_id"] not in {p["bill_id"] for p in picked} and per_topic.get(b["topic"], 0) < 2
            and per_k[b["knesset"]] < 20 and per_vote[b["has_vote"]] < 20)

def take(pool, n, reason):
    pool = sorted(pool, key=lambda b: b["bill_id"]); rng.shuffle(pool)
    for b in pool:
        if n == 0: break
        if ok(b):
            picked.append({**b, "reason": reason}); n -= 1
            per_topic[b["topic"]] = per_topic.get(b["topic"], 0) + 1
            per_k[b["knesset"]] += 1; per_vote[b["has_vote"]] += 1

B = [b for b in bills.values() if b["bill_type"] == "פרטית"]
take([b for b in B if b["old_status"] == "disputed"], 5, "disputed_old")
take([b for b in B if b["old_status"] == "no_content"], 3, "formal_no_notes")
for k in (24, 25):
    for hv in (True, False):
        take([b for b in B if b["knesset"] == k and b["has_vote"] == hv], 40, "random")
rng.shuffle(picked)
assert len(picked) == 40, len(picked)

if sys.argv[1] == "pick":
    open(os.path.join(OUT, "ids.txt"), "w").write("\n".join(str(b["bill_id"]) for b in picked) + "\n")
    print(len(picked), per_k, per_vote, file=sys.stderr)
    sys.exit()

for b in picked:
    t = text(b["bill_id"]) or {}
    b.update(notes=t.get("notes", ""), text_chars=t.get("text_chars", 0), text_error=t.get("error"))
with open(os.path.join(OUT, "sample.csv"), "w") as f:
    w = csv.writer(f); w.writerow(["bill_id", "knesset", "has_vote", "old_topic", "old_status", "reason", "notes_chars", "name"])
    for b in picked: w.writerow([b["bill_id"], b["knesset"], b["has_vote"], b["topic"], b["old_status"], b["reason"], len(b["notes"]), b["name"]])
with open(os.path.join(OUT, "blind/input.jsonl"), "w") as f:
    for b in picked: f.write(json.dumps({"bill_id": b["bill_id"], "title": b["name"], "notes": b["notes"][:NOTES_CHARS]}, ensure_ascii=False) + "\n")
print(len(picked), sum(bool(b["notes"]) for b in picked), "with notes", file=sys.stderr)
