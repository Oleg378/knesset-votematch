"""PROVISIONAL follow-up 2: list-level stability (A) and authorship stability (B).
Reuses loaders from test_hypotheses.py and helpers from test_followup.py via exec of their source (those files not modified).
Run: python3 jef/positions_test/test_followup2.py -> stdout + followup2_out.txt
"""
import numpy as np, pandas as pd

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
src = open(f'{OUT}/test_hypotheses.py').read()
g = {}
exec(src.split("posA.to_csv")[0], g)
fsrc = open(f'{OUT}/test_followup.py').read()
g['rng'] = np.random.default_rng(11)
exec(fsrc[fsrc.index('def wpos'):fsrc.index('def pair_r')], g)  # wpos, center, resid_on
X, va, rv, coal, wpos, center, resid_on, con, SGN, bill_lab = (g[k] for k in (
    'X', 'va', 'rv', 'coal', 'wpos', 'center', 'resid_on', 'con', 'SGN', 'bill_lab'))
rng = np.random.default_rng(11)
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('\n=== FOLLOW-UP 2 (PROVISIONAL formula) ===')
cs = coal.set_index(['mk_id', 'knesset']).coal_share

cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cand = cand[cand.match.isin(['exact', 'manual'])].copy(); cand['mk_id'] = cand.mk_id.astype(int)
cl = cand[['letters', 'mk_id']].drop_duplicates()
lists3 = cl[cl.mk_id.isin(set(rv.mk_id))].groupby('letters').mk_id.nunique()
lists3 = lists3[lists3 >= 3].index
cl = cl[cl.letters.isin(lists3)]

def corr_perm(w, nperm=1000):
    """w: DataFrame index (unit, d), columns 24, 25. Permute unit labels of K25."""
    r = w[24].corr(w[25])
    units = sorted(set(w.index.get_level_values(0)))
    s24 = w[24]; s25 = w[25]
    perms = []
    for _ in range(nperm):
        mp = dict(zip(units, rng.permutation(units)))
        q = s25.copy(); q.index = pd.MultiIndex.from_tuples([(mp[u], d) for u, d in q.index])
        j = pd.concat([s24, q], axis=1, keys=[24, 25]).dropna()
        perms.append(j[24].corr(j[25]) if len(j) > 2 else np.nan)
    perms = np.array(perms)
    return r, perms

# ---------------- TEST A ----------------
P('\n# TEST A: list-level stability K24 vs K25 (lists with ≥3 matched MKs; per list×Knesset×dir need ≥2 candidates with votes and ≥5 votes in total)')
roles = cl.merge(coal, on='mk_id').groupby(['letters', 'knesset']).coal_share.mean().unstack()
roles['switched'] = (roles[24] > .5) != (roles[25] > .5)
P('list mean coalition share K24 / K25 (switched?):', {l: (round(r[24], 2), round(r[25], 2), bool(r.switched)) for l, r in roles.iterrows()})
P('candidates per list in K24 / K25 with votes:', {l: (int(q[q.knesset == 24].mk_id.nunique()), int(q[q.knesset == 25].mk_id.nunique()))
   for l, q in cl.merge(X[['mk_id', 'knesset']].drop_duplicates(), on='mk_id').groupby('letters')})

def list_level(p):  # p: MK-level with val, n
    m = cl.merge(p, on='mk_id')
    a = m.groupby(['letters', 'knesset', 'd']).agg(val=('val', 'mean'), nmk=('mk_id', 'size'), nv=('n', 'sum')).reset_index()
    a = a[(a.nmk >= 2) & (a.nv >= 5)]
    return a.pivot_table(index=['letters', 'd'], columns='knesset', values='val').dropna()

def repA(name, p):
    w = list_level(p)
    r, perms = corr_perm(w)
    sw = set(roles[roles.switched].index)
    msw = w.index.get_level_values(0).isin(sw)
    rs = w[msw][24].corr(w[msw][25]); rn = w[~msw][24].corr(w[~msw][25])
    P(f'{name}: r={r:.3f} pairs {len(w)} lists {w.index.get_level_values(0).nunique()} | perm mean {np.nanmean(perms):.3f} 95% [{np.nanquantile(perms,.025):.3f}, {np.nanquantile(perms,.975):.3f}]'
      f' | switched lists r={rs:.3f} (pairs {msw.sum()}), same-role r={rn:.3f} (pairs {(~msw).sum()})')
    return w
pk = wpos(X)
wraw = repA('raw', pk.assign(val=pk.pos))
repA('centered per Knesset×dir', center(pk))
wb1 = repA('(b1) residual on coalition share (MK level) then averaged', resid_on(pk, cs))
pp = wpos(X[X.bill_type == 'פרטית'])
repA('(c) private bills only + b1', resid_on(pp, cs))
# per-list r (b1)
P('per-list r, raw / b1 (pairs):', {l: (round(wraw.loc[l][24].corr(wraw.loc[l][25]), 2), round(wb1.loc[l][24].corr(wb1.loc[l][25]), 2), len(wb1.loc[l]))
   for l in wb1.index.get_level_values(0).unique() if l in wraw.index.get_level_values(0)})

# ---------------- TEST B ----------------
P('\n# TEST B: authorship stability (initiators only, main+secondary, sign mean per MK×Knesset×dir; Knesset = bills.knesset)')
bi = con.execute("select i.bill_id, i.mk_id, b.knesset from bill_initiators i join bills b using(bill_id) where i.is_initiator").df()
rows = []
for b, (mn, sc) in bill_lab.items():
    for t in mn + sc:
        s = SGN.get(t.get('sign'))
        if s: rows.append((b, str(t['n']), s))
ab = pd.DataFrame(rows, columns=['bill_id', 'd', 's']).drop_duplicates(['bill_id', 'd'])
au = bi.merge(ab, on='bill_id').groupby(['mk_id', 'knesset', 'd']).s.agg(['mean', 'count']).reset_index().rename(columns={'mean': 'pos', 'count': 'n'})
P('authored bills by Knesset:', bi.drop_duplicates('bill_id').knesset.value_counts().to_dict(), '| MK×K×dir rows:', len(au))
both = set(au[au.knesset == 24].mk_id) & set(au[au.knesset == 25].mk_id)
P('MKs authoring in both Knessets:', len(both))

def repB(name, p, nmin):
    q = p[p.n >= nmin]
    w = q.pivot_table(index=['mk_id', 'd'], columns='knesset', values='val').dropna()
    r, perms = corr_perm(w, nperm=300)
    bothplus = ((w[24] == 1) & (w[25] == 1)).mean()
    nonp = w[(w[24] != 1) | (w[25] != 1)]
    P(f'{name} n≥{nmin}: r={r:.3f} pairs {len(w)} MKs {w.index.get_level_values(0).nunique()} | perm mean {np.nanmean(perms):.3f} 95% [{np.nanquantile(perms,.025):.3f}, {np.nanquantile(perms,.975):.3f}]'
      f' | both=+1 share {bothplus:.2f} | r on pairs with ≥1 non-+1: {nonp[24].corr(nonp[25]):.3f} (pairs {len(nonp)})')
for nmin in (3, 2):
    repB('raw', au.assign(val=au.pos), nmin)
    # center over MKs with same threshold within Knesset×dir
    q = au[au.n >= nmin]; repB('centered', q.assign(val=q.pos - q.groupby(['knesset', 'd']).pos.transform('mean')), nmin)
P('share of MK×K×dir authorship pos == +1 (n≥3):', round((au[au.n >= 3].pos == 1).mean(), 3), '| == −1:', round((au[au.n >= 3].pos == -1).mean(), 3))

# list level authorship: mean over candidates with ≥1 authored bill on d; need ≥2 such candidates
m = cl.merge(au, on='mk_id')
la = m.groupby(['letters', 'knesset', 'd']).agg(val=('pos', 'mean'), nmk=('mk_id', 'size'), nb=('n', 'sum')).reset_index()
for nm, la2 in (('raw', la), ('centered', la.assign(val=la.val - la.groupby(['knesset', 'd']).val.transform('mean')))):
    w = la2[la2.nmk >= 2].pivot_table(index=['letters', 'd'], columns='knesset', values='val').dropna()
    r, perms = corr_perm(w)
    nonp = w[(w[24] != 1) | (w[25] != 1)]
    P(f'list-level authorship {nm} (≥2 authoring candidates): r={r:.3f} pairs {len(w)} lists {w.index.get_level_values(0).nunique()} | perm mean {np.nanmean(perms):.3f} 95% [{np.nanquantile(perms,.025):.3f}, {np.nanquantile(perms,.975):.3f}]'
      f' | both=+1 {((w[24]==1)&(w[25]==1)).mean():.2f} | r non-+1 pairs {nonp[24].corr(nonp[25]):.3f} ({len(nonp)})')

open(f'{OUT}/followup2_out.txt', 'w').write('\n'.join(lines) + '\n')
