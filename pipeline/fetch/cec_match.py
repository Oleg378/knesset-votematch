"""Match 2026 candidates (manual/cec_candidates_26.csv) to MKs of Knessets 24-25 (KNS_Person via OData v4).

Writes manual/candidate_mk_26.csv: letters, position, name_he, party, mk_id, mk_name, match.
CEC prints "last first [middle]". exact: the MK's last name starts the candidate's name (or follows one
prefix token, for double-barrelled names) and one of the MK's first-name tokens is among the rest. Ambiguous matches (>1 MK) are written with match=ambiguous
and need a manual decision.
Same last name and a first name with the same consonant skeleton prefix (nicknames, spelling) gives
match=check: manual decision, never automatic. Needs an Israeli IP for the OData call (cached in data/cec/mk_persons.json).
"""
import csv, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data/cec/mk_persons.json")

def norm_tokens(s):
    s = re.sub(r"[\"'׳״`’\.\(\)]", "", s).replace("־", " ").replace("-", " ")
    return [t for t in s.split() if t]

def skel(token):
    """Consonant skeleton: drop the vowel letters ו and י so spelling variants and nicknames line up (בעז/בועז, מירי/מרים)."""
    return token[0] + re.sub(r"[וי]", "", token[1:]) if token else token

def mk_persons():
    if os.path.exists(CACHE): return json.load(open(CACHE))
    from odata4 import fetch_all
    ids = [r[0] for r in duckdb.connect(os.path.join(ROOT, "knesset.duckdb"), read_only=True)
           .sql("SELECT DISTINCT mk_id FROM mk_terms").fetchall()]
    people = []
    for i in range(0, len(ids), 100):
        people += fetch_all("KNS_Person", filter=f"Id in ({','.join(map(str, ids[i:i+100]))})")
    json.dump(people, open(CACHE, "w"), ensure_ascii=False)
    return people

def main():
    people = [(p["Id"], norm_tokens(p["LastName"] or ""), norm_tokens(p["FirstName"] or ""),
               f'{p["FirstName"]} {p["LastName"]}') for p in mk_persons()]
    cands = list(csv.DictReader(open(os.path.join(ROOT, "manual/cec_candidates_26.csv"), encoding="utf-8")))
    out = []
    for c in cands:
        toks = norm_tokens(c["name_he"])
        exact, fuzzy = [], []
        for pid, last, first, name in people:
            if not last or not first: continue
            # CEC prints the last name first; allow a double-barrelled prefix (e.g. "בדרה גולן" for MK "גולן")
            at = next((i for i in range(0, 3) if toks[i:i + len(last)] == last), None)
            if at is None: continue
            rest = toks[:at] + toks[at + len(last):]
            if any(f in rest for f in first): exact.append((pid, name))
            elif any(skel(f)[:2] == skel(r)[:2] for f in first for r in rest): fuzzy.append((pid, name))
        hits, match = (exact, "exact") if len(exact) == 1 else (exact, "ambiguous") if exact else (fuzzy, "check") if fuzzy else ([], "none")
        out.append({**{k: c[k] for k in ("letters", "position", "name_he", "party")},
                    "mk_id": ";".join(str(h[0]) for h in hits), "mk_name": ";".join(h[1] for h in hits), "match": match})
    # One MK can be only one candidate: an MK that matched several candidates (namesakes) goes to manual review.
    from collections import Counter
    used = Counter(r["mk_id"] for r in out if r["match"] == "exact")
    for r in out:
        if r["match"] == "exact" and used[r["mk_id"]] > 1: r["match"] = "ambiguous"
    # Manual decisions (L3): manual/candidate_mk_overrides.csv  letters,position,mk_id,decision(yes|no),reason
    ov_path = os.path.join(ROOT, "manual/candidate_mk_overrides.csv")
    ov = {(o["letters"], o["position"]): o for o in csv.DictReader(open(ov_path, encoding="utf-8"))} if os.path.exists(ov_path) else {}
    for r in out:
        o = ov.get((r["letters"], r["position"]))
        if not o: continue
        if o["decision"] == "yes":
            r["mk_id"], r["match"] = o["mk_id"], "manual"
            r["mk_name"] = next(n for pid, _, _, n in people if str(pid) == o["mk_id"])
        else:
            r["mk_id"], r["mk_name"], r["match"] = "", "", "manual_no"
    with open(os.path.join(ROOT, "manual/candidate_mk_26.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("candidates", len(out), Counter(r["match"] for r in out))
    for r in out:
        if r["match"] != "none": print(r["letters"], r["position"], r["name_he"], "->", r["mk_name"], r["match"])

if __name__ == "__main__":
    main()
