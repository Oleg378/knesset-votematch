"""PROVISIONAL coverage checks: (1) per-MK completeness of authorship / against-bloc data, ministers;
(2) against-bloc votes vs sustained camp switches. Thresholds below are CANDIDATE rules for comparison, not decisions.
Reuses loaders from test_hypotheses.py (exec of its source up to the first file write; not modified).
Run: python3 jef/positions_test/test_coverage.py -> stdout, coverage_out.txt, CSVs.
"""
import json, numpy as np, pandas as pd

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
src = open(f'{OUT}/test_hypotheses.py').read()
g = {}
exec(src.split("posA.to_csv")[0], g)
X, va, rv, con, SGN, bill_lab = (g[k] for k in ('X', 'va', 'rv', 'con', 'SGN', 'bill_lab'))
rng = np.random.default_rng(5)
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('\n=== COVERAGE CHECKS (PROVISIONAL) ===')

names = {p['Id']: f"{p['FirstName']} {p['LastName']}" for p in json.load(open(f'{ROOT}/data/cec/mk_persons.json'))}
cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cand = cand[cand.match.isin(['exact', 'manual'])].copy(); cand['mk_id'] = cand.mk_id.astype(int)
cl = cand[['letters', 'mk_id', 'position']].drop_duplicates('mk_id')
va['vote_date'] = pd.to_datetime(va.vote_date)
END = va.vote_date.max()

# ---------- base: against-bloc at vote level ----------
rvb = rv[rv.bloc.isin(['coalition', 'opposition'])].merge(va[['vote_id', 'vote_date', 'knesset']], on='vote_id')
bm = rvb.groupby(['vote_id', 'bloc']).v.mean().unstack()
rvb = rvb.merge(bm.stack().rename('bm').reset_index(), on=['vote_id', 'bloc'])
rvb['against_bloc'] = (np.sign(rvb.v) != np.sign(rvb.bm)) & (rvb.bm != 0)
P('MK for/against rows with bloc coal/opp:', len(rvb), '| against own bloc majority:', int(rvb.against_bloc.sum()), f'({rvb.against_bloc.mean():.2%})')
dev = X.merge(rvb[['vote_id', 'mk_id', 'against_bloc', 'vote_date']], on=['vote_id', 'mk_id'])
dev = dev[dev.against_bloc]

# ---------- CHECK 1 ----------
P('\n# CHECK 1: completeness per MK')
bi = con.execute("select i.bill_id, i.mk_id, i.is_initiator, b.knesset from bill_initiators i join bills b using(bill_id)").df()
rows = []
for b, (mn, sc) in bill_lab.items():
    for t in mn + sc:
        if SGN.get(t.get('sign')): rows.append((b, str(t['n'])))
abd = pd.DataFrame(rows, columns=['bill_id', 'd']).drop_duplicates()
ini = bi[bi.is_initiator]
auth_d = ini.merge(abd, on='bill_id').groupby(['mk_id', 'd']).bill_id.nunique()

terms = con.execute("select mk_id, knesset, cast(date_from as varchar) date_from, cast(case when date_to > date '2100-01-01' then null else date_to end as varchar) date_to from mk_terms where knesset in (24,25)").df()
terms['date_from'] = pd.to_datetime(terms.date_from); terms['date_to'] = pd.to_datetime(terms.date_to).fillna(END).clip(upper=END)
pos = json.load(open(f'{ROOT}/data/person_to_position_24_25.json'))
MIN = {39, 57, 45, 31, 50, 51, 65, 73}; DEP = {40, 59, 285079}
pp = pd.DataFrame([dict(mk_id=p['PersonID'], kind='minister' if p['PositionID'] in MIN else 'deputy', knesset=p['KnessetNum'],
                        s=p['StartDate'][:10], f=(p['FinishDate'] or '')[:10]) for p in pos if p['PositionID'] in MIN | DEP])
pp['s'] = pd.to_datetime(pp.s); pp['f'] = pd.to_datetime(pp.f.replace('', None)).fillna(END).clip(upper=END)
kt = {24: (pd.Timestamp('2021-04-06'), pd.Timestamp('2022-11-15')), 25: (pd.Timestamp('2022-11-15'), END)}

def days_union(iv):
    iv = sorted(iv); tot = 0; cur = None
    for s, f in iv:
        if f <= s: continue
        if cur is None or s > cur[1]:
            if cur: tot += (cur[1] - cur[0]).days
            cur = [s, f]
        else: cur[1] = max(cur[1], f)
    if cur: tot += (cur[1] - cur[0]).days
    return tot

def overlap_days(iv1, iv2):
    out = []
    for s1, f1 in iv1:
        for s2, f2 in iv2:
            s, f = max(s1, s2), min(f1, f2)
            if f > s: out.append((s, f))
    return days_union(out)

mk_all = sorted(set(rvb.mk_id) | set(terms.mk_id))
recs = []
for m in mk_all:
    for k in (24, 25):
        t = [(r.date_from, r.date_to) for r in terms[(terms.mk_id == m) & (terms.knesset == k)].itertuples()]
        kw = [kt[k]]
        mins = [(r.s, r.f) for r in pp[(pp.mk_id == m) & (pp.kind == 'minister')].itertuples()]
        deps = [(r.s, r.f) for r in pp[(pp.mk_id == m) & (pp.kind == 'deputy')].itertuples()]
        knes_days = (kt[k][1] - kt[k][0]).days
        mk_days = days_union(t)
        gov_days = overlap_days(kw, [*mins, *deps])
        b = bi[(bi.mk_id == m) & (bi.knesset == k)]
        vv = rvb[(rvb.mk_id == m) & (rvb.knesset == k)]
        vall = rv[rv.mk_id == m].merge(va[['vote_id', 'knesset']], on='vote_id'); vall = vall[vall.knesset == k]
        if mk_days == 0 and len(b) == 0 and len(vall) == 0: continue
        recs.append(dict(mk_id=m, name=names.get(m, ''), knesset=k, mk_days=mk_days, minister_days=overlap_days(kw, mins),
                         deputy_days=overlap_days(kw, deps), gov_share_of_knesset=round(gov_days / knes_days, 3),
                         gov_share_of_mk_tenure=round(overlap_days(t, [*mins, *deps]) / mk_days, 3) if mk_days else np.nan,
                         initiated=int(b[b.is_initiator].bill_id.nunique()), joined=int(b[~b.is_initiator].bill_id.nunique()),
                         votes_value=len(vall), against_bloc=int(vv.against_bloc.sum())))
per = pd.DataFrame(recs)
# directions (pooled over Knessets)
ad = auth_d.reset_index().rename(columns={'bill_id': 'nb'})
dd = dev.groupby(['mk_id', 'd']).vote_id.nunique().rename('na').reset_index()
tot = per.groupby('mk_id').agg(name=('name', 'first'), initiated=('initiated', 'sum'), joined=('joined', 'sum'),
                               votes_value=('votes_value', 'sum'), against_bloc=('against_bloc', 'sum'),
                               minister_days=('minister_days', 'sum'), deputy_days=('deputy_days', 'sum'), mk_days=('mk_days', 'sum'))
tot['gov_share_of_tenure'] = ((per.groupby('mk_id').apply(lambda q: (q.gov_share_of_mk_tenure * q.mk_days).sum()) / tot.mk_days)).round(3)
tot['auth_dirs_ge1'] = ad.groupby('mk_id').size().reindex(tot.index).fillna(0).astype(int)
tot['auth_dirs_ge3'] = ad[ad.nb >= 3].groupby('mk_id').size().reindex(tot.index).fillna(0).astype(int)
tot['ab_dirs_ge1'] = dd.groupby('mk_id').size().reindex(tot.index).fillna(0).astype(int)
tot['ab_dirs_ge3'] = dd[dd.na >= 3].groupby('mk_id').size().reindex(tot.index).fillna(0).astype(int)
tot = tot.join(cl.set_index('mk_id'))
per.to_csv(f'{OUT}/coverage_mk_by_knesset.csv', index=False)
tot.reset_index().to_csv(f'{OUT}/coverage_mk_total.csv', index=False)
P(f'MKs (K24–25 with term or votes): {len(tot)}; matched 2026 candidates among them: {tot.letters.notna().sum()}')
def dist(s): return {q: round(s.quantile(q), 1) for q in (.1, .25, .5, .75, .9)}
for nm, t in (('all MKs', tot), ('2026 candidates', tot[tot.letters.notna()])):
    P(f'{nm}: initiated {dist(t.initiated)} | joined {dist(t.joined)} | votes with value {dist(t.votes_value)}')
    P(f'   against-bloc votes {dist(t.against_bloc)} | auth dirs ≥1 bill {dist(t.auth_dirs_ge1)} | auth dirs ≥3 bills {dist(t.auth_dirs_ge3)}')
    P(f'   against-bloc dirs ≥1 {dist(t.ab_dirs_ge1)} | ≥3 {dist(t.ab_dirs_ge3)} | zero initiated: {(t.initiated==0).sum()} | zero against-bloc: {(t.against_bloc==0).sum()}')
# ministers vs authorship (MK×Knesset level)
pk = per[per.mk_days > 30].copy()
pk['grp'] = pd.cut(pk.gov_share_of_mk_tenure, [-.01, 0, .5, 1.01], labels=['0', '(0,0.5]', '>0.5'])
pk['init_per_year'] = pk.initiated / (pk.mk_days / 365)
P('MK×Knesset by share of tenure as minister/deputy (MK tenure>30 days): n / median initiated / median initiated per MK-year / median joined')
for gname, q in pk.groupby('grp'):
    P(f'   {gname}: n={len(q)}, initiated {q.initiated.median()}, per year {q.init_per_year.median():.1f}, joined {q.joined.median()}, zero initiated {(q.initiated==0).mean():.0%}')
mins_tot = pp.mk_id.nunique()
P(f'persons with minister/deputy positions in K24–25: {mins_tot}; among 2026 candidates: {cl.mk_id.isin(pp.mk_id).sum()}; '
  f'ministers not MKs in data (norwegian law etc.): {len(set(pp.mk_id) - set(terms.mk_id))}')
P(f'r(gov share of tenure, initiated per MK-year) over MK×Knesset: {pk.gov_share_of_mk_tenure.corr(pk.init_per_year):.3f}')
# per list
P('\nPer 2026 list (candidates matched): usable authorship rules: R_a1 = ≥3 dirs with ≥3 initiated bills; R_a2 = ≥5 dirs with ≥3; R_a3 = ≥3 dirs with ≥1')
P('                                    against-bloc rules: R_b1 = ≥3 dirs with ≥3 votes; R_b2 = ≥3 dirs with ≥1 vote; R_b3 = ≥1 dir with ≥3 votes')
c = tot[tot.letters.notna()]
lt = c.groupby('letters').apply(lambda q: pd.Series(dict(
    n=len(q), Ra1=(q.auth_dirs_ge3 >= 3).sum(), Ra2=(q.auth_dirs_ge3 >= 5).sum(), Ra3=(q.auth_dirs_ge1 >= 3).sum(),
    Rb1=(q.ab_dirs_ge3 >= 3).sum(), Rb2=(q.ab_dirs_ge1 >= 3).sum(), Rb3=(q.ab_dirs_ge3 >= 1).sum(),
    gov_gt50=(q.gov_share_of_tenure > .5).sum(), med_init=q.initiated.median(), med_ab=q.against_bloc.median()))).sort_values('n', ascending=False)
P(lt.to_string())
lt.to_csv(f'{OUT}/coverage_lists.csv')
thin = lt[(lt.Ra1 / lt.n < .5) & (lt.n >= 3)]
P('lists with ≥3 candidates where <50% have usable authorship (R_a1):', {l: f'{int(r.Ra1)}/{int(r.n)}' for l, r in thin.iterrows()})
P('candidates with gov share >0.5 and their authorship (initiated, auth dirs ≥3):',
  [(r.name, r.letters, r.gov_share_of_tenure, int(r.initiated), int(r.auth_dirs_ge3)) for r in c[c.gov_share_of_tenure > .5].sort_values('letters').itertuples()])

# ---------- CHECK 2 ----------
P('\n# CHECK 2: against-bloc vs sustained camp switch')
bmw = bm.dropna()
split = bmw[(np.sign(bmw.coalition) * np.sign(bmw.opposition) == -1)]
P(f'split votes (coal and opp majorities opposite): {len(split)} of {len(bm)} bill votes with both blocs')
sv = rvb[rvb.vote_id.isin(split.index)].copy()
sv['other_bm'] = np.where(sv.bloc == 'coalition', split.opposition.reindex(sv.vote_id).values, split.coalition.reindex(sv.vote_id).values)
sv['with_other'] = np.sign(sv.v) == np.sign(sv.other_bm)
sv = sv.sort_values(['mk_id', 'vote_date', 'vote_id'])
sv['month'] = sv.vote_date.dt.to_period('M')

RULES = {'W30>=0.5': ('win', 30, .5), 'W30>=0.7': ('win', 30, .7), 'M10>=0.5': ('month', 10, .5)}
flags = {}
periods = []
for rname, (kind, nmin, thr) in RULES.items():
    fl = pd.Series(False, index=sv.index)
    for (m, k), q in sv.groupby(['mk_id', 'knesset']):
        if kind == 'win':
            a = q.with_other.values.astype(float)
            if len(a) < nmin: continue
            cs_ = np.convolve(a, np.ones(nmin), 'valid') / nmin
            f = np.zeros(len(a), bool)
            for i in np.where(cs_ >= thr)[0]: f[i:i + nmin] = True
            fl.loc[q.index] = f
        else:
            mm = q.groupby('month').with_other.agg(['mean', 'size'])
            bad = mm[(mm['size'] >= nmin) & (mm['mean'] >= thr)].index
            fl.loc[q.index] = q.month.isin(bad).values
    flags[rname] = fl
    # contiguous runs → periods
    f2 = sv.assign(fl=fl)
    for (m, k), q in f2.groupby(['mk_id', 'knesset']):
        run = (q.fl != q.fl.shift()).cumsum()
        for _, r in q[q.fl].groupby(run[q.fl]):
            periods.append(dict(rule=rname, mk_id=m, name=names.get(m, ''), knesset=k, start=r.vote_date.min().date(), end=r.vote_date.max().date(),
                                split_votes=len(r), share_with_other=round(r.with_other.mean(), 2), bloc=r.bloc.iloc[0]))
per_df = pd.DataFrame(periods)
fm = con.execute("select m.mk_id, m.faction_id, f.name, cast(m.date_from as varchar) date_from, cast(m.date_to as varchar) date_to from faction_membership m join factions f using(faction_id)").df()
def fac(m):
    q = fm[fm.mk_id == m].sort_values('date_from')
    return '; '.join(f'{r.name[:28]} {r.date_from}→{r.date_to}' for r in q.itertuples())
if len(per_df):
    per_df['factions'] = per_df.mk_id.map(fac)
    per_df.to_csv(f'{OUT}/switch_periods.csv', index=False)
for rname in RULES:
    q = per_df[per_df.rule == rname] if len(per_df) else per_df
    P(f'\nrule {rname}: MKs flagged {q.mk_id.nunique() if len(q) else 0}, periods {len(q)}')
    if len(q):
        for r in q.sort_values(['knesset', 'start']).itertuples():
            P(f'   K{r.knesset} {r.name} ({r.mk_id}, {r.bloc}) {r.start}→{r.end}: {r.split_votes} split votes, with other bloc {r.share_with_other}')
if len(per_df):
    P('\nfaction membership of MKs flagged by any rule:')
    for m in per_df.mk_id.unique():
        P(f'   {names.get(m, m)}: {fac(m)}')

# share of against-bloc votes inside flagged periods
abv = rvb[rvb.against_bloc][['vote_id', 'mk_id', 'vote_date', 'knesset']]
def in_periods(df, rname):
    q = per_df[per_df.rule == rname] if len(per_df) else per_df
    mask = pd.Series(False, index=df.index)
    for r in q.itertuples():
        mask |= (df.mk_id == r.mk_id) & (df.vote_date >= pd.Timestamp(r.start)) & (df.vote_date <= pd.Timestamp(r.end))
    return mask
P(f'\nagainst-bloc votes total: {len(abv)}')
for rname in RULES:
    msk = in_periods(abv, rname)
    P(f'   rule {rname}: in flagged periods {int(msk.sum())} ({msk.mean():.1%}), scattered {int((~msk).sum())}')

# stability of variant (d) excluding periods
def stab(dv, label):
    p = dv.groupby(['mk_id', 'knesset', 'd']).c.agg(['mean', 'size']).reset_index()
    out = []
    for nmin in (1, 3):
        q = p[p['size'] >= nmin]
        w = q.pivot_table(index=['mk_id', 'd'], columns='knesset', values='mean').dropna()
        if len(w) < 10: out.append(f'n≥{nmin}: pairs {len(w)}'); continue
        r = w[24].corr(w[25]); mks = sorted(set(w.index.get_level_values(0)))
        p24 = q[q.knesset == 24].set_index(['mk_id', 'd'])['mean']; p25 = q[q.knesset == 25]
        perms = []
        for _ in range(300):
            mp = dict(zip(mks, rng.permutation(mks)))
            z = p25[p25.mk_id.isin(mks)].assign(mk_id=lambda x: x.mk_id.map(mp)).set_index(['mk_id', 'd'])['mean']
            j = pd.concat([p24, z], axis=1, keys=[24, 25]).dropna(); perms.append(j[24].corr(j[25]))
        out.append(f'n≥{nmin}: r={r:.3f} pairs {len(w)} MKs {len(mks)} perm 95% [{np.nanquantile(perms,.025):.2f},{np.nanquantile(perms,.975):.2f}]')
    P(f'(d) stability {label}: ' + ' | '.join(out))
stab(dev, 'all against-bloc')
for rname in RULES:
    stab(dev[~in_periods(dev, rname)], f'excluding {rname} periods')

# top 15 MKs by against-bloc count
P('\nTop 15 MKs by against-bloc votes (count | of their votes | months with any | share in busiest month | in W30>=0.5 periods | 2026 list)')
abv2 = abv.assign(month=abv.vote_date.dt.to_period('M'))
m1 = in_periods(abv2, 'W30>=0.5')
nv = rvb.groupby('mk_id').size()
for m, cnt in abv2.mk_id.value_counts().head(15).items():
    q = abv2[abv2.mk_id == m]; mc = q.month.value_counts()
    sh_busy = mc.iloc[0] / cnt; inper = m1[q.index].mean()
    pattern = 'concentrated' if (inper > .5 or sh_busy > .5) else 'scattered'
    lst = cl.set_index('mk_id').letters.get(m, '-')
    P(f'   {names.get(m, m)} ({m}): {cnt} | {cnt/nv[m]:.1%} | {len(mc)} months | {sh_busy:.0%} ({mc.index[0]}) | {inper:.0%} | {lst} → {pattern}')

open(f'{OUT}/coverage_out.txt', 'w').write('\n'.join(lines) + '\n')
