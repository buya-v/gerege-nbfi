#!/usr/bin/env python3
"""T32 -- the shape nothing has modelled: a disbursement dated STRICTLY INSIDE a
repayment period.

It is admissible under DEC-1 section 3.1's disbursement window
(ScheduleStartDate <= D < last DueDate), it is row 3 of revision 5's own
section 4.3.2 segmentation table, and it is the only in-graded-domain shape
that yields TWO NON-DEGENERATE interest periods inside one repayment period.

The question this script answers: does revision 5's TEXT determine the money on
that shape?  Two readings of the section 4.1 rate factor are run:

  days_reading="text"    both day counts come from the span the rate factor is
                         "computed over" -- so actualDays/calculatedDays == 1,
                         which is what contract.go states outright
                         ("exactly 1 ... which is every period in the graded
                         domain", DayCountFixed30Over360)
  days_reading="source"  actualDaysInPeriod  = days(interest-period FromDate, span end)
                         calculatedDaysInPeriod = days(REPAYMENT FromDate, REPAYMENT DueDate)
                         ProgressiveEMICalculator.java:1367-1370 (rate factor
                         till period due date) and :1500-1503 (recurrence rate
                         factor)

*** NO LIVE ORACLE WAS CONTACTED.  Every figure below is a RE-DERIVATION from
the pinned source, never an observation.  None may be promoted to the vector
store. ***
"""
from datetime import date
from decimal import Decimal
from t32_model import generate, summarise, fmt

SHAPES = [
    # (principal major, n, rate, schedule start, disbursement)
    (1200000, 6, "21.6", date(2024, 1, 1), date(2024, 1, 15)),
    (1014632, 6, "7.0", date(2024, 1, 1), date(2024, 1, 15)),
    (127704, 36, "16.8", date(2024, 1, 1), date(2024, 1, 20)),
    (1200000, 6, "21.6", date(2024, 1, 1), date(2024, 2, 10)),
    (50000000, 12, "18.5", date(2024, 1, 1), date(2024, 1, 2)),
]

if __name__ == "__main__":
    print("T32 -- disbursement STRICTLY INSIDE a repayment period")
    print("(re-derivation from the pinned source; NOT an oracle observation)\n")
    print(f"{'shape':<44} {'DEC-1 text (ratio 1)':>26} {'source (prorated)':>26}")
    for p, n, r, start, d in SHAPES:
        a = summarise(generate(p, n, r, start=start, disb=d, days_reading="text"))
        b = summarise(generate(p, n, r, start=start, disb=d, days_reading="source"))
        tag = f"MNT {p:,}/{n}x{r}% start {start} disb {d}"
        print(f"{tag:<44}")
        print(f"{'   level / final / total interest':<44} "
              f"{'/'.join(a):>26} {'/'.join(b):>26}   {'SAME' if a == b else 'DIVERGE'}")

    print("\nPeriod-1 detail for MNT 1,200,000 / 6 x 21.6%, start 2024-01-01, disb 2024-01-15:")
    for reading in ("text", "source"):
        rps = generate(1200000, 6, "21.6", start=date(2024, 1, 1),
                       disb=date(2024, 1, 15), days_reading=reading)
        rp = rps[0]
        print(f"  {reading:<7} interest={fmt(rp.interest):>12}  principal={fmt(rp.principal):>12}"
              f"  outstanding={fmt(rp.outstanding):>14}  emi={fmt(rp.emi):>12}")
        for ip in rp.ips:
            print(f"            ip [{ip.frm} .. {ip.due}] balance_in={fmt(ip.balance_in):>12}"
                  f" rateFactor={ip.rate_factor} rfTillDue={ip.rf_till_due}")
