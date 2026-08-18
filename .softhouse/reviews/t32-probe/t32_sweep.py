#!/usr/bin/env python3
"""T32 -- sweep: how far apart are the two readings of DEC-1 revision 5's rate
factor on a disbursement dated STRICTLY INSIDE a repayment period, and does the
unstated composition of a multi-segment period's rate factors move money?

  reading "text"   : actualDaysInPeriod / calculatedDaysInPeriod == 1, which is
                     what contract.go states outright for "every period in the
                     graded domain"
  reading "source" : calculatedDaysInPeriod is the ENCLOSING REPAYMENT period's
                     day count (ProgressiveEMICalculator.java:1367-1370, :1500-1503)

  composition "sum"   : 1 + SUM(rf over interest periods)  [RepaymentPeriod.java:216-217]
  composition "whole" : 1 + rf over the whole repayment period, which is the only
                        thing DEC-1 2.1 / contract.go:448-451 literally say

*** RE-DERIVATION ONLY.  NO LIVE ORACLE WAS CONTACTED.  Not one figure below is
an observation and none may be promoted to the vector store. ***
"""
import random
from datetime import date, timedelta
from decimal import Decimal

import t32_model as M

_orig = M.rate_factor_plus1
_cur = {}


def _whole(rp):
    return M.eadd(Decimal(1), M.rate_factor(_cur["r"], rp.frm, rp.due, rp, "source"))


def strictly_inside(start: date, n: int, d: date) -> bool:
    ds = M.due_dates(start, n, 1, d)
    return all(d != x for x in ds) and ds[0] < d < ds[-1]


def main(trials: int = 3000, seed: int = 32) -> None:
    random.seed(seed)
    start = date(2024, 1, 1)
    n_inside = day_div = comp_div = 0
    worst = None
    for _ in range(trials):
        p = random.randint(1000, 90_000_000)
        n = random.choice([6, 12, 18, 36])
        r = random.choice(["7.0", "16.8", "18.5", "21.6"])
        d = start + timedelta(days=random.randint(1, 150))
        if not strictly_inside(start, n, d):
            continue
        n_inside += 1
        _cur["r"] = Decimal(r)
        M.rate_factor_plus1 = _orig
        src = M.summarise(M.generate(p, n, r, start=start, disb=d, days_reading="source"))
        txt = M.summarise(M.generate(p, n, r, start=start, disb=d, days_reading="text"))
        M.rate_factor_plus1 = _whole
        who = M.summarise(M.generate(p, n, r, start=start, disb=d, days_reading="source"))
        M.rate_factor_plus1 = _orig
        if src != txt:
            day_div += 1
            gap = abs(Decimal(src[2]) - Decimal(txt[2]))
            if worst is None or gap > worst[0]:
                worst = (gap, p, n, r, d, src, txt)
        if src != who:
            comp_div += 1
    print(f"strictly-inside-a-period shapes drawn: {n_inside}")
    print(f"  ratio-1 reading vs source day ratio DIVERGES on : {day_div}"
          f"  ({100.0 * day_div / max(1, n_inside):.1f}%)")
    print(f"  sum vs whole-period rate-factor composition     : {comp_div}"
          f"  ({100.0 * comp_div / max(1, n_inside):.1f}%)")
    if worst:
        gap, p, n, r, d, src, txt = worst
        print(f"\n  largest total-interest gap seen: {gap}")
        print(f"    MNT {p:,} / {n} x {r}%, schedule start 2024-01-01, disbursement {d}")
        print(f"      source day ratio : level/final/interest = {'/'.join(src)}")
        print(f"      ratio-1 reading  : level/final/interest = {'/'.join(txt)}")
    print("\n(re-derivation from the pinned checkout; NOT an oracle observation)")


if __name__ == "__main__":
    main()
