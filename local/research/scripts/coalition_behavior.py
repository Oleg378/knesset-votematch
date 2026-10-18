"""Customer Р2 (2026-10-18, external audit С2): coalition for cleaning votes = faction with a minister OR a faction that votes with the
government majority in >= X % of its votes in that Knesset (outside the transition windows). Positions recomputed with positions.py
patched in memory (outputs to local/research/coalition_behavior/X/). Reports: which factions switch, and list-level effect.
Usage: python3 local/research/scripts/coalition_behavior.py 0.8 0.9
"""
import os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open(f"{ROOT}/pipeline/positions.py").read()
anchor = "rv = ro.dropna(subset=['v']).copy()\n\n# ======================= A: authorship"
assert anchor in src
patch = '''
# --- research patch: behavioural coalition (X = BEH_X) ---
_g = ro.dropna(subset=['v']); _g = _g[~_g.trans]
_gm = _g[_g.gov_side].groupby('vote_id').v.mean().rename('gm'); _g = _g.join(_gm, on='vote_id'); _g = _g[_g.gm.notna() & (_g.gm != 0)]
_g['w'] = np.sign(_g.v) == np.sign(_g.gm)
_fs = _g[_g.faction_id.notna()].groupby([_g.faction_id.astype(int), 'knesset']).agg(share=('w', 'mean'), n=('w', 'size'), ingov=('gov_side', 'mean'))
_beh = _fs[(_fs.share >= BEH_X) & (_fs.ingov < 0.5) & (_fs.n >= 200)]
P('behavioural coalition factions (X=' + str(BEH_X) + '):', [(int(f), int(k), fname.get(int(f)), round(r.share, 3), round(r.ingov, 2)) for (f, k), r in _beh.iterrows()])
_add = set()
for (f, k), r in _beh.iterrows():
    days = ro[(ro.faction_id == f) & (ro.knesset == k)].vote_date.unique()
    _add |= {(int(f), pd.Timestamp(d)) for d in days}
INGOV |= _add
ro['gov_side'] = [(int(f), d) in INGOV if pd.notna(f) else False for f, d in zip(ro.faction_id, ro.vote_date)]
'''
for x in sys.argv[1:]:
    out = f"{ROOT}/local/research/coalition_behavior/{x}"; os.makedirs(out, exist_ok=True)
    s = src.replace("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))", f"ROOT = {ROOT!r}")
    s = s.replace("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))", f"sys.path.insert(0, {ROOT + '/pipeline'!r})")
    s = s.replace("OUT = f'{ROOT}/jef/positions'", f"OUT = {out!r}").replace(anchor, patch.replace("BEH_X", x) + "\n" + anchor)
    open(f"{out}/positions_patched.py", "w").write(s)
    r = subprocess.run([sys.executable, f"{out}/positions_patched.py"], capture_output=True, text=True, cwd=ROOT)
    print(f"== X = {x}", [l for l in r.stdout.splitlines() if "behavioural" in l], r.stderr[-500:] if r.returncode else "")
