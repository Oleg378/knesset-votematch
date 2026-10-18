"""Step 1 of direction discovery (PROGRESS «Сейчас»): a fixed stratified order of up to 1 500 bills, cut into batches of 50.

Order: all committee bills, government bills up to 20 % of the sample, the rest private; Knessets 24 and 25 in
proportion to their counts; shuffled with a fixed seed, so batch k is always the same 50 bills. Pilot bills are excluded.

Usage: python3 local/research/scripts/directions_sample.py order            -> local/jef/directions/order.csv
       python3 local/research/scripts/directions_sample.py ids K            -> prints private bill ids of batch K (for bill_texts.py)
       python3 local/research/scripts/directions_sample.py build K          -> local/jef/directions/blind/batch_K.jsonl (title + notes only)
Texts: bill_texts.py (private — DOCX notes; government and committee — PDF booklet of the first reading).
Fallback for split parts («פרק ז' (חברות ממשלתיות) מתוך הצעת חוק ...») without a booklet of their own: excerpts of the
parent bill's notes around the part's subject words. Every input row carries `text_source`:
docx_notes | pdf_booklet | parent_booklet (marked: directions may be inexact) | title_only (marked likewise).
"""
import csv, json, os, random, re, sys
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "jef/directions")
N, BATCH, NOTES_CHARS = 1500, 50, 2000

def order():
    rng = random.Random(20261012)
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    pilot = {int(x) for x in open(os.path.join(ROOT, "local/research/pilot_changes/ids.txt")).read().split()}
    rows = [r for r in con.sql("select bill_id, knesset, bill_type, name from bills order by bill_id").fetchall() if r[0] not in pilot]
    by = {}
    for r in rows: by.setdefault(r[2], []).append(r)
    for v in by.values(): rng.shuffle(v)
    committee = by["ועדה"]
    government = by["ממשלתית"][: int(N * 0.2)]
    private = by["פרטית"][: N - len(committee) - len(government)]
    sample = committee + government + private
    rng.shuffle(sample)
    with open(os.path.join(OUT, "order.csv"), "w") as f:
        w = csv.writer(f); w.writerow(["batch", "bill_id", "knesset", "bill_type", "name"])
        for i, r in enumerate(sample): w.writerow([i // BATCH, *r])
    print(len(sample), {k: sum(r[2] == k for r in sample) for k in by}, file=sys.stderr)

def batch(k):
    return [r for r in csv.DictReader(open(os.path.join(OUT, "order.csv"))) if int(r["batch"]) == k]

PART = re.compile(r"^.*?\(([^()]+)\)\s*מתוך\s+(.+?)(\s*\[.*\])?$")
WINDOW = 700

def load_text(bill_id):
    p = os.path.join(ROOT, "data/bill_texts", f"{bill_id}.json")
    return json.load(open(p)) if os.path.exists(p) else {}

def parent_excerpts(name, names):
    """Excerpts of the parent's notes around the part's subject (the words in brackets before «מתוך»)."""
    m = PART.match(name)
    if not m: return ""
    subject, parent = m.group(1).strip(), m.group(2).strip()
    pid = names.get(parent)
    notes = load_text(pid).get("notes", "") if pid else ""
    hits = [x.start() for x in re.finditer(re.escape(subject), notes)]
    return "\n…\n".join(notes[max(0, i - WINDOW // 3): i + WINDOW] for i in hits)[:NOTES_CHARS]

def parent_ids(rows):
    """Parent bill ids of split parts in these rows (to download their booklets first)."""
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    names = dict(con.sql("select name, bill_id from bills").fetchall())
    return sorted({names[m.group(2).strip()] for r in rows if (m := PART.match(r["name"])) and m.group(2).strip() in names})

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "order": order()
    elif cmd == "ids":
        rows = batch(int(sys.argv[2]))
        print("\n".join([r["bill_id"] for r in rows] + [str(x) for x in parent_ids(rows)]))
    elif cmd == "build":
        k = int(sys.argv[2])
        con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
        names = dict(con.sql("select name, bill_id from bills").fetchall())
        with open(os.path.join(OUT, f"blind/batch_{k}.jsonl"), "w") as f:
            for r in batch(k):
                t = load_text(r["bill_id"])
                notes, source = t.get("notes", "")[:NOTES_CHARS], t.get("text_source", "docx_notes" if t.get("notes") else "none")
                if not notes:
                    notes = parent_excerpts(r["name"], names)
                    source = "parent_booklet" if notes else "title_only"
                f.write(json.dumps({"bill_id": int(r["bill_id"]), "title": r["name"], "text_source": source, "notes": notes}, ensure_ascii=False) + "\n")
