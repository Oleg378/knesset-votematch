"""Production computation of positions (SU 27.2–27.3). Self-contained.
Outputs -> jef/positions/ : see README.md written by this script.
Run: python3 pipeline/positions.py
"""
import json, glob, os
import numpy as np, pandas as pd, duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{ROOT}/jef/positions'
LAB = f'{ROOT}/jef/directions/labels'
os.makedirs(OUT, exist_ok=True)
SGN = {'+': 1, '−': -1, '-': -1}
W_A, W_V = 1.0, 0.25            # SU 27.3: authorship 1, private-bill votes 0.25, secondary topics = main
W_O = 0.25                      # [У] 2026-10-18 (Р1): votes against the other camp's bills (local/research/other_camp/)
BEH_X, BEH_MIN = 0.9, 200       # [У] 2026-10-18 (Р2): a faction without ministers that votes with the government in >= 90 % of
                                # >= 200 votes in a Knesset counts as coalition for cleaning votes (Ra'am K24)
MIN_IDS = {39, 57, 45, 31, 50, 51, 65, 73}   # שר/שרה/ראש הממשלה/משנה/סגן ראש הממשלה/מ"מ/סגנית/ראש הממשלה החילופי
DEP_IDS = {40, 59, 285079}                   # סגן שר / סגנית שר / סגן שרה
LOW_NA = 10                                  # [А] "личных законопроектов почти нет"
log = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); log.append(s)

con = duckdb.connect(f'{ROOT}/knesset.duckdb', read_only=True)
dirs = pd.read_csv(f'{ROOT}/jef/directions/DIRECTIONS_LIST.csv', dtype={'n': str})
dname = dict(zip(dirs.n, dirs.name_ru))
names = {p['Id']: f"{p['FirstName']} {p['LastName']}" for p in json.load(open(f'{ROOT}/data/cec/mk_persons.json'))}

# ======================= labels (pipeline/labels.py) =======================
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels
_lab = labels.load()
technical, bill_lab, pk_agent, pk_whole, SPLIT_PLAN = (_lab[k] for k in ('technical', 'bill_lab', 'pk_agent', 'pk_whole', 'split_plan'))
for k, v in SPLIT_PLAN['new'].items(): dname[k] = v['name_ru']
signed_topics = labels.signed_topics

# ======================= votes =======================
va = con.execute("""select a.vote_id, a.vote_date, a.knesset, a.bill_id, a.stage, b.bill_type, b.name bill_name
  from vote_attrs a left join bills b using(bill_id)
  where a.kind='bill' and a.stage in ('preliminary','first','second','third')""").df()
va['vote_date'] = pd.to_datetime(va.vote_date)
def vote_label(r):
    if r.vote_id in pk_agent: return pk_agent[r.vote_id]
    if r.vote_id in pk_whole: return pk_whole[r.vote_id]
    return bill_lab.get(r.bill_id)
va['topics'] = [signed_topics(vote_label(r)) if vote_label(r) is not None else {} for r in va.itertuples()]
va = va[~va.bill_id.astype(str).isin(technical)]
ro = con.execute("""select r.vote_id, r.mk_id, r.faction_id, r.result, r.bloc from vote_roster r join vote_attrs a using(vote_id)
  where a.kind='bill' and a.stage in ('preliminary','first','second','third')""").df()
ro = ro.merge(va[['vote_id', 'vote_date', 'knesset', 'bill_type']], on='vote_id')
ro['v'] = ro.result.map({'for': 1, 'against': -1})
rv = ro.dropna(subset=['v']).copy()
P(f'bill votes (4 stages, non-technical): {len(va)}; roster rows with for/against: {len(rv)}; MKs {rv.mk_id.nunique()}')

# ======================= government reference (KNS_PersonToPosition) =======================
kt = con.execute("select knesset, cast(date_from as varchar) df from knesset_terms where knesset in (24,25,26)").df()
KSTART = {int(k): pd.Timestamp(d) for k, d in zip(kt.knesset, kt.df)}
END = va.vote_date.max() + pd.Timedelta(days=1)
pos = json.load(open(f'{ROOT}/data/person_to_position_24_25.json'))
pp = pd.DataFrame([dict(mk_id=p['PersonID'], kind='min' if p['PositionID'] in MIN_IDS else 'dep', gov=p['GovernmentNum'],
                        s=pd.Timestamp(p['StartDate'][:10]), f=pd.Timestamp(p['FinishDate'][:10]) if p['FinishDate'] else END)
                   for p in pos if p['PositionID'] in MIN_IDS | DEP_IDS])
pp['s'] = pp.s.clip(lower=KSTART[24]); pp['f'] = pp.f.clip(upper=END)
pp = pp[pp.f > pp.s]
# government formation dates from the data: first start of each GovernmentNum
gstart = pp.groupby('gov').s.min()
FORM = {24: gstart.get(36), 25: gstart.get(37)}
TRANS = [(KSTART[24], FORM[24]), (KSTART[25], FORM[25])]   # transition (caretaker) windows
P('government formation (from positions):', {k: str(v.date()) for k, v in FORM.items()}, '| transition windows:', [(str(a.date()), str(b.date())) for a, b in TRANS])
def in_trans(d):
    m = np.zeros(len(d), bool)
    for a, b in TRANS: m |= (d >= a) & (d < b)
    return m

fm = con.execute("""select mk_id, faction_id, knesset, cast(date_from as varchar) df,
  cast(case when date_to > date '2100-01-01' then null else date_to end as varchar) dt from faction_membership""").df()
fm['df'] = pd.to_datetime(fm.df); fm['dt'] = pd.to_datetime(fm.dt).fillna(END)
fname = dict(con.execute("select faction_id, name from factions").fetchall())
recs = []
for p in pp.itertuples():
    mem = fm[fm.mk_id == p.mk_id]
    days = pd.date_range(p.s, p.f - pd.Timedelta(days=1))
    for d in days:
        k = 24 if d < KSTART[25] else 25
        m = mem[(mem.df <= d) & (mem.dt > d)]
        if len(m): fid = m.sort_values('df').faction_id.iloc[-1]
        else:   # not seated (e.g. Norwegian law): nearest membership in the same Knesset
            mk = mem[mem.knesset == k]
            if not len(mk): continue
            fid = mk.loc[np.minimum((mk.df - d).abs(), (mk.dt - d).abs()).idxmin(), 'faction_id']
        recs.append((int(fid), d, p.mk_id, p.kind, k))
pdays = pd.DataFrame(recs, columns=['faction_id', 'day', 'mk_id', 'kind', 'knesset']).drop_duplicates()
INGOV = set(zip(pdays.faction_id, pdays.day))
# months in government per person per Knesset (person-level, regardless of seat)
gdays = []
for p in pp.itertuples():
    for k in (24, 25):
        a, b = max(p.s, KSTART[k]), min(p.f, KSTART[25] if k == 24 else END)
        if b > a: gdays.append((p.mk_id, k, a, b))
gd = pd.DataFrame(gdays, columns=['mk_id', 'knesset', 'a', 'b'])
def union_days(q):
    s = set()
    for r in q.itertuples(): s |= set(pd.date_range(r.a, r.b - pd.Timedelta(days=1)))
    return len(s)
gov_months = (gd.groupby(['mk_id', 'knesset']).apply(union_days) / 30.44).round(1).rename('gov_months')

ro['gov_side'] = [(int(f), d) in INGOV if pd.notna(f) else False for f, d in zip(ro.faction_id, ro.vote_date)]
ro['trans'] = in_trans(ro.vote_date.values)
# [У] 2026-10-18 (Р2, external audit С2): camp for cleaning votes and for «the other camp» = government by ministers (INGOV) OR a
# faction that votes with the government majority in >= BEH_X of its votes in that Knesset (outside the transition windows) while
# having no minister most of the time. The government layer keeps INGOV (ministers only).
_g = ro.dropna(subset=['v']); _g = _g[~_g.trans]
_gm = _g[_g.gov_side].groupby('vote_id').v.mean().rename('gm'); _g = _g.join(_gm, on='vote_id'); _g = _g[_g.gm.notna() & (_g.gm != 0)]
_g = _g.assign(w=np.sign(_g.v) == np.sign(_g.gm))
_fs = _g[_g.faction_id.notna()].groupby([_g.faction_id.astype(int), 'knesset']).agg(share=('w', 'mean'), n=('w', 'size'), ingov=('gov_side', 'mean'))
_beh = _fs[(_fs.share >= BEH_X) & (_fs.ingov < 0.5) & (_fs.n >= BEH_MIN)]
INGOV_V = set(INGOV)
for (f, k), _ in _beh.iterrows():
    INGOV_V |= {(int(f), pd.Timestamp(d)) for d in ro[(ro.faction_id == f) & (ro.knesset == k)].vote_date.unique()}
P('coalition by behaviour (cleaning votes):', [(fname.get(int(f)), int(k), round(r.share, 3)) for (f, k), r in _beh.iterrows()])
ro['camp_gov'] = [(int(f), d) in INGOV_V if pd.notna(f) else False for f, d in zip(ro.faction_id, ro.vote_date)]
rv = ro.dropna(subset=['v']).copy()

# ======================= A: authorship =======================
bi = con.execute("""select i.bill_id, i.mk_id, b.knesset from bill_initiators i join bills b using(bill_id)
  where i.is_initiator and b.knesset in (24,25)""").df()
bi = bi[~bi.bill_id.astype(str).isin(technical)]
nA_total = bi.groupby('mk_id').bill_id.nunique()  # all initiated non-technical bills
arows = [(b, d, s) for b, lab in bill_lab.items() for d, s in signed_topics(lab).items()]
ab = pd.DataFrame(arows, columns=['bill_id', 'd', 's'])
A = bi.merge(ab, on='bill_id').groupby(['mk_id', 'knesset', 'd']).s.agg(['mean', 'size']).reset_index().rename(columns={'mean': 'A', 'size': 'nA'})
# [У] 2026-10-17: A is NOT centered (variant Б). Centering over the authors zeroed A wherever the bills of a direction go one way
# (every author +1 − mean +1 = 0; 32 of 199 directions); centering over all MKs would read «did not sponsor» as «against».
# Not sponsoring = no authorship signal (0); the side then comes from votes. local/research/a_centering/.

# ======================= V: private-bill votes, residual on government share =======================
share = rv[~rv.trans].groupby(['mk_id', 'knesset']).camp_gov.mean().rename('gov_share')
pv = rv[rv.bill_type == 'פרטית']
vt = va.set_index('vote_id').topics
vrows = [(r.mk_id, r.knesset, d, s * r.v) for r in pv.itertuples() for d, s in vt[r.vote_id].items()]
V = pd.DataFrame(vrows, columns=['mk_id', 'knesset', 'd', 'c']).groupby(['mk_id', 'knesset', 'd']).c.agg(['mean', 'size']).reset_index().rename(columns={'mean': 'pos', 'size': 'nV'})
V = V.join(share, on=['mk_id', 'knesset']).dropna(subset=['gov_share'])
grp = V.groupby(['knesset', 'd'])
mx, my = grp.gov_share.transform('mean'), grp.pos.transform('mean')
cov = ((V.gov_share - mx) * (V.pos - my)).groupby([V.knesset, V.d]).transform('mean')
var = ((V.gov_share - mx) ** 2).groupby([V.knesset, V.d]).transform('mean')
beta = (cov / var.where(var > 1e-9)).fillna(0)
V['V'] = V.pos - my - beta * (V.gov_share - mx)   # residual, mean 0 per Knesset × direction
P(f'A rows (MK×Knesset×dir): {len(A)}; V rows: {len(V)}')

# ======================= O: votes against the other camp's bills [У] 2026-10-18 (Р1) =======================
# A government bill is the coalition's; a private bill belongs to the camp of the majority of its initiators on the vote date. O = mean
# of topic sign × vote over the MK's votes on bills of the other camp (all four stages, outside the transition windows), NOT residualised:
# it keeps «the opposition voted against the coalition's bills on X», which V removes with the government axis (external audit К1).
_ini = con.execute("select bill_id, mk_id from bill_initiators where is_initiator").df().groupby('bill_id').mk_id.apply(list).to_dict()
_fmd = {m: q for m, q in fm.groupby('mk_id')}
def _faction_at(m, d):
    q = _fmd.get(m)
    if q is None: return None
    x = q[(q.df <= d) & (q.dt > d)]
    return int(x.sort_values('df').faction_id.iloc[-1]) if len(x) else None
bcamp = {}
for r in va.itertuples():
    if r.bill_type == 'ממשלתית': bcamp[r.vote_id] = True; continue
    if r.bill_type != 'פרטית': continue
    s_ = [(f, r.vote_date) in INGOV_V for f in (_faction_at(m, r.vote_date) for m in _ini.get(r.bill_id, [])) if f is not None]
    if s_: bcamp[r.vote_id] = bool(np.mean(s_) > 0.5)
ov = rv[~rv.trans & rv.vote_id.isin(bcamp.keys())]
ov = ov[ov.camp_gov.values != ov.vote_id.map(bcamp).values]
orows = [(r.mk_id, r.knesset, d, s * r.v) for r in ov.itertuples() for d, s in vt[r.vote_id].items()]
O = pd.DataFrame(orows, columns=['mk_id', 'knesset', 'd', 'c']).groupby(['mk_id', 'knesset', 'd']).c.agg(['mean', 'size']).reset_index().rename(columns={'mean': 'O', 'size': 'nO'})
P(f'O rows (votes on the other camp\'s bills): {len(O)}; bills with a camp: {len(bcamp)}')

# ======================= pool Knessets, topic position =======================
def pool(df, val, n):
    g = df.assign(w=df[val] * df[n]).groupby(['mk_id', 'd'])
    return pd.DataFrame({val: g.w.sum() / g[n].sum(), n: g[n].sum()})
T = pool(A, 'A', 'nA').join(pool(V, 'V', 'nV'), how='outer').join(pool(O, 'O', 'nO'), how='outer').reset_index()
T[['nA', 'nV', 'nO']] = T[['nA', 'nV', 'nO']].fillna(0).astype(int)
# [У] 2026-10-17: the model the weights were fitted on (local/research/positions_test/test_weights.py): P = A + 0.25 V, a missing
# component counts 0. Before: (A + 0.25 V) / (1[A] + 0.25 [V]) — votes of a MK without own bills on the topic went in at full weight.
T['P_A'] = W_A * T.A.fillna(0)
T['P_V'] = W_V * T.V.fillna(0)
T['P_O'] = W_O * T.O.fillna(0)
T['P'] = T.P_A + T.P_V + T.P_O   # [У] 2026-10-18: P = A + 0.25 V + 0.25 O
T['name'] = T.mk_id.map(names); T['direction'] = T.d.map(dname)
T = T[['mk_id', 'name', 'd', 'direction', 'P', 'P_A', 'P_V', 'P_O', 'A', 'nA', 'V', 'nV', 'O', 'nO']]
T.round(4).to_csv(f'{OUT}/mk_topic_positions.csv', index=False)
P(f'mk_topic_positions: {len(T)} rows, MKs {T.mk_id.nunique()}, directions {T.d.nunique()}; with A: {T.A.notna().sum()}, V only: {(T.A.isna()).sum()}')

# ======================= lists =======================
cand = pd.read_csv(f'{ROOT}/manual/candidate_mk_26.csv')
cec = pd.read_csv(f'{ROOT}/manual/cec_lists_26.csv'); lname = dict(zip(cec.letters, cec.name_en))
cm = cand[cand.match.isin(['exact', 'manual'])].copy(); cm['mk_id'] = cm.mk_id.astype(int)
cm = cm.drop_duplicates('mk_id')
L = cm[['letters', 'mk_id']].merge(T, on='mk_id')
LP = L.groupby(['letters', 'd']).agg(P=('P', 'mean'), P_A=('P_A', 'mean'), P_V=('P_V', 'mean'), n_mk=('mk_id', 'size'), sum_nA=('nA', 'sum'), sum_nV=('nV', 'sum'), P_O=('P_O', 'mean'), sum_nO=('nO', 'sum')).reset_index()
# [У] 2026-10-18 (external audit №2, С2): distinct bills behind a list × direction — sponsored, or voted on (V or O) — counted by
# name without the year, so a bill re-submitted in the next Knesset counts once. Used for «a clear position needs >= 2 MKs and
# >= 2 distinct bills» (quiz_report.is_clear).
import re as _re
_base = lambda n: _re.sub(r",?\s*(ה?תש[\"״׳'\w\-]*\s*-?\s*\d{4})\s*$", "", str(n or "")).strip()
_bn = {b: _base(n) for b, n in con.execute("select bill_id, name from bills").fetchall()}
_vb = dict(zip(va.vote_id, va.bill_id))
_ev = pd.concat([bi.merge(ab, on='bill_id')[['mk_id', 'd', 'bill_id']],
                 pd.DataFrame([(r.mk_id, d, _vb.get(r.vote_id)) for r in pv.itertuples() for d in vt[r.vote_id]], columns=['mk_id', 'd', 'bill_id']),
                 pd.DataFrame([(r.mk_id, d, _vb.get(r.vote_id)) for r in ov.itertuples() for d in vt[r.vote_id]], columns=['mk_id', 'd', 'bill_id'])])
_ev['name'] = _ev.bill_id.map(_bn)
_ev = cm[['letters', 'mk_id']].merge(_ev, on='mk_id')
LP = LP.merge(_ev.groupby(['letters', 'd']).name.nunique().rename('n_names').reset_index(), on=['letters', 'd'], how='left')
LP['n_names'] = LP.n_names.fillna(0).astype(int)
LP['low_data'] = LP.n_mk < 3
LP['list_name'] = LP.letters.map(lname); LP['direction'] = LP.d.map(dname)
LP = LP[['letters', 'list_name', 'd', 'direction', 'P', 'P_A', 'P_V', 'n_mk', 'sum_nA', 'sum_nV', 'low_data', 'P_O', 'sum_nO', 'n_names']]
LP.round(4).to_csv(f'{OUT}/list_topic_positions.csv', index=False)

cov_rows = []
for l in cec.letters:
    c = cand[cand.letters == l]; m = cm[cm.letters == l]
    exmk = len(m); top10 = int((m.position <= 10).sum())
    status = 'not_evaluated' if exmk == 0 else ('warning' if top10 < 3 else 'ok')
    q = LP[LP.letters == l]
    cov_rows.append(dict(letters=l, list_name=lname.get(l), candidates=len(c), ex_mks=exmk, ex_mks_top10=top10, status=status,
                         dirs_nmk_ge1=int((q.n_mk >= 1).sum()), dirs_nmk_ge3=int((q.n_mk >= 3).sum()),
                         median_nA_per_exmk=float(m.mk_id.map(nA_total).fillna(0).median()) if exmk else np.nan))
LC = pd.DataFrame(cov_rows).sort_values(['ex_mks'], ascending=False)
LC.to_csv(f'{OUT}/list_coverage.csv', index=False)

# ======================= government layer =======================
g = rv[~rv.trans]
gm = g[g.gov_side].groupby('vote_id').v.mean().rename('gov_maj')
g = g.join(gm, on='vote_id'); g = g[g.gov_maj.notna() & (g.gov_maj != 0)]
g['with_gov'] = np.sign(g.v) == np.sign(g.gov_maj)
GM = g.groupby(['mk_id', 'knesset']).agg(n_votes=('v', 'size'), with_gov=('with_gov', 'sum')).reset_index()
GM['share_with_gov'] = (GM.with_gov / GM.n_votes).round(4)
GM['gov_months'] = [gov_months.get((m, k), 0.0) for m, k in zip(GM.mk_id, GM.knesset)]
GM['name'] = GM.mk_id.map(names)
GM = GM.merge(cm[['mk_id', 'letters']], on='mk_id', how='left')
GM[['mk_id', 'name', 'letters', 'knesset', 'n_votes', 'with_gov', 'share_with_gov', 'gov_months']].to_csv(f'{OUT}/government_layer_mk.csv', index=False)
GL = GM.dropna(subset=['letters']).groupby(['letters', 'knesset']).agg(n_mk=('mk_id', 'size'), n_votes=('n_votes', 'sum'), with_gov=('with_gov', 'sum'),
                                                                      mean_mk_share=('share_with_gov', 'mean')).reset_index()
GL['share_with_gov'] = (GL.with_gov / GL.n_votes).round(4); GL['mean_mk_share'] = GL.mean_mk_share.round(4)
GL['list_name'] = GL.letters.map(lname)
GL.to_csv(f'{OUT}/government_layer_list.csv', index=False)

# ======================= camp (behavioral) and against-camp examples =======================
fr = ro[ro.faction_id.notna()].copy(); fr['faction_id'] = fr.faction_id.astype(int)
fv = fr.groupby(['vote_id', 'faction_id']).agg(date=('vote_date', 'first'), knesset=('knesset', 'first'),
        a=('bloc', lambda b: b.mode().iloc[0] if b.notna().any() else 'none'), vsum=('v', 'sum'), nval=('v', 'count')).reset_index()
fv = fv[fv.nval > 0]
bs = fv.groupby(['vote_id', 'a']).vsum.sum().unstack().fillna(0)
fv['coal_ex'] = bs.coalition.reindex(fv.vote_id).values - np.where(fv.a == 'coalition', fv.vsum, 0)
fv['opp_ex'] = bs.opposition.reindex(fv.vote_id).values - np.where(fv.a == 'opposition', fv.vsum, 0)
fv['split'] = (np.sign(fv.coal_ex) * np.sign(fv.opp_ex) == -1) & (np.sign(fv.vsum) != 0)
fv['with_coal'] = np.sign(fv.vsum) == np.sign(fv.coal_ex)
fv = fv.sort_values(['faction_id', 'date', 'vote_id']).reset_index(drop=True)
FLIP = {'coalition': 'opposition', 'opposition': 'coalition'}

def w30_runs(dates, with_other, n=30, thr=.7):
    a = np.asarray(with_other, float); f = np.zeros(len(a), bool)
    if len(a) >= n:
        cs_ = np.convolve(a, np.ones(n), 'valid') / n
        for i in np.where(cs_ >= thr)[0]: f[i:i + n] = True
    out, cur = [], None
    for d, x in zip(dates, f):
        if x and cur is None: cur = [d, d]
        elif x: cur[1] = d
        elif cur is not None: out.append(tuple(cur)); cur = None
    if cur is not None: out.append(tuple(cur))
    return out

base = {}
for (f, k), q in fv.groupby(['faction_id', 'knesset']):
    z = q[q.a.isin(['coalition', 'opposition']) & (q.date >= FORM[k])]
    z = z if len(z) else q[q.a.isin(['coalition', 'opposition'])]
    base[(f, k)] = z.a.head(30).mode().iloc[0] if len(z) else 'none'
fv['base'] = [base[(f, k)] if a != 'none' else 'none' for f, k, a in zip(fv.faction_id, fv.knesset, fv.a)]
camp = fv.base.values.copy(); fac_switch = []
for (f, k), q in fv.groupby(['faction_id', 'knesset']):
    s = q[q.split & q.base.isin(['coalition', 'opposition'])]
    wo = np.where(s.base == 'coalition', ~s.with_coal, s.with_coal)
    for st, en in w30_runs(s.date.values, wo):
        idx = q.index[(q.date >= st) & (q.date <= en) & q.base.isin(['coalition', 'opposition'])]
        camp[idx] = [FLIP[x] for x in fv.base.values[idx]]
        fac_switch.append((f, fname.get(f), str(pd.Timestamp(st).date()), str(pd.Timestamp(en).date())))
fv['camp'] = camp
P('faction camp switches (W30≥0.7):', fac_switch)
rc = rv.merge(fv[['vote_id', 'faction_id', 'camp']], on=['vote_id', 'faction_id'], how='left')
rc = rc[rc.camp.isin(['coalition', 'opposition'])]
cmaj = rc.groupby(['vote_id', 'camp']).v.mean().unstack()
rc = rc.join(cmaj.rename(columns={'coalition': 'm_coal', 'opposition': 'm_opp'}), on='vote_id')
rc['own'] = np.where(rc.camp == 'coalition', rc.m_coal, rc.m_opp)
rc['other'] = np.where(rc.camp == 'coalition', rc.m_opp, rc.m_coal)
rc['against'] = (np.sign(rc.v) != np.sign(rc.own)) & (rc.own != 0)
# MK-level switch periods
sp = rc[np.sign(rc.own) * np.sign(rc.other) == -1].sort_values(['mk_id', 'vote_date', 'vote_id'])
mk_sw = []
for (m, k), q in sp.groupby(['mk_id', 'knesset']):
    for st, en in w30_runs(q.vote_date.values, np.sign(q.v) == np.sign(q.other)):
        mk_sw.append((m, pd.Timestamp(st), pd.Timestamp(en)))
excl = pd.Series(False, index=rc.index)
for m, st, en in mk_sw:
    excl |= (rc.mk_id == m) & (rc.vote_date >= st) & (rc.vote_date <= en)
P('MK camp-switch periods (W30≥0.7):', [(names.get(m, m), str(a.date()), str(b.date())) for m, a, b in mk_sw])
ex = rc[rc.against & ~excl].merge(va[['vote_id', 'bill_id', 'bill_name', 'stage', 'topics']], on='vote_id')
ex['topics_signed'] = [ '; '.join(f'{d}{"+" if s > 0 else "−"} {dname.get(d, "")}' for d, s in t.items()) for t in ex.topics]
ex['vote'] = ex.result; ex['camp_majority'] = np.where(ex.own > 0, 'for', 'against')
ex['name'] = ex.mk_id.map(names); ex = ex.merge(cm[['mk_id', 'letters']], on='mk_id', how='left')
ex = ex.sort_values(['mk_id', 'vote_date'])
ex[['mk_id', 'name', 'letters', 'knesset', 'vote_id', 'vote_date', 'bill_id', 'bill_name', 'stage', 'camp', 'vote', 'camp_majority', 'topics_signed']].to_csv(
    f'{OUT}/against_camp_examples.csv', index=False)
P(f'against-camp rows: {int(rc.against.sum())}, in MK switch periods {int((rc.against & excl).sum())}, examples written {len(ex)}')

# ======================= candidate notes =======================
cn = cand[cand.match.isin(['exact', 'manual'])].copy(); cn['mk_id'] = cn.mk_id.astype(int)
cn['gov_months_k24'] = [gov_months.get((m, 24), 0.0) for m in cn.mk_id]
cn['gov_months_k25'] = [gov_months.get((m, 25), 0.0) for m in cn.mk_id]
cn['nA'] = cn.mk_id.map(nA_total).fillna(0).astype(int)
cn['nA_labeled'] = cn.mk_id.map(bi[bi.bill_id.isin(ab.bill_id)].groupby('mk_id').bill_id.nunique()).fillna(0).astype(int)
cn['dirs_with_P'] = cn.mk_id.map(T.groupby('mk_id').size()).fillna(0).astype(int)
cn['note'] = np.where(cn.nA < LOW_NA, 'личных законопроектов почти нет', '')
cn['list_name'] = cn.letters.map(lname)
cn[['letters', 'list_name', 'position', 'name_he', 'mk_id', 'gov_months_k24', 'gov_months_k25', 'nA', 'nA_labeled', 'dirs_with_P', 'note']].sort_values(['letters', 'position']).to_csv(
    f'{OUT}/candidates_notes.csv', index=False)

# ======================= summary numbers =======================
P('\n# list coverage'); P(LC.to_string(index=False))
big = LP[LP.n_mk >= 3]
sd = big.groupby('d').P.agg(['std', 'size']); sd = sd[sd['size'] >= 3].sort_values('std', ascending=False)
P('\n# top-10 differentiating directions (SD of list P among lists with n_mk≥3)')
for d, r in sd.head(10).iterrows():
    vals = big[big.d == d].set_index('letters').P.round(2).to_dict()
    P(f'  {d} {dname[d]}: SD {r["std"]:.3f} ({int(r["size"])} lists) {vals}')
P(f'directions with ≥3 lists: {len(sd)}; SD quantiles {sd["std"].quantile([.1,.5,.9]).round(3).to_dict()}')
P('\n# government layer per list'); P(GL[['letters', 'knesset', 'n_mk', 'n_votes', 'share_with_gov', 'mean_mk_share']].to_string(index=False))
P('\n# candidates with note:', cn[cn.note != ''][['letters', 'name_he', 'nA', 'gov_months_k24', 'gov_months_k25']].values.tolist())

# ======================= README =======================
readme = f"""# Позиции депутатов и списков 2026

Считает `pipeline/positions.py` (запуск: `python3 pipeline/positions.py`). Правила — SU п. 27.2–27.3 (`docs/SHARED_UNDERSTANDING.md`).
Метки [У] — решение заказчика, [А] — решение исполнителя (на пересмотр, SU п. 28).

## Правила
- **Слой тем [У, 27.2–27.3].** На депутата × направление, оба созыва вместе.
  - **A — авторство.** Законопроекты, где депутат инициатор (`is_initiator`), все инициаторы с равным весом. Каждый законопроект даёт свои темы (главные и побочные наравне) со знаком ±1. Темы без знака пропускаются. Технические законопроекты (`overrides.json`, SU 23c) исключены. Метки бюджетных пакетов на A не влияют. A = средний знак, nA = число законопроектов.
  - **V — голоса по частным законопроектам.** «За» = +1, «против» = −1; вклад = знак темы × голос. Берётся остаток после регрессии на долю голосов депутата, поданных, когда его фракция была на стороне правительства (внутри созыва × направления). nV = число голосов.
  - A не центрируется (вариант Б, SU 27.3, 2026-10-17): знак законопроектов как есть, не вносил — 0 (нет сигнала). V — остаток, его среднее по созыву × направлению равно 0. Созывы объединяются с весом n.
  - **O — голоса против законопроектов другого лагеря [У, 2026-10-18].** Правительственный законопроект — коалиционный; частный — лагеря большинства его инициаторов на дату голосования. O = средний знак темы × голос по законопроектам чужого лагеря (все четыре чтения, без переходных окон), **без** вычета оси правительства: так видно «оппозиция голосовала против законов коалиции о X». nO = число голосов.
  - **Лагерь для очистки голосов и для O [У, 2026-10-18]** — правительство по министрам **или** фракция без министров, голосующая с большинством правительства в ≥ 90 % из ≥ 200 голосов в созыве (сейчас так только РААМ в K24). Слой правительства по-прежнему только по министрам.
  - **P = 1·A + 0,25·V + 0,25·O; нет компоненты — 0** (A и V — как при подборе весов, SU 27.3, 2026-10-17; O — 2026-10-18). P_A и P_V — вклады авторства и голосов. Метки, снятые по двум независимым проверкам (`overrides.json` «remove», SU 27.3, 2026-10-18), не учитываются; Jev-фильтр относимости выключен (`labels.REL_T = None`). Голоса по правительственным законопроектам (и статьям пакетов) и голоса против лагеря — вес 0. Авторство: только `is_initiator`; отозванные подписи (KNS_BillHistoryInitiator «חזר בו», 4 случая) не вычитаются [А]. Сжатия нет ни здесь, ни при ранжировании (K = 0, 2026-10-18).
- **Правительство [У, 27.3].** Фракция с ≥1 министром или замминистром на дату (`data/person_to_position_24_25.json`; должности {sorted(MIN_IDS)} и {sorted(DEP_IDS)}).
  - Человек → фракция по `faction_membership` на дату. Если он не депутат (норвежский закон), берётся его ближайшее членство в том же созыве [А]. Из-за этого министры, сложившие мандат, относятся к фракции до раскола (например, Дерех Эрец).
  - Переходные окна от начала созыва до формирования правительства ({', '.join(f'{a.date()}–{b.date()}' for a, b in TRANS)}; дата — первая запись должностей правительства 36/37) исключены из доли «на стороне правительства» и из слоя правительства [А].
  - Известные расхождения с политической реальностью: РААМ в K24 без министров — «не в правительстве»; Ноам и ЯХадут Тора с 2026-01 держатся только замминистром.
- **Позиция списка [У, п. 17, 27.3].** Среднее с равным весом по сопоставленным кандидатам — бывшим депутатам (`manual/candidate_mk_26.csv`, match exact/manual), у которых есть P. Если n_mk < 3, ставится low_data [У, 27.2: пометка «мало данных»].
- **Покрытие [У, п. 20].** Нет бывших депутатов → not_evaluated. Меньше 3 бывших депутатов в первой десятке → warning.
- **Слой правительства [У, 27.2–27.3].** По созывам отдельно: доля голосов «за/против» по законопроектам, совпавших с большинством стороны правительства (по министрам); переходные окна исключены. Месяцы на должности министра или замминистра считаются по человеку, независимо от мандата.
- **Лагерь и голоса против лагеря [У, 27.3; реализация — А].** Лагерь — поведенческий: метка блока фракции сразу после формирования правительства (мода `vote_roster.bloc`) плюс смены по правилу «окно 30 голосований, где лагеря разошлись, ≥70 % с чужим лагерем» (уровень фракции). Голоса против большинства своего лагеря выводятся как примеры. Голоса в периодах индивидуальной смены лагеря (то же правило на уровне депутата) не считаются. В позицию эти голоса не входят.
- **Министры [У, 27.2].** Даты подачи законопроектов в данных нет, поэтому авторство по периодам должности не разделяется. Министры и замминистры не подают частные законопроекты, поэтому их авторство и так относится к периодам без должности [А]. Пометка «личных законопроектов почти нет» ставится, если nA < {LOW_NA} [А, порог предварительный].

## Файлы
- `mk_topic_positions.csv` — депутат × направление: P, A, nA (законопроекты, оба созыва), V, nV (голоса).
- `list_topic_positions.csv` — список × направление: P, P_A, P_V, P_O, n_mk, sum_nA, sum_nV, sum_nO, low_data, n_names (разные законопроекты за позицией: внесённые и голосованные, по названию без года).
- `list_coverage.csv` — по каждому списку 2026: кандидатов, бывших депутатов (всего и в первой десятке), статус покрытия (п. 20), число направлений с n_mk≥1 и ≥3, медиана nA на бывшего депутата.
- `government_layer_mk.csv` — депутат × созыв: голосов, совпавших с правительством, доля, месяцы на должности.
- `government_layer_list.csv` — список × созыв: те же суммы по кандидатам; share_with_gov — по всем голосам, mean_mk_share — среднее по депутатам.
- `against_camp_examples.csv` — голоса депутата против большинства своего лагеря (вне периодов смены лагеря): законопроект, стадия, дата, темы со знаками.
- `candidates_notes.csv` — кандидат: месяцы министром или замминистром (K24, K25), nA (все внесённые законопроекты) и nA_labeled (из них с размеченными темами со знаком), число направлений с P, пометка.
- `run_log.txt` — числа последнего запуска.
"""
open(f'{OUT}/README.md', 'w').write(readme)
open(f'{OUT}/run_log.txt', 'w').write('\n'.join(log) + '\n')
