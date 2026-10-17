"""Parse saved CEC list pages (data/cec/raw/<letters>.txt, saved from gov.il via Chrome) into
manual/cec_candidates_26.csv: letters, list_name, position, name_he (as published: last name first),
party (the party within a joint list the candidate runs for), url.
"""
import csv, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data/cec/raw")

def parse(path, letters, list_name):
    lines = []
    for l in open(path, encoding="utf-8"):
        # some pages run several candidates together on one line: "... 23. רהב ציון 24. גרבי ..."
        lines += [x.strip() for x in re.split(r"\s+(?=\d{1,3}\.)", l.strip())]
    url = lines[0].strip()
    rows, cur = [], None
    for l in lines[1:]:
        m = re.match(r"^(\d{1,3})\.\s*(\D.*)$", l)
        if m:
            cur = {"letters": letters, "list_name": list_name, "position": int(m.group(1)),
                   "name_he": m.group(2).strip(), "party": "", "url": url}
            rows.append(cur)
        elif cur and l.startswith("מטעם"):
            cur["party"] = re.sub(r"^מטעם\s+(מפלגת\s+|תנועת\s+)?", "", l).strip()
    # positions must run 1..n without gaps
    if not rows:  # single-candidate list printed without a number (e.g. שמע): name follows the ballot image line
        i = next((k for k, l in enumerate(lines) if l.startswith("תמונת פתק")), None)
        name = next((l for l in lines[i + 1:] if l), "") if i is not None else ""
        if name and not name.startswith("קבצים"):
            rows = [{"letters": letters, "list_name": list_name, "position": 1, "name_he": name, "party": "", "url": url}]
    pos = [r["position"] for r in rows]
    ok = pos == list(range(1, len(rows) + 1))
    gaps = sorted(set(range(1, max(pos) + 1)) - set(pos)) if pos else []
    return rows, (ok, gaps)

def main():
    links = [l.rstrip("\n").split("\t") for l in open(os.path.join(RAW, "_links.txt"), encoding="utf-8") if l.strip()]
    out, report = [], []
    for letters, name, url in links:
        p = os.path.join(RAW, f"{letters}.txt")
        if not os.path.exists(p):
            report.append((letters, name, "missing", 0)); continue
        rows, (ok, gaps) = parse(p, letters, name)
        out += rows
        report.append((letters, name, "ok" if ok else f"GAPS {gaps[:10]}", len(rows)))
    with open(os.path.join(ROOT, "manual/cec_candidates_26.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["letters", "list_name", "position", "name_he", "party", "url"])
        w.writeheader(); w.writerows(out)
    for r in report: print(*r, sep="\t")
    print("candidates:", len(out))

if __name__ == "__main__":
    main()
