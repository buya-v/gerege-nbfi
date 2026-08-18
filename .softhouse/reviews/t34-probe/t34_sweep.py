"""
T34 (C): sweep DEC-1 section 3.1's graded domain for shapes where the document's
normative `RepaymentEvery` multiplier and the pinned source's `periodRatio`
multiplier return different money.

*** NO ORACLE WAS CONTACTED.  Every figure is a RE-DERIVATION, a CANDIDATE SHAPE
*** TO CAPTURE, never an observation.
"""
from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import Request, generate, totals, m2s, MINOR
from t34_periodratio import period_ratios_for, both

RATES = ["7.0", "16.8", "18.5", "21.6"]
TERMS = [6, 12, 18, 36]
PRINCIPALS = [100, 127704, 1200000, 5000000, 50000000]


def scan_ratio_only():
    """First: for which (schedule start day, disbursement day) pairs does the
    oracle's periodRatio differ from RepaymentEvery at all?  This is a pure
    date-arithmetic question, independent of the money."""
    hits = []
    for sday in range(1, 32):
        for dday in range(1, 32):
            try:
                start = date(2024, 1, sday)
                disb = date(2024, 1, dday)
            except ValueError:
                continue
            if disb < start:
                continue
            req = Request(start=start, disb=disb, principal_minor=120000000,
                          n=6, rate_pct=Decimal("21.6"))
            ratios = period_ratios_for(req)
            if any(r != Decimal(1) for r in ratios):
                hits.append((sday, dday, [str(r) for r in ratios]))
    return hits


def sweep_money(pairs):
    """Then: on those date shapes, how much money moves?"""
    div = 0
    total = 0
    worst = None
    examples = []
    for sday, dday, _ in pairs:
        for n in TERMS:
            for r in RATES:
                for p in PRINCIPALS:
                    start = date(2024, 1, sday)
                    disb = date(2024, 1, dday)
                    req = Request(start=start, disb=disb,
                                  principal_minor=p * 100, n=n,
                                  rate_pct=Decimal(r))
                    total += 1
                    a, b = both(req)
                    ta, tb = totals(a), totals(b)
                    rowdiff = any(
                        (x.principal_minor, x.interest_minor, x.outstanding_minor,
                         x.emi_minor) != (y.principal_minor, y.interest_minor,
                                          y.outstanding_minor, y.emi_minor)
                        for x, y in zip(a, b))
                    if ta != tb or rowdiff:
                        div += 1
                        gap = abs(ta[1] - tb[1])
                        if worst is None or gap > worst[0]:
                            worst = (gap, sday, dday, n, r, p, ta[1], tb[1])
                        if len(examples) < 6:
                            examples.append((sday, dday, n, r, p, ta[1], tb[1]))
    return div, total, worst, examples


def main():
    print("=" * 78)
    print("T34 (C) -- DEC-1 rev 6's `RepaymentEvery` multiplier vs the pinned")
    print("source's `periodRatio` [ProgressiveEMICalculator.java:1404-1413].")
    print("RE-DERIVATION ONLY.  NO ORACLE WAS CONTACTED.")
    print("=" * 78)
    print()
    print("(1) date shapes in the graded domain where periodRatio != RepaymentEvery")
    print("    (schedule start and disbursement both in January 2024, 6 monthly")
    print("     periods, single disbursement, ScheduleStart <= D):")
    hits = scan_ratio_only()
    print(f"    {len(hits)} of the 496 admissible (start day, disbursement day) pairs")
    for sday, dday, ratios in hits[:12]:
        nz = [(i + 1, r) for i, r in enumerate(ratios) if r != "1"]
        print(f"      start 2024-01-{sday:02d}  disb 2024-01-{dday:02d}  "
              f"non-unit ratios: {nz}")
    if len(hits) > 12:
        print(f"      ... and {len(hits) - 12} more")
    print()

    print("(2) money divergence over those date shapes x "
          f"{len(TERMS)} terms x {len(RATES)} rates x {len(PRINCIPALS)} principals:")
    div, total, worst, examples = sweep_money(hits)
    print(f"    {div} of {total} shapes return DIFFERENT MONEY "
          f"({100.0 * div / total:.1f}%)" if total else "    no shapes")
    if worst:
        gap, sday, dday, n, r, p, ta, tb = worst
        print()
        print("    worst total-interest gap:")
        print(f"      start 2024-01-{sday:02d}, disbursement 2024-01-{dday:02d}, "
              f"{p:,} major units, {n} x {r}%")
        print(f"      DEC-1 as written : total interest {m2s(ta)}")
        print(f"      pinned source    : total interest {m2s(tb)}")
        print(f"      gap              : {m2s(gap)}")
    print()
    print("    first divergent shapes:")
    for sday, dday, n, r, p, ta, tb in examples:
        print(f"      start 2024-01-{sday:02d} disb 2024-01-{dday:02d} "
              f"{p:>10,} {n:>3} x {r:>5}%   DEC-1 {m2s(ta):>14}   "
              f"source {m2s(tb):>14}   gap {m2s(abs(ta - tb))}")
    print()

    print("(3) the worked shape, row by row")
    req = Request(start=date(2024, 1, 28), disb=date(2024, 1, 31),
                  principal_minor=1200000 * 100, n=6, rate_pct=Decimal("21.6"))
    ratios = period_ratios_for(req)
    a, b = both(req)
    print("    MNT 1,200,000 / 6 x 21.6%, schedule start 2024-01-28, "
          "single disbursement 2024-01-31")
    print(f"    periodRatio per period: {[str(x) for x in ratios]}")
    print(f"    {'period':>7} {'from':>11} {'due':>11} "
          f"{'DEC-1 prin':>13} {'DEC-1 int':>12} | {'src prin':>13} {'src int':>12}")
    for i, (x, y) in enumerate(zip(a, b), start=1):
        print(f"    {i:>7} {str(x.frm):>11} {str(x.due):>11} "
              f"{m2s(x.principal_minor):>13} {m2s(x.interest_minor):>12} | "
              f"{m2s(y.principal_minor):>13} {m2s(y.interest_minor):>12}")
    print(f"    total interest: DEC-1 {m2s(totals(a)[1])}   "
          f"pinned source {m2s(totals(b)[1])}   "
          f"gap {m2s(abs(totals(a)[1] - totals(b)[1]))}")
    print()
    print("Every figure above is a RE-DERIVATION from the pinned checkout and is")
    print("recorded as a CANDIDATE SHAPE TO CAPTURE.  None may be promoted to the")
    print("vector store.  No live oracle was contacted by task T34.")


if __name__ == "__main__":
    main()
