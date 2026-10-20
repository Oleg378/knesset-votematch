"""Compare two blind groupings of the dropped bills (dropped_input.py -> A/out.json, B/out.json).

Per item: theme in A and in B, catalog match in A and in B. Agreement: pairs of items put together by both (co-membership), catalog id
agreement per item, and matched themes (Jaccard of member sets >= 0.5, best partner). A theme can pass the volume criterion of
quiz_select.py (>= 5 distinct names) only if it has >= 5 items, so smaller themes are reported but can never become a statement.
-> local/research/dropped_bills/{compare.csv, compare.md}
"""
import csv, json, os, itertools, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = f"{ROOT}/local/research/dropped_bills"
items = list(csv.DictReader(open(f"{OUT}/items.csv"))); ids = [it["id"] for it in items]
G = {}
for X in "AB":
    o = json.load(open(f"{OUT}/{X}/out.json"))
    th = {i: ("TECH", None) for i in o.get("technical", [])}
    for k, t in enumerate(o["themes"]):
        for i in t["members"]: th[i] = (f"{X}{k}", t.get("catalog") or None)
    miss = [i for i in ids if i not in th]; dup = [i for i, c in collections.Counter(sum((t["members"] for t in o["themes"]), []) + o.get("technical", [])).items() if c > 1]
    print(X, "themes", len(o["themes"]), "catalog-matched", sum(bool(t.get("catalog")) for t in o["themes"]), "technical", len(o.get("technical", [])), "missing", len(miss), "duplicated", len(dup))
    G[X] = (o, th)
(oA, A), (oB, B) = G["A"], G["B"]
tog = lambda T, a, b: T.get(a, ("?",))[0] == T.get(b, ("?",))[0] and T.get(a, ("?",))[0] != "TECH"
pa = pb = both = 0
for a, b in itertools.combinations(ids, 2):
    x, y = tog(A, a, b), tog(B, a, b); pa += x; pb += y; both += x and y
print(f"pairs together: A {pa}, B {pb}, both {both}; F1 {2 * both / (pa + pb):.2f}")
cat_same = sum(A.get(i, (0, None))[1] == B.get(i, (0, None))[1] for i in ids)
print(f"items with the same catalog answer (id or none): {cat_same}/{len(ids)}")
mem = lambda o: [set(t["members"]) for t in o["themes"]]
MA, MB = mem(oA), mem(oB); rows = []
for k, s in enumerate(MA):
    j, m = max(((len(s & t) / len(s | t), n) for n, t in enumerate(MB)), default=(0, None))
    tA, tB = oA["themes"][k], oB["themes"][m] if m is not None else {}
    rows.append(dict(A=f"A{k}", nA=len(s), theme_A=tA["theme_en"], cat_A=tA.get("catalog"), B=f"B{m}", nB=len(MB[m]) if m is not None else 0,
                     theme_B=tB.get("theme_en"), cat_B=tB.get("catalog"), jaccard=round(j, 2), common=len(s & MB[m]) if m is not None else 0))
seen = {r["B"] for r in rows}
for m, t in enumerate(MB):   # B themes that are nobody's best partner from the A side
    if f"B{m}" in seen: continue
    j, k = max(((len(t & s) / len(t | s), n) for n, s in enumerate(MA)), default=(0, 0))
    rows.append(dict(A=f"A{k}", nA=len(MA[k]), theme_A=oA["themes"][k]["theme_en"], cat_A=oA["themes"][k].get("catalog"), B=f"B{m}", nB=len(t),
                     theme_B=oB["themes"][m]["theme_en"], cat_B=oB["themes"][m].get("catalog"), jaccard=round(j, 2), common=len(t & MA[k])))
rows.sort(key=lambda r: -max(r["nA"], r["nB"]))
with open(f"{OUT}/compare.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
big = [r for r in rows if r["nA"] >= 5 or r["nB"] >= 5]
L = ["# Сверка двух группировок выпавших законопроектов", "", f"Тем ≥ 5 названий (могут пройти порог объёма) у A: {sum(len(s) >= 5 for s in MA)}, у B: {sum(len(s) >= 5 for s in MB)}.", "",
     "| A | n | тема A | каталог A | B | n | тема B | каталог B | Жаккар |", "|---|---|---|---|---|---|---|---|---|"]
L += [f"| {r['A']} | {r['nA']} | {r['theme_A']} | {r['cat_A'] or '—'} | {r['B']} | {r['nB']} | {r['theme_B']} | {r['cat_B'] or '—'} | {r['jaccard']} |" for r in big]
open(f"{OUT}/compare.md", "w").write("\n".join(L) + "\n")
print(len(big), "rows with a theme of >= 5 items")
