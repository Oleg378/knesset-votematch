"""Snapshot of the inputs that are not in git but that make data and make check need: the database and the raw files
positions.py and export.py read. Kept in the private repository Oleg378/knesset-votematch-data, so the pipeline can run off the
customer's laptop (the downloads themselves need an Israeli IP).

Usage: python3 pipeline/snapshot.py save      copy the files into the snapshot repository (../knesset-votematch-data, cloned
                                             if missing), commit and push
       python3 pipeline/snapshot.py restore   clone the snapshot (or pull it) and copy the files into place here
Env:   SNAPSHOT_DIR  where the snapshot repository lives (default: ../knesset-votematch-data)
       SNAPSHOT_URL  its git URL (default: https://github.com/Oleg378/knesset-votematch-data.git; CI uses a deploy key)
"""
import json, os, shutil, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["knesset.duckdb",                          # pipeline/build/build.py
         "raw/bills/bill.json",                     # export.py (download date), build
         "raw/person_to_position_24_25.json",      # positions.py (government layer), build
         "raw/cec/mk_persons.json"]                 # positions.py (names), cec_match.py
DIR = os.environ.get("SNAPSHOT_DIR", os.path.join(ROOT, "..", "knesset-votematch-data"))
URL = os.environ.get("SNAPSHOT_URL", "https://github.com/Oleg378/knesset-votematch-data.git")

def git(*a, cwd=DIR):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout

def ensure_repo():
    if not os.path.isdir(os.path.join(DIR, ".git")):
        subprocess.run(["git", "clone", "--depth", "1", URL, DIR], check=True)
    else:
        git("pull", "--ff-only")

def save():
    ensure_repo()
    for f in FILES:
        dst = os.path.join(DIR, f); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(os.path.join(ROOT, f), dst)
    # modification times: export.py takes the download date («fetched») from raw/bills/bill.json; a git checkout would reset it
    json.dump({f: os.path.getmtime(os.path.join(ROOT, f)) for f in FILES}, open(os.path.join(DIR, "mtimes.json"), "w"), indent=1)
    with open(os.path.join(DIR, "README.md"), "w") as r:
        r.write("# knesset-votematch-data\n\nPrivate snapshot of the inputs of https://github.com/Oleg378/knesset-votematch that are not in git.\n"
                "Written by `python3 pipeline/snapshot.py save` there; restored by `python3 pipeline/snapshot.py restore`.\n\n"
                + "".join(f"- `{f}`\n" for f in FILES) + "- `mtimes.json` — their modification times (the download date comes from them)\n")
    git("add", "-A")
    if git("status", "--porcelain").strip():
        git("commit", "-q", "-m", f"Snapshot {datetime.date.today()} from {git('rev-parse', '--short', 'HEAD', cwd=ROOT).strip()} of knesset-votematch")
        git("push", "-u", "origin", "HEAD")
        print("pushed")
    else:
        print("no change")

def restore():
    ensure_repo()
    for f in FILES:
        dst = os.path.join(ROOT, f); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(os.path.join(DIR, f), dst)
        print("restored", f)
    for f, t in json.load(open(os.path.join(DIR, "mtimes.json"))).items():
        os.utime(os.path.join(ROOT, f), (t, t))

if __name__ == "__main__":
    {"save": save, "restore": restore}[sys.argv[1]]()
