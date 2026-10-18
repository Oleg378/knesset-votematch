"""PROVISIONAL follow-up tests (formula is NOT a decision, SU p.27 open).
Reuses data loading from test_hypotheses.py (executes its code up to the first file write; that file is not modified).
Run: python3 jef/positions_test/test_followup.py  -> stdout + followup_out.txt
"""
import numpy as np, pandas as pd

ROOT = '/Users/oleg/Documents/elections-research'
SRC = f'{ROOT}/jef/positions_test/test_hypotheses.py'
src = open(SRC).read()
g = {}
exec(src.split("posA.to_csv")[0], g)  # loading + mkpos(), no file writes
pca_src = src[src.index('def pca_mat'):src.index('pcs = {}')]
exec(pca_src, g)
X, va, vd, rv, ro, coal, mkpos, pca_mat = (g[k] for k in ('X', 'va', 'vd', 'rv', 'ro', 'coal', 'mkpos', 'pca_mat'))
OUT = f'{ROOT}/jef/positions_test'
rng = np.random.default_rng(7)
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('\n=== FOLLOW-UP (PROVISIONAL formula) ===')

# ---------------- TEST 1 ----------------
P('\n# TEST 1: stability of residual K24 vs K25 (same MK, same direction); base filter n>=3 votes per Knesset')
cs = coal.set_index(['mk_id', 'knesset']).coal_share

def wpos(df, w=None):
    df = df.assign(w=1.0 if w is None else w)
    df = df.assign(wc=df.c * df.w)
    a = df.groupby(['mk_id', 'knesset', 'd']).agg(sw=('w', 'sum'), swc=('wc', 'sum'), n=('c', 'size')).reset_index()
    a['pos'] = a.swc / a.sw
    return a[['mk_id', 'knesset', 'd', 'pos', 'n']]

def center(p):
    return p.assign(val=p.pos - p.groupby(['knesset', 'd']).pos.transform('mean'))

def resid_on(p, z):  # z: Series indexed (mk_id, knesset)
    p = p.copy(); p['z'] = [z.get((m, k), np.nan) for m, k in zip(p.mk_id, p.knesset)]
    p = p.dropna(subset=['z']); out = []
    for (k, d), q in p.groupby(['knesset', 'd']):
        if len(q) < 5 or q.z.std() == 0:
            continue
        b = np.polyfit(q.z, q.pos, 1); out.append(q.assign(val=q.pos - np.polyval(b, q.z)))
    return pd.concat(out)

def pair_r(p, nmin=3, nperm=200):
    p = p[p.n >= nmin]
    w = p.pivot_table(index=['mk_id', 'd'], columns='knesset', values='val')
    nn = p.pivot_table(index=['mk_id', 'd'], columns='knesset', values='n')
    w = w.dropna(); nn = nn.loc[w.index]
    r = w[24].corr(w[25]); m5 = (nn[24] >= 5) & (nn[25] >= 5)
    r5 = w[m5][24].corr(w[m5][25])
    # permutation: shuffle MK ids of K25 among MKs present in both
    p24 = p[p.knesset == 24].set_index(['mk_id', 'd']).val
    p25 = p[p.knesset == 25]
    mks = sorted(set(p24.index.get_level_values(0)) & set(p25.mk_id))
    perms = []
    for _ in range(nperm):
        mp = dict(zip(mks, rng.permutation(mks)))
        q = p25[p25.mk_id.isin(mks)].assign(mk_id=lambda x: x.mk_id.map(mp)).set_index(['mk_id', 'd']).val
        j = pd.concat([p24, q], axis=1, keys=[24, 25]).dropna()
        perms.append(j[24].corr(j[25]))
    perms = np.array(perms)
    return r, len(w), r5, int(m5.sum()), len(set(w.index.get_level_values(0))), perms

def report(name, p, nperm=200):
    r, n, r5, n5, nmk, perms = pair_r(p, nperm=nperm)
    P(f'{name}: r={r:.3f} (pairs {n}, MKs {nmk}) | both ≥5 votes: r={r5:.3f} (pairs {n5}) | permutation r mean {perms.mean():.3f}, 95% [{np.quantile(perms,.025):.3f}, {np.quantile(perms,.975):.3f}]')
    return r

pk = wpos(X)
raw = pk.assign(val=pk.pos)
report('raw (check, expect 0.17)', raw)
report('(a) centered per Knesset×direction', center(pk))
report('(b1) residual on coalition share, per Knesset', resid_on(pk, cs))
pc1 = {}
for k in (24, 25):
    M, ev, sc, ld = pca_mat(pk[pk.knesset == k][['mk_id', 'd', 'pos', 'n']])
    for m, v in sc.PC1.items(): pc1[(m, k)] = v
report('(b2) residual on PC1 (per-Knesset PCA as in H3)', resid_on(pk, pd.Series(pc1)))
priv = X[X.bill_type == 'פרטית']
pp = wpos(priv)
report('(c) private bills only, residual on coalition share', resid_on(pp, cs))
report('(c0) private bills only, centered (no regression)', center(pp))

# (d) against own bloc
maj = rv[rv.bloc.isin(['coalition', 'opposition'])].groupby(['vote_id', 'bloc']).v.mean().rename('bm').reset_index()
Xd = X.merge(maj, on=['vote_id', 'bloc'])
dev = Xd[(np.sign(Xd.v) != np.sign(Xd.bm)) & (Xd.bm != 0)]
P(f'(d) against-own-bloc contributions: {len(dev)} of {len(Xd)} ({len(dev)/len(Xd):.1%}); distinct votes {dev.vote_id.nunique()}')
pdv = wpos(dev)
both = set(pdv[pdv.knesset == 24].mk_id) & set(pdv[pdv.knesset == 25].mk_id)
for nmin in (1, 3, 5):
    q = pdv[pdv.n >= nmin]; w = q.pivot_table(index=['mk_id', 'd'], columns='knesset', values='pos').dropna()
    P(f'   pairs MK×dir with ≥{nmin} deviant votes in BOTH Knessets: {len(w)} (MKs {w.index.get_level_values(0).nunique()})' +
      (f', r={w[24].corr(w[25]):.3f}' if len(w) > 10 else ''))
if True:
    q = pdv.assign(val=pdv.pos)
    r, n, r5, n5, nmk, perms = pair_r(q, nmin=1)
    P(f'(d) n≥1: r={r:.3f} pairs {n} MKs {nmk}; both≥5: r={r5:.3f} pairs {n5}; perm mean {perms.mean():.3f} 95% [{np.quantile(perms,.025):.3f},{np.quantile(perms,.975):.3f}]')
    # deviant MKs: share deviant votes and top
    sh = Xd.drop_duplicates(['vote_id', 'mk_id']).assign(dv=lambda x: (np.sign(x.v) != np.sign(x.bm)) & (x.bm != 0))
    P('   share of deviant votes per MK: median', round(sh.groupby('mk_id').dv.mean().median(), 3), 'p90', round(sh.groupby('mk_id').dv.mean().quantile(.9), 3))

# package weighting: weight = 1/number of topics of the vote
ntop = vd.groupby('vote_id').d.nunique()
w_all = 1 / X.vote_id.map(ntop)
pkw = wpos(X, w_all.values)
report('(b1) weight 1/n_topics for ALL votes', resid_on(pkw, cs))
whole_ids = set(g['pk_whole'])
w_wh = np.where(X.vote_id.isin(whole_ids), w_all, 1.0)
report('(b1) weight 1/n_topics for package-whole votes only', resid_on(wpos(X, w_wh), cs))
P(f'   package-whole votes: {len(whole_ids & set(X.vote_id))}, topics per vote {sorted(ntop.reindex(list(whole_ids)).dropna().astype(int).tolist())}; median topics per ordinary vote {ntop.median()}')

# ---------------- TEST 2 ----------------
P('\n# TEST 2: absences and boycott (SU 14.3: own bloc participation <0.1 while other ≥0.4)')
con = g['con']
vp = con.execute("""select vote_id, coal_participation cp, opp_participation op, participation_pattern pat from vote_attrs
  where kind='bill' and stage in ('preliminary','first','second','third')""").df().merge(va[['vote_id', 'bill_type', 'knesset']], on='vote_id')
r2 = ro.merge(vp, on='vote_id')
r2['own'] = np.where(r2.bloc == 'coalition', r2.cp, np.where(r2.bloc == 'opposition', r2.op, np.nan))
r2['oth'] = np.where(r2.bloc == 'coalition', r2.op, np.where(r2.bloc == 'opposition', r2.cp, np.nan))
r2['boy'] = (r2.own < 0.1) & (r2.oth >= 0.4)
ab = r2[r2.result.isna()]
P(f'absent rows: {len(ab)}; on own-bloc boycott votes: {int(ab.boy.sum())} ({ab.boy.mean():.1%})')
P('absent rows by bloc: total / boycott:', {b: (len(q), int(q.boy.sum())) for b, q in ab.groupby('bloc', dropna=False)})
P('absent rows by bloc × bill type (total / boycott):')
for (b, t), q in ab.groupby(['bloc', 'bill_type']):
    P(f'   {b:11s} {t:8s}: {len(q):7d} / {int(q.boy.sum()):6d} ({q.boy.mean():.1%})')
bv = vp.assign(coal_boy=(vp.cp < .1) & (vp.op >= .4), opp_boy=(vp.op < .1) & (vp.cp >= .4))
P(f'votes with coalition boycott: {int(bv.coal_boy.sum())}, opposition boycott: {int(bv.opp_boy.sum())} of {len(bv)}; by bill type:',
  bv.groupby('bill_type')[['coal_boy', 'opp_boy']].sum().astype(int).to_dict('index'))
P('boycott votes by participation_pattern:', bv[bv.coal_boy | bv.opp_boy].pat.value_counts().to_dict())
P('low_turnout votes (both blocs <~0.1?): both <0.1:', int(((vp.cp < .1) & (vp.op < .1)).sum()),
  '| absent rows on such votes:', int(((ab.cp < .1) & (ab.op < .1)).sum()))
P('absent rows on votes where own bloc ≥0.4 participation (individual absence):', int((ab.own >= .4).sum()))

def agreement(df):
    d = df[df.bloc.isin(['coalition', 'opposition'])]
    m = d.groupby(['vote_id', 'bloc']).v.mean().rename('bm').reset_index()
    d = d.merge(m, on=['vote_id', 'bloc'])
    ag = np.sign(d.v) == np.sign(d.bm)
    return ag.mean(), len(d), d.assign(ag=ag)
a0, n0, d0 = agreement(r2.assign(v=r2.result.map({'for': 1, 'against': -1})).dropna(subset=['v']))
r3 = r2.assign(v=r2.result.map({'for': 1, 'against': -1}))
r3.loc[r3.result.isna() & r3.boy, 'v'] = -1
a1, n1, d1 = agreement(r3.dropna(subset=['v']))
P(f'match own bloc majority: votes only {a0:.4f} (n={n0}) -> boycott-absence as "against" {a1:.4f} (n={n1}, +{n1-n0} rows)')
for nm, d in (('votes only', d0), ('with boycott', d1)):
    P(f'   {nm} by bill type:', d.groupby('bill_type').ag.mean().round(4).to_dict(), '| by bloc:', d.groupby('bloc').ag.mean().round(4).to_dict())
# on boycott votes specifically: present voters of boycotting bloc
bb = d1[d1.boy]
P(f'   rows on own-bloc boycott votes: {len(bb)}; of them absences-as-against {int(bb.result.isna().sum())}; present voters {int(bb.result.notna().sum())}, their agreement {bb[bb.result.notna()].ag.mean():.3f}')
# support share for gov bills by opposition with boycott counted
for nm, d in (('votes only', d0), ('with boycott', d1)):
    t = d.groupby(['bloc', 'bill_type']).v.apply(lambda x: (x == 1).mean()).round(3).to_dict()
    P(f'   share "for" by bloc×bill type ({nm}):', t)

open(f'{OUT}/followup_out.txt', 'w').write('\n'.join(lines) + '\n')
