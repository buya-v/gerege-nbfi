#!/usr/bin/env python3
"""T29 -- under-determination sweeps over DEC-1 revision 4's own graded domain.

*** NO LIVE ORACLE. *** Everything below is a re-derivation from the pinned
Fineract checkout 426a23544 via `t29_rederive.py`, whose source-faithful arm is
validated against 13 committed observations by `t29_validate.py`. None of the
figures printed here is an observation and none may enter the vector store.

SWEEP A -- `n` in the EMI re-adjust loop.
  DEC-1 4.3.1 (and contract.go's Period doc, identically) assert:
    "n is the number of related repayment periods, which inside the graded
     domain is NumberOfRepayments".
  Re-derived from source, n == relatedRepaymentPeriods.size(), which equals
  NumberOfRepayments only when the disbursement lands in the FIRST repayment
  period AND not on its due date.  The graded domain admits
     ScheduleStartDate <= Disbursements[0].Date < last DueDate,
  and the Run-1 corpus contains such a capture (start 2024-01-01,
  disbursement 2024-02-01).  This sweep asks whether the two readings ever
  return different money inside the graded domain.

SWEEP B -- the actualDays/calcDays correction.
  contract.go DayCountFixed30Over360 says the correction
  "actualDaysInPeriod / calculatedDaysInPeriod ... is exactly 1 ... which is
  every period in the graded domain", while DEC-1 4.1's worked example performs
  the multiply and the divide (and shows them perturbing the last digit at
  precision 12).  Does performing vs skipping them change money at 19?
"""

from datetime import date
from t29_rederive import generate, f

RATES = ["7.0", "16.8", "18.5", "21.6", "12.0", "24.0", "9.6", "30.0"]


def sweep_a(limit=25):
    print("=" * 78)
    print("SWEEP A -- n == NumberOfRepayments (DEC-1 text) vs n == |related| (source)")
    print("=" * 78)
    hits, checked = [], 0
    for n in range(2, 37):
        for j in range(1, min(n, 4)):          # disbursement on period j's due date
            for rate in RATES:
                for p in range(1000, 400000, 371):
                    start = date(2024, 1, 1)
                    wins_due = None
                    # period j's due date == start + j months (day 1, no re-anchor)
                    m = start.month - 1 + j
                    disb = date(start.year + m // 12, m % 12 + 1, 1)
                    src = generate(p, n, rate, disb=disb, model="source")
                    txt = generate(p, n, rate, disb=disb, model="text")
                    if src is None:
                        continue
                    checked += 1
                    a = [(r["emi"], r["interest"], r["principal"]) for r in src]
                    b = [(r["emi"], r["interest"], r["principal"]) for r in txt]
                    if a != b:
                        rel_s = [x for x in src if x["emi"] != 0]
                        rel_t = [x for x in txt if x["emi"] != 0]
                        hits.append((p, n, rate, j, f(rel_s[0]["emi"]), f(src[-1]["emi"]),
                                     f(sum(x["interest"] for x in src)),
                                     f(rel_t[0]["emi"]), f(txt[-1]["emi"]),
                                     f(sum(x["interest"] for x in txt))))
                        if len(hits) >= limit:
                            report_a(hits, checked)
                            return hits
    report_a(hits, checked)
    return hits


def report_a(hits, checked):
    print(f"  shapes compared: {checked}    DIVERGENT: {len(hits)}")
    for h in hits:
        p, n, rate, j, sl, sf, si, tl, tf, ti = h
        print(f"   P={p:<8} n={n:<3} {rate:>5}%  disb on period {j}'s due date")
        print(f"      source (n=|related|={n-j}): level {sl:>12}  final {sf:>12}  interest {si:>12}")
        print(f"      text   (n=NumberOfRepayments={n}): level {tl:>12}  final {tf:>12}  interest {ti:>12}")


def sweep_b():
    print()
    print("=" * 78)
    print("SWEEP B -- actualDays/calcDays correction performed vs skipped, at (19, HALF_UP)")
    print("=" * 78)
    diffs = 0
    checked = 0
    for n in (6, 12, 18, 36):
        for rate in RATES:
            for p in range(100, 3_000_000, 7919):
                for seed in (date(2024, 1, 1), date(2024, 1, 31), date(2023, 3, 15)):
                    a = generate(p, n, rate, start=seed, model="source",
                                 apply_day_correction=True)
                    b = generate(p, n, rate, start=seed, model="source",
                                 apply_day_correction=False)
                    checked += 1
                    if [r["emi"] for r in a] != [r["emi"] for r in b]:
                        diffs += 1
                        if diffs <= 5:
                            print(f"   DIVERGES: P={p} n={n} {rate}% start={seed}")
    print(f"  shapes compared: {checked}    divergent: {diffs}")


if __name__ == "__main__":
    sweep_a()
    sweep_b()
