"""Label batches 9..12 one after another (approved 2026-10-14). Stops if (a) the estimated Jev balance would not cover the
next batch, or (b) a batch reports errors or did not label all its bills. Balance at start: $8.59 (given by the user)."""
import json, subprocess, sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L = f"{ROOT}/jef/directions/labels"
balance, per_bill, margin = 8.59, 0.00166, 1.10
for batch in range(9, 13):
    ids = subprocess.run(["python3", "jev_label.py", "ids", str(batch)], cwd=f"{ROOT}/pipeline/labeling", capture_output=True, text=True).stdout.split()
    if not ids: print(f"batch {batch}: empty, done", flush=True); break
    need = len(ids) * per_bill * margin
    if need > balance:
        print(f"STOP before batch {batch}: need ~${need:.2f}, balance ~${balance:.2f}", flush=True); break
    open(f"{L}/ids_{batch:02d}.txt", "w").write("\n".join(ids) + "\n")
    t = subprocess.run(["python3", "bill_texts.py", "--file", f"{L}/ids_{batch:02d}.txt"], cwd=f"{ROOT}/pipeline/labeling", capture_output=True, text=True)
    print(f"batch {batch}: {len(ids)} bills, texts: {t.stderr.strip().splitlines()[-1] if t.stderr.strip() else 'ok'}", flush=True)
    with open(f"{ROOT}/jef/directions/labels_batch_{batch:02d}.log", "w") as log:
        r = subprocess.run(["python3", "jev_label.py", str(batch)], cwd=f"{ROOT}/pipeline/labeling", stdout=subprocess.PIPE, stderr=log, text=True)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: res = {"labeled": 0, "errors": -1, "usd": 0, "stopped": True}
    balance -= res.get("usd", 0)
    print(f"batch {batch}: {json.dumps(res)}  balance ~${balance:.2f}", flush=True)
    done = sum(1 for _ in open(f"{L}/batch_{batch:02d}.jsonl"))
    if r.returncode or res.get("errors") or res.get("stopped") or done != len(ids):
        print(f"STOP: batch {batch} failed or incomplete ({done}/{len(ids)})", flush=True); break
print("FINISHED", flush=True)
