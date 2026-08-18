#!/usr/bin/env python3
"""T36 — T22 P1-11, second clause: find a shape that makes the EMI re-adjust loop ITERATE.

The loop is `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
(ProgressiveEMICalculator.java:1258-1308, at most 3 iterations).  It fires when
`EmiAdjustment.shouldBeAdjusted()` (EmiAdjustment.java:31-36) holds:

    floor(n/2) > 0  AND  emiDifference != 0  AND  |emiDifference| * 100 > originalEmi.copy(floor(n/2))

THE TRAP that got three earlier probe scripts retracted: `Money.copy(double)` REPLACES the
amount (Money.java:220-221 -> :216-217 -> the private ctor at :40-52, which setScales to the
currency's decimal places).  So the right-hand side is **Money(floor(n/2))** — for n = 12 that
is 6.00 — NOT `EMI x 6`.  With 12 periods the loop therefore needs |residual| > 0.06.
On all four committed captures the residual is at most +-0.05, so it never fires.

This module does NOT author any expected value.  It uses T22's audited re-derivation
(`t22_rederive.derive`, verified digit-for-digit against B-01/B-02 at both modes, and which
does NOT implement the loop) purely to SELECT CANDIDATE PRINCIPALS worth putting to the
oracle.  Every number that ends up in the record is observed from the running server.

Usage:  python3 t36_emiloop_search.py [start] [count]     (whole-MNT principals)
"""
import datetime
import importlib.util
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    't22_rederive', os.path.join(HERE, '..', 't22-audit', 't22_rederive.py'))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

N = 12
FIRST_FROM = datetime.date(2026, 1, 1)
DUE = [datetime.date(2026 + (m // 12), (m % 12) + 1, 1) for m in range(1, N + 1)]
RATE = Decimal('21.6')


def q2(x):
    return x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def walk(principal, emi, rfs):
    """One pass of the schedule walk at a GIVEN emi; returns (rows, residual).

    Mirrors RepaymentPeriod.java:251-257 / :272-285 / :345-349 and the final-installment
    residual at ProgressiveEMICalculator.java:1202-1205.  Exact Decimal throughout.
    """
    bal = principal
    rows = []
    for i in range(N):
        calc_int = q2(bal * rfs[i])
        due_int = min(calc_int, emi)
        due_pri = max(Decimal(0), emi - due_int)
        bal = bal - due_pri
        rows.append({'emi': emi, 'interest': due_int, 'principal': due_pri, 'balance': bal})
    total_int = sum((r['interest'] for r in rows), Decimal(0))
    total_emi = emi * N
    residual = principal + total_int - total_emi
    return rows, residual


def rate_factors():
    """Rate factor per period for SAME_AS_REPAYMENT_PERIOD + MONTHLY (:1510-1516)."""
    d = rd.derive(Decimal('1200000'), N, RATE, DUE, FIRST_FROM, mode='HALF_UP')
    # derive() does not expose rfs; recompute with the identical steps it uses.
    from decimal import localcontext, ROUND_HALF_UP as RHU
    with localcontext() as ctx:
        ctx.prec = 19
        ctx.rounding = RHU
        rate = RATE / Decimal(100)
        f = rate * (Decimal(1) / Decimal(12))
        f = f.quantize(Decimal(1).scaleb(-19), rounding=RHU)
        return [f] * N, d


RFS, _b01 = rate_factors()


def emi_for(principal):
    """Unrounded->quantised EMI, exactly as derive() computes it (:1838-1841, Money.java:52)."""
    from decimal import localcontext, ROUND_HALF_UP as RHU
    with localcontext() as ctx:
        ctx.prec = 19
        ctx.rounding = RHU
        rfp1 = [Decimal(1) + f for f in RFS]
        rate_factor_n = Decimal(1)
        for v in rfp1:
            rate_factor_n = rate_factor_n * v
        fn = Decimal(1)
        for v in rfp1[1:]:
            fn = Decimal(1) + fn * v
        return q2(rate_factor_n * principal / fn)


def loop_prediction(principal):
    """What the loop would do, from source. n=12, no multiplesOf, uncountablePeriods=0."""
    emi = emi_for(principal)
    rows, residual = walk(principal, emi, RFS)
    trace = []
    lower_half = Decimal(N // 2)                       # floor(n/2) -> Money(6.00)
    for it in range(1, 4):
        fires = lower_half > 0 and residual != 0 and abs(residual) * 100 > lower_half
        trace.append({'iter': it, 'emi': emi, 'residual': residual, 'fires': fires})
        if not fires:
            break
        adjustment = q2(residual / Decimal(N))         # EmiAdjustment.adjustment() -> Money(2dp)
        new_emi = emi + adjustment                     # adjustedEmi()
        if new_emi == emi:                             # isEqualTo(originalEmi) -> break
            trace[-1]['stopped'] = 'adjustedEmi == originalEmi'
            break
        _r2, residual2 = walk(principal, new_emi, RFS)
        if not abs(residual2) < abs(residual):         # hasLessEmiDifference -> break
            trace[-1]['stopped'] = 'difference did not shrink'
            break
        trace[-1]['adopted_emi'] = new_emi
        emi, residual = new_emi, residual2
    return emi, residual, trace


def main(start, count):
    hits = []
    for k in range(count):
        p = Decimal(start + k)
        emi = emi_for(p)
        _rows, residual = walk(p, emi, RFS)
        if abs(residual) * 100 > Decimal(N // 2):
            final_emi, final_res, trace = loop_prediction(p)
            adopted = any('adopted_emi' in t for t in trace)
            hits.append((p, emi, residual, final_emi, final_res, adopted))
    print('scanned %d whole-MNT principals from %d; %d predicted to ENTER the loop'
          % (count, start, len(hits)))
    print('%-14s %-13s %-9s %-13s %-9s %s' %
          ('principal', 'unlooped EMI', 'residual', 'looped EMI', 'residual', 'loop ADOPTED a new EMI?'))
    for p, emi, res, femi, fres, adopted in hits[:40]:
        print('%-14s %-13s %-9s %-13s %-9s %s' % (p, emi, res, femi, fres, adopted))
    adopters = [h for h in hits if h[5]]
    print('\ncandidates where the loop ADOPTS a changed EMI (observable divergence): %d' % len(adopters))
    for p, emi, res, femi, fres, _a in adopters[:20]:
        print('  principal %s : unlooped EMI %s (residual %s) -> looped EMI %s (residual %s)'
              % (p, emi, res, femi, fres))
    return adopters


if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 1200000
    c = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    main(s, c)
