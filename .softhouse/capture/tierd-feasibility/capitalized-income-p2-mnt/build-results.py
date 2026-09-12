#!/usr/bin/env python3
"""OH-TIERD29-DO: parse the LoanCapitalizedIncome-Part2 MNT replay into per-scenario
results, validate the scenario->loan map, and write `scenario-results.json` and
`replay-result-table.md`.

Copy of OH-TIERD26-DJ `chargeoff-p2-mnt/build-results.py`; the parsing and the
scenario->loan attribution rule are the same, extended for SKIPPED scenarios.
LoanCapitalizedIncome-Part2.feature has 35 plain `Scenario:` blocks and no `Scenario
Outline`, of which 1 is tagged `@Skip` (C3744).  The e2e runner's `TestRunner` carries
`@ExcludeTags("Skip")` and the Gradle cucumber task excludes `@Skip` by default, so
Cucumber executes only 34 of the 35 scenarios.  The skipped scenario contains a
`creates a client` step but no loan-create step, so it owns no loan; the result
table keeps all 35 rows and marks it as `SKIPPED`.

Loan attribution: every EXECUTED scenario creates exactly one client and one loan at
the top, in feature order, so the r-th executed scenario owns loan id r (clientId r),
r = 1..34.  The map is validated, not assumed: the extracted loan ids must be exactly
1..N for the N executed scenarios, and each loan's create-request `clientId` must
equal its own id (validation runs once `stage/` exists; before extraction the map is
reported as unvalidated).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/LoanCapitalizedIncome-Part2.feature')
LOG = os.path.join(HERE, 'replay-capitalized-income-p2-mnt.log')
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
    skip = False
    i = 0
    while i < n:
        s = lines[i].strip()
        m = TAG_RE.search(s)
        if s.startswith('@'):
            # Tag lines carry @Skip alongside @TestRailId; the runner excludes @Skip.
            tag = m.group(1) if m else tag
            skip = '@Skip' in s
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
                        'feature_line': i + 1, 'skip': skip,
                        'feature_product': _scan_product(lines, i, stop)})
            tag = None
            skip = False
        elif ho:
            outline = ho.group(1).strip()
            i += 1
            while i < n:
                t = lines[i].strip()
                tm = TAG_RE.search(t)
                if t.startswith('@'):
                    tag = tm.group(1) if tm else tag
                    skip = '@Skip' in t
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
                                        'name': name, 'feature_line': j + 1, 'skip': skip,
                                        'feature_product': row.get('loanProduct')})
                        j += 1
                    i = j
                    tag = None
                    skip = False
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

    executed = [f for f in feature if not f['skip']]
    skipped = [f for f in feature if f['skip']]
    assert len(executed) == len(replay), (len(executed), len(replay))
    for a, b in zip(executed, replay):
        assert a['feature_line'] == b['feature_line'], (a, b)

    validated = bool(facts)
    problems = []
    if validated:
        expected_ids = list(range(1, len(executed) + 1))
        if sorted(facts) != expected_ids:
            problems.append('extracted loan ids %s != expected %s'
                            % (sorted(facts), expected_ids))

    by_index = {}
    for rank, (f, r) in enumerate(zip(executed, replay), 1):
        by_index[f['index']] = (rank, r)

    scenarios = []
    for f in feature:
        s = {k: f[k] for k in ('index', 'tag', 'name', 'feature_line', 'skip',
                               'feature_product')}
        if f['skip']:
            s.update({'result': 'SKIPPED', 'failed_steps': [], 'loan': None,
                      'executed_rank': None, 'loan_client_id': None})
            scenarios.append(s)
            continue
        rank, r = by_index[f['index']]
        s['result'] = r['result']
        s['failed_steps'] = r['failed_steps']
        s['loan'] = rank
        s['executed_rank'] = rank
        fid = facts.get(rank, {})
        s['loan_client_id'] = fid.get('clientId')
        if validated and fid.get('clientId') != rank:
            problems.append('executed rank %d: loan %d clientId=%s (expected %d)'
                            % (rank, rank, fid.get('clientId'), rank))
        scenarios.append(s)

    npass = sum(1 for s in scenarios if s['result'] == 'PASSED')
    nfail = sum(1 for s in scenarios if s['result'] == 'FAILED')
    nskip = sum(1 for s in scenarios if s['result'] == 'SKIPPED')
    obj = {'feature': os.path.basename(FEATURE), 'scenario_count': len(scenarios),
           'executed': len(executed), 'skipped': nskip,
           'passed': npass, 'failed': nfail, 'steps': parse_step_summary(),
           'currency': 'MNT', 'tenant': 'tierd',
           'skip_reason': ('@Skip scenarios are excluded by TestRunner '
                           '@ExcludeTags("Skip") and the Gradle cucumber tag filter'),
           'attribution_validated': validated, 'scenarios': scenarios}
    with open(os.path.join(HERE, 'scenario-results.json'), 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('scenarios: %d (executed %d, skipped %d); passed: %d; failed: %d; '
          'attribution validated: %s; problems: %d'
          % (len(scenarios), len(executed), nskip, npass, nfail, validated,
             len(problems)))
    for p in problems:
        print('  MISMATCH', p)

    write_table(obj)
    return 0 if not problems else 1


def write_table(obj):
    ss = obj['scenarios']
    out = []
    w = out.append
    w('# Replay result table — `LoanCapitalizedIncome-Part2.feature` in MNT')
    w('')
    w('Worktree `/Users/buv/oh-gerege-tierd29`, task OH-TIERD29-DO. Whole-file replay of the')
    w('%d-scenario feature against the throwaway reference oracle (tenant `tierd`), with the' % obj['scenario_count'])
    w('Feign capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below')
    w('is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal')
    w('major units the oracle emitted. Feature line numbers are from')
    w('`fineract-e2e-tests-runner/src/test/resources/features/LoanCapitalizedIncome-Part2.feature`.')
    w('')
    w('The feature has 35 plain `Scenario:` blocks and no `Scenario Outline`, so there are 35')
    w('rows below. One scenario (C3744) is tagged `@Skip`; the e2e runner\'s `TestRunner` carries')
    w('`@ExcludeTags("Skip")` and the Gradle cucumber tag filter excludes it, so Cucumber')
    w('executes %d of the 35 and only those give loans. The skipped scenario contains a'
      % obj['executed'])
    w('`creates a client` step but no loan-create step, so it owns no loan and is marked')
    w('`SKIPPED` below. The capitalized-income create, capitalized-income adjustment,')
    w('amortization and amortization-adjustment arms, the charge-off and not-charged-off arms,')
    w('and the capitalized-income charge-off behaviour are spread across the executed scenarios.')
    w('')
    st = obj['steps']
    w('Result: **%d scenarios (%d executed: %d passed, %d failed; %d skipped by `@Skip`)**; '
      '%s steps (%s passed, %s skipped, %s failed).'
      % (obj['scenario_count'], obj['executed'], obj['passed'], obj['failed'],
         obj['skipped'], st['total'], st['passed'], st['skipped'], st['failed']))
    w('')
    w('| # | TestRailId | feature line | result | loan | product |')
    w('| --- | --- | --- | --- | --- | --- |')
    for s in ss:
        prod = ('`%s`' % s['feature_product']) if s['feature_product'] else '_(default progressive)_'
        loan = s['loan'] if s['loan'] is not None else '—'
        w('| %d | %s | %d | %s | %s | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], loan, prod))
    w('')
    failed = [s for s in ss if s['result'] == 'FAILED']
    w('## Failures — %d scenario%s' % (len(failed), '' if len(failed) == 1 else 's'))
    w('')
    if not failed:
        w('None. Every executed scenario passed (the %d `@Skip` scenario was not run), so'
          % obj['skipped'])
        w('the capitalized-income replay — with it the capitalized-income create, the')
        w('capitalized-income adjustment, the amortization and amortization-adjustment postings,')
        w('the charge-off and not-charged-off arms and the capitalized-income charge-off')
        w('behaviour — was exercised and the oracle agreed with every `.feature` expectation.')
        w('A failure, had there been one, would be recorded (not diagnosed) with the')
        w('actual-vs-expected values the oracle printed.')
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
