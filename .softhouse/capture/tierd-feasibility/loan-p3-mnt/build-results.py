#!/usr/bin/env python3
"""OH-TIERD27-DL: parse the Loan-Part3 MNT replay into per-scenario results,
validate the scenario->loan map, and write `scenario-results.json` and
`replay-result-table.md`.

Copy of OH-TIERD22-DB `merchant-refund-mnt/build-results.py`, then of the
chargeoff-p4/p2 mapping rule; only the feature, the log and the prose are
task-specific.  LoanPart3.feature has 50 plain `Scenario:` blocks and no
`Scenario Outline`, so Cucumber executes 50 scenarios.

Loan attribution differs from the earlier captures and is derived, not assumed:
every scenario creates exactly one client at the top, in feature order, so
scenario k owns client id k.  A loan is attributed to the scenario whose
`clientId` it was created for (each loan's create-request `clientId`), never by
loan id order.  This matters here because scenario 34 (`... UC7 ... results an
ERROR`) attempts a loan and gets a 403, creating NO loan, so loan ids no longer
equal scenario positions from that point on.  The map is validated, not assumed:
every loan must be attributed to exactly one scenario, and a scenario that
creates a loan must own exactly one loan.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/Loan-Part3.feature')
LOG = os.path.join(HERE, 'replay-loan-p3-mnt.log')
STAGE = os.path.join(HERE, 'stage')
ANSI = re.compile(r'\x1b\[[0-9;]*m')
HEAD_RE = re.compile(r'^\s*Scenario(?: Outline)?:\s*(.*?)\s*#\s*\S+\.feature:(\d+)\s*$')
TAG_RE = re.compile(r'@TestRailId:(\S+)')
AT_RE = re.compile(r'\.feature:(\d+)\)')
DETAIL_RE = re.compile(r'(?i)(actual|expected|wrong value)')
LOAN_CREATE_RE = re.compile(r'creates a fully customized loan')


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
    """Ordered scenarios with tag, name, feature line, explicit product and
    whether the scenario contains a loan-create step."""
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
            body = '\n'.join(lines[i:stop])
            out.append({'index': len(out) + 1, 'tag': tag, 'name': h.group(1).strip(),
                        'feature_line': i + 1,
                        'creates_loan': bool(LOAN_CREATE_RE.search(body)),
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
                                        'creates_loan': True,
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
    """loan id -> clientId from the create-request (empty when stage/ is absent)."""
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


def main():
    feature = parse_feature()
    replay = parse_replay()
    facts = loan_facts()
    validated = bool(facts)

    assert len(feature) == len(replay), (len(feature), len(replay))
    for a, b in zip(feature, replay):
        assert a['feature_line'] == b['feature_line'], (a, b)

    # scenario k creates client k; attribute each loan by its create clientId.
    client_to_loans = {}
    for lid, f in facts.items():
        cid = f.get('clientId')
        if cid is not None:
            client_to_loans.setdefault(cid, []).append(lid)
    attributed = {lid for lids in client_to_loans.values() for lid in lids}

    scenarios = []
    problems = []
    for f, r in zip(feature, replay):
        s = dict(f)
        s['result'] = r['result']
        s['failed_steps'] = r['failed_steps']
        idx = s['index']
        lids = sorted(client_to_loans.get(idx, []))
        s['loan'] = lids[0] if len(lids) == 1 else None
        s['loan_client_id'] = idx if lids else None
        if validated:
            if s['creates_loan'] and len(lids) != 1:
                problems.append('scenario %d creates a loan but owns %d (client %d)'
                                % (idx, len(lids), idx))
            if not s['creates_loan'] and lids:
                problems.append('scenario %d creates NO loan but owns %s (client %d)'
                                % (idx, lids, idx))
        scenarios.append(s)

    unattributed = sorted(lid for lid in facts if lid not in attributed)
    if unattributed:
        problems.append('loan(s) attributed to no scenario: %s' % unattributed)

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
    w('# Replay result table — `Loan-Part3.feature` in MNT')
    w('')
    w('Worktree `/Users/buv/oh-gerege-tierd27`, task OH-TIERD27-DL. Whole-file replay of all')
    w('%d scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign' % obj['scenario_count'])
    w('capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is')
    w('integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal')
    w('major units the oracle emitted. Feature line numbers are from')
    w('`fineract-e2e-tests-runner/src/test/resources/features/Loan-Part3.feature`.')
    w('')
    w('The feature has 50 plain `Scenario:` blocks and no `Scenario Outline`, so the 50')
    w('Gherkin scenarios give the %d rows below. Forty-nine create a loan; scenario 34' % obj['scenario_count'])
    w('(`... UC7 ... results an ERROR`) attempts a loan and gets a 403, so it creates none.')
    w('Loan ids are attributed by client id, not by row position: scenario k owns client k')
    w('and a loan is attributed to the scenario whose `clientId` it was created for.')
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
        loan = s['loan'] if s['loan'] is not None else '_(none)_'
        w('| %d | %s | %d | %s | %s | %s |' % (
            s['index'], s['tag'], s['feature_line'], s['result'], loan, prod))
    w('')
    failed = [s for s in ss if s['result'] == 'FAILED']
    w('## Failures — %d scenario%s' % (len(failed), '' if len(failed) == 1 else 's'))
    w('')
    if not failed:
        w('None. Every scenario passed: the Part-3 replay — and with it the REFUND transaction')
        w('on an active loan (`createJournalEntriesForRefundForActiveLoan`), the merchant-issued')
        w('refund, payout refund, credit balance refund and interest refund families, plus the')
        w('advanced-payment-allocation and interest-recalculation arms — was exercised and the')
        w('oracle agreed with every `.feature` expectation.')
    else:
        w('Each failure is recorded with the failing step and the actual-vs-expected values')
        w('exactly as the oracle printed them; the cause is NOT decided here (the driver')
        w('dispatches an EUR control). Amounts in the log are decimal major units.')
        w('')
        for s in failed:
            w('### %d — %s — `FAILED` — loan %s — %s' % (
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
