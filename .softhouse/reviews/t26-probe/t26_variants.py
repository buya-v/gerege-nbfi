#!/usr/bin/env python3
"""
T26: does DEC-1 revision 3 determine the answer for a request inside the
graded domain on which the EMI re-adjust guard fires?

NOT RUN AGAINST A LIVE ORACLE. Pure re-derivation from the pinned source plus
three ALTERNATIVE loop bodies, each of which is consistent with everything
DEC-1 revision 3 and contract.go actually SAY (they specify the guard and the
3-iteration cap; they do not specify the adjustment magnitude, the
apply-then-re-measure step, or the `hasLessEmiDifference` adoption test).

If the variants disagree, two implementations can conform to DEC-1 as written
and still return different money for the same in-graded-domain request.
"""
from decimal import Decimal
from t26_rederive import (rate_factor, level_emi, rebuild, should_be_adjusted,
                          due_dates, money, mc)
from datetime import date


def loop(principal, rfs, lengths, rows, magnitude, adoption_test, cap=3):
    n = len(rows)
    c = 1
    while c <= cap:
        fires, emi_diff, original = should_be_adjusted(rows)
        if not fires:
            break
        adj = magnitude(emi_diff, n)
        adjusted = original + adj
        if adjusted == original:
            break
        new_rows = rebuild(principal, rfs, [adjusted] * n, lengths)
        _, new_diff, _ = should_be_adjusted(new_rows)
        if adoption_test and not (abs(new_diff) < abs(emi_diff)):
            break
        rows = new_rows
        c += 1
    return rows


VARIANTS = {
    "V0 oracle (diff/n, adoption test)  [Java :1258-1308 + EmiAdjustment:38-48]":
        (lambda d, n: money(mc(lambda: d / Decimal(n))), True),
    "V1 diff/n, NO adoption test        [DEC-1 says nothing about it]":
        (lambda d, n: money(mc(lambda: d / Decimal(n))), False),
    "V2 whole diff onto the level EMI   [a plausible reading of 'smoothing']":
        (lambda d, n: d, True),
    "V3 diff/(n-1)                      [another plausible divisor]":
        (lambda d, n: money(mc(lambda: d / Decimal(max(1, n - 1)))), True),
}

CASES = [(1014632, 6, "7.0"), (127704, 36, "16.8"), (5000000, 12, "21.6"),
         (2500001, 18, "18.5")]

print(__doc__)
for principal_major, n, pct in CASES:
    P = Decimal(principal_major)
    per = due_dates(date(2024, 1, 1), date(2024, 1, 1), n)
    lengths = [(d - f).days for f, d in per]
    rfs = [rate_factor(pct, L, L) for L in lengths]
    base = rebuild(P, rfs, [level_emi(P, rfs)] * n, lengths)
    fires, d0, _ = should_be_adjusted(base)
    print(f"\n=== MNT {principal_major} / {n} x {pct}%  (guard fires: {fires}, "
          f"pre-loop |diff|={abs(d0)}) ===")
    if not fires:
        print("    guard does not fire -- every variant agrees")
        continue
    for name, (mag, adopt) in VARIANTS.items():
        r = loop(P, rfs, lengths, base, mag, adopt)
        ti = sum((x["interest"] for x in r), Decimal(0))
        print(f"  {name}\n      level EMI {r[0]['emi']}   final EMI {r[-1]['emi']}"
              f"   total interest {ti}")
