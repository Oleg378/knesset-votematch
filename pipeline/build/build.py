"""Rebuild knesset.duckdb from data/ (raw OData dumps) and manual/ (hand-maintained CSV).

Usage: python3 pipeline/build/build.py   (from the repo root or anywhere)
Runs every build/NN_*.sql in order inside one fresh database.
"""
import glob, os, sys, time
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "knesset.duckdb")

def main():
    os.chdir(ROOT)  # SQL files use repo-relative paths
    if os.path.exists(DB): os.remove(DB)
    con = duckdb.connect(DB)
    for path in sorted(glob.glob("pipeline/build/[0-9][0-9]_*.sql")):
        t = time.time()
        con.execute(open(path).read())
        print(f"{os.path.basename(path)}: {time.time() - t:.1f}s", file=sys.stderr)
    con.close()

if __name__ == "__main__":
    main()
