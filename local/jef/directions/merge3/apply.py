"""Apply the approved manual merges (all 82 of merge3/proposals.json, approved 2026-10-13) to the 374 directions.
Union-find with sign parity: '~N' joins with the opposite sign to the first id of its proposal.
Output: merge3/directions_v6.json — [{key, name_ru, members:[{n, name, plus, minus, flip}]}]."""
import csv, json
D = {r["n"]: r for r in csv.DictReader(open("jev_test/directions.tsv"), delimiter="\t")}
P = json.load(open("merge3/proposals.json"))
parent, par = {n: n for n in D}, {n: 0 for n in D}   # par: sign parity to parent
def find(x):
    if parent[x] == x: return x, 0
    r, p = find(parent[x]); parent[x], par[x] = r, par[x] ^ p
    return r, par[x]
def union(a, b, flip):
    (ra, pa), (rb, pb) = find(a), find(b)
    if ra == rb:
        assert pa ^ pb == flip, f"sign conflict {a} {b}"; return
    parent[rb], par[rb] = ra, pa ^ pb ^ flip
names = {}
for ids, name in P:
    base = ids[0].lstrip("~")
    for x in ids[1:]: union(base, x.lstrip("~"), int(x.startswith("~")) ^ int(ids[0].startswith("~")))
    names.setdefault(base, []).append(name)
clusters = {}
for n in D:
    r, p = find(n); clusters.setdefault(r, []).append((n, p))
out = []
for r, mem in clusters.items():
    base = [m for m in mem if m[1] == 0][0][0] if r not in names else r
    cand = [nm for b in names for nm in names[b] if find(b)[0] == r]
    out.append({"key": r, "name_ru": min(cand, key=len) if cand else D[r]["name"],
                "members": [{"n": n, "name": D[n]["name"], "plus": D[n]["plus"], "minus": D[n]["minus"], "flip": bool(p)} for n, p in mem]})
json.dump(out, open("merge3/directions_v6.json", "w"), ensure_ascii=False, indent=1)
print(len(D), "->", len(out), "directions;", sum(len(c["members"]) > 1 for c in out), "merged")
for c in out:
    if len(c["members"]) > 4: print(c["name_ru"], [("⇄" if m["flip"] else "") + m["n"] for m in c["members"]])
