"""Bill and vote labels as the positions use them (shared by positions.py and jev_relevance.py).

load() -> dict(technical, bill_lab, pk_agent, pk_whole, split_plan):
  bill_lab[bill_id] = (main, secondary) after the split of heterogeneous directions, the point corrections and the relevance
  filter (a quiz direction is removed from a bill that is not about the issue of its quiz statements; SU 27.3, 2026-10-17);
  pk_agent / pk_whole — labels of budget-package votes (by vote_id).
signed_topics(lab) -> {direction: ±1} over main and secondary (equal weight; unsigned skipped).
"""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "jef/directions/labels")
SGN = {'+': 1, '−': -1, '-': -1}
REL_FILE = os.path.join(ROOT, "jef/directions/relevance/relevance_q2.jsonl")   # pipeline/jev_relevance.py
REL_T = None   # threshold of «the bill is about the statement's issue»; None = filter off: not accepted by the customer
               # (SU 27.3, 2026-10-17 evening) [О]; options and tests: local/research/relevance_impact/, local/jef/directions/relevance/pilot_gold.csv

def irrelevant():
    """(bill_id, direction) pairs below the relevance threshold. Pairs without a check are kept."""
    if REL_T is None or not os.path.exists(REL_FILE): return set()
    return {(r['bill_id'], r['d']) for r in map(json.loads, open(REL_FILE)) if r['p'] < REL_T}

def load(relevance=True, stage2=True):
    technical = set()
    for v in json.load(open(f'{LAB}/overrides.json'))['technical'].values():
        technical |= set(v['bill_ids'])
    bill_lab = {}
    for f in sorted(glob.glob(f'{LAB}/batch_*.jsonl')):
        for l in open(f):
            r = json.loads(l)
            if r['bill_id'] in technical: continue
            bill_lab[int(r['bill_id'])] = (r.get('main') or [], r.get('secondary') or [])
    # split of heterogeneous quiz directions (PROGRESS «План», 2026-10-16; jef/directions/split/plan.json, labels/split_choice.jsonl):
    # for a bill whose parent direction got sub-directions/transfers, the parent topic is replaced by the chosen candidates with the
    # parent's role; a bill with no candidate keeps the parent (leftover). A candidate already present keeps its existing entry.
    split_plan = json.load(open(f'{ROOT}/jef/directions/split/plan.json'))
    for l in open(f'{LAB}/split_choice.jsonl'):
        r = json.loads(l)
        b = int(r['bill_id'])
        if b not in bill_lab or not r['assigned']: continue
        main, sec = [list(x) for x in bill_lab[b]]
        lst = main if r['role'] == 'main' else sec
        lst[:] = [t for t in lst if str(t['n']) != r['parent']]
        have = {str(t['n']) for t in main + sec}
        for a in r['assigned']:
            if a['n'] not in have: lst.append({'n': a['n'], 'sign': a['sign']}); have.add(a['n'])
        bill_lab[b] = (main, sec)
    # point corrections of resonant laws (customer decision 2026-10-17: gross errors in high-profile laws are fixed point-wise;
    # local/jef/h9_check/landmark/fix/, applied from overrides.json «labels»)
    for b, v in json.load(open(f'{LAB}/overrides.json')).get('labels', {}).items():
        if int(b) in bill_lab: bill_lab[int(b)] = (v['main'], v['secondary'])
    # stage 2 (2026-10-18 [У]): directions split by the statement audit (jef/directions/split/plan2.json, labels/split2_choice.jsonl),
    # applied after stage 1 and the overrides in the same way; sub-directions keep the parent's sign.
    plan2 = json.load(open(f'{ROOT}/jef/directions/split/plan2.json'))
    if stage2 and os.path.exists(f'{LAB}/split2_choice.jsonl'):
        for l in open(f'{LAB}/split2_choice.jsonl'):
            r = json.loads(l)
            b = int(r['bill_id'])
            if b not in bill_lab or not r['assigned']: continue
            main, sec = [list(x) for x in bill_lab[b]]
            lst = main if r['role'] == 'main' else sec
            lst[:] = [t for t in lst if str(t['n']) != r['parent']]
            have = {str(t['n']) for t in main + sec}
            for a in r['assigned']:
                if a['n'] not in have: lst.append({'n': a['n'], 'sign': a['sign']}); have.add(a['n'])
            bill_lab[b] = (main, sec)
    split_plan = {**split_plan, 'new': {**split_plan['new'], **plan2['new']}, 'parents': {**split_plan['parents'], **plan2['parents']}}
    if relevance:
        drop = irrelevant()
        for b, (main, sec) in list(bill_lab.items()):
            if any((str(b), str(t['n'])) in drop for t in main + sec):
                bill_lab[b] = ([t for t in main if (str(b), str(t['n'])) not in drop], [t for t in sec if (str(b), str(t['n'])) not in drop])
    pk_agent, pk_whole = {}, {}
    for l in open(f'{LAB}/packages_agent.jsonl'):
        r = json.loads(l)
        pk_agent[int(r['vote_id'])] = ([], []) if r.get('technical') else (r.get('main') or [], r.get('secondary') or [])
    for l in open(f'{LAB}/packages_whole.jsonl'):
        r = json.loads(l)
        for v in r['votes']: pk_whole[int(v['vote_id'])] = (r['main'], [])
    return dict(technical=technical, bill_lab=bill_lab, pk_agent=pk_agent, pk_whole=pk_whole, split_plan=split_plan)

def signed_topics(lab):
    out = {}
    for lst in lab:
        for t in lst:
            s = SGN.get(t.get('sign'))
            if s and str(t['n']) not in out: out[str(t['n'])] = s
    return out  # d -> sign (main and secondary equal weight; unsigned skipped)
