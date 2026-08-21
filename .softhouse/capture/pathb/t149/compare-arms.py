#!/usr/bin/env python3
"""T149 — the two OBSERVED arms of the exact tie, compared cell by cell.

There is no model in this comparison. Both arms are observations of the reference
oracle taken from ONE running JVM, differing in exactly one input: the tenant's
`RoundingMode` ordinal (gerege = 4 HALF_UP, default = 6 HALF_EVEN). T136 established
that the two loan-product rows are twins in 89 columns with only `id` differing; this
script re-establishes that independently before it compares any money, because without
it the divergence has a second possible cause.

    python3 compare-arms.py
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HU = os.path.join(HERE, 'out', 'gerege', 'canary-halfcent-raw.json')          # gerege, product 11
HE = os.path.join(HERE, 'out', 'default-HALF-EVEN-ARM', 'pmode2-default-raw.json')  # default, product 10
DB = 'fineract-db-1'

MONEY = ['principalOriginalDue', 'principalDue', 'principalLoanBalanceOutstanding',
         'interestOriginalDue', 'interestDue', 'totalOriginalDueForPeriod']
TOTALS = ['totalPrincipalDisbursed', 'totalInterestCharged', 'totalRepaymentExpected']


def minor(text, digits=2):
    t = str(text)
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    whole, _, frac = t.partition('.')
    if len(frac) > digits:
        if frac[digits:].strip('0'):
            raise ValueError(text)
        frac = frac[:digits]
    frac = frac.ljust(digits, '0')
    v = ((whole or '0') + frac).lstrip('0') or '0'
    return -int(v) if neg else int(v)


def q(db, sql):
    p = subprocess.run(['docker', 'exec', DB, 'psql', '-U', 'root', '-d', db, '-At', '-c', sql],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit('psql failed: %s' % p.stderr.strip())
    return p.stdout.strip()


def product_twin_check():
    a = json.loads(q('fineract_default', "select to_jsonb(t) from m_product_loan t where id=10;"),
                   parse_float=str)
    b = json.loads(q('fineract_gerege', "select to_jsonb(t) from m_product_loan t where id=11;"),
                   parse_float=str)
    keys = sorted(set(a) | set(b))
    differing = [k for k in keys if a.get(k) != b.get(k)]
    print('PRODUCT TWIN CHECK — m_product_loan id 10 @ fineract_default vs id 11 @ fineract_gerege')
    print('  columns compared: %d   differing: %d   -> %s'
          % (len(keys), len(differing), differing))
    for k in differing:
        print('     %s: default=%r gerege=%r' % (k, a.get(k), b.get(k)))
    ok = differing == ['id']
    print('  VERDICT: %s' % ('TWINS — the rounding mode is the only remaining cause' if ok
                             else 'NOT TWINS — a second cause is possible; the margin below is NOT attributable'))
    return ok


def main():
    ok = product_twin_check()
    hu = json.load(open(HU), parse_float=str)
    he = json.load(open(HE), parse_float=str)
    print()
    print('ROUNDING-MODE ARMS, same JVM, same request shape, same 89-column product')
    print('  HALF_UP  arm: tenant gerege  (RoundingMode ordinal 4)  %s' % os.path.relpath(HU, HERE))
    print('  HALF_EVEN arm: tenant default (RoundingMode ordinal 6)  %s' % os.path.relpath(HE, HERE))
    print()
    ndiff = 0
    widest = (0, '')
    for k in TOTALS:
        d = minor(hu[k]) - minor(he[k])
        mark = '' if d == 0 else '   <-- DIVERGES'
        if d:
            ndiff += 1
            if abs(d) > widest[0]:
                widest = (abs(d), '%s: HALF_UP %s vs HALF_EVEN %s' % (k, hu[k], he[k]))
        print('  %-28s HALF_UP %14s   HALF_EVEN %14s   delta %+d%s' % (k, hu[k], he[k], d, mark))
    print()
    for i, (a, b) in enumerate(zip(hu['periods'], he['periods'])):
        if 'period' not in a:
            continue
        row = []
        for k in MONEY:
            d = minor(a[k]) - minor(b[k])
            if d:
                ndiff += 1
                if abs(d) > widest[0]:
                    widest = (abs(d), 'period[%d].%s: HALF_UP %s vs HALF_EVEN %s' % (i, k, a[k], b[k]))
                row.append('%s %s/%s (%+d)' % (k, a[k], b[k], d))
        print('  period %-3d %s' % (a['period'], '; '.join(row) if row else 'identical'))
    print()
    print('  money cells diverging: %d' % ndiff)
    print('  widest single-cell disagreement: %d minor unit(s) — %s' % widest)
    print()
    print('  period-1 interest: HALF_UP %s   HALF_EVEN %s   (exact tie 1162502.50 x 0.018 = 20925.045)'
          % (hu['periods'][1]['interestOriginalDue'], he['periods'][1]['interestOriginalDue']))
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
