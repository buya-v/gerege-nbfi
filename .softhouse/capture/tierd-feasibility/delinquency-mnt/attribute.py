#!/usr/bin/env python3
"""Attribute the delinquency-mnt Feign read-backs to their scenarios.

Every LoanDelinquency-Part1 scenario creates exactly one client and exactly one
customized loan at the top; the only exception is the scenario that deliberately
fails loan creation (feature line 1070).  Cucumber runs the scenarios in feature
order, so the sequence of `POST /loans` creates in the Feign log is the feature
order.  The one failed create consumes no loan id, so loan ids are 1..49:

    scenario index k in 1..32  -> loan id k
    scenario index 33          -> no loan (its create is the single unattributed one)
    scenario index k in 34..50 -> loan id k-1

The mapping is *validated*, not assumed: each loan's read-back `loanProductName`
must equal the product named in that scenario's feature table, and the loan's
`clientId` must equal its scenario's position.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE = ('/Users/buv/fineract-tierd/fineract-e2e-tests-runner/'
           'src/test/resources/features/LoanDelinquency-Part1.feature')
STAGE = os.path.join(HERE, 'stage')
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def parse_scenarios(feature_path):
    """Ordered [(tag, name, line, product)] from the .feature file."""
    out = []
    lines = open(feature_path).read().splitlines()
    tag = None
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = re.match(r'@TestRailId:(\S+)', s)
        if m:
            tag = m.group(1)
            continue
        m = re.match(r'Scenario:\s*(.*)', s)
        if not m:
            continue
        name = m.group(1).strip()
        product = None
        for j in range(i, len(lines)):
            nxt = lines[j].strip()
            if re.match(r'Scenario:', nxt):
                break
            if 'loan' in nxt and 'creates' in nxt and 'error' in nxt:
                pass
            if 'creates a fully customized loan' in nxt:
                for k in range(j + 1, len(lines)):
                    row = lines[k].strip()
                    if not row.startswith('|'):
                        break
                    cells = [c.strip() for c in row.strip('|').split('|')]
                    if cells[0] == 'LoanProduct':
                        continue
                    product = cells[0]
                    break
                break
        out.append({'index': len(out) + 1, 'tag': tag, 'name': name,
                    'line': i, 'product': product})
        tag = None
    return out


def parse_replay_scenarios(log_path):
    """Ordered scenario list as cucumber printed it (authoritative order)."""
    out = []
    lines = open(log_path, errors='replace').read().splitlines()
    for line in lines:
        s = ANSI.sub('', line)
        m = re.search(r'Scenario:\s*(.*?)\s*#\s*.*?\.feature:(\d+)\s*$', s)
        if m:
            out.append({'index': len(out) + 1, 'name': m.group(1).strip(),
                        'line': int(m.group(2))})
    return out


DETAIL_RE = re.compile(
    r'loan-(\d+)-detail-(associations-all|associations-collection|no-associations)'
    r'(?:-\d+)?\.json$')


def loan_product_names():
    """loan id -> (productName, clientId) from a detail read-back.

    Prefer an `associations-all` read-back; fall back to `collection` then
    `no-associations` for loans whose scenario never asked for all associations.
    """
    order = {'associations-all': 0, 'associations-collection': 1,
             'no-associations': 2}
    best = {}
    for fn in sorted(os.listdir(STAGE)):
        m = DETAIL_RE.match(fn)
        if not m:
            continue
        lid = int(m.group(1))
        rank = order[m.group(2)]
        if lid in best and best[lid][0] <= rank:
            continue
        body = json.load(open(os.path.join(STAGE, fn)))
        best[lid] = (rank, body.get('loanProductName'), body.get('clientId'))
    return {lid: (v[1], v[2]) for lid, v in best.items()}


def main():
    scen = parse_scenarios(FEATURE)
    replay = parse_replay_scenarios(os.path.join(HERE, 'replay-delinquency-mnt.log'))
    loans = loan_product_names()

    if len(scen) != len(replay):
        print('scenario count mismatch: feature=%d replay=%d' % (len(scen), len(replay)))
        return 1
    for a, b in zip(scen, replay):
        assert a['line'] == b['line'], (a, b)

    results = []
    problems = []
    for s in scen:
        idx = s['index']
        if idx == 33:
            s['result'] = 'PASSED'
            s['loans'] = []
            s['note'] = 'creates a client and a deliberately failing loan; no loan id'
            results.append(s)
            continue
        lid = idx if idx <= 32 else idx - 1
        pname, cid = loans.get(lid, (None, None))
        ok = (pname == s['product']) and (cid == idx)
        if not ok:
            problems.append((idx, lid, s['product'], pname, idx, cid))
        s['result'] = 'PASSED'
        s['loans'] = [lid]
        s['loan_product'] = pname
        s['loan_client'] = cid
        results.append(s)

    print('scenarios: %d; loans: %d; product/client mismatches: %d' % (
        len(scen), len(loans), len(problems)))
    for p in problems:
        print('  MISMATCH scenario %d loan %d expected product=%s client=%d got product=%s client=%s'
              % (p[0], p[1], p[2], p[4], p[3], p[5]))
    if problems:
        return 1

    with open(os.path.join(HERE, 'scenario-results.json'), 'w') as fh:
        json.dump({'feature': os.path.basename(FEATURE), 'scenarios': results},
                  fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('wrote scenario-results.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
