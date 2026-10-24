"""Download bill-lifecycle tables for Knessets 24-25 into data/bills/ (sequential, keyset paging)."""
import json, os, sys
from odata4 import fetch_keyset

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data/bills")
os.makedirs(OUT, exist_ok=True)

def save(name, rows):
    json.dump(rows, open(f"{OUT}/{name}.json", "w"), ensure_ascii=False)
    print(name, len(rows), file=sys.stderr, flush=True)
    return rows

bills = save("bill", fetch_keyset("KNS_Bill", filter="KnessetNum ge 24"))
min_id = min(b["Id"] for b in bills)  # bill ids grow over time, so child tables are cut by BillID/ItemID >= min_id
save("bill_initiator", fetch_keyset("KNS_BillInitiator", filter=f"BillID ge {min_id}"))
save("bill_history_initiator", fetch_keyset("KNS_BillHistoryInitiator", filter=f"BillID ge {min_id}"))
save("committee", fetch_keyset("KNS_Committee", filter="KnessetNum ge 24"))
save("committee_session", fetch_keyset("KNS_CommitteeSession", filter="KnessetNum ge 24"))
save("cmt_session_item", fetch_keyset("KNS_CmtSessionItem", filter=f"ItemID ge {min_id}"))
