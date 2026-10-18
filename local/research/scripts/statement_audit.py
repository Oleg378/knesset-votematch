"""Audit of all quiz statements against the bills their list positions rest on (customer decision 2026-10-17, point 1).

Algorithm of the customer: statement narrower than / off its direction → rewrite broader → if the wording becomes vague → split
the direction → parts that fail the selection criteria are dropped. Opus judges each direction blind (no Jev scores, no list
positions): statement(s) + direction name + the up to 40 bills with the most weight in the list positions.

Weight of a bill in a direction = number of 2026 candidates (ex-MKs of evaluated lists) who initiated it + 0.25 × number of their
for/against votes on it (private bills, 4 stages) — the same weights as the position (P = A + 0.25 V). Bills are grouped by
name (the same bill re-submitted counts once, weights summed). Labels without the relevance filter (as in production).

Usage: python3 local/research/scripts/statement_audit.py build   -> local/research/statement_audit/input_{1,2,3}.md
       python3 local/research/scripts/statement_audit.py table   -> local/research/statement_audit/audit.csv (after out_{1,2,3}.jsonl)
"""
import collections, csv, json, os, sys
import duckdb, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# NEW=1: audit only the statements added on 2026-10-18 (q >= 72) into statement_audit_new/, 2 input files (customer, 2026-10-18)
NEW = os.environ.get("NEW") == "1"
# QS=12,16,...: audit only these statements (after the label removals, customer 2026-10-18) into statement_audit_<TAG or "qs">/
QS = set(os.environ["QS"].split(",")) if os.environ.get("QS") else None
OUT = os.path.join(ROOT, f"local/research/statement_audit_{os.environ.get('TAG', 'qs')}" if QS else
                   "local/research/statement_audit_new" if NEW else "local/research/statement_audit"); os.makedirs(OUT, exist_ok=True)
PARTS = int(os.environ.get("PARTS", 1)) if QS else 2 if NEW else 3
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels

def build():
    lab = labels.load(relevance=False)["bill_lab"]
    st = collections.defaultdict(list)
    for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")):
        if r["status"] == "ok" and (not NEW or int(r["q"]) >= 72) and (QS is None or r["q"] in QS): st[r["d"]].append(r)
    dirs = pd.read_csv(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv", dtype={"n": str})
    dname = dict(zip(dirs.n, dirs.get("name_en", dirs.name_ru)))
    for p in [json.load(open(f"{ROOT}/jef/directions/split/plan.json"))] + labels.later_plans():   # all split stages
        for k, v in p["new"].items(): dname[k] = v.get("name_en") or v["name_ru"]
    cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cm = cand[cand.match.isin(["exact", "manual"])]
    cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); shown = set(cov[cov.status != "not_evaluated"].letters)
    mks = set(cm[cm.letters.isin(shown)].mk_id.astype(int))
    con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
    bills = con.sql("select bill_id, name, knesset, bill_type from bills where knesset in (24, 25)").df().set_index("bill_id")
    ini = con.sql("select distinct bill_id, mk_id from bill_initiators where is_initiator").df()
    ini = ini[ini.mk_id.isin(mks) & ini.bill_id.isin(bills.index)]
    votes = con.sql("""select a.bill_id, r.mk_id from vote_roster r join vote_attrs a using(vote_id) join bills b using(bill_id)
        where a.kind='bill' and a.stage in ('preliminary','first','second','third') and b.bill_type='פרטית'
          and r.result in ('for','against')""").df()
    votes = votes[votes.mk_id.isin(mks)]
    w = collections.Counter()
    for x in ini.bill_id: w[x] += 1
    for x in votes.bill_id: w[x] += 0.25
    items = []
    for d, sts in st.items():
        agg = collections.defaultdict(lambda: [0.0, 0, 0, set(), set()])   # weight, authors, votes, signs, roles
        na = collections.Counter(ini.bill_id); nv = collections.Counter(votes.bill_id)
        for x, l in lab.items():
            if x not in bills.index or x not in w: continue
            s = labels.signed_topics(l).get(d)
            if not s: continue
            role = "main" if d in {str(t["n"]) for t in l[0]} else "secondary"
            a = agg[bills.name[x]]; a[0] += w[x]; a[1] += na[x]; a[2] += nv[x]; a[3].add(s); a[4].add(role)
        tot = sum(a[0] for a in agg.values())
        top = sorted(agg.items(), key=lambda kv: -kv[1][0])[:40]
        items.append(dict(d=d, sts=sts, top=top, tot=tot, n=len(agg), share=sum(a[0] for _, a in top) / tot if tot else 0))
    items.sort(key=lambda it: int(it["sts"][0]["q"]))
    parts = [items[i::PARTS] for i in range(PARTS)]
    for k, part in enumerate(parts, 1):
        L = []
        for it in part:
            L.append(f"## Direction {it['d']} — {dname.get(it['d'], '')}\n")
            for s in it["sts"]:
                L.append(f"- q{s['q']} «{s['title_en']}» (agree = {'more' if s['agree_key'] == '+' else 'less'} of the direction): {s['statement_en']}")
            L.append(f"\nBills behind the list positions: {it['n']} distinct; the {len(it['top'])} with the most weight below cover "
                     f"{it['share']:.0%} of the weight. Weight = candidates who initiated it + 0.25 × candidates' votes on it. "
                     f"«toward» = the label says passing the bill moves policy toward agreeing with the first statement.\n")
            L.append("| # | Bill (Hebrew title) | weight | initiators | votes | label: direction vs statement | label role |")
            L.append("|---|---|---|---|---|---|---|")
            key = 1 if it["sts"][0]["agree_key"] == "+" else -1
            for i, (name, a) in enumerate(it["top"], 1):
                sg = "/".join(sorted("toward" if s * key > 0 else "away" for s in a[3]))
                L.append(f"| {i} | {name} | {a[0]:.1f} | {a[1]} | {a[2]} | {sg} | {'/'.join(sorted(a[4]))} |")
            L.append("")
        open(f"{OUT}/input_{k}.md", "w").write("\n".join(L))
        print(f"input_{k}.md: {len(part)} directions, {sum(len(it['sts']) for it in part)} statements")

def table():
    st = {r["q"]: r for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")) if r["status"] == "ok"}
    rows = []
    for k in range(1, PARTS + 1):
        for l in open(f"{OUT}/out_{k}.jsonl"):
            if not l.strip(): continue
            o = json.loads(l)
            for s in o["statements"]:
                q = str(s["q"]).lstrip("q")
                rows.append(dict(q=int(q), d=o["d"], verdict=o["verdict"], title_en=st[q]["title_en"], statement_en=st[q]["statement_en"],
                                 new_statement_en=s.get("new_statement_en", ""), new_agree_key=s.get("new_agree_key", ""),
                                 split=json.dumps(o.get("split", []), ensure_ascii=False) if o.get("split") else "",
                                 bills_off=o.get("bills_off", ""), reason=o.get("reason", "")))
    T = pd.DataFrame(rows).sort_values("q"); T.to_csv(f"{OUT}/audit.csv", index=False)
    print(T.verdict.value_counts().to_string()); print(f"statements {len(T)}")

if __name__ == "__main__":
    {"build": build, "table": table}[sys.argv[1]]()
