"""Independent accuracy check of Jev on a stratified 100-bill sample (local/research/independent/).

  python3 local/research/scripts/independent_eval.py pass2   # build the direction packet (scales only, no Jev sides) after pass 1
  python3 local/research/scripts/independent_eval.py eval    # compare blind labels with Jev (key_DO_NOT_SHOW.csv)
"""
import csv, json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_direction_all import question, ROOT

IND = os.path.join(ROOT, "local/research/independent")
BLIND = os.path.join(IND, "blind")

def key():
    return {r["sample_id"]: r for r in csv.DictReader(open(os.path.join(IND, "key_DO_NOT_SHOW.csv"), encoding="utf-8"))}

def pass2():
    axes = json.load(open(os.path.join(ROOT, "local/research/direction/axes.json")))
    bills = {str(b["sample_id"]): b for b in json.load(open(os.path.join(BLIND, "bills.json")))}
    items = []
    for sid, k in key().items():
        if not k["axis"]: continue
        q = question(axes, k["axis"])
        items.append({"sample_id": sid, "bill_id": k["bill_id"], "title_he": bills[sid]["title_he"],
                      "notes_he": bills[sid]["notes_he"], "question": q.instructions, "levels": list(q.criteria)})
    json.dump(items, open(os.path.join(BLIND, "direction_items.json"), "w"), ensure_ascii=False, indent=1)
    print(len(items), "direction items")

def side(level):
    return 0 if abs(level - 2) < 0.5 else (1 if level > 2 else -1)

def evaluate():
    K = key()
    T = {r["sample_id"]: r for r in csv.DictReader(open(os.path.join(BLIND, "labels_topic.csv"), encoding="utf-8"))}
    n = len(T)
    top1 = sum(T[s]["primary"] == K[s]["jev_issue"] for s in T)
    lenient = sum(K[s]["jev_issue"] in (T[s]["primary"], T[s]["secondary"]) for s in T)
    print(f"TOPIC  n={n}  Jev == annotator primary: {top1}/{n} ({top1/n:.0%})  Jev in primary/secondary: {lenient}/{n} ({lenient/n:.0%})")
    for lo, hi in ((0.8, 1.01), (0.5, 0.8), (0, 0.5)):
        s = [x for x in T if lo <= float(K[x]["jev_issue_conf"]) < hi]
        if s: print(f"   Jev conf {lo}-{hi}: n={len(s)}  agree {sum(T[x]['primary'] == K[x]['jev_issue'] for x in s)}/{len(s)}")
    for per in ("K24", "K25_pre", "K25_post"):
        s = [x for x in T if K[x]["period"] == per]
        if s: print(f"   {per:9s} n={len(s)}  agree {sum(T[x]['primary'] == K[x]['jev_issue'] for x in s)}/{len(s)}")
    for cert in ("high", "medium", "low"):
        s = [x for x in T if T[x]["certainty"] == cert]
        if s: print(f"   annotator {cert:6s} n={len(s)}  agree {sum(T[x]['primary'] == K[x]['jev_issue'] for x in s)}/{len(s)}")
    p = os.path.join(BLIND, "labels_direction.csv")
    if not os.path.exists(p): return
    D = {r["sample_id"]: r for r in csv.DictReader(open(p, encoding="utf-8"))}
    rows = [(s, K[s], D[s]) for s in D]
    fits = [(s, k, d) for s, k, d in rows if d["scale_fits"] == "yes" and d["level"] not in ("", "na")]
    print(f"\nDIRECTION  items={len(rows)}  scale fits per annotator: {len(fits)}")
    dec = [(s, k, d) for s, k, d in fits if k["jev_status"] == "decided"]
    ok = sum(int(k["jev_side"]) == side(float(d["level"])) for s, k, d in dec)
    clear = [(s, k, d) for s, k, d in dec if side(float(d["level"])) != 0]
    okc = sum(int(k["jev_side"]) == side(float(d["level"])) for s, k, d in clear)
    print(f"   Jev decided: {len(dec)}  same side as annotator (incl. annotator-neutral): {ok}/{len(dec)}")
    print(f"   where annotator sees a side: {okc}/{len(clear)} ({okc/max(len(clear),1):.0%})  opposite side: "
          f"{sum(int(k['jev_side']) == -side(float(d['level'])) for s, k, d in clear)}")
    for rel in ("high", "medium"):
        s = [(x, k, d) for x, k, d in clear if k["jev_reliability"] == rel]
        if s: print(f"   reliability {rel}: {sum(int(k['jev_side']) == side(float(d['level'])) for x, k, d in s)}/{len(s)}")
    other = collections.Counter(k["jev_status"] for s, k, d in fits if k["jev_status"] != "decided")
    print(f"   not decided by Jev (unclear/disputed): {dict(other)}")
    print("\n   disagreements:")
    for s, k, d in clear:
        if int(k["jev_side"]) != side(float(d["level"])):
            print(f"     #{s} bill {k['bill_id']} axis={k['axis']} jev_side={k['jev_side']} annotator_level={d['level']} ({d.get('note','')[:60]})")

if __name__ == "__main__":
    {"pass2": pass2, "eval": evaluate}[sys.argv[1]]()
