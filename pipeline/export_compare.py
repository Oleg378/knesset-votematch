"""Does the committed export/ match what the pipeline builds now? Compares the four data files by content, ignoring the two
metadata fields that change with every build (source_commit, generated), and golden.json byte for byte.

Usage: make data && python3 pipeline/export_compare.py     exit 1 and the first differences if the export is stale
The GitHub check (.github/workflows/pipeline.yml) runs exactly this after restoring the snapshot of the inputs.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["export/quiz_core.json", "export/quiz_data.json", "export/quiz_bills.json", "export/stats.json"]
META = {"source_commit", "generated"}

def strip(d):
    if isinstance(d, dict): return {k: strip(v) for k, v in d.items() if k not in META}
    if isinstance(d, list): return [strip(x) for x in d]
    return d

def committed(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"{path}: not in HEAD")
    return r.stdout

def first_diff(a, b, path="$"):
    if type(a) != type(b): return f"{path}: {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b: return f"{path}.{k}: only in {'built' if k in b else 'committed'}"
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d: return d
    elif isinstance(a, list):
        if len(a) != len(b): return f"{path}: {len(a)} vs {len(b)} items"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d: return d
    elif a != b: return f"{path}: {a!r} vs {b!r}"
    return None

bad = []
for f in FILES:
    d = first_diff(strip(json.loads(committed(f))), strip(json.load(open(os.path.join(ROOT, f)))))
    if d: bad.append(f"{f}: {d}")
if committed("export/golden.json") != open(os.path.join(ROOT, "export/golden.json")).read():
    bad.append("export/golden.json: differs from HEAD")
if bad:
    print("export/ is stale (committed vs built):\n  " + "\n  ".join(bad)); sys.exit(1)
print("export/ matches the pipeline (metadata fields ignored)")
