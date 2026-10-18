"""PROVISIONAL: choose component weights by out-of-sample prediction between Knessets (K24→K25 and K25→K24).
Nothing here is a decision. Reuses loaders: test_blocs.py PART 1 (which itself execs test_hypotheses.py loaders);
its single CSV write is disabled in memory — no existing file is modified.
Run: python3 jef/positions_test/test_weights.py -> stdout, weights_out.txt, weights_grid.csv, weights_rare_k.csv
"""
import itertools, numpy as np, pandas as pd

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
bsrc = open(f'{OUT}/test_blocs.py').read()
part1 = bsrc.split('# ================= PART 2')[0]
wr = "iv.to_csv(f'{OUT}/blocs_reference_intervals.csv', index=False)"
assert wr in part1
part1 = part1.replace(wr, 'pass').replace("open(f'{OUT}/blocs_out.txt'", "open('/dev/null'")
gb = {}
exec(part1, gb)
g = gb['g']
X, va, rv, coal, con, SGN, bill_lab = (g[k] for k in ('X', 'va', 'rv', 'coal', 'con', 'SGN', 'bill_lab'))
ref_bloc = gb['ref_bloc']
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('\n=== WEIGHTS BY OUT-OF-SAMPLE PREDICTION (PROVISIONAL) ===')
va = va.copy(); va['vote_date'] = pd.to_datetime(va.vote_date)

# ---------------- MKs, lists ----------------
both = set(rv.merge(va[['vote_id', 'knesset']], on='vote_id').groupby('mk_id').knesset.nunique().loc[lambda s: s == 2].index)
cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cand = cand[cand.match.isin(['exact', 'manual'])].copy(); cand['mk_id'] = cand.mk_id.astype(int)
cl = cand[['letters', 'mk_id', 'position']].drop_duplicates('mk_id').set_index('mk_id')
P(f'MKs with votes in both Knessets: {len(both)}; of them 2026 candidates: {len(both & set(cl.index))}')

# ---------------- coalition shares ----------------
cs_roster = coal.set_index(['mk_id', 'knesset']).coal_share
ro = con.execute("select r.vote_id, r.mk_id, r.faction_id from vote_roster r join vote_attrs a using(vote_id) where a.kind='bill' and a.stage in ('preliminary','first','second','third') and r.faction_id is not null").df()
ro = ro.merge(va[['vote_id', 'vote_date', 'knesset']], on='vote_id')
ro['refc'] = [ref_bloc(int(f), d) == 'coalition' for f, d in zip(ro.faction_id, ro.vote_date)]
cs_ref = ro.groupby(['mk_id', 'knesset']).refc.mean()
j = pd.concat([cs_roster, cs_ref], axis=1, keys=['r', 'f']).dropna()
P(f'coalition share roster vs reference: r={j.r.corr(j.f):.3f}, mean |diff|={np.abs(j.r-j.f).mean():.3f}, MK×K with |diff|>0.2: {(np.abs(j.r-j.f)>.2).sum()}')

# ---------------- against-bloc rows, W30>=0.7 MK switch periods removed ----------------
rvb = rv[rv.bloc.isin(['coalition', 'opposition'])].merge(va[['vote_id', 'vote_date', 'knesset']], on='vote_id')
bm = rvb.groupby(['vote_id', 'bloc']).v.mean().unstack()
rvb = rvb.merge(bm.stack().rename('bm').reset_index(), on=['vote_id', 'bloc'])
rvb['ab'] = (np.sign(rvb.v) != np.sign(rvb.bm)) & (rvb.bm != 0)
bmw = bm.dropna(); split = bmw[np.sign(bmw.coalition) * np.sign(bmw.opposition) == -1]
sv = rvb[rvb.vote_id.isin(split.index)].copy()
sv['other'] = np.where(sv.bloc == 'coalition', split.opposition.reindex(sv.vote_id).values, split.coalition.reindex(sv.vote_id).values)
sv['wo'] = np.sign(sv.v) == np.sign(sv.other)
sv = sv.sort_values(['mk_id', 'vote_date', 'vote_id'])
periods = []
for (m, k), q in sv.groupby(['mk_id', 'knesset']):
    a = q.wo.values.astype(float)
    if len(a) < 30: continue
    cs_ = np.convolve(a, np.ones(30), 'valid') / 30; f = np.zeros(len(a), bool)
    for i in np.where(cs_ >= .7)[0]: f[i:i + 30] = True
    d = q.vote_date.values; cur = None
    for di, fi in zip(d, f):
        if fi and cur is None: cur = [di, di]
        elif fi: cur[1] = di
        elif cur is not None: periods.append((m, *cur)); cur = None
    if cur is not None: periods.append((m, *cur))
abrows = rvb[rvb.ab][['vote_id', 'mk_id', 'vote_date']].copy()
excl = pd.Series(False, index=abrows.index)
for m, s, e in periods:
    excl |= (abrows.mk_id == m) & (abrows.vote_date >= s) & (abrows.vote_date <= e)
abkeep = abrows[~excl]
P(f'against-bloc vote rows {len(abrows)}; in W30>=0.7 MK periods {int(excl.sum())} removed; kept {len(abkeep)}')
XB = X.merge(abkeep[['vote_id', 'mk_id']], on=['vote_id', 'mk_id'])

# ---------------- authorship rows ----------------
bi = con.execute("select i.bill_id, i.mk_id, b.knesset from bill_initiators i join bills b using(bill_id) where i.is_initiator and b.knesset in (24,25)").df()
rows = []
for b, (mn, sc) in bill_lab.items():
    for role, lst in (('main', mn), ('sec', sc)):
        for t in lst:
            s = SGN.get(t.get('sign'))
            if s: rows.append((b, str(t['n']), s, role))
lab = pd.DataFrame(rows, columns=['bill_id', 'd', 'c', 'role']).drop_duplicates(['bill_id', 'd'])
AU = bi.merge(lab, on='bill_id')
XV = X[X.bill_type == 'פרטית']; XG = X[X.bill_type.isin(['ממשלתית', 'ועדה'])]
P(f'rows: authorship {len(AU)}, private votes {len(XV)}, gov/committee votes {len(XG)}, against-bloc {len(XB)}')

KEY = ['mk_id', 'knesset', 'd']
def agg(df, wsec):
    w = np.where(df.role == 'main', 1.0, wsec)
    a = df.assign(w=w, wc=w * df.c)
    a = a[a.w > 0]
    return a.groupby(KEY).agg(S=('wc', 'sum'), N=('w', 'sum'), cnt=('c', 'size')).reset_index()

def resid(a, cs):
    a = a.copy(); a['pos'] = a.S / a.N
    a['cs'] = cs.reindex(pd.MultiIndex.from_arrays([a.mk_id, a.knesset])).values
    a = a.dropna(subset=['cs'])
    gm = a.groupby(['knesset', 'd'])
    mx = gm.cs.transform('mean'); my = gm.pos.transform('mean')
    cov = ((a.cs - mx) * (a.pos - my)).groupby([a.knesset, a.d]).transform('mean')
    var = ((a.cs - mx) ** 2).groupby([a.knesset, a.d]).transform('mean')
    b = np.where(var > 1e-9, cov / var.replace(0, np.nan), 0.0); b = np.nan_to_num(b)
    a['res'] = a.pos - my - b * (a.cs - mx)
    return a

# ---------------- targets (test Knesset), fixed definition: main+sec equal weight, unshrunk, n>=3 ----------------
def targets(cs):
    A = agg(AU, 1.0); A = A[A.cnt >= 3].copy(); A['pos'] = A.S / A.N
    A['T1'] = A.pos - A.groupby(['knesset', 'd']).pos.transform('mean')
    V = resid(agg(XV, 1.0), cs); V = V[V.cnt >= 3].rename(columns={'res': 'T2'})
    T = A.set_index(KEY)[['T1']].join(V.set_index(KEY)[['T2']], how='outer')
    T['T3'] = (T.T1 + T.T2) / 2
    return T
T_roster = targets(cs_roster)

# ---------------- components (train), per wsec; shrink at eval ----------------
def components(wsec, cs):
    A = agg(AU, wsec)
    V = resid(agg(XV, wsec), cs); G = resid(agg(XG, wsec), cs); B = agg(XB, wsec)
    return dict(A=A.set_index(KEY)[['S', 'N', 'cnt']], V=V.set_index(KEY)[['res', 'N']],
                G=G.set_index(KEY)[['res', 'N']], B=B.set_index(KEY)[['S', 'N']])

def comp_values(C, k):
    out = {}
    for nm in ('A', 'B'):
        c = C[nm]; v = c.S / (c.N + k)
        v = v - v.groupby(level=['knesset', 'd']).transform('mean')
        out[nm] = v
    for nm in ('V', 'G'):
        c = C[nm]; out[nm] = c.res * c.N / (c.N + k)
    return out

WS = [0, .25, .5, 1]; KS = [0, 2, 5, 10, 20]
WGRID = np.array([w for w in itertools.product(WS, repeat=4) if max(w) == 1])  # normalized: max = 1
P(f'grid: {len(WS)} w_sec × {len(KS)} k × {len(WGRID)} weight vectors (max=1) = {len(WS)*len(KS)*len(WGRID)} settings')

def corr_cols(Pm, t):
    t = (t - t.mean()) / t.std()
    Z = (Pm - Pm.mean(0)) / np.where(Pm.std(0) > 0, Pm.std(0), np.nan)
    return (Z * t[:, None]).mean(0) * len(t) / (len(t) - 1) * (len(t) - 1) / len(t)

def build_eval(T, tr, te, tname):
    t = T[tname].dropna().reset_index()
    t = t[(t.knesset == te) & t.mk_id.isin(both)]
    keys = list(zip(t.mk_id, [tr] * len(t), t.d))
    # list aggregation
    lists = t.mk_id.map(cl.letters)
    grp = pd.DataFrame({'l': lists.values, 'd': t.d.values}).reset_index(drop=True)
    ok = grp.l.notna()
    gk = grp[ok].groupby(['l', 'd']).size(); gk = gk[gk >= 2]
    gi = {k: i for i, k in enumerate(gk.index)}
    M = np.zeros((len(gi), len(t)))
    for i, (l, d) in enumerate(zip(grp.l, grp.d)):
        if (l, d) in gi: M[gi[(l, d)], i] = 1
    M = M / np.maximum(M.sum(1, keepdims=True), 1)
    return dict(t=t[tname].values, idx=pd.MultiIndex.from_tuples(keys, names=KEY), M=M, mk=t.mk_id.values, d=t.d.values, lists=grp.l.values)

def comp_matrix(vals, idx):
    return np.column_stack([vals[nm].reindex(idx).fillna(0).values for nm in 'AVGB'])

grid = []
rare_rows = []
DIRS = [(24, 25), (25, 24)]
comps_cache = {}
for wsec in WS:
    comps_cache[wsec] = components(wsec, cs_roster)
for tr, te in DIRS:
    for tname in ('T1', 'T2', 'T3'):
        E = build_eval(T_roster, tr, te, tname)
        tl = E['M'] @ E['t']
        for wsec in WS:
            C = comps_cache[wsec]
            Acnt = C['A'].cnt.reindex(E['idx']).fillna(0).values
            rare = (Acnt >= 1) & (Acnt <= 4)
            for k in KS:
                Cm = comp_matrix(comp_values(C, k), E['idx'])
                Pm = Cm @ WGRID.T
                r = corr_cols(Pm, E['t'])
                rl = corr_cols(E['M'] @ Pm, tl)
                rr = corr_cols(Pm[rare], E['t'][rare]) if rare.sum() > 10 else np.full(len(WGRID), np.nan)
                for wi, w in enumerate(WGRID):
                    grid.append((f'{tr}->{te}', tname, wsec, k, *w, r[wi], rl[wi]))
                    rare_rows.append((f'{tr}->{te}', tname, wsec, k, *w, rr[wi], int(rare.sum())))
        P(f'eval {tr}->{te} {tname}: pairs {len(E["t"])}, MKs {len(set(E["mk"]))}, list×dir groups {E["M"].shape[0]}')
G_ = pd.DataFrame(grid, columns=['dir', 'target', 'wsec', 'k', 'wA', 'wV', 'wG', 'wB', 'r', 'r_list'])
G_.to_csv(f'{OUT}/weights_grid.csv', index=False)
R_ = pd.DataFrame(rare_rows, columns=['dir', 'target', 'wsec', 'k', 'wA', 'wV', 'wG', 'wB', 'r_rare', 'n_rare'])
R_.to_csv(f'{OUT}/weights_rare_k.csv', index=False)

S = ['wsec', 'k', 'wA', 'wV', 'wG', 'wB']
def fmt(r): return f"wsec={r.wsec} k={r.k} A={r.wA} V={r.wV} G={r.wG} B={r.wB}"
P('\n# Best settings (MK×direction r; list r) per target and direction')
for tname in ('T1', 'T2', 'T3'):
    for metric in ('r', 'r_list'):
        q = G_[G_.target == tname]
        piv = q.pivot_table(index=S, columns='dir', values=metric)
        piv['mean'] = piv.mean(1)
        for dcol in ['24->25', '25->24', 'mean']:
            top = piv.sort_values(dcol, ascending=False)
            b = top.iloc[0]; nm = dict(zip(S, top.index[0]))
            P(f'{tname} {metric:6s} best by {dcol:6s}: {fmt(pd.Series(nm))} | r 24->25 {b["24->25"]:.3f}, 25->24 {b["25->24"]:.3f}, mean {b["mean"]:.3f} | top10 range {top[dcol].iloc[9]:.3f}–{top[dcol].iloc[0]:.3f}')
        b1 = piv['24->25'].idxmax(); b2 = piv['25->24'].idxmax()
        P(f'   same best in both directions: {b1 == b2}; best(24->25) evaluated 25->24: {piv.loc[b1, "25->24"]:.3f} (vs its own best {piv["25->24"].max():.3f}); best(25->24) on 24->25: {piv.loc[b2, "24->25"]:.3f} (vs {piv["24->25"].max():.3f})')

P('\n# Single components (best wsec,k for that component; and at wsec=1,k=5)')
for tname in ('T1', 'T2', 'T3'):
    for comp in 'AVGB':
        others = [c for c in 'AVGB' if c != comp]
        q = G_[(G_.target == tname) & (G_[f'w{comp}'] == 1) & (G_[[f'w{o}' for o in others]].sum(1) == 0)]
        piv = q.pivot_table(index=['wsec', 'k'], columns='dir', values=['r', 'r_list']); m = piv['r'].mean(1)
        bi_ = m.idxmax(); d5 = piv.loc[(1, 5)]
        P(f'{tname} {comp} only: best (wsec,k)={bi_}: r 24->25 {piv.loc[bi_, ("r","24->25")]:.3f}, 25->24 {piv.loc[bi_, ("r","25->24")]:.3f}, list mean {piv.loc[bi_, "r_list"].mean():.3f} | at (1,5): r mean {d5["r"].mean():.3f}, list mean {d5["r_list"].mean():.3f}')

P('\n# k on RARE topics (pairs with 1–4 authored bills in train), max r over weights per k (wsec=1) and A-only')
for tname in ('T1', 'T3'):
    q = R_[(R_.target == tname) & (R_.wsec == 1)]
    best = q.groupby(['dir', 'k']).r_rare.max().unstack(0)
    aon = q[(q.wA == 1) & (q.wV == 0) & (q.wG == 0) & (q.wB == 0)].set_index(['k', 'dir']).r_rare.unstack()
    P(f'{tname} (n rare pairs: {q.groupby("dir").n_rare.first().to_dict()})')
    for k in KS:
        P(f'   k={k:2d}: best-weights r {best.loc[k].round(3).to_dict()} | A-only r {aon.loc[k].round(3).to_dict()}')

# ---------------- bloc sensitivity ----------------
P('\n# Bloc sensitivity: coalition share from ministerial reference instead of vote_roster.bloc')
for tname in ('T2', 'T3', 'T1'):
    q = G_[G_.target == tname].pivot_table(index=S, columns='dir', values='r'); q['mean'] = q.mean(1)
    best = dict(zip(S, q['mean'].idxmax()))
    for tgt_ref in (False, True):
        Tt = targets(cs_ref) if tgt_ref else T_roster
        rs = []
        for tr, te in DIRS:
            E = build_eval(Tt, tr, te, tname)
            for lab_, cs in (('roster', cs_roster), ('ref', cs_ref)):
                C = components(best['wsec'], cs)
                Cm = comp_matrix(comp_values(C, best['k']), E['idx'])
                p = Cm @ np.array([best['wA'], best['wV'], best['wG'], best['wB']])
                rs.append((f'{tr}->{te}', lab_, np.corrcoef(p, E['t'])[0, 1], np.corrcoef(E['M'] @ p, E['M'] @ E['t'])[0, 1]))
        P(f'{tname} best {fmt(pd.Series(best))}, target residual on {"REFERENCE" if tgt_ref else "roster"} share: ' +
          '; '.join(f'{d} comps={l}: r {r:.3f} list {rl:.3f}' for d, l, r, rl in rs))

# ---------------- candidate weighting by list position ----------------
P('\n# Candidate weight by list position (target = list-level T1 in test Knesset, equal weights → circular for the equal variant)')
q = G_[G_.target == 'T1'].pivot_table(index=S, columns='dir', values='r_list'); q['mean'] = q.mean(1)
best = dict(zip(S, q['mean'].idxmax())); P('setting (best list-level T1 by mean):', fmt(pd.Series(best)))
for tr, te in DIRS:
    E = build_eval(T_roster, tr, te, 'T1')
    C = comps_cache[best['wsec']]
    p = comp_matrix(comp_values(C, best['k']), E['idx']) @ np.array([best['wA'], best['wV'], best['wG'], best['wB']])
    df = pd.DataFrame({'l': E['lists'], 'd': E['d'], 'mk': E['mk'], 'p': p, 't': E['t']}).dropna(subset=['l'])
    df['pos'] = df.mk.map(cl.position)
    tg = df.groupby(['l', 'd']).filter(lambda x: len(x) >= 2).groupby(['l', 'd']).t.mean()
    res = {}
    for nm, w in (('equal', np.ones(len(df))), ('1/position', 1 / df.pos.values), ('top10 only', (df.pos <= 10).astype(float).values)):
        dfx = df.assign(w=w)
        dfx = dfx[dfx.w > 0]
        pr = dfx.groupby(['l', 'd']).apply(lambda x: np.average(x.p, weights=x.w))
        jj = pd.concat([pr, tg], axis=1, keys=['p', 't']).dropna()
        res[nm] = f'{jj.p.corr(jj.t):.3f} (n {len(jj)})'
    P(f'   {tr}->{te}: {res}; candidates in both Knessets per list: {df.groupby("l").mk.nunique().to_dict()}')

open(f'{OUT}/weights_out.txt', 'w').write('\n'.join(lines) + '\n')
