"""Nested theme pairs for the meaning check (SHARED_UNDERSTANDING «Вложенные темы — глобальный аудит», [У] 2026-10-20): every pair where
≥ 50 % of the narrow theme's bills (by name without the year) are also in the broad theme (theme_overlap.py -> nested_small_in_big.csv).
Blind: the checker sees the two themes' names and «+»/«−» definitions only (no counts, no statements, no positions), in a shuffled order.
-> local/research/theme_overlap/nested_items.md, nested_key.csv
"""
import csv, os, sys, random
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = f"{ROOT}/local/research/theme_overlap"
sys.path.insert(0, f"{ROOT}/pipeline"); import labels as LB
D = {r["n"]: (r["name_en"], r["plus"], r["minus"]) for r in csv.DictReader(open(f"{ROOT}/jef/directions/DIRECTIONS_LIST.csv"))}
for k, v in LB.load()["split_plan"]["new"].items(): D[k] = (v["name_en"], v.get("plus_en", ""), v.get("minus_en", ""))
N = pd.read_csv(f"{O}/nested_small_in_big.csv", dtype={"small_d": str, "big_d": str})
N = N[N.pct_small >= 0.5].sample(frac=1, random_state=20261020).reset_index(drop=True)
N["pid"] = [f"P{i+1}" for i in range(len(N))]
L = ["# Pairs of themes", ""]
for r in N.itertuples():
    a, b = D[r.small_d], D[r.big_d]
    L += [f"## {r.pid}", f"Theme 1: «{a[0]}». +: {a[1]} −: {a[2]}", f"Theme 2: «{b[0]}». +: {b[1]} −: {b[2]}", ""]
open(f"{O}/nested_items.md", "w").write("\n".join(L) + "\n")
N.to_csv(f"{O}/nested_key.csv", index=False)
print(len(N), "pairs")
