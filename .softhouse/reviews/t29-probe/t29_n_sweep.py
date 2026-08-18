#!/usr/bin/env python3
"""
T29 -- reachability sweep for the `n` defect found in DEC-1 revision 4.

DEC-1 rev 4 section 4.3.1 and contract.go's `Period` doc both state, as
normative text:

    "n is the number of related repayment periods, which inside the graded
     domain is NumberOfRepayments (ProgressiveLoanInterestScheduleModel
     .java:191-194)."

Re-derived from the pinned source (426a23544), that identity does NOT hold
across the graded domain:

  ProgressiveEMICalculator.java:749 passes `relatedRepaymentPeriods` to
  checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods; that list is built at
  :732 by getRelatedRepaymentPeriods(calculateFromRepaymentPeriodDueDate)
  (ProgressiveLoanInterestScheduleModel.java:191-198 -- periods whose dueDate
  is NOT BEFORE the given date), and the date comes from
  getEffectiveRepaymentDueDate (:250-263) applied to the repayment period the
  disbursement landed in (:146-151). Only when the disbursement lands in the
  FIRST period's window is that list the whole schedule.

  EmiAdjustment.numberOfRelatedPeriods() is relatedRepaymentPeriods.size()
  (EmiAdjustment.java:54-56), and it drives BOTH
    - the guard threshold  floor(n/2)  (EmiAdjustment.java:32-35), and
    - the adjustment divisor max(1, n - uncountablePeriods)
                                          (EmiAdjustment.java:38-40).

DEC-1's own graded domain admits `ScheduleStartDate <= Disbursements[0].Date
< the last repayment period's DueDate`, and DEC-1 sections 4.2 and 4.6 both
cite an OBSERVED case (t23-probe Q0b) where the disbursement is dated on
repayment 1's due date -- there n = 5 while NumberOfRepayments = 6.

This sweep asks: inside the graded domain, does that difference MOVE MONEY?

*** NOT RUN AGAINST A LIVE ORACLE. *** Every number below is a re-derivation
from the pinned source. No new observation was taken; none may be promoted.
"""

from datetime import date
from decimal import Decimal
import t29_from_text as T


def build_case(principal_major, N, annual_pct, j, start=date(2024, 1, 1)):
    """Schedule with the single disbursement dated exactly on period j's due
    date (j == 0 => on ScheduleStartDate). Returns (rows_full, rfs, lengths,
    principal_minor, n_related). rows_full carries the leading all-zero rows
    that the oracle emits for periods before the disbursement (OBSERVED,
    t23-probe Q0b), so the `rows` an implementer indexes is the whole
    schedule -- the most charitable reading of DEC-1's text.
    """
    principal_minor = int(round(principal_major * T.SCALE))
    wins = T.period_windows(start, start, N)
    seed = start if j == 0 else wins[j - 1][1]
    if j:
        wins = T.period_windows(start, seed, N)
    related = wins[j:]
    lengths = [(d - f).days for f, d in related]
    rfs = [T.rate_factor(Decimal(str(annual_pct)), L, L) for L in lengths]
    level = T.level_installment_minor(principal_minor, rfs)
    rows = T.build(principal_minor, rfs, level, lengths)
    zero = [{"emi": 0, "interest": 0, "principal": 0, "outstanding": 0} for _ in range(j)]
    return zero + rows, rfs, lengths, principal_minor, len(related)


def run_loop(principal_minor, rfs, lengths, rows_full, j, n):
    """The section 4.3.1 body with a caller-supplied n. `rows_full` includes
    the j leading zero rows; the trial rebuild only ever touches the related
    suffix (:1279-1286), so the zero rows ride along unchanged.
    """
    rows = rows_full
    counter = 1
    adopted = 0
    while True:
        if n < 2 or len(rows) < 2:
            break
        original = rows[-2]["emi"]
        emi_diff = rows[-1]["emi"] - original
        lower_half = n // 2
        if not (lower_half > 0 and emi_diff != 0
                and abs(emi_diff) * 100 > lower_half * T.SCALE):
            break
        d = max(1, n - 0)
        adjustment = T.div_round_half_up(emi_diff, d)
        adjusted = original + adjustment
        if adjusted == original:
            break
        trial_tail = T.build(principal_minor, rfs, adjusted, lengths)
        trial = [dict(r) for r in rows[:j]] + trial_tail
        new_diff = trial[-1]["emi"] - trial[-2]["emi"]
        if not (abs(new_diff) < abs(emi_diff)):
            break
        rows = trial
        adopted += 1
        counter += 1
        if counter > 3:
            break
    return rows, adopted


def money(rows):
    return (rows[-2]["emi"], rows[-1]["emi"], sum(r["interest"] for r in rows))


if __name__ == "__main__":
    print(__doc__)
    print("=" * 78)
    print("SWEEP: graded-domain shapes, single disbursement dated on period j's")
    print("due date (0 = ScheduleStartDate). n_text = NumberOfRepayments (what")
    print("DEC-1 rev 4 says); n_src = |relatedRepaymentPeriods| (what the source")
    print("does). A row is printed only where the two return DIFFERENT money.")
    print("=" * 78)

    rates = ["7.0", "16.8", "18.5", "21.6"]
    diverge = 0
    fired = 0
    total = 0
    first = []
    for N in (6, 12, 18, 24, 36):
        for j in (0, 1, 2, 3):
            if j >= N - 1:
                continue
            for r in rates:
                for p in range(100000, 100400):
                    total += 1
                    rows0, rfs, lengths, pmin, n_src = build_case(p, N, r, j)
                    rt, at = run_loop(pmin, rfs, lengths, [dict(x) for x in rows0], j, N)
                    rs, asrc = run_loop(pmin, rfs, lengths, [dict(x) for x in rows0], j, n_src)
                    if at or asrc:
                        fired += 1
                    if money(rt) != money(rs):
                        diverge += 1
                        if len(first) < 8:
                            first.append((p, N, r, j, n_src, money(rt), money(rs)))
    print(f"\nshapes swept                      : {total}")
    print(f"shapes where the loop adopted     : {fired}")
    print(f"shapes where TEXT != SOURCE money : {diverge}")
    print("\nfirst divergent shapes (re-derived, NOT observed):")
    for p, N, r, j, n_src, mt, ms in first:
        print(f"  MNT {p} / {N} x {r}%, disbursement on period {j}'s due date "
              f"(NumberOfRepayments={N}, |related|={n_src})")
        print(f"     as DEC-1 text  : penult={T.fmt(mt[0])} final={T.fmt(mt[1])} "
              f"totalInterest={T.fmt(mt[2])}")
        print(f"     as the source  : penult={T.fmt(ms[0])} final={T.fmt(ms[1])} "
              f"totalInterest={T.fmt(ms[2])}")
