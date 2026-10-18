"""Point 2 after «authorship not centered» (SU 27.3, 2026-10-17, variant Б): re-run the weight test that chose A = 1, V = 0.25
(local/research/positions_test/test_weights.py, 2026-10-14) with A not centered, next to the original run on today's data.

Variant «uncentered»: the authorship component A (and the authorship target T1) keep the raw sign; non-authors stay 0 as before.
V, G (residuals) and B (against-bloc votes) unchanged. Nothing else in the test is touched; outputs go to
local/research/weights_uncentered/{centered,uncentered}/ (weights_out.txt, grids). The original files are not modified.

Usage: python3 local/research/scripts/weights_uncentered.py [centered|uncentered]   (default: both)
"""
import contextlib, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PT = os.path.join(ROOT, "local/research/positions_test")
OLD = "/Users/oleg/Documents/elections-research/jef/positions_test"
src = open(f"{PT}/test_weights.py").read()
T1 = "A['T1'] = A.pos - A.groupby(['knesset', 'd']).pos.transform('mean')"
CV = "        v = v - v.groupby(level=['knesset', 'd']).transform('mean')"
BS = "bsrc = open(f'{OUT}/test_blocs.py').read()"
for s in (T1, CV, BS, "OUT = f'{ROOT}/jef/positions_test'"): assert s in src, s

def run(variant):
    out = os.path.join(ROOT, "local/research/weights_uncentered", variant); os.makedirs(out, exist_ok=True)
    s = src.replace("OUT = f'{ROOT}/jef/positions_test'", f"OUT = {out!r}")
    # test_blocs.py and, inside it, test_hypotheses.py are read from the moved folder
    s = s.replace(BS, f"bsrc = open({PT + '/test_blocs.py'!r}).read().replace(\"f'{{ROOT}}/jef/positions_test'\", {repr(repr(PT))})")
    if variant == "uncentered":
        s = s.replace(T1, "A['T1'] = A.pos   # variant: not centered")
        s = s.replace(CV, "        if nm == 'B': v = v - v.groupby(level=['knesset', 'd']).transform('mean')   # variant: A not centered")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(s, f"test_weights_{variant}", "exec"), {"__name__": "tw"})
    print(f"== {variant}: {out}/weights_out.txt")

for v in (sys.argv[1:] or ["centered", "uncentered"]): run(v)
