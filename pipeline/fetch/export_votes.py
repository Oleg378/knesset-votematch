"""Export plenum votes with per-MK results, faction on vote date and normalized direction.

Usage: python3 pipeline/fetch/export_votes.py 2021-04-06 2026-11-10 ../data/export
Needs an Israeli IP. ~0.5 s per 100-row page; Knessets 24+25 (~780k result rows) take ~30 min with 2 threads.
"""
import collections, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from odata4 import fetch_all, fetch_keyset

# ForOptionID -> stage. For every bill stage "בעד" means "for the bill" (AgainstOption is always 24 "לדחות").
STAGE = {12: "preliminary", 13: "preliminary", 32: "preliminary",
         1: "first", 2: "first", 6: "second", 8: "third", 9: "continuity"}
RESULT = {7: "for", 8: "against", 9: "abstain", 6: "present_not_voting"}
FACTION_POSITIONS = (54, 48)  # חבר/ת סיעה, יו"ר סיעה

def main(date_from, date_to, out):
    os.makedirs(out, exist_ok=True)
    rng = f"ge {date_from}T00:00:00Z and {{f}} lt {date_to}T00:00:00Z"
    votes = fetch_all("KNS_PlenumVote", filter="VoteDateTime " + rng.format(f="VoteDateTime"))
    ptp = fetch_all("KNS_PersonToPosition", filter=f"FactionID ne null and StartDate lt {date_to}T00:00:00Z")
    bill_ids = sorted({v["ItemID"] for v in votes if v["ForOptionID"] in STAGE})
    bills = {}
    for i in range(0, len(bill_ids), 100):  # "or" chains hit the server's MaxNodeCount=100; "in" does not
        chunk = ",".join(map(str, bill_ids[i:i + 100]))
        bills.update({b["Id"]: b for b in fetch_all("KNS_Bill", filter=f"Id in ({chunk})")})

    # Results are paged by 100; split by month, cache each month (re-running resumes),
    # and keep parallelism low: 4 threads trip the anti-bot layer (HTTP 481) after ~9 min.
    months = sorted({v["VoteDateTime"][:7] for v in votes})
    os.makedirs(f"{out}/months", exist_ok=True)
    def month_results(m):
        cache = f"{out}/months/{m}.json"
        if os.path.exists(cache): return json.load(open(cache))
        y, mo = map(int, m.split("-")); nxt = f"{y + mo // 12}-{mo % 12 + 1:02d}"
        rs = fetch_keyset("KNS_PlenumVoteResult", filter=f"VoteDate ge {m}-01T00:00:00Z and VoteDate lt {nxt}-01T00:00:00Z")
        json.dump(rs, open(cache, "w"), ensure_ascii=False)
        print(m, len(rs), file=sys.stderr, flush=True)
        return rs
    with ThreadPoolExecutor(2) as ex:
        results = [r for rs in ex.map(month_results, months) for r in rs]

    member = collections.defaultdict(list)
    for p in ptp:
        if p["PositionID"] in FACTION_POSITIONS:
            member[p["PersonID"]].append((p["StartDate"][:10], (p["FinishDate"] or "9999")[:10], p["FactionID"], p["FactionName"].strip()))
    vote_by_id = {v["Id"]: v for v in votes}
    rows, unmatched = [], 0
    for r in results:
        v = vote_by_id.get(r["VoteID"])
        if not v: continue
        d = v["VoteDateTime"][:10]
        f = [(fid, name) for a, b, fid, name in member[r["MkId"]] if a <= d <= b]
        unmatched += not f
        rows.append({"vote_id": r["VoteID"], "mk_id": r["MkId"], "name": f'{r["FirstName"]} {r["LastName"]}'.strip(),
                     "faction_id": f[0][0] if f else None, "faction": f[0][1] if f else None,
                     "result": RESULT.get(r["ResultCode"], r["ResultDesc"])})
    for v in votes:
        v["stage"] = STAGE.get(v["ForOptionID"])
        v["bill"] = bills.get(v["ItemID"]) if v["stage"] else None

    json.dump(votes, open(f"{out}/votes.json", "w"), ensure_ascii=False)
    json.dump(rows, open(f"{out}/vote_results.json", "w"), ensure_ascii=False)
    print(f"votes={len(votes)} results={len(rows)} bills={len(bills)} faction_unmatched={unmatched}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
