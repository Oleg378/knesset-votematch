"""Export bills for jef classification: local/research/input/bills.jsonl (one bill per line).

Usage: python3 local/research/scripts/jef_prepare.py   (needs knesset.duckdb; see pipeline/build/build.py)
"""
import json, os
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    con = duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
    rows = con.sql("""
        SELECT b.bill_id, b.knesset, b.bill_type, b.name, nullif(trim(b.summary), '') AS summary,
               b.bill_id IN (SELECT bill_id FROM votes WHERE bill_id IS NOT NULL) AS has_plenum_vote
        FROM bills b ORDER BY b.bill_id""").fetchall()
    with open(os.path.join(ROOT, "local/research/input/bills.jsonl"), "w") as f:
        for bill_id, knesset, bill_type, name, summary, voted in rows:
            # `state` is the only text the classifier sees.
            state = name if not summary else f"{name}\n\n{summary}"
            f.write(json.dumps({"bill_id": bill_id, "knesset": knesset, "bill_type": bill_type,
                                "has_plenum_vote": voted, "state": state}, ensure_ascii=False) + "\n")
    print(len(rows), "bills")

if __name__ == "__main__":
    main()
