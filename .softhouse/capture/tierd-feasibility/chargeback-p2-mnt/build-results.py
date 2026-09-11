#!/usr/bin/env python3
"""OH-TIERD15-CM: parse the LoanChargeback-Part2 MNT replay into per-scenario
results, validate the scenario->loan map, and write `scenario-results.json` and
`replay-result-table.md`.

Copy of OH-TIERD14-CL `interest-payment-waiver-mnt/build-results.py`, itself adopted
from OH-TIERD13-CI `chargeoff-p3-mnt/build-results.py`.  Only the feature, the log
and the prose are task-specific; the parsing and the scenario->loan attribution rule
are the same.

Loan attribution: every scenario creates exactly one client and one loan at the
top, in feature order, so scenario k owns loan id k (clientId k).  The map is
validated, not assumed: each loan's create-request `clientId` must equal the
scenario position (validation runs once `stage/` exists; before extraction the
map is reported as unvalidated).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/LoanChargeback-Part2.feature')
LOG = os.path.join(HERE, 'replay-chargeback-p2-mnt.log')
STAGE = os.path.join(HERE, 'stage')
ANSI = re.compile(r'\x1b\[[0-9;]*m')
HEAD_RE = re.compile(r'^\s*Scenario:\s*(.*?)\s*#\s*\S+\.feature:(\d+)\s*$')
TAG_RE = re.compile(r'@TestRailId:(\S+)')
AT_RE = re.compile(r'\.feature:(\d+)\)')
DETAIL_RE = re.compile(r'(?i)(actual|expected|wrong value)')
EV_RE = re.compile(r'^\[([^\]]*)\]')


def parse_feature():
    """Ordered scenarios with tag, name, feature line and explicit product."""
    lines = open(FEATURE).read().splitlines()
    out = []
    tag = None
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = TAG_RE.search(s)
        if m and s.startswith('@'):
            tag = m.group(1)
        h = re.match(r'Scenario:\s*(.*)', s)
        if not h:
            continue
        name = h.group(1).strip()
        product = None
        in_table = False
        for j in range(i, len(lines)):
            t = lines[j].strip()
            if re.match(r'Scenario:', t) or t.startswith('@TestRailId') or t.startswith('@Loan'):
                break
            if t.startswith('|'):
                cells = [c.strip() for c in t.strip('|').split('|')]
                if in_table and cells and cells[0] not in ('LoanProduct',):
                    product = cells[0]
                    break
                if 'LoanProduct' in cells:
                    in_table = True
            else:
                in_table = False
        out.append({'index': len(out) + 1, 'tag': tag, 'name': name,
                    'feature_line': i, 'feature_product': product})
        tag = None
    return out


def parse_replay():
    lines = [ANSI.sub('', l.rstrip('\n')) for l in open(LOG, errors='replace')]
    heads = []
    for i, l in enumerate(lines):
        m = HEAD_RE.match(l)
        if m:
            heads.append({'index': len(heads) + 1, 'name': m.group(1).strip(),
                          'feature_line': int(m.group(2)), 'start': i})
    for k, h in enumerate(heads):
        h['end'] = heads[k + 1]['start'] if k + 1 < len(heads) else len(lines)
    for h in heads:
        block = lines[h['start']:h['end']]
        failed = [j for j, l in enumerate(block) if l.strip().startswith('✘')]
        h['result'] = 'FAILED' if failed else 'PASSED'
        h['failed_steps'] = []
        for fi in failed:
            step = block[fi].split('#')[0].strip().lstrip('✘').strip()
            d = {'step': step, 'step_feature_line': None, 'detail_lines': [],
                 'resource': None, 'tab_line': None, 'actual': None, 'expected': None}
            am = AT_RE.search(block[fi])
            if am:
                d['step_feature_line'] = int(am.group(1))
            for j in range(fi, min(fi + 60, len(block))):
                s = block[j].strip()
                if j > fi and s.startswith('Scenario:'):
                    break
                if d['step_feature_line'] is None:
                    fm = AT_RE.search(block[j])
                    if fm:
                        d['step_feature_line'] = int(fm.group(1))
                mm = re.search(r'Wrong value in (?:Repayment schedule of resource|'
                               r'resource) (\d+)', s)
                if mm:
                    d['resource'] = int(mm.group(1))
                if s.startswith('[') and d['actual'] is None:
                    d['actual'] = s
                elif s.startswith('[') and d['expected'] is None:
                    d['expected'] = s
                if s.startswith('[') or DETAIL_RE.search(s):
                    d['detail_lines'].append(s)
                if len(d['detail_lines']) >= 8:
                    break
            h['failed_steps'].append(d)
        h.pop('start')
        h.pop('end')
    return heads


def loan_facts():
    """loan id -> clientId from create-request (empty when stage/ is absent)."""
    facts = {}
    if not os.path.isdir(STAGE):
        return facts
    for fn in sorted(os.listdir(STAGE)):
        m = re.match(r'loan-(\d+)-create-request\.json$', fn)
        if m:
            lid = int(m.group(1))
            body = json.load(open(os.path.join(STAGE, fn)))
            facts.setdefault(lid, {})['clientId'] = body.get('clientId')
    return facts


def parse_step_summary():
    """Cucumber's final `N steps (...)` line; zero skipped/failed are omitted."""
    pat = re.compile(r'(\d+) steps \((.*)\)')
    for line in open(LOG, errors='replace'):
        m = pat.search(ANSI.sub('', line))
        if not m:
            continue
        total = int(m.group(1))
        counts = {label: int(n) for n, label in re.findall(
            r'(\d+) (passed|skipped|failed|ambiguous|undefined|pending)', m.group(2))}
        return {'total': total, 'passed': counts.get('passed', 0),
                'skipped': counts.get('skipped', 0), 'failed': counts.get('failed', 0)}
    return {'total': None, 'passed': None, 'skipped': None, 'failed': None}


def minor(value):
    """Decimal money text -> integer minor units (MNT, 2 digits)."""
    if value is None:
        return None
    neg = value.strip().startswith('-')
    v = value.strip().lstrip('-')
    if '.' in v:
        whole, frac = v.split('.', 1)
        frac = (frac + '00')[:2]
    else:
        whole, frac = v, '00'
    return ('-' if neg else '') + str(int(whole or '0') * 100 + int(frac))


def main():
    feature = parse_feature()
    replay = parse_replay()
    facts = loan_facts()
    validated = bool(facts)

    assert len(feature) == len(replay), (len(feature), len(replay))
    for a, b in zip(feature, replay):
        assert a['feature_line'] == b['feature_line'], (a, b)

    scenarios = []
    problems = []
    for f, r in zip(feature, replay):
        s = dict(f)
        s['result'] = r['result']
        s['failed_steps'] = r['failed_steps']
        lid = s['index']
        s['loan'] = lid
        fid = facts.get(lid, {})
        s['loan_client_id'] = fid.get('clientId')
        if validated and fid.get('clientId') != lid:
            problems.append('scenario %d: loan %d clientId=%s (expected %d)'
                            % (s['index'], lid, fid.get('clientId'), lid))
        scenarios.append(s)

    npass = sum(1 for s in scenarios if s['result'] == 'PASSED')
    obj = {'feature': os.path.basename(FEATURE), 'scenario_count': len(scenarios),
           'passed': npass, 'failed': len(scenarios) - npass, 'steps': parse_step_summary(),
           'currency': 'MNT', 'tenant': 'tierd',
           'attribution_validated': validated, 'scenarios': scenarios}
    with open(os.path.join(HERE, 'scenario-results.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('scenarios: %d; passed: %d; failed: %d; attribution validated: %s; problems: %d'
          % (len(scenarios), npass, len(scenarios) - npass, validated, len(problems)))
    for p in problems:
        print('  MISMATCH', p)

    write_table(obj)
    return 0 if not problems else 1


def write_table(obj):
    ss = obj['scenarios']
    out = []
    w = out.append
    w('# Replay result table — `LoanChargeback-Part2.feature` in MNT')
    w('')
    w('Worktree `/Users/buv/oh-gerege-tierd15`, task OH-TIERD15-CM. Whole-file replay of all')
    w('%d scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign' % obj['scenario_count'])
    w('capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is')
    w('integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal')
    w('major units the oracle emitted. Feature line numbers are from')
    w('`fineract-e2e-tests-runner/src/test/resources/features/LoanChargeback-Part2.feature`.')
    w('')
    st = obj['steps']
    w('Result: **%d scenarios (%d passed, %d failed)**; %s steps (%s passed, %s skipped, %s failed).'
      % (obj['scenario_count'], obj['passed'], obj['failed'], st['total'],
         st['passed'], st['skipped'], st['failed']))
    w('')
    w('| # | TestRailId | feature line | result | loan | product |')
    w('| --- | --- | --- | --- | --- | --- |')
    for s in ss:
        prod = ('`%s`' % s['feature_product']) if s['feature_product'] else '_(default progressive)_'
        w('| %d | %s | %d | %s | %d | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], s['loan'], prod))
    w('')
    failed = [s for s in ss if s['result'] == 'FAILED']
    w('## Failures — %d scenario%s' % (len(failed), '' if len(failed) == 1 else 's'))
    w('')
    if not failed:
        w('None. Every scenario passed: the chargeback replay — and with it the chargeback')
        w('posting (`createJournalEntriesForChargeback`) plus its charged-off and')
        w('fee/penalty-portion shapes — was exercised and the oracle agreed with every')
        w('`.feature` expectation.')
    else:
        w('Each failure is recorded with the failing step and the actual-vs-expected values')
        w('exactly as the oracle printed them; the cause is NOT decided here (the driver')
        w('dispatches an EUR control). Amounts in the log are decimal major units.')
        w('')
        for s in failed:
            w('### %d — %s — `FAILED` — loan %d — %s' % (
                s['index'], s['tag'], s['loan'], s['name']))
            w('')
            for d in s['failed_steps']:
                w('- failing step (feature line %s): `%s`' % (d['step_feature_line'], d['step']))
                if d['resource'] is not None:
                    w('  - resource/loan id in the assertion: %s' % d['resource'])
                w('')
                w('```')
                for line in d['detail_lines'] or ['(no Actual/expected line captured)']:
                    w(line)
                w('```')
            w('')
    with open(os.path.join(HERE, 'replay-result-table.md'), 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote replay-result-table.md')


if __name__ == '__main__':
    raise SystemExit(main())
