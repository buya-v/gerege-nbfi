#!/usr/bin/env python3
"""T100 — what domain was ACTUALLY swept, per capture. Needed because every conclusion in the G-8
write-up has to be scoped to the domain it was measured over, and neither T83's nor T84's write-up
states its sweep as a set.

NOTE ON `float`: used once, to sort ANNUAL RATE LABELS for display. No money value is converted."""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from classify_two_families import load, classify   # noqa: E402

for path in sys.argv[1:]:
    caps = [c for c in load(path)['captures'] if not c['id'].startswith('P-CAL')]
    rs = collections.defaultdict(set)
    ns, principals = set(), set()
    for c in caps:
        r = classify(c)
        rs[r['rate']].add(r['n'])
        ns.add(r['n'])
        principals.add(r['disbursed_minor'])
    print('== %s : %d non-calibration cells' % (path.split('/')[-1], len(caps)))
    for rate in sorted(rs, key=lambda x: float(x)):
        n = sorted(rs[rate])
        print('   rate %-7s n in %s' % (rate, n if len(n) <= 12 else '[%d..%d] (%d values)'
                                        % (n[0], n[-1], len(n))))
    print('   principals swept (minor): %d..%d' % (min(principals), max(principals)))
