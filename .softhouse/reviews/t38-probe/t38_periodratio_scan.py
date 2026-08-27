"""
T38 (E) -- how wide is the region in which `periodRatio != RepaymentEvery`?

Independently re-derived by this task from revision 7's own text (via
t38_model.period_ratio), NOT taken from T34's t34_scan_broad.py.  The point of
running it again is that T34's 55/5,767 figure is the sort of number that gets
quoted forever; either it reproduces from an independent transcription or it
does not.

EVERY NUMBER HERE IS A RE-DERIVATION.  No oracle was contacted.
"""
import calendar
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t38_model import repayment_boundaries, period_ratio

N = 6
EVERY = 1


def scan(year: int):
    total = 0
    drift = 0
    by_start_day = {}
    examples = []
    for month in range(1, 13):
        dim = calendar.monthrange(year, month)[1]
        for sd in range(1, dim + 1):
            for dd in range(sd, dim + 1):   # ScheduleStartDate <= Disbursement.Date
                start = date(year, month, sd)
                disb = date(year, month, dd)
                bounds = repayment_boundaries(start, disb, N, EVERY)
                # graded domain: disbursement strictly before the last due date
                if not (start <= disb < bounds[-1][1]):
                    continue
                total += 1
                ratios = [period_ratio(start, f, d, EVERY) for f, d in bounds]
                if any(r != Decimal(EVERY) for r in ratios):
                    drift += 1
                    by_start_day[sd] = by_start_day.get(sd, 0) + 1
                    if len(examples) < 6:
                        examples.append((start, disb,
                                         [str(r) for r in ratios if r != Decimal(EVERY)][:2]))
    return total, drift, by_start_day, examples


def main():
    print("=" * 78)
    print("E  (ScheduleStartDate, Disbursement.Date) pairs in the SAME month, all")
    print(f"   twelve months, {N} monthly periods, RepaymentEvery {EVERY}.")
    print("   'drift' = at least one repayment period whose periodRatio != RepaymentEvery")
    print("=" * 78)
    for year in (2024, 2025):
        total, drift, by_day, ex = scan(year)
        pct = (Decimal(drift) * 100 / Decimal(total)).quantize(Decimal("0.01"))
        print(f"\n{year}: admissible same-month pairs {total}, "
              f"drifted {drift} ({pct} %)")
        print("      by ScheduleStartDate day-of-month: "
              + ", ".join(f"day {k}: {v}" for k, v in sorted(by_day.items())))
        for s, d, r in ex:
            print(f"      e.g. start {s}, disbursement {d}, "
                  f"non-unit periodRatio(s) {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
