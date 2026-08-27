"""
T34 (C2): how wide is the periodRatio != RepaymentEvery region?

Sweeps every (ScheduleStartDate, Disbursement.Date) pair with both dates in the
same month, over all twelve months of a leap year (2024) and a common year
(2025), for 6- and 12-period monthly loans.

*** RE-DERIVATION ONLY.  NO ORACLE WAS CONTACTED. ***
"""
from __future__ import annotations

import calendar
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import Request, repayment_boundaries
from t34_periodratio import period_ratios_for


def scan(year: int, n: int):
    admissible = 0
    hits = 0
    by_startday: dict[int, int] = {}
    examples = []
    for month in range(1, 13):
        last = calendar.monthrange(year, month)[1]
        for sday in range(1, last + 1):
            for dday in range(sday, last + 1):
                start = date(year, month, sday)
                disb = date(year, month, dday)
                req = Request(start=start, disb=disb,
                              principal_minor=120000000, n=n,
                              rate_pct=Decimal("21.6"))
                bounds = repayment_boundaries(start, disb, n, 1)
                if not (start <= disb < bounds[-1][1]):
                    continue
                admissible += 1
                ratios = period_ratios_for(req)
                bad = [(i + 1, r) for i, r in enumerate(ratios) if r != Decimal(1)]
                if bad:
                    hits += 1
                    by_startday[sday] = by_startday.get(sday, 0) + 1
                    if len(examples) < 10:
                        examples.append((start, disb, bad))
    return admissible, hits, by_startday, examples


def main():
    print("T34 (C2) -- width of the region where the pinned source's periodRatio")
    print("differs from DEC-1 revision 6's normative `RepaymentEvery`.")
    print("RE-DERIVATION ONLY.  NO ORACLE WAS CONTACTED.")
    print()
    for year in (2024, 2025):
        for n in (6, 12):
            adm, hits, by_startday, examples = scan(year, n)
            pct = 100.0 * hits / adm if adm else 0.0
            print(f"  year {year}, {n} monthly periods: "
                  f"{hits} of {adm} admissible same-month "
                  f"(ScheduleStartDate, Disbursement.Date) pairs -> {pct:.2f}%")
            print(f"      by ScheduleStartDate day-of-month: "
                  f"{dict(sorted(by_startday.items()))}")
    print()
    print("  first ten divergent shapes (year 2024, 6 periods):")
    _, _, _, ex = scan(2024, 6)
    for start, disb, bad in ex:
        print(f"      start {start}  disb {disb}  "
              f"non-unit periodRatio on periods {[i for i, _ in bad]}")
    print()
    print("  Every figure is a RE-DERIVATION from the pinned checkout.")


if __name__ == "__main__":
    main()
