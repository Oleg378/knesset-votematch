"""Bill and vote labels as the positions use them (shared by positions.py and jev_relevance.py).

load() -> dict(technical, bill_lab, pk_agent, pk_whole, split_plan):
  bill_lab[bill_id] = (main, secondary) after the split of heterogeneous directions (stages 1–3), the point corrections, the
  label removals (overrides.json «remove»: two checks found the bill is not about the statement's question; SU 27.3, 2026-10-18)
  and the relevance filter (off: REL_T = None);
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

LATER = [(2, 'plan2.json', 'split2_choice.jsonl'), (3, 'plan3.json', 'split3_choice.jsonl'), (4, 'plan4.json', 'split4_choice.jsonl'),
         (5, 'plan5.json', 'split5_choice.jsonl'),
         (6, 'plan6.json', 'split6_choice.jsonl')]   # later split stages, in order (5, 6: baskets, 2026-10-20; choice and sign by Sonnet)

def later_plans():
    """Plans of the later split stages (2: audit of the statements, 3: audit of the new statements, 4: audit after the label removals,
    5: the basket directions that pass the selection criteria), in order."""
    return [json.load(open(f'{ROOT}/jef/directions/split/{p}')) for _, p, _ in LATER]

def load(relevance=True, stages=99, nested=True):
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
    # later stages (2026-10-18 [У]): directions split by the audits of the statements (jef/directions/split/plan2.json, plan3.json;
    # labels/split2_choice.jsonl, split3_choice.jsonl), applied after stage 1 and the overrides, in order; parts keep the parent's
    # sign. stages=N applies stages up to N (jev_split.py takes the bills of stage N from the labels after stage N-1).
    for k, p, out in LATER:
        plan_k = json.load(open(f'{ROOT}/jef/directions/split/{p}'))
        split_plan = {**split_plan, 'new': {**split_plan['new'], **plan_k['new']}, 'parents': {**split_plan['parents'], **plan_k['parents']}}
        if k > stages or not os.path.exists(f'{LAB}/{out}'): continue
        for l in open(f'{LAB}/{out}'):
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
    # label removals (customer decision 2026-10-18 [У]): a bill's label on a direction is removed when it is not about the question of
    # that direction's statement (Opus audit of the bills that create the list spread + an independent blind second check; only
    # removals both agree on; local/research/secondary_weight_v2/). Applied after the splits, so part directions (e.g. 130b) work.
    rm = {(str(r['bill_id']), str(r['d'])) for r in json.load(open(f'{LAB}/overrides.json')).get('remove', {}).get('items', [])}
    for b, (main, sec) in list(bill_lab.items()):
        if any((str(b), str(t['n'])) in rm for t in main + sec):
            bill_lab[b] = ([t for t in main if (str(b), str(t['n'])) not in rm], [t for t in sec if (str(b), str(t['n'])) not in rm])
    # symmetric corrections (customer decision 2026-10-18, Р8 / external audit С7): a label's sign flipped, or a missing label added,
    # where two independent checks agree (overrides.json «flip», «add»; local/research/r8_labels/). Applied after the removals.
    ov = json.load(open(f'{LAB}/overrides.json'))
    for r in ov.get('flip', {}).get('items', []):
        b = int(r['bill_id'])
        if b in bill_lab:
            bill_lab[b] = tuple([dict(t, sign=r['sign']) if str(t['n']) == str(r['d']) else t for t in lst] for lst in bill_lab[b])
    for r in ov.get('add', {}).get('items', []):
        b = int(r['bill_id'])
        if b in bill_lab and not any(str(t['n']) == str(r['d']) for t in bill_lab[b][0] + bill_lab[b][1]):
            main, sec = [list(x) for x in bill_lab[b]]
            (main if r.get('role') == 'main' else sec).append({'n': str(r['d']), 'sign': r['sign']})
            bill_lab[b] = (main, sec)
    # nested themes (global audit, [У] 2026-10-20): where ≥ 50 % of a narrow theme's bills are also in a broad theme, the shared bills
    # count in only one of them, chosen by meaning (nested_removals.json; local/research/theme_overlap/). Applied last, on the result above.
    nf = f'{LAB}/nested_removals.json'
    if nested and os.path.exists(nf):
        nr = {(str(r['bill_id']), str(r['d'])) for r in json.load(open(nf))['items']}
        for b, (main, sec) in list(bill_lab.items()):
            if any((str(b), str(t['n'])) in nr for t in main + sec):
                bill_lab[b] = ([t for t in main if (str(b), str(t['n'])) not in nr], [t for t in sec if (str(b), str(t['n'])) not in nr])
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
