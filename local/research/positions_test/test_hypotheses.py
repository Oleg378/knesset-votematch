"""PROVISIONAL hypothesis tests for party positions on directions.
Formula is NOT a decision (SU p.27 open). Run: python3 jef/positions_test/test_hypotheses.py
Outputs: CSVs + out.txt (numbers for REPORT.md) in jef/positions_test/.
"""
import json, glob, os, itertools
import numpy as np, pandas as pd, duckdb

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
LAB = f'{ROOT}/jef/directions/labels'
rng = np.random.default_rng(42)
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)

SGN = {'+': 1, '−': -1, '-': -1}
con = duckdb.connect(f'{ROOT}/knesset.duckdb', read_only=True)
dirs = pd.read_csv(f'{ROOT}/jef/directions/DIRECTIONS_LIST.csv', dtype={'n': str})
dname = dict(zip(dirs.n, dirs.name_ru))
ALLD = list(dirs.n)

# ---------- labels ----------
winter = set(json.load(open(f'{LAB}/overrides.json'))['technical']['winter_time']['bill_ids'])
bill_lab = {}
for f in sorted(glob.glob(f'{LAB}/batch_*.jsonl')):
    for l in open(f):
        r = json.loads(l)
        if r['bill_id'] in winter: continue
        bill_lab[int(r['bill_id'])] = (r.get('main') or [], r.get('secondary') or [])
pk_agent = {}
for l in open(f'{LAB}/packages_agent.jsonl'):
    r = json.loads(l)
    pk_agent[int(r['vote_id'])] = ([], []) if r.get('technical') else (r.get('main') or [], r.get('secondary') or [])
pk_whole = {}
for l in open(f'{LAB}/packages_whole.jsonl'):
    r = json.loads(l)
    for v in r['votes']:
        pk_whole[int(v['vote_id'])] = (r['main'], [])

va = con.execute("""select vote_id, knesset, bill_id, stage, vote_date from vote_attrs
  where kind='bill' and stage in ('preliminary','first','second','third')""").df()
bt = con.execute("select bill_id, bill_type from bills").df()
va = va.merge(bt, on='bill_id', how='left')
P('# DATA')
P('bill votes (4 stages):', len(va), '| by knesset', va.knesset.value_counts().to_dict())

rows = []; nolab = 0; src_cnt = {'agent': 0, 'whole': 0, 'bill': 0, 'winter': 0}
for v in va.itertuples():
    if v.vote_id in pk_agent: lab = pk_agent[v.vote_id]; src_cnt['agent'] += 1
    elif v.vote_id in pk_whole: lab = pk_whole[v.vote_id]; src_cnt['whole'] += 1
    elif v.bill_id in bill_lab: lab = bill_lab[v.bill_id]; src_cnt['bill'] += 1
    elif str(v.bill_id) in winter: src_cnt['winter'] += 1; continue
    else: nolab += 1; continue
    for role, lst in (('main', lab[0]), ('sec', lab[1])):
        for t in lst:
            s = SGN.get(t.get('sign'))
            rows.append((v.vote_id, str(t['n']), s if s else 0, role))
P('label source per vote:', src_cnt, '| votes whose bill has no label:', nolab)
vd = pd.DataFrame(rows, columns=['vote_id', 'd', 's', 'role']).drop_duplicates(['vote_id', 'd'])
vd = vd.merge(va[['vote_id', 'knesset', 'bill_id', 'stage', 'bill_type']], on='vote_id')
P('vote×direction rows:', len(vd), '| with null/? sign:', int((vd.s == 0).sum()))
P('votes with ≥1 direction:', vd.vote_id.nunique(), '| votes with only null-sign topics or none:',
  len(va) - vd[vd.s != 0].vote_id.nunique())
unk_dirs = set(vd.d) - set(ALLD)
if unk_dirs: P('direction ids not in DIRECTIONS_LIST:', sorted(unk_dirs))

ro = con.execute("""select r.vote_id, r.mk_id, r.result, r.bloc from vote_roster r
  join vote_attrs a using(vote_id) where a.kind='bill' and a.stage in ('preliminary','first','second','third')""").df()
P('roster rows on these votes:', len(ro), '| result counts:', ro.result.value_counts(dropna=False).to_dict())
ro['v'] = ro.result.map({'for': 1, 'against': -1})
rv = ro.dropna(subset=['v'])
P('roster rows with value (for/against):', len(rv), f'({len(rv)/len(ro):.1%})', '| MKs:', rv.mk_id.nunique())

# coalition share per MK per knesset
rok = ro.merge(va[['vote_id', 'knesset']], on='vote_id')
coal = rok[rok.bloc.isin(['coalition', 'opposition'])].groupby(['mk_id', 'knesset']).bloc.apply(
    lambda b: (b == 'coalition').mean()).rename('coal_share').reset_index()
coal_all = rok[rok.bloc.isin(['coalition', 'opposition'])].groupby('mk_id').bloc.apply(
    lambda b: (b == 'coalition').mean()).rename('coal_share')

# contributions
X = rv[['vote_id', 'mk_id', 'v', 'bloc']].merge(vd[vd.s != 0], on='vote_id')
X['c'] = X.s * X.v
P('MK×vote×direction contributions (A):', len(X), '| main only (B):', int((X.role == 'main').sum()))

def mkpos(df, by=('mk_id', 'd')):
    g = df.groupby(list(by)).c.agg(['mean', 'count', 'sum']).reset_index()
    return g.rename(columns={'mean': 'pos', 'count': 'n'})
posA = mkpos(X); posB = mkpos(X[X.role == 'main'])
posA_k = mkpos(X, ('mk_id', 'knesset', 'd'))
posA.to_csv(f'{OUT}/mk_positions_A.csv', index=False)

# ---------- H1 coverage ----------
P('\n# H1 coverage')
vds = vd[vd.s != 0]
cov = pd.DataFrame({'d': ALLD}); cov['name'] = cov.d.map(dname)
for role, sub in (('A', vds), ('B', vds[vds.role == 'main'])):
    cov[f'votes_{role}'] = cov.d.map(sub.groupby('d').vote_id.nunique()).fillna(0).astype(int)
    cov[f'bills_voted_{role}'] = cov.d.map(sub.groupby('d').bill_id.nunique()).fillna(0).astype(int)
for st in ['preliminary', 'first', 'second', 'third']:
    cov[f'votes_A_{st}'] = cov.d.map(vds[vds.stage == st].groupby('d').vote_id.nunique()).fillna(0).astype(int)
cov['votes_A_2or3'] = cov.d.map(vds[vds.stage.isin(['second', 'third'])].groupby('d').vote_id.nunique()).fillna(0).astype(int)
lc = dirs.set_index('n')
cov['bills_labeled_main'] = cov.d.map(lc.bills_main); cov['bills_labeled_any'] = cov.d.map(lc.bills_main + lc.bills_secondary)
cov.to_csv(f'{OUT}/h1_coverage.csv', index=False)
for role in 'AB':
    c = cov[f'votes_{role}']
    P(f'variant {role}: dirs with ≥1/≥5/≥20/≥50 votes:', (c >= 1).sum(), (c >= 5).sum(), (c >= 20).sum(), (c >= 50).sum(),
      '| median votes', c.median(), '| p10', c.quantile(.1))
P('dirs with ≥1 second/third vote (A):', (cov.votes_A_2or3 >= 1).sum(), '| ≥5:', (cov.votes_A_2or3 >= 5).sum())
P('ratio voted bills / labeled bills (any role), median:', round((cov.bills_voted_A / cov.bills_labeled_any.replace(0, np.nan)).median(), 3))
P('total labeled bills:', len(bill_lab), '| bills with ≥1 vote (4 stages):', va.bill_id.nunique(),
  '| labeled bills with votes:', len(set(va.bill_id) & set(bill_lab)))
P('lowest 10 by votes_A:', cov.nsmallest(10, 'votes_A')[['d', 'name', 'votes_A', 'bills_labeled_any']].values.tolist())

# ---------- lists ----------
cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cand = cand[cand.match.isin(['exact', 'manual'])].copy(); cand['mk_id'] = cand.mk_id.astype(int)
cec = pd.read_csv(f'{ROOT}/manual/cec_lists_26.csv'); lname = dict(zip(cec.letters, cec.name_en))
mk_has_votes = set(rv.mk_id)
lst_n = cand.groupby('letters').mk_id.agg(lambda s: len(set(s))).rename('matched')
lst_v = cand[cand.mk_id.isin(mk_has_votes)].groupby('letters').mk_id.nunique().rename('with_votes')
lists_tbl = pd.concat([lst_n, lst_v], axis=1).fillna(0).astype(int).sort_values('matched', ascending=False)
lists_tbl['name'] = lists_tbl.index.map(lname)
P('\n# Lists: matched candidates (exact+manual) per list'); P(lists_tbl.to_string())
dup = cand.mk_id.value_counts(); P('MKs on >1 list:', int((dup > 1).sum()))

def list_positions(pos, min_mk=3):
    m = cand[['letters', 'mk_id']].drop_duplicates().merge(pos, on='mk_id')
    g = m.groupby(['letters', 'd']).pos.agg(['mean', 'count']).reset_index()
    return g[g['count'] >= min_mk].rename(columns={'mean': 'lpos', 'count': 'n_mk'})

# ---------- H2 ----------
P('\n# H2 distinguishability (SD of list positions, lists with ≥3 matched MKs having ≥1 vote on d)')
h2 = []
for role, pos in (('A', posA), ('B', posB)):
    lp = list_positions(pos)
    sd = lp.groupby('d').agg(sd=('lpos', 'std'), n_lists=('lpos', 'size'), rng=('lpos', lambda x: x.max() - x.min()))
    sd = sd[sd.n_lists >= 3]
    q = sd.sd.quantile([.1, .25, .5, .75, .9]).round(3).to_dict()
    P(f'variant {role}: dirs with ≥3 lists: {len(sd)}; SD quantiles {q}; SD<0.1: {(sd.sd<0.1).sum()}, <0.2: {(sd.sd<0.2).sum()}, ≥0.4: {(sd.sd>=0.4).sum()}; range<0.2: {(sd.rng<0.2).sum()}')
    sd['variant'] = role; h2.append(sd.reset_index())
    if role == 'A': lpA = lp
h2 = pd.concat(h2); h2['name'] = h2.d.map(dname); h2.to_csv(f'{OUT}/h2_list_sd.csv', index=False)
P('n lists used per direction (A) median:', h2[h2.variant == 'A'].n_lists.median())
wide = lpA.pivot(index='d', columns='letters', values='lpos')
P('mean list position over dirs (A):', wide.mean().round(2).sort_values().to_dict())
wide.assign(name=wide.index.map(dname)).to_csv(f'{OUT}/list_positions_A.csv')

# ---------- H3 PCA ----------
P('\n# H3 dimensionality (PCA, MK×direction, impute = column mean, centered, not scaled)')
def pca_mat(pos, min_n=3, min_mk=20):
    p = pos[pos.n >= min_n]
    keep = p.groupby('d').mk_id.nunique(); keep = keep[keep >= min_mk].index
    M = p[p.d.isin(keep)].pivot(index='mk_id', columns='d', values='pos')
    M = M[M.notna().mean(axis=1) >= 0.3]  # MKs with ≥30% of those dirs
    Mi = M.fillna(M.mean()); Z = Mi - Mi.mean()
    U, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
    ev = S**2 / (S**2).sum()
    scores = pd.DataFrame(U[:, :5] * S[:5], index=M.index, columns=[f'PC{i+1}' for i in range(5)])
    load = pd.DataFrame(Vt[:5].T, index=M.columns, columns=scores.columns)
    return M, ev, scores, load
pcs = {}
for k in (24, 25, None):
    pos = posA if k is None else posA_k[posA_k.knesset == k]
    M, ev, sc, ld = pca_mat(pos)
    cs = coal_all if k is None else coal[coal.knesset == k].set_index('mk_id').coal_share
    cs = cs.reindex(sc.index)
    r = np.corrcoef(sc.PC1, cs)[0, 1]
    if r < 0: sc['PC1'] *= -1; ld['PC1'] *= -1; r = -r
    r2 = np.corrcoef(sc.PC2, cs)[0, 1]
    P(f'K{k or "24+25 pooled"}: MKs {M.shape[0]}, dirs {M.shape[1]}, missing {M.isna().mean().mean():.0%}; var expl PC1..5 {np.round(ev[:5],3).tolist()} cum5 {ev[:5].sum():.3f}; r(PC1,coal_share)={r:.3f}; r(PC2,coal_share)={r2:.3f}')
    pcs[k] = (M, sc, ld, cs)
# stable axis or government side?
sc24, sc25 = pcs[24][1], pcs[25][1]
both = sc24.index.intersection(sc25.index)
P('MKs in both K24 and K25 PCA:', len(both), '| r(PC1_K24, PC1_K25) (each oriented coalition=+):',
  round(np.corrcoef(sc24.loc[both, 'PC1'], sc25.loc[both, 'PC1'])[0, 1], 3))
ld24, ld25 = pcs[24][2], pcs[25][2]; cd = ld24.index.intersection(ld25.index)
P('common dirs:', len(cd), '| r(loadings PC1 K24, PC1 K25):', round(np.corrcoef(ld24.loc[cd, 'PC1'], ld25.loc[cd, 'PC1'])[0, 1], 3))
# raw positions: per-direction position correlation across Knessets for same MKs
pk = posA_k[posA_k.n >= 3].pivot_table(index=['mk_id', 'd'], columns='knesset', values='pos').dropna()
P('same MK same direction, K24 vs K25 positions (n≥3 each): pairs', len(pk), 'r =', round(pk[24].corr(pk[25]), 3))
# by K25 bloc: who switched
cs24 = coal[coal.knesset == 24].set_index('mk_id').coal_share; cs25 = coal[coal.knesset == 25].set_index('mk_id').coal_share
grp = pd.DataFrame({'c24': cs24.reindex(both), 'c25': cs25.reindex(both), 'pc24': sc24.loc[both, 'PC1'], 'pc25': sc25.loc[both, 'PC1']})
grp['g'] = pd.Series(np.where(grp.c24 > .5, 'coal24', 'opp24'), index=grp.index) + '_' + pd.Series(np.where(grp.c25 > .5, 'coal25', 'opp25'), index=grp.index)
P('mean PC1 by bloc path (PC1 oriented coalition=+ in each K):', grp.groupby('g')[['pc24', 'pc25']].mean().round(2).assign(n=grp.g.value_counts()).to_dict('index'))
# within-bloc PCA (K25 opposition / coalition separately) PC1 share
for k in (24, 25):
    M, sc, ld, cs = pcs[k]
    for side, mask in (('coal', cs > .5), ('opp', cs <= .5)):
        Mi = M[mask.values]; Mi = Mi.loc[:, Mi.notna().sum() >= 5]; Z = Mi.fillna(Mi.mean()); Z = Z - Z.mean(); Z = Z.fillna(0)
        S = np.linalg.svd(Z.values, compute_uv=False); ev = S**2 / (S**2).sum()
        P(f'  K{k} {side} only: MKs {Mi.shape[0]} PC1..3 {np.round(ev[:3],3).tolist()}')
for k in (24, 25):
    ld = pcs[k][2]
    top = ld.PC1.sort_values()
    P(f'K{k} PC1 top+ loadings:', [(d, dname[d][:40], round(x, 2)) for d, x in top[-5:].items()])
    P(f'K{k} PC1 top− loadings:', [(d, dname[d][:40], round(x, 2)) for d, x in top[:5].items()])

# ---------- H4 ----------
P('\n# H4 bloc voting vs real position')
XA = X.copy()
def support(df):
    return (df.v == 1).mean()
res = []
for d, g in XA.groupby('d'):
    nplus = g[g.s == 1].vote_id.nunique(); nminus = g[g.s == -1].vote_id.nunique()
    if nplus < 5 or nminus < 5: continue
    m = g.groupby(['mk_id', 's']).v.agg(lambda x: (x == 1).mean()).unstack()
    cnt = g.groupby(['mk_id', 's']).size().unstack()
    m = m[(cnt[1] >= 3) & (cnt[-1] >= 3)]
    if len(m) < 10: continue
    diff = m[1] - m[-1]
    res.append(dict(d=d, name=dname[d], votes_plus=nplus, votes_minus=nminus, mks=len(m),
                    mean_sup_plus=m[1].mean(), mean_sup_minus=m[-1].mean(),
                    mean_abs_diff=diff.abs().mean(), share_absdiff_lt_0_2=(diff.abs() < .2).mean(),
                    share_absdiff_ge_0_5=(diff.abs() >= .5).mean(),
                    gov_share_plus=(g[g.s == 1].drop_duplicates('vote_id').bill_type == 'ממשלתית').mean(),
                    gov_share_minus=(g[g.s == -1].drop_duplicates('vote_id').bill_type == 'ממשלתית').mean()))
h4 = pd.DataFrame(res).sort_values('votes_minus', ascending=False)
h4.to_csv(f'{OUT}/h4_plus_minus.csv', index=False)
P('dirs with ≥5 "+" and ≥5 "−" votes and ≥10 MKs with ≥3 each:', len(h4))
P('across these dirs: median mean|sup+ − sup−| =', round(h4.mean_abs_diff.median(), 3),
  '| median share of MKs with |diff|<0.2 =', round(h4.share_absdiff_lt_0_2.median(), 3),
  '| with |diff|≥0.5 =', round(h4.share_absdiff_ge_0_5.median(), 3))
# variance decomposition: MK vote v ~ bloc-line vs sign*pos
# bloc line: majority of own bloc on that vote
bl = rv.merge(va[['vote_id', 'bill_type']], on='vote_id')
maj = bl[bl.bloc.isin(['coalition', 'opposition'])].groupby(['vote_id', 'bloc']).v.mean().rename('bloc_mean').reset_index()
bl = bl.merge(maj, on=['vote_id', 'bloc'])
bl['agree_bloc'] = np.sign(bl.v) == np.sign(bl.bloc_mean)
P('share of MK for/against votes that match own bloc majority:', round(bl.agree_bloc.mean(), 3),
  '| by bill type:', bl.groupby('bill_type').agree_bloc.mean().round(3).to_dict())
P('support (share for) by bloc × bill type:', bl.groupby(['bloc', 'bill_type']).v.apply(lambda x: (x == 1).mean()).round(3).to_dict())
# within private bills only: sign effect
priv = XA[XA.vote_id.isin(va[va.bill_type == 'פרטית'].vote_id)]
for nm, sub in (('all', XA), ('private only', priv), ('gov only', XA[XA.vote_id.isin(va[va.bill_type == 'ממשלתית'].vote_id)])):
    t = sub.groupby(['bloc', 's']).v.apply(lambda x: (x == 1).mean()).round(3).to_dict()
    P(f'support by bloc × label sign ({nm}):', t)
# list-level examples
cl = cand[['letters', 'mk_id']].drop_duplicates()
ex = []
for d in h4.d.head(8):
    g = XA[XA.d == d].merge(cl, on='mk_id')
    t = g.groupby(['letters', 's']).v.apply(lambda x: (x == 1).mean()).unstack()
    t = t[g.groupby('letters').mk_id.nunique() >= 3]
    ex.append((d, t))
    P(f'  d{d} {dname[d][:45]}: list sup(+)/sup(−):', {l: f'{r[1]:.2f}/{r[-1]:.2f}' for l, r in t.iterrows()})
# within-bloc comparison: does sign predict vote after bloc×vote fixed effect? r between v and s*bloc-dev
bl2 = XA.merge(maj, on=['vote_id', 'bloc'])
bl2['dev'] = bl2.v - bl2.bloc_mean
P('share of MK-vote obs that deviate from own bloc majority:', round((np.sign(bl2.v) != np.sign(bl2.bloc_mean)).mean(), 3))

# ---------- H5 ----------
P('\n# H5 duplicates (MK position vectors, variant A, pooled, MK n≥3 per direction, ≥30 shared MKs)')
p3 = posA[posA.n >= 3].pivot(index='mk_id', columns='d', values='pos')
p3 = p3.loc[:, p3.notna().sum() >= 30]
C = p3.corr(min_periods=30)
# partial: residualize on coalition share (pooled) and on pooled PC1
Mp, scp, ldp, csp = pcs[None]
cov_pc1 = scp.PC1.reindex(p3.index); cov_cs = coal_all.reindex(p3.index)
def resid(df, z):
    out = df.copy()
    for c in df.columns:
        m = df[c].notna() & z.notna()
        if m.sum() < 10: out[c] = np.nan; continue
        b = np.polyfit(z[m], df[c][m], 1); out.loc[m, c] = df[c][m] - np.polyval(b, z[m]); out.loc[~m, c] = np.nan
    return out
Cp = resid(p3, cov_pc1).corr(min_periods=30)
Cc = resid(p3, cov_cs).corr(min_periods=30)
nn = p3.notna().astype(int); shared = nn.T @ nn
pr = []
for a, b in itertools.combinations(p3.columns, 2):
    if shared.loc[a, b] < 30 or pd.isna(C.loc[a, b]): continue
    pr.append((a, b, dname[a], dname[b], shared.loc[a, b], C.loc[a, b], Cp.loc[a, b], Cc.loc[a, b]))
pairs = pd.DataFrame(pr, columns=['d1', 'd2', 'name1', 'name2', 'shared_mks', 'r', 'r_partial_PC1', 'r_partial_coalshare'])
pairs['absr'] = pairs.r.abs(); pairs = pairs.sort_values('absr', ascending=False)
pairs.to_csv(f'{OUT}/h5_pairs.csv', index=False)
P('directions:', p3.shape[1], '| pairs:', len(pairs), '| |r|≥0.9:', (pairs.absr >= .9).sum(), '| ≥0.8:', (pairs.absr >= .8).sum(),
  '| median |r|:', round(pairs.absr.median(), 3))
P('after removing PC1: |r_p|≥0.9:', (pairs.r_partial_PC1.abs() >= .9).sum(), '≥0.8:', (pairs.r_partial_PC1.abs() >= .8).sum(),
  '≥0.7:', (pairs.r_partial_PC1.abs() >= .7).sum(), 'median |r_p|:', round(pairs.r_partial_PC1.abs().median(), 3))
P('after removing coal_share: |r_c|≥0.9:', (pairs.r_partial_coalshare.abs() >= .9).sum(), '≥0.8:', (pairs.r_partial_coalshare.abs() >= .8).sum())
P('top 20 by |r|:')
for r in pairs.head(20).itertuples():
    P(f'  {r.d1} {r.name1[:35]} | {r.d2} {r.name2[:35]} | n={r.shared_mks} r={r.r:.3f} r_pPC1={r.r_partial_PC1:.3f}')
pp = pairs.assign(ap=pairs.r_partial_PC1.abs()).sort_values('ap', ascending=False)
P('top 10 by |r| after removing PC1:')
for r in pp.head(10).itertuples():
    P(f'  {r.d1} {r.name1[:35]} | {r.d2} {r.name2[:35]} | n={r.shared_mks} r={r.r:.3f} r_pPC1={r.r_partial_PC1:.3f}')
for a, b in (('19', '20'), ('1', '277')):
    q = pairs[((pairs.d1 == a) & (pairs.d2 == b)) | ((pairs.d1 == b) & (pairs.d2 == a))]
    # vote overlap
    va_ = set(vds[vds.d == a].vote_id); vb_ = set(vds[vds.d == b].vote_id)
    jac = len(va_ & vb_) / max(1, len(va_ | vb_))
    P(f'pair {a} ({dname.get(a)}) vs {b} ({dname.get(b)}): votes {len(va_)}/{len(vb_)}, shared votes {len(va_ & vb_)}, Jaccard {jac:.2f};',
      q[['shared_mks', 'r', 'r_partial_PC1']].round(3).to_dict('records'))
# vote overlap duplicates: Jaccard of vote sets
vs = vds.groupby('d').vote_id.apply(set)
jac = [(a, b, len(vs[a] & vs[b]) / len(vs[a] | vs[b])) for a, b in itertools.combinations(vs.index, 2) if len(vs[a]) >= 10 and len(vs[b]) >= 10]
jac = pd.DataFrame(jac, columns=['d1', 'd2', 'jaccard']).sort_values('jaccard', ascending=False)
P('vote-set Jaccard (dirs ≥10 votes): pairs ≥0.5:', (jac.jaccard >= .5).sum(), '≥0.8:', (jac.jaccard >= .8).sum(),
  'top5:', [(a, b, round(j, 2)) for a, b, j in jac.head(5).values])
pairs['v1'] = pairs.d1.map(votesA_ := cov.set_index('d').votes_A); pairs['v2'] = pairs.d2.map(votesA_)
big = pairs[(pairs.v1 >= 20) & (pairs.v2 >= 20)]
P('only dirs with ≥20 votes each: pairs', len(big), '| |r|≥0.9:', (big.absr >= .9).sum(), '| |r_pPC1|≥0.9:', (big.r_partial_PC1.abs() >= .9).sum(),
  '≥0.8:', (big.r_partial_PC1.abs() >= .8).sum())
P('top 10 (≥20 votes) by |r_pPC1|:')
for r in big.assign(ap=big.r_partial_PC1.abs()).sort_values('ap', ascending=False).head(10).itertuples():
    P(f'  {r.d1} {r.name1[:35]} ({r.v1}) | {r.d2} {r.name2[:35]} ({r.v2}) | n={r.shared_mks} r={r.r:.3f} r_pPC1={r.r_partial_PC1:.3f}')
# K25 only, partial on K25 PC1
q25 = posA_k[(posA_k.knesset == 25) & (posA_k.n >= 3)].pivot(index='mk_id', columns='d', values='pos')
v25 = vds[vds.knesset == 25].groupby('d').vote_id.nunique()
q25 = q25.loc[:, [d for d in q25.columns if q25[d].notna().sum() >= 30 and v25.get(d, 0) >= 20]]
C25 = q25.corr(min_periods=30); C25p = resid(q25, pcs[25][1].PC1.reindex(q25.index)).corr(min_periods=30)
iu = np.triu_indices(len(C25), 1); a1 = C25.values[iu]; a2 = C25p.values[iu]; ok = ~np.isnan(a1) & ~np.isnan(a2)
P(f'K25 only, dirs ≥20 K25 votes: dirs {q25.shape[1]}, pairs {ok.sum()}, |r|≥0.9: {(np.abs(a1[ok])>=.9).sum()}, after removing K25 PC1 |r|≥0.9: {(np.abs(a2[ok])>=.9).sum()}, ≥0.7: {(np.abs(a2[ok])>=.7).sum()}, median |r| {np.median(np.abs(a1[ok])):.3f} -> {np.median(np.abs(a2[ok])):.3f}')
for a, b in (('19', '20'), ('1', '277')):
    if a in C25 and b in C25: P(f'  K25 {a} vs {b}: r={C25.loc[a,b]:.3f}, r_pPC1={C25p.loc[a,b]:.3f}')

# ---------- H7 ----------
P('\n# H7 rare topics + shrinkage (k=5, provisional); 200 synthetic users, 30 dirs = 20 frequent + 10 rare')
votesA = cov.set_index('d').votes_A
K = 5
posS = posA.copy(); posS['pos'] = posS['sum'] / (posS.n + K)
def lp_wide(pos):
    lp = list_positions(pos, min_mk=1)
    return lp.pivot(index='letters', columns='d', values='lpos')
lists3 = lists_tbl[lists_tbl.with_votes >= 3].index
W_raw = lp_wide(posA).reindex(lists3); W_shr = lp_wide(posS).reindex(lists3)
covered = [d for d in W_raw.columns if W_raw[d].notna().sum() >= 3]
freq = [d for d in covered if votesA[d] >= 10]; rare = [d for d in covered if 1 <= votesA[d] < 10]
P('lists used:', len(lists3), list(lists3), '| freq dirs avail:', len(freq), '| rare dirs avail (1–9 votes, ≥3 lists):', len(rare))
def top_list(W, ds, u):
    sc = (W[ds].fillna(0).values * u).sum(axis=1); return W.index[np.argmax(sc)], sc
out = {'raw': [0, 0], 'shr': [0, 0], 'base_raw': [0, 0], 'base_shr': [0, 0]}
NU = 200
for i in range(NU):
    df_ = list(rng.choice(freq, 20, replace=False)); dr = list(rng.choice(rare, min(10, len(rare)), replace=False))
    ds = df_ + dr; u = rng.choice([-1, 1], len(ds))
    for nm, W in (('raw', W_raw), ('shr', W_shr)):
        t_all, _ = top_list(W, ds, u); t_f, _ = top_list(W, df_, u[:20])
        out[nm][0] += t_all != t_f
        # baseline: 30 frequent, drop 10 frequent
        f30 = list(rng.choice(freq, 30, replace=False)); u30 = rng.choice([-1, 1], 30)
        out['base_' + nm][0] += top_list(W, f30, u30)[0] != top_list(W, f30[:20], u30[:20])[0]
for nm in ('raw', 'shr'):
    P(f'{nm}: top list changes when 10 rare dirs added to 20 frequent: {out[nm][0]}/{NU} = {out[nm][0]/NU:.0%}; '
      f'baseline (adding 10 frequent instead): {out["base_"+nm][0]}/{NU} = {out["base_"+nm][0]/NU:.0%}')
P('mean |list pos| rare dirs raw vs shrunk:', round(W_raw[rare].abs().mean().mean(), 3), round(W_shr[rare].abs().mean().mean(), 3),
  '| frequent:', round(W_raw[freq].abs().mean().mean(), 3), round(W_shr[freq].abs().mean().mean(), 3))
# winners distribution
wins = {'raw': {}, 'shr': {}}
for i in range(NU):
    ds = list(rng.choice(covered, 30, replace=False)); u = rng.choice([-1, 1], 30)
    for nm, W in (('raw', W_raw), ('shr', W_shr)):
        t = top_list(W, ds, u)[0]; wins[nm][t] = wins[nm].get(t, 0) + 1
P('top-list distribution over 200 random users (30 random covered dirs):', wins)

# ---------- H8 ----------
P('\n# H8 authorship vs voting')
bi = con.execute("select bill_id, mk_id, is_initiator from bill_initiators").df()
arows = []
for b, (mn, sc_) in bill_lab.items():
    for t in mn + sc_:
        s = SGN.get(t.get('sign'))
        if s: arows.append((b, str(t['n']), s))
ab = pd.DataFrame(arows, columns=['bill_id', 'd', 's']).drop_duplicates(['bill_id', 'd'])
for nm, sel in (('initiators', bi[bi.is_initiator]), ('initiators+joined', bi)):
    a = sel.merge(ab, on='bill_id').groupby(['mk_id', 'd']).s.agg(['mean', 'count']).reset_index().rename(columns={'mean': 'apos', 'count': 'na'})
    m = a.merge(posA, on=['mk_id', 'd'])
    P(f'{nm}: MK×dir pairs with any authorship: {len(a)}; share of apos==+1: {(a.apos==1).mean():.3f}; mean apos {a.apos.mean():.3f}')
    for na, nv in ((3, 5), (1, 5), (5, 10)):
        mm = m[(m.na >= na) & (m.n >= nv)]
        if len(mm) > 5:
            r = mm.apos.corr(mm.pos)
            # within-direction (demeaned) correlation
            dm = mm.assign(ap=mm.apos - mm.groupby('d').apos.transform('mean'), vp=mm.pos - mm.groupby('d').pos.transform('mean'))
            P(f'  na≥{na}, nv≥{nv}: n={len(mm)}, MKs {mm.mk_id.nunique()}, dirs {mm.d.nunique()}, r={r:.3f}, r_within_dir={dm.ap.corr(dm.vp):.3f}, sd(apos)={mm.apos.std():.3f}, share apos=+1 {(mm.apos==1).mean():.2f}')
    if nm == 'initiators': m.to_csv(f'{OUT}/h8_author_vs_vote.csv', index=False)
# label sign balance overall
P('label sign balance (bills, main+sec): +', int((ab.s == 1).sum()), '−', int((ab.s == -1).sum()))

open(f'{OUT}/out.txt', 'w').write('\n'.join(lines) + '\n')
