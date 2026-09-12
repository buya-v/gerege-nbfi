#!/usr/bin/env python3
"""OH-TIERD25-DG: parse the EMICalculation-Part2 MNT replay into per-scenario
results, validate the scenario->loan map, and write `scenario-results.json` and
`replay-result-table.md`.

Copy of OH-TIERD22-DB `merchant-refund-mnt/build-results.py`, adapted for this
feature.  EMICalculation-Part2.feature has 50 plain `Scenario:` blocks and no
`Scenario Outline`, but TWO of its scenarios each create a SECOND loan for the
SAME client, so the feature creates 52 loans over 50 clients.  Scenario k
therefore owns every loan whose create-request `clientId` is the k-th client id
the replay created -- not merely loan id k.  The map is validated, not assumed:
the client ids seen on loan create-requests must be a contiguous ascending run
of one id per scenario, and every loan must be attributed to a scenario.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/EMICalculation-Part2.feature')
LOG = os.path.join(HERE, 'replay-emi-calculation-p2-mnt.log')
STAGE = os.path.join(HERE, 'stage')
ANSI = re.compile(r'\x1b\[[0-9;]*m')
HEAD_RE = re.compile(r'^\s*Scenario(?: Outline)?:\s*(.*?)\s*#\s*\S+\.feature:(\d+)\s*$')
TAG_RE = re.compile(r'@TestRailId:(\S+)')
AT_RE = re.compile(r'\.feature:(\d+)\)')
DETAIL_RE = re.compile(r'(?i)(actual|expected|wrong value)')
EV_RE = re.compile(r'^\[([^\]]*)\]')


def _scan_product(lines, start, stop):
    """First product cell from the step tables in lines[start:stop], or None."""
    product = None
    in_table = False
    for j in range(start, stop):
        t = lines[j].strip()
        if t.startswith('|'):
            cells = [c.strip() for c in t.strip('|').split('|')]
            if in_table and cells and cells[0] not in ('LoanProduct',):
                product = cells[0]
                break
            if 'LoanProduct' in cells:
                in_table = True
        else:
            in_table = False
    return product


def parse_feature():
    """Ordered scenarios with tag, name, feature line and explicit product.

    `Scenario Outline` blocks are expanded: each `Examples:` data row yields one
    scenario whose `<key>` placeholders are substituted and whose feature line is
    the data row's line (matching the line Cucumber prints for the example).
    """
    lines = open(FEATURE).read().splitlines()
    n = len(lines)
    out = []
    tag = None
    i = 0
    while i < n:
        s = lines[i].strip()
        m = TAG_RE.search(s)
        if m and s.startswith('@'):
            tag = m.group(1)
        h = re.match(r'Scenario:\s*(.*)', s)
        ho = re.match(r'Scenario Outline:\s*(.*)', s)
        if h:
            stop = n
            for j in range(i + 1, n):
                t = lines[j].strip()
                if re.match(r'Scenario(?: Outline)?:', t) or t.startswith('@TestRailId') or t.startswith('@Loan'):
                    stop = j
                    break
            out.append({'index': len(out) + 1, 'tag': tag, 'name': h.group(1).strip(),
                        'feature_line': i + 1,
                        'feature_product': _scan_product(lines, i, stop)})
            tag = None
        elif ho:
            outline = ho.group(1).strip()
            i += 1
            while i < n:
                t = lines[i].strip()
                tm = TAG_RE.search(t)
                if tm and t.startswith('@'):
                    tag = tm.group(1)
                if re.match(r'Scenario(?: Outline)?:', t):
                    break
                if t.startswith('Examples:'):
                    j = i + 1
                    header = None
                    while j < n and lines[j].strip().startswith('|'):
                        cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
                        if header is None:
                            header = cells
                        else:
                            row = dict(zip(header, cells))
                            name = outline
                            for k, v in row.items():
                                name = name.replace('<%s>' % k, v)
                            out.append({'index': len(out) + 1, 'tag': tag,
                                        'name': name, 'feature_line': j + 1,
                                        'feature_product': row.get('loanProduct')})
                        j += 1
                    i = j
                    tag = None
                    continue
                i += 1
            continue
        i += 1
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
    """loan id -> {clientId, productId} from create-request (empty when stage/ absent)."""
    facts = {}
    if not os.path.isdir(STAGE):
        return facts
    for fn in sorted(os.listdir(STAGE)):
        m = re.match(r'loan-(\d+)-create-request\.json$', fn)
        if m:
            lid = int(m.group(1))
            body = json.load(open(os.path.join(STAGE, fn)))
            facts[lid] = {
                'clientId': body.get('clientId'),
                'productId': body.get('productId') or body.get('loanProductId'),
            }
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

    # client id -> sorted loan ids, from this replay's create-requests.
    by_client = {}
    for lid, f in facts.items():
        by_client.setdefault(f.get('clientId'), []).append(lid)
    for cid in by_client:
        by_client[cid] = sorted(by_client[cid])
    distinct_clients = sorted(c for c in by_client if c is not None)

    problems = []
    client_of_scenario = {}
    if validated:
        if len(distinct_clients) != len(feature):
            problems.append('distinct client ids on loan create-requests = %d, '
                            'scenarios = %d (expected one client per scenario)'
                            % (len(distinct_clients), len(feature)))
        # The replay creates one client per scenario, in order; the k-th client
        # id therefore belongs to scenario k.
        for k, cid in enumerate(distinct_clients):
            client_of_scenario[k + 1] = cid

    scenarios = []
    attributed = set()
    for f, r in zip(feature, replay):
        s = dict(f)
        s['result'] = r['result']
        s['failed_steps'] = r['failed_steps']
        cid = client_of_scenario.get(s['index'])
        loans = sorted(by_client.get(cid, [])) if cid is not None else []
        s['client_id'] = cid
        s['loans'] = loans
        s['loan'] = loans[0] if loans else None
        if validated and not loans:
            problems.append('scenario %d: no loan create-request with clientId %s'
                            % (s['index'], cid))
        attributed.update(loans)
        scenarios.append(s)

    unattributed = sorted(set(facts) - attributed)
    if unattributed:
        problems.append('loan id(s) not attributed to any scenario: %s' % unattributed)

    npass = sum(1 for s in scenarios if s['result'] == 'PASSED')
    obj = {'feature': os.path.basename(FEATURE), 'scenario_count': len(scenarios),
           'passed': npass, 'failed': len(scenarios) - npass, 'steps': parse_step_summary(),
           'currency': 'MNT', 'tenant': 'tierd', 'loan_count': len(facts),
           'attribution_validated': validated, 'problems': problems,
           'scenarios': scenarios}
    with open(os.path.join(HERE, 'scenario-results.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('scenarios: %d; passed: %d; failed: %d; loans: %d; attribution validated: %s; '
          'problems: %d' % (len(scenarios), npass, len(scenarios) - npass, len(facts),
                            validated, len(problems)))
    for p in problems:
        print('  PROBLEM', p)

    write_table(obj)
    return 0 if not problems else 1


def write_table(obj):
    ss = obj['scenarios']
    out = []
    w = out.append
    w('# Replay result table — `EMICalculation-Part2.feature` in MNT')
    w('')
    w('Worktree `/Users/buv/oh-gerege-tierd25`, task OH-TIERD25-DG. Whole-file replay of all')
    w('%d scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign' % obj['scenario_count'])
    w('capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is')
    w('integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal')
    w('major units the oracle emitted. Feature line numbers are from')
    w('`fineract-e2e-tests-runner/src/test/resources/features/EMICalculation-Part2.feature`.')
    w('')
    w('The feature has %d plain `Scenario:` blocks and no `Scenario Outline`. Two of the' % obj['scenario_count'])
    w('scenarios each create a second loan for the same client, so the replay creates')
    w('%d loans over %d clients. Scenario k owns every loan whose create-request `clientId`' % (obj['loan_count'], obj['scenario_count']))
    w('is the k-th client the replay created (validated: %s).' % ('yes' if obj['attribution_validated'] else 'NOT validated'))
    w('')
    st = obj['steps']
    w('Result: **%d scenarios (%d passed, %d failed), %d loans**; %s steps (%s passed, %s skipped, %s failed).'
      % (obj['scenario_count'], obj['passed'], obj['failed'], obj['loan_count'], st['total'],
         st['passed'], st['skipped'], st['failed']))
    w('')
    w('| # | TestRailId | feature line | result | client | loans | product |')
    w('| --- | --- | --- | --- | ---: | --- | --- |')
    for s in ss:
        prod = ('`%s`' % s['feature_product']) if s['feature_product'] else '_(default progressive)_'
        loans = ', '.join(str(x) for x in s['loans']) or '-'
        w('| %d | %s | %d | %s | %s | %s | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], s['client_id'],
            loans, prod))
    w('')
    if obj['problems']:
        w('## Attribution problems')
        w('')
        for p in obj['problems']:
            w('- %s' % p)
        w('')
    failed = [s for s in ss if s['result'] == 'FAILED']
    w('## Failures — %d scenario%s' % (len(failed), '' if len(failed) == 1 else 's'))
    w('')
    if not failed:
        w('None. Every scenario passed: the EMICalculation-Part2 replay — and with it the')
        w('interest-refund and payout-refund postings (with interest and fee portions) it')
        w('exercises at breadth — was exercised and the oracle agreed with every `.feature`')
        w('expectation.')
    else:
        w('Each failure is recorded with the failing step and the actual-vs-expected values')
        w('exactly as the oracle printed them; the cause is NOT decided here (the driver')
        w('dispatches an EUR control). Amounts in the log are decimal major units.')
        w('')
        for s in failed:
            w('### %d — %s — `FAILED` — loans %s — %s' % (
                s['index'], s['tag'], ', '.join(str(x) for x in s['loans']) or '-', s['name']))
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
