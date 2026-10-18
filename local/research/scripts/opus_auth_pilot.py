"""Opus pilot on authorship labels (customer approval 2026-10-17): 50 (bill × quiz direction) pairs where a list's side rests on
few bills, checked blind by Opus — is the bill about the statement's issue, which way it moves relative to the statement, is
the issue its main purpose or a side effect. Measures the real cost and how Opus agrees with the labels and with Jev.

Sample: list × direction cells (shown lists, quiz directions) with <= 5 distinct bills authored by the list's ex-MKs (Knessets
24–25); their pairs, deduplicated by (bill name, direction); stratified by the Jev relevance score (relevance_q2.jsonl) —
[0, 0.1), [0.1, 0.3), [0.3, 0.7), [0.7, 1]: 12 / 13 / 13 / 12; seed 20261017. Input = what Jev saw: Hebrew title + first 3,000
characters of the explanatory notes.

Usage: python3 local/research/scripts/opus_auth_pilot.py build    -> local/research/opus_pilot/input_{1,2}.md (blind), key.csv
       python3 local/research/scripts/opus_auth_pilot.py compare  -> local/research/opus_pilot/summary.txt (after out_{1,2}.jsonl)
"""
import collections, csv, json, os, random, sys
import duckdb, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "local/research/opus_pilot"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import labels

def build():
    lab = labels.load(relevance=False)["bill_lab"]
    cand = pd.read_csv(f"{ROOT}/manual/candidate_mk_26.csv"); cm = cand[cand.match.isin(["exact", "manual"])]
    cov = pd.read_csv(f"{ROOT}/jef/positions/list_coverage.csv"); shown = set(cov[cov.status != "not_evaluated"].letters)
    cm = cm[cm.letters.isin(shown)].drop_duplicates("mk_id"); mk2l = dict(zip(cm.mk_id.astype(int), cm.letters))
    st = collections.defaultdict(list)
    for r in csv.DictReader(open(f"{ROOT}/jef/quiz/statements_v4.csv")):
        if r["status"] == "ok": st[r["d"]].append(r)
    con = duckdb.connect(f"{ROOT}/knesset.duckdb", read_only=True)
    ini = con.sql("select distinct bill_id, mk_id from bill_initiators where is_initiator").df()
    b = con.sql("select bill_id, knesset, name from bills where knesset in (24, 25)").df().set_index("bill_id")
    ini = ini[ini.mk_id.isin(mk2l) & ini.bill_id.isin(b.index)]
    rel = {(int(r["bill_id"]), r["d"]): r["p"] for r in map(json.loads, open(labels.REL_FILE))}
    cells = collections.defaultdict(set)
    for x, m in zip(ini.bill_id, ini.mk_id):
        if x in lab:
            for d in labels.signed_topics(lab[x]):
                if d in st: cells[(mk2l[m], d)].add(x)
    pool, seen = [], set()
    for (l, d), bills in sorted(cells.items()):
        if len(bills) > 5: continue
        for x in sorted(bills):
            k = (b.name[x], d)
            if k in seen: continue
            seen.add(k); pool.append((x, d))
    rnd = random.Random(20261017)
    sample = []
    for (lo, hi), n in zip([(0, .1), (.1, .3), (.3, .7), (.7, 1.01)], (12, 13, 13, 12)):
        sample += rnd.sample([p for p in pool if lo <= rel[p] < hi], n)
    rnd.shuffle(sample)
    key = []
    for i, (x, d) in enumerate(sample, 1):
        main, sec = lab[x]
        sign = labels.signed_topics(lab[x])[d]
        role = "main" if d in {str(t["n"]) for t in main} else "secondary"
        for s in st[d]:
            key.append(dict(id=i, bill_id=x, d=d, q=s["q"], label_dir="agree" if sign * (1 if s["agree_key"] == "+" else -1) > 0 else "disagree",
                            label_role=role, jev_p=rel[(x, d)], name=b.name[x]))
    pd.DataFrame(key).to_csv(f"{OUT}/key.csv", index=False)
    for part, items in ((1, list(enumerate(sample, 1))[:25]), (2, list(enumerate(sample, 1))[25:])):
        L = []
        for i, (x, d) in items:
            p = f"{ROOT}/data/bill_texts/{x}.json"
            notes = json.load(open(p))["notes"][:3000] if os.path.exists(p) else "(no explanatory notes)"
            L.append(f"## Pair {i}\n\nStatement(s):")
            for s in st[d]: L.append(f"- q{s['q']} «{s['title_en']}»: {s['statement_en']}")
            L.append(f"\nBill title (Hebrew): {b.name[x]}\n\nExplanatory notes (Hebrew, first 3,000 characters):\n\n{notes.strip()}\n")
        open(f"{OUT}/input_{part}.md", "w").write("\n".join(L))
    print(f"pool {len(pool)} pairs; sample {len(sample)}; statements in key {len(key)}")

def compare():
    K = pd.read_csv(f"{OUT}/key.csv", dtype={"d": str, "q": str})
    O = [json.loads(l) for f in ("out_1.jsonl", "out_2.jsonl") for l in open(f"{OUT}/{f}") if l.strip()]
    pair = {o["id"]: o for o in O}
    dirs = {(o["id"], str(s["q"]).lstrip("q")): s["direction"] for o in O for s in o["statements"]}
    K["about"] = K.id.map(lambda i: pair[i]["about_issue"]); K["role"] = K.id.map(lambda i: pair[i]["role"])
    K["dir"] = [dirs.get((i, q)) for i, q in zip(K.id, K.q)]
    K.to_csv(f"{OUT}/compared.csv", index=False)
    P = K.drop_duplicates("id")
    L = []
    def p(*a): L.append(" ".join(str(x) for x in a)); print(L[-1])
    p(f"pairs {len(P)}, statements {len(K)}")
    p("\nOpus «about the statement's issue» by Jev band:")
    P = P.assign(band=pd.cut(P.jev_p, [0, .1, .3, .7, 1.01], right=False))
    p(pd.crosstab(P.band, P.about).to_string())
    yes = P.about.isin(["yes", "partly"])
    for t in (0.1, 0.2, 0.3, 0.5):
        j = P.jev_p >= t
        p(f"Jev threshold {t}: agree with Opus (yes+partly = about) {(j == yes).mean():.0%}; Opus-about kept {(j & yes).sum()}/{yes.sum()}; "
          f"Opus-not-about removed {(~j & ~yes).sum()}/{(~yes).sum()}")
    a = K[K.about.isin(["yes", "partly"])]
    p(f"\nsign (pairs Opus says are about the issue; per statement): label = Opus {(a.label_dir == a.dir).sum()}, "
      f"opposite {((a.dir.isin(['agree', 'disagree'])) & (a.label_dir != a.dir)).sum()}, Opus «neither» {(a.dir == 'neither').sum()} of {len(a)}")
    p("\nrole, label vs Opus (all pairs):"); p(pd.crosstab(P.label_role, P.role).to_string())
    p("\nper role of the label: share Opus says is about the issue")
    for r, g in P.groupby("label_role"): p(f"  {r}: {g.about.isin(['yes', 'partly']).mean():.0%} (n={len(g)})")
    open(f"{OUT}/summary.txt", "w").write("\n".join(L) + "\n")

if __name__ == "__main__":
    {"build": build, "compare": compare}[sys.argv[1]]()
