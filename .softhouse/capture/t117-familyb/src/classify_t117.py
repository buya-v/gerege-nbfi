#!/usr/bin/env python3
"""T117 — classify the family-B extent probe and compare it to the REGISTERED prediction.

MONEY DISCIPLINE (P-25). Every money quantity in this file is an INTEGER COUNT OF MINOR UNITS.
Decimal strings are split on '.' and padded to the currency's decimal places; nothing is ever
parsed as a binary float. `json.load` is called with `parse_float=Decimal` so that even a numeric
money literal — there are none in this capture, every money value is emitted by
BigDecimal.toPlainString() as a JSON STRING — could not silently become a double. The one
conclusion this script exists to support ("can the failing principal exceed one minor unit?") is
decided by comparing INTEGERS.

SKIP DISCIPLINE (P-40). Nothing is silently dropped. The script reports, per leg:
    asked / observed / errored / missing
and it exits non-zero if any case in the registered prediction has no observation, naming them.
There is no bare `except: continue` anywhere in this file.

FAMILY DISCRIMINATORS, taken verbatim from .softhouse/gates.md § "Read this first":
    family A : final REPAYMENT balance != 0  AND  sum(REPAYMENT principal) == disbursed
    family B : sum(REPAYMENT principal) != disbursed
    clean    : final REPAYMENT balance == 0  AND  sum(REPAYMENT principal) == disbursed
"""
import collections
import gzip
import json
import sys
from decimal import Decimal


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
        if frac[dp:].strip('0'):
            raise ValueError('more precision than dp in %r' % s)
        frac = frac[:dp]
    frac = (frac + '0' * dp)[:dp]
    v = int(whole or '0') * (10 ** dp) + int(frac or '0')
    return -v if neg else v


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def classify(cap):
    inp, obs = cap['inputs'], cap['observed']
    dp = int(inp['currencyDecimalPlaces'])
    disb = None
    sum_p = 0
    sum_i = 0
    final_bal = None
    final_interest = None
    n_rows = 0
    nonzero_principal_rows = 0
    for p in obs['periods']:
        if p['type'] == 'DISBURSEMENT':
            disb = minor(p['principal'], dp)
        else:
            n_rows += 1
            pm = minor(p['principal'], dp)
            sum_p += pm
            if pm != 0:
                nonzero_principal_rows += 1
            sum_i += minor(p['interest'], dp)
            final_bal = minor(p['balance'], dp)
            final_interest = minor(p['interest'], dp)
    sums = (sum_p == disb)
    fam = 'clean' if (final_bal == 0 and sums) else ('A' if sums else 'B')
    return {
        'id': cap['id'],
        'rate': inp['annualNominalInterestRate'],
        'n': inp['numberOfRepayments'],
        'dp': dp,
        'disbursed_minor': disb,
        'sum_principal_minor': sum_p,
        'sum_interest_minor': sum_i,
        'final_balance_minor': final_bal,
        'final_row_interest_minor': final_interest,
        'nonzero_principal_rows': nonzero_principal_rows,
        'total_principal_amount_minor': minor(obs.get('totalPrincipalAmount'), dp),
        'total_interest_amount_minor': minor(obs.get('totalInterestAmount'), dp),
        'total_repayment_amount_minor': minor(obs.get('totalRepaymentAmount'), dp),
        'total_outstanding_amount_raw': obs.get('totalOutstandingAmount'),
        'repayment_rows': n_rows,
        'family': fam,
        # the failing principal, in integer minor units: 0 when the cell is clean
        'failing_principal_minor': (0 if fam == 'clean' else disb),
    }


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: classify_t117.py <capture.json[.gz]> <prediction.json>")
    cappath, predpath = sys.argv[1], sys.argv[2]
    doc = load(cappath)
    pred = load(predpath)['cases']

    rows = []
    errored = []
    for cap in doc['captures']:
        if cap.get('observed') is None:
            errored.append({'id': cap['id'], 'error': cap.get('error', '(no error key emitted)')})
            continue
        rows.append(classify(cap))

    by_id = {r['id']: r for r in rows}
    missing = sorted(i for i in pred if i not in by_id)

    # ---- prediction comparison, per case ---------------------------------------------------
    agree, disagree = [], []
    for pid, p in sorted(pred.items()):
        r = by_id.get(pid)
        if r is None:
            continue                                   # counted in `missing`, never silently dropped
        predicted_family = p['predictedFamily']         # 'B' or None
        observed_family = r['family']
        ok_p2 = (observed_family == 'B') == (predicted_family == 'B')
        ok_full = (observed_family == (predicted_family if predicted_family else 'clean'))
        rec = {'id': pid, 'leg': p['leg'], 'n': p['n'], 'B_minor': p['B_minor'],
               'predictedFamily': predicted_family, 'observedFamily': observed_family,
               'familyB_call_correct': ok_p2, 'full_call_correct': ok_full,
               'confidence': p['confidence']}
        (agree if ok_full else disagree).append(rec)

    # ---- leg accounting: asked / observed / errored / missing (P-40) ------------------------
    legs = collections.defaultdict(lambda: {'asked': 0, 'observed': 0, 'missing': 0, 'errored': 0,
                                            'families': collections.Counter()})
    err_ids = {e['id'] for e in errored}
    for pid, p in pred.items():
        L = legs[p['leg']]
        L['asked'] += 1
        if pid in by_id:
            L['observed'] += 1
            L['families'][by_id[pid]['family']] += 1
        elif pid in err_ids:
            L['errored'] += 1
        else:
            L['missing'] += 1
    legs = {k: {**v, 'families': dict(v['families'])} for k, v in sorted(legs.items())}

    # ---- THE MONEY CLAIM, decided in integers -----------------------------------------------
    famB = [r for r in rows if r['family'] == 'B']
    famA = [r for r in rows if r['family'] == 'A']
    clean = [r for r in rows if r['family'] == 'clean']
    largest_failing_minor = max((r['failing_principal_minor'] for r in rows), default=0)
    largest_famB_minor = max((r['disbursed_minor'] for r in famB), default=None)

    # ---- (i) half-line or island: the n-extent of family B at B = 1 -------------------------
    b1 = sorted((r['n'], r['family']) for r in rows if r['disbursed_minor'] == 1)
    b1_famB_n = sorted(n for n, f in b1 if f == 'B')
    b1_not_famB_n = sorted(n for n, f in b1 if f != 'B')
    # contiguity, over the two blocks that were asked contiguously
    def contiguous_run(lo, hi):
        asked = sorted(n for n, _ in b1 if lo <= n <= hi)
        got = sorted(n for n in b1_famB_n if lo <= n <= hi)
        return {'range': [lo, hi], 'asked': len(asked), 'familyB': len(got),
                'all_asked_present': asked == list(range(lo, hi + 1)),
                'all_familyB': asked == got}

    out = {
        'source': cappath,
        'prediction': predpath,
        'caseCounts': {
            'capturesInFile': len(doc['captures']),
            'registeredInPrediction': len(pred),
            'observed': len(rows),
            'errored': len(errored),
            'missing': len(missing),
        },
        'erroredCases': errored,
        'missingCases': missing,
        'legAccounting': legs,
        'tally': dict(collections.Counter(r['family'] for r in rows)),
        'moneyClaim': {
            'units': 'INTEGER MINOR UNITS — decided in integers, no float on this path',
            'largestFailingPrincipal_minor': largest_failing_minor,
            'largestFamilyBPrincipal_minor': largest_famB_minor,
            'familyB_distinct_principals_minor': sorted({r['disbursed_minor'] for r in famB}),
            'familyA_count': len(famA),
            'clean_count': len(clean),
            'familyB_count': len(famB),
        },
        'extentInN_atB1': {
            'familyB_n': b1_famB_n,
            'notFamilyB_n': b1_not_famB_n,
            'familyB_min_n': (min(b1_famB_n) if b1_famB_n else None),
            'familyB_max_n': (max(b1_famB_n) if b1_famB_n else None),
            'contiguousBlock_300_400': contiguous_run(300, 400),
            'contiguousBlock_995_999': contiguous_run(995, 999),
        },
        'predictionComparison': {
            'agree': len(agree),
            'disagree': len(disagree),
            'disagreements': disagree,
            'familyB_call_correct': sum(1 for r in agree + disagree if r['familyB_call_correct']),
            'familyB_call_wrong': [r for r in agree + disagree if not r['familyB_call_correct']],
        },
        'rows': rows,
    }
    json.dump(out, sys.stdout, indent=1, default=str)
    print()
    if missing or errored:
        print("NON-ZERO EXIT: %d missing, %d errored — see missingCases / erroredCases"
              % (len(missing), len(errored)), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
