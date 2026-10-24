"""Steps of the systematic label check (docs/LABEL_CHECK.md) for one statement, after core_full_input.py built items_*.md / key.csv.

Usage: python3 tools/label_check_step.py <q> merge1   -> merged1.csv; prints candidates and proposed sign changes;
                                                                          writes check2_items.md / check2_key.csv (removal candidates
                                                                          + controls, ≥ a third of the candidates, at least 2) and
                                                                          flip_in.csv (sign changes + 2 controls) for flip_check.py
       python3 tools/label_check_step.py <q> merge2   -> check2_merged.csv; check3_items.md / check3_key.csv
                                                                          (candidates the second check called borderline)
       python3 tools/label_check_step.py <q> apply    -> overrides.json «remove» (two checks, or 2 of 3) and «flip»
                                                                          (first check and the full-notes check agree);
                                                                          borderline_resolved.csv for the third-check items
"""
import csv, glob, json, math, os, random, re, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q, STEP = sys.argv[1], sys.argv[2]
D = f"{ROOT}/local/research/label_check_q{Q}"
LAB = f"{ROOT}/data/directions/labels"
SRC = os.environ.get("SRC", f"label check q{Q} (2026-10-19)")

def rows(f, cols):
    out = []
    for l in open(f).read().splitlines()[1:]:
        p = l.split(",", len(cols) - 1)
        out.append({c: (p[i].strip('"').replace("-", "−") if c.startswith("s") and len(c) <= 6 else p[i].strip('"')) if i < len(p) else "" for i, c in enumerate(cols)})
    return pd.DataFrame(out)

def sections():
    sec = {}
    for f in glob.glob(f"{D}/items_*.md"):
        sec.update({h: b for h, b in re.findall(r"## (F\d+-\d+)\n(.*?)(?=\n## |\Z)", open(f).read(), re.S)})
    return sec

def write_items(df, idcol, out, title):
    sec = sections(); L = [f"# Items: {title}", ""]
    for _, x in df.iterrows(): L += [f"## {x[idcol]}", sec[x.id].strip(), ""]
    open(f"{D}/{out}", "w").write("\n".join(L) + "\n")

if STEP == "merge1":
    k = pd.read_csv(f"{D}/key.csv", dtype=str)
    r = pd.concat([rows(f, ["id", "verdict", "sign_j", "reason"]) for f in sorted(glob.glob(f"{D}/result_*.csv"))])
    r["sign_j"] = r.sign_j.str.replace("-", "−")
    m = k.merge(r, on="id", how="left"); m.to_csv(f"{D}/merged1.csv", index=False)
    print(len(m), "groups", m.verdict.value_counts().to_dict(), "missing", int(m.verdict.isna().sum()))
    cand = m[m.verdict == "not_about"].assign(kind="candidate")
    flip = m[(m.verdict != "not_about") & m.sign_j.notna() & (m.sign_j != m.sign)].assign(kind="flip")
    for _, x in pd.concat([cand, flip]).iterrows():
        print(x.kind, x.id, x.sign, "->", x.sign_j, len(x.bills.split()), x["name"][:80], "|", x.reason)
    ok = list(m[(m.verdict == "about") & (m.sign_j == m.sign)].index); rnd = random.Random(20261019)
    if len(cand):
        n = min(len(ok), max(2, math.ceil(len(cand) / 3)))
        kk = pd.concat([cand, m.loc[rnd.sample(ok, n)].assign(kind="control")]).sample(frac=1, random_state=19).reset_index(drop=True)
        kk["cid"] = [f"C{i+1}" for i in range(len(kk))]
        write_items(kk, "cid", "check2_items.md", "is the bill about the statement's question, and which way?")
        kk.to_csv(f"{D}/check2_key.csv", index=False); print("check2:", len(cand), "candidates +", n, "controls")
    if len(flip):
        rest = [i for i in ok if i not in set(kk.index)] if len(cand) else ok
        fc = m.loc[rnd.sample(ok, min(len(ok), 2))].assign(kind="control")
        pd.concat([flip, fc])[["q", "d", "rep", "name", "kind", "sign", "sign_j"]].to_csv(f"{D}/flip_in.csv", index=False)
        print("flip_in:", len(flip), "sign changes + 2 controls -> run flip_check.py")

elif STEP == "merge2":
    k = pd.read_csv(f"{D}/check2_key.csv", dtype=str)
    m = k.merge(rows(f"{D}/check2_result.csv", ["cid", "v2", "s2", "r2"]), on="cid"); m.to_csv(f"{D}/check2_merged.csv", index=False)
    print(m.groupby(["kind", "v2"]).size().to_dict())
    t = m[(m.kind == "candidate") & (m.v2 == "borderline")].reset_index(drop=True)
    if len(t):
        t["tid"] = [f"T{i+1}" for i in range(len(t))]
        write_items(t, "tid", "check3_items.md", "is the bill about the statement's question?")
        t.to_csv(f"{D}/check3_key.csv", index=False)
    print("check3:", len(t))

elif STEP == "apply":
    p = f"{LAB}/overrides.json"; o = json.load(open(p))
    have = {(i["bill_id"], i["d"]) for i in o["remove"]["items"]}; nr = nf = 0
    def rm(x, src):
        global nr
        for b in x.bills.split():
            if (b, x.d) not in have: o["remove"]["items"].append(dict(bill_id=b, d=x.d, q=x.q, role=x.role, source=src, reason=x.reason)); nr += 1
    if os.path.exists(f"{D}/check2_merged.csv"):
        m = pd.read_csv(f"{D}/check2_merged.csv", dtype=str)
        for _, x in m[(m.kind == "candidate") & (m.v2 == "not_about")].iterrows(): rm(x, f"{SRC}: two blind checks «not about»")
    if os.path.exists(f"{D}/check3_result.csv"):
        t = pd.read_csv(f"{D}/check3_key.csv", dtype=str)
        c3 = {r["id"]: r for _, r in rows(f"{D}/check3_result.csv", ["id", "v3", "r3"]).iterrows()}
        w = csv.writer(open(f"{LAB}/borderline_resolved.csv", "a", newline=""), lineterminator="\n")
        for _, x in t.iterrows():
            v3 = c3[x.tid]["v3"]
            if v3 == "not_about": rm(x, f"{SRC}: 2 of 3 blind checks «not about»")
            for b in x.bills.split():
                w.writerow([f"label check q{Q}", x.q, x.d, b, x.role, "not about", x.v2, x.r2, v3,
                            "removed (2 of 3 «not about»)" if v3 == "not_about" else "kept (majority not «not about»)"])
    if os.path.exists(f"{D}/flip_result.csv"):
        k = pd.read_csv(f"{D}/flip_key.csv", dtype=str); m1 = pd.read_csv(f"{D}/merged1.csv", dtype=str)
        f = k.merge(rows(f"{D}/flip_result.csv", ["sid", "v", "s", "why"]), on="sid"); f.to_csv(f"{D}/flip_merged.csv", index=False)
        print(f[["sid", "kind", "rep", "sign", "sign_j", "v", "s"]].to_string())
        for _, x in f[(f.kind == "flip") & (f.v != "not_about") & (f.s == f.sign_j) & (f.s != f.sign)].iterrows():
            g = m1[m1.rep == x.rep].iloc[0]
            for b in g.bills.split():
                o["flip"]["items"].append(dict(bill_id=b, d=x.d, q=x.q, sign=x.s, role=g.role,
                                               source=f"{SRC}: first check and the check on the full notes agree on the sign", reason=x.why)); nf += 1
    open(p, "w").write(json.dumps(o, ensure_ascii=False, indent=1)); print("removed", nr, "flipped", nf)
