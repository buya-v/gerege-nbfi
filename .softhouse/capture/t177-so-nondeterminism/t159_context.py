#!/usr/bin/env python3
"""Extract, from the COMMITTED T159 capture, the totals of the disputed cell and of the cells the
G-8 headline rests on. Quote by extraction (P-46) — nothing here is retyped.

Usage: t159_context.py <repo-root> <cell-id> [<cell-id> ...]
"""
import gzip
import json
import sys

repo = sys.argv[1]
want = sys.argv[2:]
with gzip.open(repo + '/.softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz', 'rt') as f:
    cap = json.load(f)
found = 0
for c in cap['captures']:
    if c['id'] in want:
        found += 1
        o = c.get('observed')
        print(c['id'])
        if not o:
            print('   NOT OBSERVED — errorStackTop[0]=%s' % (c.get('errorStackTop') or ['<none>'])[0])
            continue
        for k in ('loanTermInDays', 'totalDisbursedAmount', 'totalPrincipalAmount', 'totalInterestAmount',
                  'totalRepaymentAmount', 'totalOutstandingAmount'):
            print('   %-24s %s' % (k, o[k]))
        print('   periodCount              %d' % len(o['periods']))
if found == 0:
    print('ERROR: none of %r found — an extraction that inspected nothing is a FAILURE (P-35)' % want)
    sys.exit(1)
print('inspected %d of %d requested cells' % (found, len(want)))
