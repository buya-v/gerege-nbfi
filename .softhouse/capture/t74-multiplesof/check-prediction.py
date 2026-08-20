#!/usr/bin/env python3
"""Grade capture pass 3i against the prediction registered before it ran — task T74.

    python3 check-prediction.py <capture-prod3i-raw.json> <predicted.json>

Exit 0 if every registered prediction held, 1 otherwise. It prints EVERY mismatch,
because the interesting outcome of a prediction is the part that was wrong.

It compares MONEY AS INTEGER MINOR UNITS throughout: a money string is parsed by
exact string/integer arithmetic at the case's own currency scale, never through a
float. Where a case runs at currencyDecimalPlaces 0 the "minor unit" is one whole
tugrik, which is what that currency's own record says it is.

This script OBSERVES NOTHING and DECIDES NOTHING about promotion.
"""
import json
import sys

MONEY_KEYS_TOTALS = ("totalDisbursedAmount", "totalPrincipalAmount", "totalInterestAmount",
                     "totalFeeAmount", "totalPenaltyAmount", "totalRepaymentAmount",
                     "totalOutstandingAmount")
MONEY_KEYS_PERIOD = ("principal", "interest", "feeAmount", "penaltyAmount", "total",
                     "balance", "totalOutstandingBalance")


def minor(text, scale):
    """Exact decimal string -> integer minor units at `scale`. No float anywhere."""
    if text is None:
        return None
    s = str(text).strip()
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    if 'e' in s or 'E' in s:
        raise ValueError("exponent in money string %r" % text)
    if '.' in s:
        whole, frac = s.split('.', 1)
    else:
        whole, frac = s, ''
    if len(frac) > scale:
        if frac[scale:].strip('0'):
            raise ValueError("money string %r carries a significant digit beyond scale %d"
                             % (text, scale))
        frac = frac[:scale]
    frac = frac.ljust(scale, '0')
    v = int((whole or '0') + frac) if scale else int(whole or '0')
    return -v if neg else v


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def main(capture_path, predicted_path):
    doc = json.load(open(capture_path, encoding='utf-8'))
    pred = json.load(open(predicted_path, encoding='utf-8'))
    cases = {c['id']: c for c in doc['captures']}
    fails = []
    checks = 0
    cells = 0

    def scale_of(cid):
        return cases[cid]['inputs']['currencyDecimalPlaces']

    # --- 1. identities -----------------------------------------------------------------
    for it in pred['identities']:
        checks += 1
        a, b = it['case'], it['equals']
        if a not in cases or b not in cases:
            fails.append("IDENTITY %s == %s: a case is missing from the capture" % (a, b))
            continue
        if canon(cases[a]['observed']) != canon(cases[b]['observed']):
            fails.append("IDENTITY REFUTED: %s != %s\n    %s -> interest %s\n    %s -> interest %s"
                         % (a, b, a, cases[a]['observed']['totalInterestAmount'],
                            b, cases[b]['observed']['totalInterestAmount']))

    # --- 2. differences ----------------------------------------------------------------
    for it in pred['differences']:
        checks += 1
        a, b = it['case'], it['differsFrom']
        if a not in cases or b not in cases:
            fails.append("DIFFERENCE %s vs %s: a case is missing from the capture" % (a, b))
            continue
        if canon(cases[a]['observed']) == canon(cases[b]['observed']):
            fails.append("DIFFERENCE REFUTED: %s is IDENTICAL to %s (predicted to differ)" % (a, b))

    # --- 3. full schedules, cell for cell ----------------------------------------------
    for cid, spec in pred['full_schedules'].items():
        if cid not in cases:
            fails.append("FULL SCHEDULE %s: case missing from the capture" % cid)
            continue
        want = spec['observed']
        got = cases[cid]['observed']
        sc = scale_of(cid)
        if got.get('loanTermInDays') != want['loanTermInDays']:
            checks += 1
            fails.append("%s loanTermInDays: got %r want %r"
                         % (cid, got.get('loanTermInDays'), want['loanTermInDays']))
        for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
            checks += 1
            cells += 1
            if minor(got.get(k), sc) != minor(want[k], sc):
                fails.append("%s %s: got %r want %r" % (cid, k, got.get(k), want[k]))
        gp, wp = got.get('periods', []), want['periods']
        if len(gp) != len(wp):
            checks += 1
            fails.append("%s period count: got %d want %d" % (cid, len(gp), len(wp)))
            continue
        for idx, (g, w) in enumerate(zip(gp, wp)):
            for k, v in w.items():
                checks += 1
                if k in MONEY_KEYS_PERIOD or k == 'principal':
                    cells += 1
                    if minor(g.get(k), sc) != minor(v, sc):
                        fails.append("%s period[%d].%s: got %r want %r" % (cid, idx, k, g.get(k), v))
                else:
                    if g.get(k) != v:
                        fails.append("%s period[%d].%s: got %r want %r" % (cid, idx, k, g.get(k), v))

    # --- 4. multiple-of structure ------------------------------------------------------
    for spec in pred['money_cells_are_multiples_of']:
        cid, m = spec['case'], spec['modulus']
        if cid not in cases:
            fails.append("MULTIPLES %s: case missing" % cid)
            continue
        sc = scale_of(cid)
        if sc != 0:
            fails.append("MULTIPLES %s: this claim is only meaningful at currencyDecimalPlaces 0, "
                         "the case ran at %d" % (cid, sc))
            continue
        obs = cases[cid]['observed']
        offenders = []
        for k in MONEY_KEYS_TOTALS:
            if k in obs:
                checks += 1
                cells += 1
                if minor(obs[k], 0) % m != 0:
                    offenders.append("%s=%s" % (k, obs[k]))
        for idx, p in enumerate(obs.get('periods', [])):
            for k in MONEY_KEYS_PERIOD:
                if k in p:
                    checks += 1
                    cells += 1
                    if minor(p[k], 0) % m != 0:
                        offenders.append("period[%d].%s=%s" % (idx, k, p[k]))
        if offenders:
            fails.append("MULTIPLES REFUTED: %s has money cells that are not multiples of %d: %s"
                         % (cid, m, ", ".join(offenders[:12])))

    # --- 5. totals ---------------------------------------------------------------------
    for cid, spec in pred['totals'].items():
        if cid not in cases:
            fails.append("TOTALS %s: case missing" % cid)
            continue
        sc = scale_of(cid)
        for k in ("totalInterestAmount", "totalRepaymentAmount"):
            checks += 1
            cells += 1
            got = cases[cid]['observed'].get(k)
            if minor(got, sc) != minor(spec[k], sc):
                fails.append("TOTALS REFUTED: %s %s got %r want %r" % (cid, k, got, spec[k]))

    # --- 6. sharp claims ---------------------------------------------------------------
    for cl in pred['sharp_claims']:
        cid = cl['case']
        if cl['id'] == 'S1':
            checks += 1
            obs = cases[cid]['observed']
            bad = [p for p in obs['periods'] if p.get('type') == 'REPAYMENT'
                   and minor(p.get('interest'), 0) != 0]
            if minor(obs['totalInterestAmount'], 0) != 0 or bad:
                fails.append("S1 REFUTED: %s totalInterest=%s, %d repayment rows with non-zero "
                             "interest" % (cid, obs['totalInterestAmount'], len(bad)))
        elif cl['id'] == 'S2':
            checks += 1
            obs = cases[cid]['observed']
            reps = [p for p in obs['periods'] if p.get('type') == 'REPAYMENT']
            nz = [p for p in reps if minor(p.get('principal'), 0) != 0]
            ok = (len(nz) == 1 and nz[0].get('periodNumber') == 6
                  and minor(nz[0].get('principal'), 0) == 1000
                  and minor(nz[0].get('interest'), 0) == 0
                  and minor(nz[0].get('total'), 0) == 1000
                  and minor(nz[0].get('balance'), 0) == 0
                  and all(minor(p.get('balance'), 0) == 1000
                          for p in reps if p.get('periodNumber') != 6))
            if not ok:
                fails.append("S2 REFUTED: %s -> %d non-zero-principal repayment rows %r"
                             % (cid, len(nz),
                                [(p.get('periodNumber'), p.get('principal'), p.get('interest'),
                                  p.get('total'), p.get('balance')) for p in reps]))
        elif cl['id'] == 'S3':
            checks += 1
            rows = cases[cid]['mechanism']['periods']
            zero_emi = [r for r in rows if minor(r.get('emi'), 0) == 0]
            if len(zero_emi) < 5:
                fails.append("S3 REFUTED: %s has %d zero-EMI mechanism rows, predicted at least 5. "
                             "emis=%r" % (cid, len(zero_emi), [r.get('emi') for r in rows]))
        elif cl['id'] == 'S4':
            for c in doc['captures']:
                checks += 1
                if c.get('pathIdentity', {}).get('identical') is not True:
                    fails.append("S4 REFUTED: %s pathIdentity not identical" % c['id'])
                if (c['inputs'].get('ambientMoneyHelperPrecision') != 19
                        or c['inputs'].get('ambientMoneyHelperRoundingModeOrdinal') != 4):
                    fails.append("S4 REFUTED: %s ambient MoneyHelper (%s, ordinal %s)"
                                 % (c['id'], c['inputs'].get('ambientMoneyHelperPrecision'),
                                    c['inputs'].get('ambientMoneyHelperRoundingModeOrdinal')))
        elif cl['id'] == 'S5':
            checks += 1
            obs = cases[cid]['observed']
            p1 = [p for p in obs['periods']
                  if p.get('type') == 'REPAYMENT' and p.get('periodNumber') == 1]
            if not p1 or minor(p1[0].get('interest'), 0) != 77100:
                fails.append("S5 REFUTED: %s period 1 interest is %r, predicted 77100"
                             % (cid, p1[0].get('interest') if p1 else None))
        elif cl['id'] == 'S6':
            for base in ("T74-E-P4", "T74-E-P59", "T74-E-P72", "T74-E-P340",
                         "T74-E-P426", "T74-E-P6940"):
                checks += 1
                if canon(cases[base]['observed']) == canon(cases[base + '-p12']['observed']):
                    fails.append("S6 REFUTED: %s is IDENTICAL to its precision-12 companion — "
                                 "T21 section 6.2 recorded DIFFERENT" % base)

    print("checked %d predictions over %d money cells" % (checks, cells))
    if fails:
        print("\nPREDICTION MISMATCHES: %d\n" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("ALL REGISTERED PREDICTIONS HELD.")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
