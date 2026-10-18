"""Recognition vs number of questions (core 5 + clarifying, fixed length), at 10 % and 20 % answers against the persona's list:
own list 1st, in top 3, and the gain per extra question. Usage: python3 local/research/scripts/flow_curve.py [N]"""
import collections, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import flow_grid as fg

def persona(l, rnd, flip):
    ans = {}
    for r in fg.st:
        x = fg.pos[l].get(r["d"])
        if not x or rnd.random() < 0.2: ans[r["q"]] = "dk"; continue
        a = 0 if abs(x[0]) < 0.1 else (1 if abs(x[0]) < 0.5 else 2); a = int(np.sign(x[0]) * r["key_s"] * a)
        if a and rnd.random() < flip: a = -a
        ans[r["q"]] = a
    return ans
def main():
    N = int(sys.argv[1]) if sys.argv[1:] else 20
    LEN = [5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 50, 60, 70, len(fg.st)]
    for flip in (0.1, 0.2):
        R1, R3 = collections.Counter(), collections.Counter(); rnd = random.Random(2)
        for _ in range(N):
            for l in fg.ok:
                full = persona(l, rnd, flip); core, cl = fg.sequence(full, 5, len(fg.st) - 5); seq = core + cl
                for n in LEN:
                    t = fg.top({q: full[q] for q in seq[:n]}); R1[n] += t[:1] == [l]; R3[n] += l in t
        k = N * len(fg.ok); print(f"\nflip {flip:.0%}")
        prev = None
        for n in LEN:
            a, b = R1[n] / k, R3[n] / k
            print(f"{n:>3} {a:.2f} {b:.2f} " + (f"{(a - prev[1]) / (n - prev[0]) * 100:+.1f}" if prev else ""), flush=True); prev = (n, a)

if __name__ == "__main__": main()
