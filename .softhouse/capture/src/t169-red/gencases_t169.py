#!/usr/bin/env python3
"""T169 — the case list for the pre-fix/post-fix pair. Five cells, the same five for both runs.

Principals are INTEGER MINOR UNITS and are emitted as `new BigDecimal(<int>).movePointLeft(2)`, so
no decimal literal and no float appears anywhere between here and the JVM (P-25, and the project
non-negotiable on money).

The three sweep cells are T159's, not invented here:

  T169-CTRL-R600p0-N200-B10001   control at the SAME principal and a term nobody has seen throw.
  T169-RED-R600p0-N2000-B10001   T159's detonation. The reference oracle threw
                                 java.lang.StackOverflowError on this shape
                                 [VERIFIED: t159-review-t117/out/capture-t159-raw.json.gz ->
                                 T159-R600p0-N2000-B10001].
  T169-TWIN-R600p0-N3000-B10001  T159's NON-MONOTONE twin: a LONGER term at the same principal that
                                 the oracle evaluates fine [VERIFIED: same capture ->
                                 T159-R600p0-N3000-B10001, totalInterestAmount 846.70]. It is in the
                                 list so that the post-fix run has to distinguish threw from
                                 observed on two cells that differ only in n.

Tenant ids are disjoint from T159's, so nothing here can be a replay of a cached T159 anything.

Usage: gencases_t169.py <cases-out.java> <ids-out.json>
"""
import json
import sys

CASES = [
    # (id, principal in MINOR UNITS, numberOfRepayments, annual rate string, purpose)
    ('T169-CTRL-R600p0-N200-B10001', 10001, 200, '600.0',
     'T169 rig probe (CTRL) - same principal as the detonation at a term the oracle evaluates; this cell must be OBSERVED in both runs'),
    ('T169-RED-R600p0-N2000-B10001', 10001, 2000, '600.0',
     'T169 rig probe (RED) - T159 observed java.lang.StackOverflowError from the reference oracle on this exact shape; the pre-fix handler cannot see it'),
    ('T169-TWIN-R600p0-N3000-B10001', 10001, 3000, '600.0',
     'T169 rig probe (TWIN) - a LONGER term at the same principal that T159 observed cleanly; the throw is not monotone in n'),
]

TEMPLATE = ('        cases.add(prodDates("%s", "%s", LocalDate.of(2024, 1, 1), '
            'LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), %d, '
            'new BigDecimal("%s"), "%s"));')


def main():
    cases_out, ids_out = sys.argv[1], sys.argv[2]
    lines = []
    ids = []
    for cid, minor, n, rate, purpose in CASES:
        assert isinstance(minor, int) and isinstance(n, int), 'money and terms are integers here'
        tenant = cid.lower().replace('-', '_')
        lines.append(TEMPLATE % (cid, purpose, minor, n, rate, tenant))
        ids.append(cid)
    open(cases_out, 'w').write('\n'.join(lines) + '\n')
    # The two rig calibrations are emitted by the harness itself, ahead of the sweep, and the
    # postcheck prepends them to the asked list -- exactly as T117's and T159's postchecks do.
    open(ids_out, 'w').write(json.dumps(ids, indent=1) + '\n')
    print('wrote %d sweep cases and %d ids' % (len(lines), len(ids)))


if __name__ == '__main__':
    main()
