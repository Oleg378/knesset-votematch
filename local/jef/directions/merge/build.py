"""Input for the trial synonym merge: unique general directions of batches 0–6 (gov bills of 0–1 from g01/g01b reruns)."""
import json, collections
B = "blind/"
bills = {}  # bill_id -> (batch, directions)
for k in range(30):
    f = B + (f"batch_{k}.v1.out.json" if k < 2 else f"batch_{k}.out.json")
    for b in json.load(open(f))["bills"]: bills[b["bill_id"]] = (k, b.get("directions", []))
for f in ("batch_g01.out.json", "batch_g01b.out.json"):
    for b in json.load(open(B + f))["bills"]: bills[b["bill_id"]] = (bills[b["bill_id"]][0], b.get("directions", []))
defs = {}
for f in [f"batch_{k}{'.v1' if k < 2 else ''}.out.json" for k in range(30)] + ["batch_g01.out.json", "batch_g01b.out.json"]:
    for g in json.load(open(B + f))["general_directions"]: defs.setdefault(g["name"], (g.get("plus", ""), g.get("minus", "")))
names = collections.defaultdict(lambda: {"n": 0, "ex": []})
for bid, (k, ds) in bills.items():
    for d in ds:
        e = names[d["general"]]; e["n"] += 1
        if len(e["ex"]) < 1 and d["specific"] not in e["ex"]: e["ex"].append(d["specific"])
json.dump({str(b): [k, sorted({d["general"] for d in ds})] for b, (k, ds) in bills.items()}, open("merge/bill_generals.json", "w"), ensure_ascii=False)
with open("merge/input.tsv", "w") as out:
    out.write("id\tname\tplus\tminus\tlaws\texamples\n")
    for i, (n, e) in enumerate(sorted(names.items(), key=lambda x: -x[1]["n"]), 1):
        p, m = defs.get(n, ("", ""))
        out.write(f"G{i}\t{n}\t{p[:90]}\t{m[:60]}\t{e['n']}\t{' | '.join(x[:90] for x in e['ex'])}\n")
print(len(bills), "bills", len(names), "general names")
