"""Steps 2–3 of the add check (add_check_input.py): a label on a statement's direction is ADDED only where two independent blind checks
say «about» with the same sign (overrides.json «add», rule of 2026-10-18). First-check «borderline» and «not_about» are not added.

Usage: python3 add_check_step.py <dir> merge1 [PARTS]   -> merged1.csv; check2_items_K.md, check2_key.csv: candidates (first check «about»)
                                                          + controls (first check «not_about», a third of the candidates)
       python3 add_check_step.py <dir> apply            -> overrides.json «add» (after check2_result_K.csv)
Env SRC: the source tag written into overrides.json.
"""
import csv, glob, json, math, os, random, re, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D, STEP = os.path.join(ROOT, sys.argv[1]) if not sys.argv[1].startswith("/") else sys.argv[1], sys.argv[2]
SRC = os.environ.get("SRC", "add check (2026-10-21)")
def rows(pattern, cols):
    out = []
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for l in open(f).read().splitlines()[1:]:
            p = l.split(",", len(cols) - 1)
            out.append({c: (p[i].strip().strip('"') if i < len(p) else "") for i, c in enumerate(cols)})
    return pd.DataFrame(out)
def sections():
    sec = {}
    for f in glob.glob(f"{D}/items_*.md"):
        sec.update({h: b for h, b in re.findall(r"## (F\d+-\d+)\n(.*?)(?=\n## |\Z)", open(f).read(), re.S)})
    return sec
if STEP == "merge1":
    parts = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    k = pd.read_csv(f"{D}/key.csv", dtype=str)
    r = rows("result_*.csv", ["id", "verdict", "sign1", "reason1"]); r["sign1"] = r.sign1.str.replace("-", "−")
    m = k.merge(r, on="id", how="left"); m.to_csv(f"{D}/merged1.csv", index=False)
    print(len(m), "groups", m.verdict.value_counts().to_dict(), "missing", int(m.verdict.isna().sum()))
    cand = m[(m.verdict == "about") & m.sign1.isin(["+", "−"])].assign(kind="candidate")
    no = list(m[m.verdict == "not_about"].index); rnd = random.Random(20261021)
    ctrl = m.loc[rnd.sample(no, min(len(no), max(2, math.ceil(len(cand) / 3))))].assign(kind="control")
    kk = pd.concat([cand, ctrl]).sample(frac=1, random_state=21).reset_index(drop=True); kk["cid"] = [f"C{i+1}" for i in range(len(kk))]
    sec = sections(); size = math.ceil(len(kk) / parts)
    for p in range(parts):
        L = ["# Items: is the bill about the statement's question, and which way?", ""]
        for _, x in kk.iloc[p * size:(p + 1) * size].iterrows(): L += [f"## {x.cid}", sec[x.id].strip(), ""]
        open(f"{D}/check2_items_{p + 1}.md", "w").write("\n".join(L) + "\n")
    kk.to_csv(f"{D}/check2_key.csv", index=False); print("check2:", len(cand), "candidates +", len(ctrl), "controls in", parts, "parts")
elif STEP == "apply":
    k = pd.read_csv(f"{D}/check2_key.csv", dtype=str)
    r = rows("check2_result_*.csv", ["cid", "v2", "s2", "r2"]); r["s2"] = r.s2.str.replace("-", "−")
    m = k.merge(r, on="cid"); m.to_csv(f"{D}/check2_merged.csv", index=False)
    print(m.groupby(["kind", "v2"]).size().to_dict())
    p = f"{ROOT}/jef/directions/labels/overrides.json"; o = json.load(open(p)); o.setdefault("add", {}).setdefault("items", [])
    have = {(str(i["bill_id"]), str(i["d"])) for i in o["add"]["items"]}; n = 0
    for _, x in m[(m.kind == "candidate") & (m.v2 == "about") & (m.s2 == m.sign1)].iterrows():
        for b in x.bills.split():
            if (b, x.d) not in have:
                o["add"]["items"].append(dict(bill_id=b, d=x.d, sign=x.s2, role="secondary", source=f"{SRC}: two blind checks «about», same sign",
                                              reason=x.reason1, from_theme=x.src)); n += 1
    open(p, "w").write(json.dumps(o, ensure_ascii=False, indent=1)); print("added", n, "labels")
