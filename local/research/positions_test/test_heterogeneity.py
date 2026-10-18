"""PROVISIONAL: detect "basket" directions — same-sign bills authored by opposite camps.
Camp axis = PC1 of MK × direction authorship matrix (centered A from jef/positions/mk_topic_positions.csv).
Loads labels by exec of the label section of scripts/positions.py (no file writes there). Thresholds are NOT decisions.
Run: python3 jef/positions_test/test_heterogeneity.py -> heterogeneity.csv, heterogeneity_examples.csv, heterogeneity_out.txt
"""
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
src = open(f'{ROOT}/scripts/positions.py').read()
g = {'__file__': f'{ROOT}/scripts/positions.py'}
exec(src.split('# ======================= votes')[0], g)
bill_lab, signed_topics, dname, names, con, technical = (g[k] for k in ('bill_lab', 'signed_topics', 'dname', 'names', 'con', 'technical'))
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('=== HETEROGENEITY ("basket" directions), PROVISIONAL ===')

# ---------- camp axis ----------
T = pd.read_csv(f'{ROOT}/jef/positions/mk_topic_positions.csv', dtype={'d': str})
bi = con.execute("""select i.bill_id, i.mk_id from bill_initiators i join bills b using(bill_id)
  where i.is_initiator and b.knesset in (24,25) and b.bill_type='פרטית'""").df()
bi = bi[~bi.bill_id.astype(str).isin(technical) & bi.bill_id.isin(bill_lab.keys())]
nb = bi.groupby('mk_id').bill_id.nunique()
mks = nb[nb >= 20].index
M = T[T.mk_id.isin(mks) & T.A.notna()].pivot(index='mk_id', columns='d', values='A').reindex(mks).fillna(0)
M = M.loc[:, (M != 0).sum() >= 1]
Z = M - M.mean()
U, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
ev = S**2 / (S**2).sum()
pc1 = pd.Series(U[:, 0] * S[0], index=M.index)
cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cand = cand[cand.match.isin(['exact', 'manual'])].copy(); cand['mk_id'] = cand.mk_id.astype(int)
cl = cand.drop_duplicates('mk_id').set_index('mk_id').letters
if pc1[pc1.index.isin(cl[cl == 'מחל'].index)].mean() < 0: pc1 = -pc1; Vt[0] = -Vt[0]
P(f'authorship matrix: {M.shape[0]} MKs (≥20 labeled private bills as initiator) × {M.shape[1]} directions; impute 0; column-centered')
P(f'PC1..5 variance share: {np.round(ev[:5], 3).tolist()}  (orientation convention: Likud ex-MKs mean > 0)')
lo = pc1.groupby(cl.reindex(pc1.index)).agg(['mean', 'size']).dropna().sort_values('mean')
P('2026 lists on PC1 (mean of ex-MKs in matrix, n):', {l: (round(r['mean'], 2), int(r['size'])) for l, r in lo.iterrows()})
load = pd.Series(Vt[0], index=M.columns).sort_values()
P('PC1 top+ loadings:', [(d, dname[d][:35], round(x, 2)) for d, x in load[-6:].items()])
P('PC1 top− loadings:', [(d, dname[d][:35], round(x, 2)) for d, x in load[:6].items()])
km = KMeans(2, n_init=20, random_state=0).fit(Z.values)
kc = pd.Series(km.labels_, index=M.index)
comp = pd.crosstab(cl.reindex(kc.index).fillna('(not 2026)'), kc)
P('k-means(2) composition by 2026 list:', comp.to_dict('index'))
P(f'k-means vs PC1 sign agreement: {max(((pc1 > 0) == (kc == 1)).mean(), ((pc1 > 0) == (kc == 0)).mean()):.3f}')
q1, q2 = pc1.quantile([1/3, 2/3])
P(f'PC1 tercile cutoffs: {q1:.3f}, {q2:.3f}')

# ---------- per bill camp score ----------
bscore = bi[bi.mk_id.isin(pc1.index)].assign(s=lambda x: x.mk_id.map(pc1)).groupby('bill_id').s.mean()
P(f'private labeled bills with initiators: {bi.bill_id.nunique()}; with ≥1 scored initiator: {len(bscore)}')
rows = []
for b, lab in bill_lab.items():
    if b not in bscore.index: continue
    mains = {str(t['n']) for t in lab[0]}
    for d, s in signed_topics(lab).items():
        rows.append((b, d, s, d in mains, bscore[b]))
BD = pd.DataFrame(rows, columns=['bill_id', 'd', 's', 'is_main', 'score'])
BD['tier'] = np.where(BD.score >= q2, 'top', np.where(BD.score <= q1, 'bot', 'mid'))
ub = BD.drop_duplicates('bill_id')
P(f'baseline over all bills: top-tier share {(ub.tier=="top").mean():.3f}, bottom-tier {(ub.tier=="bot").mean():.3f} -> split of a camp-neutral direction ≈ {min((ub.tier=="top").mean(), (ub.tier=="bot").mean()):.3f}')

def metrics(bd, loo_scores=None):
    out = []
    for d in dname:
        q = bd[bd.d == d]
        r = dict(d=d, name=dname[d], n_bills=len(q))
        for sg, nm in ((1, 'plus'), (-1, 'minus')):
            z = q[q.s == sg]
            r[f'n_{nm}'] = len(z)
            r[f'top_{nm}'] = (z.tier == 'top').mean() if len(z) else np.nan
            r[f'bot_{nm}'] = (z.tier == 'bot').mean() if len(z) else np.nan
            r[f'bimod_{nm}'] = min(r[f'top_{nm}'], r[f'bot_{nm}']) if len(z) else np.nan
            r[f'mean_{nm}'] = z.score.mean() if len(z) else np.nan
        dom = 'plus' if r['n_plus'] >= r['n_minus'] else 'minus'
        r['dominant'] = '+' if dom == 'plus' else '−'
        r['split'] = r[f'bimod_{dom}']
        r['separation'] = abs(r['mean_plus'] - r['mean_minus']) if r['n_plus'] >= 3 and r['n_minus'] >= 3 else np.nan
        out.append(r)
    return pd.DataFrame(out)
H = metrics(BD)

# leave-one-direction-out PC1 (circularity check): recompute PC1 without column d, re-score bills
loo_split = {}
for d in H.d:
    if d not in M.columns:
        loo_split[d] = H.set_index('d').split.get(d); continue
    Zd = Z.drop(columns=d); u, s_, vt = np.linalg.svd(Zd.values, full_matrices=False)
    p = pd.Series(u[:, 0] * s_[0], index=M.index)
    if np.corrcoef(p, pc1)[0, 1] < 0: p = -p
    a1, a2 = p.quantile([1/3, 2/3])
    bs = bi[bi.mk_id.isin(p.index)].assign(s=lambda x: x.mk_id.map(p)).groupby('bill_id').s.mean()
    z = BD[BD.d == d]
    dom = 1 if (z.s == 1).sum() >= (z.s == -1).sum() else -1
    sc = z[z.s == dom].bill_id.map(bs)
    loo_split[d] = min((sc >= a2).mean(), (sc <= a1).mean()) if len(sc) else np.nan
H['split_loo'] = H.d.map(loo_split)
P(f'split vs leave-one-direction-out split: r={H.split.corr(H.split_loo):.3f}, mean |diff| {np.abs(H.split - H.split_loo).mean():.3f}')

# ---------- distributions ----------
H10 = H[H[['n_plus', 'n_minus']].max(axis=1) >= 10]
P(f'\ndirections total {len(H)}; with ≥1 scored bill {int((H.n_bills>0).sum())}; with ≥10 bills of dominant sign {len(H10)}')
P('split (min(top,bottom) share, dominant sign) quantiles, dirs with ≥10 dominant bills:', H10.split.quantile([.1, .25, .5, .75, .9]).round(3).to_dict())
P('separation quantiles (dirs with ≥3 bills of each sign):', H.separation.dropna().quantile([.1, .25, .5, .75, .9]).round(3).to_dict(), f'n={H.separation.notna().sum()}')
P(f'dominant sign "+": {(H10.dominant == "+").mean():.2f} of dirs; share of bills with minority sign: median {(H10[["n_plus","n_minus"]].min(axis=1)/H10[["n_plus","n_minus"]].sum(axis=1)).median():.3f}')
CUTS = [0.20, 0.25, 0.30]
for c in CUTS:
    P(f'  split ≥ {c}: {int((H10.split >= c).sum())} dirs (of {len(H10)} with ≥10 dominant bills)')

# ---------- validation vs content review ----------
al = pd.concat([pd.read_csv(f'{ROOT}/jef/quiz/align_out_{i}.csv', dtype={'d': str}) for i in (1, 2)])
P('review duplicates:', al[al.d.duplicated(keep=False)][['d', 'heterogeneous']].values.tolist(), '-> "yes" if any reviewer said yes')
al = al.sort_values('heterogeneous', ascending=False).drop_duplicates('d')
al['het'] = (al.heterogeneous == 'yes').astype(int)
V = al[['d', 'het', 'core_subject']].merge(H, on='d', how='left')
P(f'\n# validation: content review dirs {len(V)} (heterogeneous yes {int(V.het.sum())})')
for col, sign in (('split', 1), ('split_loo', 1), ('bimod_plus', 1), ('separation', -1)):
    z = V.dropna(subset=[col])
    if z.het.nunique() == 2:
        P(f'  AUC {col}{" (lower=basket)" if sign < 0 else ""}: {roc_auc_score(z.het, sign * z[col]):.3f} (n={len(z)}, yes {int(z.het.sum())})')
P('  mean split: yes', round(V[V.het == 1].split.mean(), 3), '| no', round(V[V.het == 0].split.mean(), 3))
for c in CUTS:
    fp = V[(V.split >= c) & (V.het == 0)]; fn = V[(V.split < c) & (V.het == 1)]
    tp = int(((V.split >= c) & (V.het == 1)).sum())
    P(f'  cutoff split ≥ {c}: TP {tp}, FP {len(fp)}, FN {len(fn)}')
    P(f'     FP: {[(r.d, r.name[:30], round(r.split, 2)) for r in fp.itertuples()]}')
    P(f'     FN: {[(r.d, r.name[:30], round(r.split, 2)) for r in fn.itertuples()]}')

H = H.merge(al[['d', 'heterogeneous']], on='d', how='left')
for c in CUTS: H[f'flag_split_ge_{c}'] = (H.split >= c) & (H[['n_plus', 'n_minus']].max(axis=1) >= 10)
H.sort_values('split', ascending=False).round(4).to_csv(f'{OUT}/heterogeneity.csv', index=False)

# ---------- examples ----------
bn = dict(con.execute("select bill_id, name from bills").fetchall())
top = H10.sort_values('split', ascending=False).head(40)
ex = []
for r in top.itertuples():
    sg = 1 if r.dominant == '+' else -1
    z = BD[(BD.d == r.d) & (BD.s == sg) & BD.is_main]
    t_top = z[z.tier == 'top'].sort_values('score', ascending=False).head(3)
    t_bot = z[z.tier == 'bot'].sort_values('score').head(3)
    ex.append(dict(d=r.d, name=r.name, dominant=r.dominant, n_dominant=max(r.n_plus, r.n_minus), split=round(r.split, 3),
                   separation=None if pd.isna(r.separation) else round(r.separation, 3),
                   review_heterogeneous=al.set_index('d').heterogeneous.get(r.d, ''),
                   camp_pos_titles=' | '.join(f'{b}: {str(bn.get(b, ""))[:90]}' for b in t_top.bill_id),
                   camp_neg_titles=' | '.join(f'{b}: {str(bn.get(b, ""))[:90]}' for b in t_bot.bill_id)))
pd.DataFrame(ex).to_csv(f'{OUT}/heterogeneity_examples.csv', index=False)
P('\n# top 20 by split (≥10 dominant bills): d, name, dominant, n, split, separation, review')
for r in top.head(20).itertuples():
    P(f'  {r.d} {r.name[:45]} | {r.dominant} n={max(r.n_plus, r.n_minus)} | split {r.split:.2f} | sep {r.separation if pd.isna(r.separation) else round(r.separation, 2)} | review {al.set_index("d").heterogeneous.get(r.d, "-")}')
open(f'{OUT}/heterogeneity_out.txt', 'w').write('\n'.join(lines) + '\n')
