#!/usr/bin/env python3
"""T100 — independent two-family classifier over ANY of the committed G-8 raw captures.

Written from scratch for T100. It does NOT import T83's classify-boundary.py nor T84's
classify.py; it re-derives every number from the raw `captures` array so that the family
split in the G-8 write-up rests on a third reading of the same oracle output.

Money is handled as INTEGER MINOR UNITS throughout: decimal strings are split on '.' and
padded to the currency's decimal places, never parsed as float.

Classification, per case:
  sum_principal_minor  = sum of the REPAYMENT rows' `principal`
  disbursed_minor      = the DISBURSEMENT row's `principal`
  final_balance_minor  = the LAST REPAYMENT row's `balance`
  family A  : final_balance_minor != 0 AND sum_principal_minor == disbursed_minor
              (stale derived column: the principal column still repays the loan)
  family B  : sum_principal_minor != disbursed_minor
              (genuine non-amortization: the principal column does not repay the loan)
  clean     : final_balance_minor == 0 AND sum_principal_minor == disbursed_minor
"""
import json, gzip, sys, collections


def minor(s, dp):
    """Decimal string -> integer minor units. No float anywhere."""
    if s is None:
        return None
    s = str(s).strip()
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
    else:
        whole, frac = s, ''
    if len(frac) > dp:
        # never silently round money
        if frac[dp:].strip('0'):
            raise ValueError('more precision than dp in %r' % s)
        frac = frac[:dp]
    frac = (frac + '0' * dp)[:dp]
    v = int(whole or '0') * (10 ** dp) + int(frac or '0')
    return -v if neg else v


def load(path):
    return json.load(gzip.open(path)) if path.endswith('.gz') else json.load(open(path))


def classify(cap):
    inp, obs = cap['inputs'], cap['observed']
    dp = int(inp['currencyDecimalPlaces'])
    disb = None
    sum_p = 0
    final_bal = None
    n_rows = 0
    for p in obs['periods']:
        if p['type'] == 'DISBURSEMENT':
            disb = minor(p['principal'], dp)
        else:
            n_rows += 1
            sum_p += minor(p['principal'], dp)
            final_bal = minor(p['balance'], dp)
    sums = (sum_p == disb)
    fam = 'clean' if (final_bal == 0 and sums) else ('A' if sums else 'B')
    return {
        'id': cap['id'],
        'purpose_head': cap.get('purpose', '')[:40],
        'rate': inp['annualNominalInterestRate'],
        'n': inp['numberOfRepayments'],
        'dp': dp,
        'disbursed_minor': disb,
        'sum_principal_minor': sum_p,
        'final_balance_minor': final_bal,
        'total_principal_amount_minor': minor(obs.get('totalPrincipalAmount'), dp),
        'total_outstanding_amount_minor': minor(obs.get('totalOutstandingAmount'), dp),
        'rows': n_rows,
        'family': fam,
    }


def main():
    rows = []
    for path in sys.argv[1:]:
        d = load(path)
        for cap in d['captures']:
            r = classify(cap)
            r['source'] = path.split('/')[-1]
            rows.append(r)
    tally = collections.Counter(r['family'] for r in rows)
    out = {
        'sources': sys.argv[1:],
        'cases': len(rows),
        'tally': dict(tally),
        'familyB': [r for r in rows if r['family'] == 'B'],
        'familyA_count': tally['A'],
        'all': rows,
    }
    json.dump(out, sys.stdout, indent=1, sort_keys=False)
    print()


if __name__ == '__main__':
    main()
