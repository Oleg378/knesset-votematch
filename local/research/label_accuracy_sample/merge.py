import csv, collections
key = {r["id"]: r for r in csv.DictReader(open("key.csv"))}
J = {}
for k in (1, 2):
    for j in "ab":
        for r in csv.DictReader(open(f"result_{k}_{j}.csv")):
            J.setdefault(r["id"], {})[j] = (r["verdict"].strip(), r["sign"].strip().replace("-", "−"))
assert len(J) == 100 and all(len(v) == 2 for v in J.values())
V = collections.Counter(); S = collections.Counter(); dis = []
for i, k in key.items():
    a, b = J[i]["a"], J[i]["b"]
    va, vb = a[0], b[0]
    if va == vb: topic = va
    elif "borderline" in (va, vb): topic = "borderline/" + (va if vb == "borderline" else vb)
    else: topic = "disagree"; dis.append(i)
    V[topic] += 1
    if va != "not_about" and vb != "not_about":
        sa, sb = a[1], b[1]
        S["both agree with ours" if sa == sb == k["sign"] else "both against ours" if sa == sb and sa != k["sign"] else "judges differ"] += 1
print("topic verdicts (judge a / judge b):"); [print(f"  {k:28} {v}") for k, v in V.most_common()]
print("sign among items no judge called not_about:"); [print(f"  {k:28} {v}") for k, v in S.most_common()]
print("disagree about/not_about:", dis)
# per-judge
for j in "ab":
    c = collections.Counter(v[j][0] for v in J.values()); sg = sum(1 for i, v in J.items() if v[j][0] != "not_about" and v[j][1] == key[i]["sign"]); n = sum(1 for v in J.values() if v[j][0] != "not_about")
    print(f"judge {j}: {dict(c)}; sign = ours in {sg}/{n}")
print("roles in sample:", collections.Counter(k["role"] for k in key.values()))
