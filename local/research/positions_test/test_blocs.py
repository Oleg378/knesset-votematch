"""PROVISIONAL: (1) official reference "faction in government" from KNS_PersonToPosition;
(2) bloc definitions vs reference (current vote_roster.bloc and 3 camp-switch rules at faction level; MK-level flags);
(3) authorship data: initiators per bill, ordinal, weighted authorship stability.
Nothing here is a decision. Reuses loaders from test_hypotheses.py via exec (not modified).
Run: python3 jef/positions_test/test_blocs.py -> stdout, blocs_out.txt, CSVs.
"""
import json, numpy as np, pandas as pd

ROOT = '/Users/oleg/Documents/elections-research'
OUT = f'{ROOT}/jef/positions_test'
src = open(f'{OUT}/test_hypotheses.py').read()
g = {}
exec(src.split("posA.to_csv")[0], g)
va, rv, ro, con, SGN, bill_lab = (g[k] for k in ('va', 'rv', 'ro', 'con', 'SGN', 'bill_lab'))
rng = np.random.default_rng(3)
lines = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); lines.append(s)
P('\n=== BLOCS & AUTHORSHIP (PROVISIONAL) ===')
va['vote_date'] = pd.to_datetime(va.vote_date)
END = va.vote_date.max() + pd.Timedelta(days=1)
K25_START = pd.Timestamp('2022-11-15')
names = {p['Id']: f"{p['FirstName']} {p['LastName']}" for p in json.load(open(f'{ROOT}/data/cec/mk_persons.json'))}

# ================= PART 1 =================
P('\n# PART 1: reference "faction has ≥1 minister/deputy minister" (KNS_PersonToPosition)')
posdesc = {p['Id']: p['Description'] for p in json.load(open(f'{ROOT}/data/position.json'))}
MIN = [39, 57, 45, 31, 50, 51, 65, 73]; DEP = [40, 59, 285079]
P('minister-type ids:', {i: posdesc[i] for i in MIN}); P('deputy ids:', {i: posdesc[i] for i in DEP})
P('NOT counted (for check):', {i: d for i, d in posdesc.items() if i not in MIN + DEP and any(w in d for w in ('שר', 'ממשלה'))})
pos = json.load(open(f'{ROOT}/data/person_to_position_24_25.json'))
pp = pd.DataFrame([dict(mk_id=p['PersonID'], pid=p['PositionID'], kind='min' if p['PositionID'] in MIN else 'dep',
                        s=pd.Timestamp(p['StartDate'][:10]), f=pd.Timestamp(p['FinishDate'][:10]) if p['FinishDate'] else END,
                        gov=p['GovernmentNum'], fac_field=p['FactionID'])
                   for p in pos if p['PositionID'] in MIN + DEP])
pp['f'] = pp.f.clip(upper=END); pp['s'] = pp.s.clip(lower=pd.Timestamp('2021-04-06'))  # K24 start
P(f'position records: {len(pp)} (min {int((pp.kind=="min").sum())}, dep {int((pp.kind=="dep").sum())}); FactionID field filled: {int(pp.fac_field.notna().sum())}; persons {pp.mk_id.nunique()}')
fm = con.execute("""select m.mk_id, m.faction_id, m.knesset, cast(m.date_from as varchar) df, cast(case when m.date_to > date '2100-01-01' then null else m.date_to end as varchar) dt, f.name
  from faction_membership m join factions f using(faction_id)""").df()
fm['df'] = pd.to_datetime(fm.df); fm['dt'] = pd.to_datetime(fm.dt).fillna(END)
fname = dict(con.execute("select faction_id, name from factions").fetchall())

# person-day → faction
recs = []; unmapped = {}; fallback_days = {}
for p in pp.itertuples():
    days = pd.date_range(p.s, p.f - pd.Timedelta(days=1)) if p.f > p.s else []
    mem = fm[fm.mk_id == p.mk_id]
    for d in days:
        k = 24 if d < K25_START else 25
        m = mem[(mem.df <= d) & (mem.dt > d)]
        if len(m):
            fid = m.sort_values('df').faction_id.iloc[-1]
        else:
            mk = mem[mem.knesset == k]
            if not len(mk):
                unmapped[p.mk_id] = unmapped.get(p.mk_id, 0) + 1; continue
            dist = np.minimum((mk.df - d).abs(), (mk.dt - d).abs())
            fid = mk.loc[dist.idxmin(), 'faction_id']
            fallback_days[p.mk_id] = fallback_days.get(p.mk_id, 0) + 1
        recs.append((fid, d, p.mk_id, p.kind))
pdays = pd.DataFrame(recs, columns=['faction_id', 'day', 'mk_id', 'kind']).drop_duplicates()
P(f'person-days mapped: {len(pdays)}; via nearest membership (not seated, e.g. Norwegian law): ' +
  str({names.get(m, m): n for m, n in sorted(fallback_days.items(), key=lambda x: -x[1])}))
P('UNMAPPED persons (no faction in that Knesset — non-MK ministers):', {names.get(m, m): n for m, n in unmapped.items()})
fd = pdays.groupby(['faction_id', 'day']).agg(n_min=('kind', lambda k: (k == 'min').sum()), n_dep=('kind', lambda k: (k == 'dep').sum()),
                                               persons=('mk_id', lambda m: len(set(m)))).reset_index()
ingov = set(zip(fd.faction_id, fd.day))
# intervals
ivs = []
for f, q in fd.sort_values('day').groupby('faction_id'):
    run = (q.day.diff() != pd.Timedelta(days=1)).cumsum()
    for _, r in q.groupby(run):
        ivs.append(dict(faction_id=f, name=fname.get(f, ''), start=r.day.min().date(), end=(r.day.max() + pd.Timedelta(days=1)).date(),
                        days=len(r), max_ministers=int(r.n_min.max()), max_deputies=int(r.n_dep.max()),
                        deputy_only_days=int(((r.n_min == 0) & (r.n_dep > 0)).sum()), max_persons=int(r.persons.max())))
iv = pd.DataFrame(ivs).sort_values(['faction_id', 'start'])
iv.to_csv(f'{OUT}/blocs_reference_intervals.csv', index=False)
P('reference in-government intervals per faction (end exclusive; mins/deps max; deputy-only days):')
for r in iv.itertuples():
    flag = ' <-- deputy-only' if r.deputy_only_days == r.days else (' <-- has deputy-only days' if r.deputy_only_days else '')
    flag += ' <-- short (<30 d)' if r.days < 30 else ''
    P(f'   {r.faction_id} {r.name[:40]}: {r.start}→{r.end} ({r.days} d) min {r.max_ministers} dep {r.max_deputies}{flag}')
fac_k = con.execute("select faction_id, knesset, cast(date_from as varchar) df, cast(case when date_to > date '2100-01-01' then null else date_to end as varchar) dt from factions where knesset in (24,25)").df()
P('factions with NO in-government day:', [f'{r.faction_id} {fname[r.faction_id][:30]}' for r in fac_k.itertuples() if r.faction_id not in set(iv.faction_id)])

def ref_bloc(fid, d):
    return 'coalition' if (fid, d) in ingov else 'opposition'

# ================= PART 2 =================
P('\n# PART 2: bloc definitions vs reference (faction × bill vote rows)')
ro = con.execute("select vote_id, mk_id, faction_id, result, bloc from vote_roster").df()
r2 = ro.merge(va[['vote_id', 'vote_date', 'knesset']], on='vote_id')
r2 = r2[r2.faction_id.notna()].copy(); r2['faction_id'] = r2.faction_id.astype(int)
r2['v'] = r2.result.map({'for': 1, 'against': -1})
r2['ref'] = [ref_bloc(f, d) for f, d in zip(r2.faction_id, r2.vote_date)]
fv = r2.groupby(['vote_id', 'faction_id']).agg(date=('vote_date', 'first'), knesset=('knesset', 'first'),
        a=('bloc', lambda b: b.mode().iloc[0] if b.notna().any() else 'none'), ref=('ref', 'first'),
        vsum=('v', 'sum'), nval=('v', 'count')).reset_index()
fv = fv[fv.nval > 0]  # faction took part
P(f'faction-vote rows (faction had ≥1 for/against): {len(fv)}; (a) labels: {fv.a.value_counts().to_dict()}')
# bloc majorities by (a) excluding the faction itself
bs = fv.groupby(['vote_id', 'a']).vsum.sum().unstack().fillna(0)
fv['coal_ex'] = bs.coalition.reindex(fv.vote_id).values - np.where(fv.a == 'coalition', fv.vsum, 0)
fv['opp_ex'] = bs.opposition.reindex(fv.vote_id).values - np.where(fv.a == 'opposition', fv.vsum, 0)
fv['fs'] = np.sign(fv.vsum)
fv['split'] = (np.sign(fv.coal_ex) * np.sign(fv.opp_ex) == -1) & (fv.fs != 0)
fv['with_coal'] = fv.fs == np.sign(fv.coal_ex)
fv = fv.sort_values(['faction_id', 'date', 'vote_id']).reset_index(drop=True)
fv['month'] = fv.date.dt.to_period('M')

RULES = {'W30>=0.5': ('win', 30, .5), 'W30>=0.7': ('win', 30, .7), 'M10>=0.5': ('month', 10, .5)}
def flag_seq(q, kind, nmin, thr):
    """q: split rows of one unit (sorted) with column with_other; returns boolean array"""
    if kind == 'win':
        a = q.with_other.values.astype(float); f = np.zeros(len(a), bool)
        if len(a) >= nmin:
            cs = np.convolve(a, np.ones(nmin), 'valid') / nmin
            for i in np.where(cs >= thr)[0]: f[i:i + nmin] = True
        return f
    mm = q.groupby('month').with_other.agg(['mean', 'size'])
    bad = mm[(mm['size'] >= nmin) & (mm['mean'] >= thr)].index
    return q.month.isin(bad).values

def runs(dates, flags):
    out = []; cur = None
    for d, f in zip(dates, flags):
        if f and cur is None: cur = [d, d]
        elif f: cur[1] = d
        elif cur is not None: out.append(tuple(cur)); cur = None
    if cur is not None: out.append(tuple(cur))
    return out

FLIP = {'coalition': 'opposition', 'opposition': 'coalition'}
defs = {'a_current': fv.a.values.copy()}
fac_periods = []
for rname, (kind, nmin, thr) in RULES.items():
    lab = fv.a.values.copy()
    for (f, k), q in fv.groupby(['faction_id', 'knesset']):
        s = q[q.split & q.a.isin(['coalition', 'opposition'])].copy()
        if not len(s): continue
        s['with_other'] = np.where(s.a == 'coalition', ~s.with_coal, s.with_coal)
        fl = flag_seq(s, kind, nmin, thr)
        for st, en in runs(s.date.values, fl):
            idx = q.index[(q.date >= st) & (q.date <= en) & q.a.isin(['coalition', 'opposition'])]
            lab[idx] = [FLIP[x] for x in fv.a.values[idx]]
            fac_periods.append(dict(rule=rname, faction_id=f, name=fname.get(f, ''), start=pd.Timestamp(st).date(), end=pd.Timestamp(en).date(), votes=len(idx)))
    defs[rname] = lab
# variant: baseline = faction's bloc right after government formation in that Knesset (no later (a) corrections), then rule flips
FORM = {24: pd.Timestamp('2021-06-13'), 25: pd.Timestamp('2022-12-29')}
basel = {}
for (f, k), q in fv.groupby(['faction_id', 'knesset']):
    z = q[q.a.isin(['coalition', 'opposition']) & (q.date >= FORM[k])]
    z = z if len(z) else q[q.a.isin(['coalition', 'opposition'])]
    basel[(f, k)] = z.a.head(30).mode().iloc[0] if len(z) else 'none'
fv['base'] = [basel[(f, k)] if a != 'none' else 'none' for f, k, a in zip(fv.faction_id, fv.knesset, fv.a)]
defs['base_only'] = fv.base.values.copy()
for rname, (kind, nmin, thr) in RULES.items():
    lab = fv.base.values.copy()
    for (f, k), q in fv.groupby(['faction_id', 'knesset']):
        s = q[q.split & q.base.isin(['coalition', 'opposition'])].copy()
        if not len(s): continue
        s['with_other'] = np.where(s.base == 'coalition', ~s.with_coal, s.with_coal)
        for st, en in runs(s.date.values, flag_seq(s, kind, nmin, thr)):
            idx = q.index[(q.date >= st) & (q.date <= en) & q.base.isin(['coalition', 'opposition'])]
            lab[idx] = [FLIP[x] for x in fv.base.values[idx]]
            fac_periods.append(dict(rule='base+' + rname, faction_id=f, name=fname.get(f, ''), start=pd.Timestamp(st).date(), end=pd.Timestamp(en).date(), votes=len(idx)))
    defs['base+' + rname] = lab
fpd = pd.DataFrame(fac_periods); fpd.to_csv(f'{OUT}/blocs_faction_switch_periods.csv', index=False)
P('faction-level flagged periods per rule:')
for r in fpd.sort_values(['rule', 'start']).itertuples():
    P(f'   {r.rule}: {r.faction_id} {r.name[:35]} {r.start}→{r.end} ({r.votes} faction-votes flipped)')

# caretaker / interregnum windows (reference = outgoing government)
care = ((fv.date >= '2021-04-06') & (fv.date < '2021-06-13')) | ((fv.date >= '2022-11-15') & (fv.date < '2022-12-29'))
P(f'faction-vote rows in caretaker windows (2021-04-06..06-13, 2022-11-15..12-29): {int(care.sum())}')
tbl = []
for dn, lab in defs.items():
    ok = lab == fv.ref.values
    nn = lab != 'none'
    tbl.append(dict(definition=dn, agree_all=ok.mean(), agree_excl_caretaker=ok[~care.values].mean(),
                    agree_excl_none_and_caretaker=ok[(~care.values) & nn].mean(), none_rows=int((~nn).sum()),
                    agree_mk_weighted=np.average(ok[~care.values], weights=fv.nval.values[~care.values])))
tb = pd.DataFrame(tbl); tb.to_csv(f'{OUT}/blocs_agreement.csv', index=False)
P('agreement with reference:'); P(tb.round(4).to_string(index=False))

# transitions in reference (excluding caretaker windows and faction start)
P('\nreference transitions (faction state change between consecutive faction votes) and detection lag (days, + = later):')
fv['refc'] = fv.ref
trans = []
for f, q in fv.groupby('faction_id'):
    q = q[~care.loc[q.index].values]
    ch = q[q.ref != q.ref.shift()].iloc[1:]
    for i, r in ch.iterrows():
        prev = q.loc[:i].iloc[-2]
        trans.append(dict(faction_id=f, name=fname.get(f, ''), ref_date=r.date, prev_vote=prev.date, to=r.ref))
tr = pd.DataFrame(trans)
lagrows = []
for t in tr.itertuples():
    q = fv[(fv.faction_id == t.faction_id)]
    row = dict(faction=f'{t.faction_id} {t.name[:28]}', to=t.to, ref_first_vote=t.ref_date.date(), prev_vote=t.prev_vote.date())
    for dn, lab in defs.items():
        L = pd.Series(lab[q.index], index=q.index)
        chg = q[(L != L.shift()) & (L == t.to)].date
        if len(chg):
            dd = (chg - t.ref_date).dt.days; j = dd.abs().idxmin()
            row[dn] = int(dd[j]) if abs(dd[j]) <= 365 else 'missed'
        else:
            row[dn] = 'missed' if not (L == t.to).all() else 'always'
    lagrows.append(row)
lg = pd.DataFrame(lagrows); lg.to_csv(f'{OUT}/blocs_transition_lags.csv', index=False)
P(lg.to_string(index=False))

# false switches: runs of disagreement with reference ≥5 faction-votes
P('\ndisagreement runs vs reference (≥5 consecutive faction-votes, excl caretaker windows), per definition:')
fs_rows = []
for dn, lab in defs.items():
    for f, q in fv[~care.values].groupby('faction_id'):
        bad = lab[q.index] != q.ref.values
        rr = (pd.Series(bad, index=q.index) != pd.Series(bad, index=q.index).shift()).cumsum()
        for _, z in q[bad].groupby(rr[bad]):
            if len(z) >= 5:
                fs_rows.append(dict(definition=dn, faction=f'{f} {fname.get(f,"")[:28]}', start=z.date.min().date(), end=z.date.max().date(),
                                    votes=len(z), label=pd.Series(lab[z.index]).mode().iloc[0], ref=z.ref.iloc[0]))
fsd = pd.DataFrame(fs_rows); fsd.to_csv(f'{OUT}/blocs_disagreement_runs.csv', index=False)
for dn in defs:
    q = fsd[fsd.definition == dn]
    P(f'  {dn}: {len(q)} runs, {int(q.votes.sum())} faction-votes')
    for r in q.sort_values('votes', ascending=False).head(12).itertuples():
        P(f'     {r.faction} {r.start}→{r.end}: {r.votes} votes, label {r.label} vs ref {r.ref}')

# ---- MK level ----
P('\nMK-level rules (relative to MK row bloc in vote_roster; bloc majorities incl. MK):')
mk = r2[r2.v.notna() & r2.bloc.isin(['coalition', 'opposition'])].copy()
bm = mk.groupby(['vote_id', 'bloc']).v.sum().unstack()
mk = mk.merge(bm.rename(columns={'coalition': 'cs', 'opposition': 'os'}), left_on='vote_id', right_index=True)
mk = mk[np.sign(mk.cs) * np.sign(mk.os) == -1].sort_values(['mk_id', 'vote_date', 'vote_id'])
mk['with_other'] = np.sign(mk.v) == np.where(mk.bloc == 'coalition', np.sign(mk.os), np.sign(mk.cs))
mk['month'] = mk.vote_date.dt.to_period('M')
mkp = []
for rname, (kind, nmin, thr) in RULES.items():
    for (m, k), q in mk.groupby(['mk_id', 'knesset']):
        for st, en in runs(q.vote_date.values, flag_seq(q, kind, nmin, thr)):
            st, en = pd.Timestamp(st), pd.Timestamp(en)
            facs = q[(q.vote_date >= st) & (q.vote_date <= en)].faction_id.unique()
            covered = len(fpd) and ((fpd.rule == rname) & fpd.faction_id.isin(facs) & (pd.to_datetime(fpd.start) <= en) & (pd.to_datetime(fpd.end) >= st)).any()
            mkp.append(dict(rule=rname, mk_id=m, name=names.get(m, m), start=st.date(), end=en.date(),
                            factions=';'.join(f'{f} {fname.get(f,"")[:20]}' for f in facs), faction_flagged_too=bool(covered)))
mkp = pd.DataFrame(mkp); mkp.to_csv(f'{OUT}/blocs_mk_switch_periods.csv', index=False)
for rname in RULES:
    q = mkp[mkp.rule == rname]
    P(f'  {rname}: MK periods {len(q)}, of which faction also flagged {int(q.faction_flagged_too.sum())}; individual-only:')
    for r in q[~q.faction_flagged_too].itertuples():
        P(f'     {r.name} {r.start}→{r.end} [{r.factions}]')
P('Chikli (30786) faction membership:', [(r.faction_id, r.name[:25], r.df.date(), r.dt.date()) for r in fm[fm.mk_id == 30786].sort_values('df').itertuples()])
P('Chikli flagged periods:', mkp[mkp.mk_id == 30786][['rule', 'start', 'end']].values.tolist())
cq = mk[(mk.mk_id == 30786) & (mk.knesset == 24)]
P('Chikli monthly share with other bloc (split votes):', {str(m): f'{q.with_other.mean():.2f}/{len(q)}' for m, q in cq.groupby('month')})

# ---- reference-based against-bloc ----
P('\nreference-based bloc for MK rows:')
def bloc_stats(df, col):
    d = df[df.v.notna() & df[col].isin(['coalition', 'opposition'])]
    m = d.groupby(['vote_id', col]).v.mean().rename('bm').reset_index()
    d = d.merge(m, on=['vote_id', col])
    ag = np.sign(d.v) == np.sign(d.bm)
    ab = (np.sign(d.v) != np.sign(d.bm)) & (d.bm != 0)
    return ag.mean(), ab.mean(), int(ab.sum()), len(d)
r2c = r2.copy()
for col, lab in (('bloc', 'current vote_roster.bloc'), ('ref', 'reference (≥1 minister/deputy)')):
    a, b, n, N = bloc_stats(r2c, col)
    P(f'   {lab}: with own bloc majority {a:.4f}, against-bloc {b:.4f} ({n} of {N})')
nc = ~((r2c.vote_date >= '2021-04-06') & (r2c.vote_date < '2021-06-13')) & ~((r2c.vote_date >= '2022-11-15') & (r2c.vote_date < '2022-12-29'))
a, b, n, N = bloc_stats(r2c[nc], 'ref'); P(f'   reference, excl caretaker windows: with bloc {a:.4f}, against {b:.4f} ({n} of {N})')
a, b, n, N = bloc_stats(r2c[nc], 'bloc'); P(f'   current, excl caretaker windows: with bloc {a:.4f}, against {b:.4f} ({n} of {N})')
P(f'   MK rows with faction_id missing (excluded): {int(r2.faction_id.isna().sum()) if "faction_id" in r2 else 0}')

# ================= PART 3 =================
P('\n# PART 3: authorship data')
bi = con.execute("select i.bill_id, i.mk_id, i.is_initiator, i.ordinal, b.bill_type, b.knesset from bill_initiators i join bills b using(bill_id)").df()
prv = bi[bi.bill_type == 'פרטית']
ni = prv[prv.is_initiator].groupby('bill_id').size()
nj = prv[~prv.is_initiator].groupby('bill_id').size().reindex(ni.index).fillna(0)
P(f'private bills with initiators: {len(ni)}; initiators per bill: mean {ni.mean():.2f}, median {ni.median()}, p90 {ni.quantile(.9)}, max {ni.max()}')
P('share of bills with 1 / 2–5 / 6–10 / >10 initiators:', [round(x, 3) for x in ((ni == 1).mean(), ni.between(2, 5).mean(), ni.between(6, 10).mean(), (ni > 10).mean())])
P(f'joiners (is_initiator=false): rows {int((~prv.is_initiator).sum())}, bills with ≥1 joiner {(nj>0).mean():.3f}, mean per bill {nj.mean():.2f}')
P('other bill types initiator rows:', bi[bi.bill_type != 'פרטית'].groupby(['bill_type', 'is_initiator']).size().to_dict())
# ordinal
o = prv[prv.is_initiator]
chk = o.groupby('bill_id').ordinal.agg(lambda s: sorted(s) == list(range(1, len(s) + 1)))
jmin = prv[~prv.is_initiator].groupby('bill_id').ordinal.min(); imax = o.groupby('bill_id').ordinal.max().reindex(jmin.index)
P(f'initiator ordinals are exactly 1..n: {chk.mean():.3f}; joiner ordinals start after last initiator: {(jmin > imax).mean():.3f}')
ln = {p['Id']: p['LastName'] for p in json.load(open(f'{ROOT}/data/cec/mk_persons.json'))}
multi = o[o.bill_id.isin(ni[ni >= 3].index)].sort_values(['bill_id', 'ordinal'])
alpha = multi.groupby('bill_id').mk_id.apply(lambda s: [ln.get(m, '') for m in s] == sorted(ln.get(m, '') for m in s))
P(f'bills with ≥3 initiators whose ordinal order is alphabetical by last name: {alpha.mean():.3f} (n={len(alpha)}); random baseline for 3+ names ≤ 1/6')
first = o[o.ordinal == 1]
fc = first.mk_id.value_counts(); tc = o.mk_id.value_counts()
share_first = (fc.reindex(tc.index).fillna(0) / tc)
P(f'share of an MK\'s initiated bills where they are ordinal 1: median {share_first.median():.2f}, p10 {share_first.quantile(.1):.2f}, p90 {share_first.quantile(.9):.2f}')
# same MK repeatedly first with same co-initiators? concentration: ordinal-1 MK's faction = most common faction among initiators
P('Is ordinal 1 "first initiator"? see share above: if ordinal were arbitrary, share ≈ 1/n_initiators of bills per MK.')
exp_share = o.merge(ni.rename('n').reset_index(), on='bill_id').assign(e=lambda x: 1 / x.n).groupby('mk_id').e.mean()
P(f'   expected share if random (mean 1/n over MK bills): median {exp_share.median():.2f}; observed/expected median {(share_first / exp_share).median():.2f}, '
  f'corr across MKs {share_first.corr(exp_share):.2f}')

# authorship stability variants
rows = []
for b, (mn, sc) in bill_lab.items():
    for t in mn + sc:
        s = SGN.get(t.get('sign'))
        if s: rows.append((b, str(t['n']), s))
ab = pd.DataFrame(rows, columns=['bill_id', 'd', 's']).drop_duplicates(['bill_id', 'd'])
nall = bi[bi.is_initiator].groupby('bill_id').size().rename('n_init')
base = bi[bi.is_initiator].merge(nall, on='bill_id').merge(ab, on='bill_id')

def stab(df, wcol=None, nmin=3, label=''):
    df = df.assign(w=1.0 if wcol is None else df[wcol])
    a = df.assign(ws=df.w * df.s).groupby(['mk_id', 'knesset', 'd']).agg(sw=('w', 'sum'), ws=('ws', 'sum'), n=('s', 'size')).reset_index()
    a['pos'] = a.ws / a.sw
    a = a[a.n >= nmin]
    a['val'] = a.pos - a.groupby(['knesset', 'd']).pos.transform('mean')
    w = a.pivot_table(index=['mk_id', 'd'], columns='knesset', values='val').dropna()
    r = w[24].corr(w[25]); mks = sorted(set(w.index.get_level_values(0)))
    p24 = a[a.knesset == 24].set_index(['mk_id', 'd']).val; p25 = a[a.knesset == 25]
    perms = []
    for _ in range(200):
        mp = dict(zip(mks, rng.permutation(mks)))
        z = p25[p25.mk_id.isin(mks)].assign(mk_id=lambda x: x.mk_id.map(mp)).set_index(['mk_id', 'd']).val
        j = pd.concat([p24, z], axis=1, keys=[24, 25]).dropna(); perms.append(j[24].corr(j[25]))
    P(f'   {label}: r={r:.3f} pairs {len(w)} MKs {len(mks)} | perm 95% [{np.quantile(perms,.025):.3f}, {np.quantile(perms,.975):.3f}]')
P('authorship stability K24↔K25 (centered per Knesset×dir, MK level, ≥3 bills each Knesset):')
stab(base, None, label='all initiators, equal weight (expect ≈0.52)')
base['w_inv'] = 1 / base.n_init
stab(base, 'w_inv', label='weight 1/n_initiators (n = weighted-count still ≥3 bills)')
stab(base[base.ordinal == 1], None, label='first initiator only (ordinal=1)')
stab(base[base.n_init <= 5], None, label='only bills with ≤5 initiators')

open(f'{OUT}/blocs_out.txt', 'w').write('\n'.join(lines) + '\n')
