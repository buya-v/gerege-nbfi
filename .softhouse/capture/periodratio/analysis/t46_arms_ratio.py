#!/usr/bin/env python3
"""T46 -- what the `arms` pass DISCRIMINATES.

`patterns.md`: *coverage is what a corpus can distinguish, never what it contains.*  This
script answers that question for the eleven new T46 captures, and it answers it by
RE-IMPLEMENTING `calculatePeriodRatio` from the pinned source in exact integer date
arithmetic -- never by reading T39's or T44's analysis code.

Sources re-implemented here, and nothing else:
  ProgressiveEMICalculator.java:1419-1459   calculatePeriodRatio
  ProgressiveEMICalculator.java:1461-1479   calculateSeedDate
  DateUtils.java:308-321                    getDifference / getExactDifference / getDifferenceInDays
                                            (== ChronoUnit.<unit>.between)

Only the per-period `fromDate` / `dueDate` are taken from the OBSERVED payload; the ratio is
computed here.  No money value is read, computed or predicted by this file -- it reports the
RATIO, which is the quantity the two contested readings disagree about, so the report says
what the captures can tell apart without asserting any amount.

Four readings, exactly as T44 named them:
  R1  multiplier is RepaymentEvery                       (DEC-1 revision 6's reading)
  R2  periodRatio, packed whole-units, month-end special case PRESENT   (the pinned source)
  R3  periodRatio, packed whole-units, month-end special case OMITTED
  R4  periodRatio, naive whole-units, month-end special case OMITTED
"""
import json
import pathlib
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP  # noqa: F401  (exact decimal only)

HERE = pathlib.Path(__file__).resolve().parent.parent
PAYLOADS = [HERE / "out" / "t46-periodratio-arms.json",
            HERE / "out" / "t46-periodratio-reemit.json"]

getcontext().prec = 19  # the ratified production precision; used only for the divide at :1453


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def plus(dt, n, unit):
    """LocalDate.plus(n, unit) -- java.time semantics, including end-of-month clamping."""
    if unit == "DAYS":
        return dt + timedelta(days=n)
    if unit == "WEEKS":
        return dt + timedelta(days=7 * n)
    if unit == "MONTHS":
        total = dt.year * 12 + (dt.month - 1) + n
        y, m = divmod(total, 12)
        m += 1
        return date(y, m, min(dt.day, monthrange(y, m)[1]))
    if unit == "YEARS":
        y = dt.year + n
        return date(y, dt.month, min(dt.day, monthrange(y, dt.month)[1]))
    raise ValueError(unit)


def between(a, b, unit):
    """ChronoUnit.<unit>.between(a, b) -- the PACKED rule for MONTHS and YEARS."""
    if unit == "DAYS":
        return (b - a).days
    if unit == "WEEKS":
        return int((b - a).days / 7) if (b - a).days >= 0 else -int((a - b).days / 7)
    if unit == "MONTHS":
        k = (b.year * 12 + b.month) - (a.year * 12 + a.month)
        packed = k * 32 + (b.day - a.day)
        return int(packed / 32)  # java integer division truncates toward zero
    if unit == "YEARS":
        return int(between(a, b, "MONTHS") / 12)
    raise ValueError(unit)


def naive_between(a, b, unit):
    """"count whole units, step back one if plus() overshoots" -- the obvious port."""
    if unit in ("DAYS", "WEEKS"):
        return between(a, b, unit)
    if unit == "MONTHS":
        k = (b.year * 12 + b.month) - (a.year * 12 + a.month)
    elif unit == "YEARS":
        k = b.year - a.year
    else:
        raise ValueError(unit)
    if plus(a, k, unit) > b:
        k -= 1
    return k


def n_reading(seed, from_date, unit, reading):
    """`numberOfPeriodBetweenSeedDateAndActualRepaymentPeriod` under R2 / R3 / R4."""
    if unit != "MONTHS":
        # :1424 -- DAYS, WEEKS, YEARS have NO special case at all
        return naive_between(seed, from_date, unit) if reading == "R4" else between(seed, from_date, unit)
    last_day = monthrange(from_date.year, from_date.month)[1]
    fires = last_day == from_date.day and seed.day > from_date.day
    if reading == "R2":
        return between(seed, from_date + timedelta(days=1), unit) if fires else between(seed, from_date, unit)
    if reading == "R3":
        return between(seed, from_date, unit)
    if reading == "R4":
        return naive_between(seed, from_date, unit)
    raise ValueError(reading)


def seed_date(schedule_start, from_date, due_date, unit, repay_every):
    """calculateSeedDate, :1461-1479."""
    seed = schedule_start
    mult = 1
    while True:
        calculated = plus(seed, mult, unit)
        mult += 1
        if not calculated < due_date:
            break
    if calculated == due_date and plus(calculated, -repay_every, unit) == from_date:
        return seed
    return from_date


def period_ratio(schedule_start, from_date, due_date, unit, repay_every, reading):
    """calculatePeriodRatio, :1419-1458, with the n-reading swapped in."""
    seed = seed_date(schedule_start, from_date, due_date, unit, repay_every)
    n = n_reading(seed, from_date, unit, reading)
    mult = n + 1
    cursor = from_date
    while cursor < due_date:
        cursor = plus(seed, mult, unit)
        if not cursor > due_date:
            mult += 1
        else:
            full_period_date = cursor
            mult = mult - n - 1
            cursor = plus(seed, mult, unit)
            diff = (due_date - cursor).days
            full = (full_period_date - cursor).days
            return Decimal(diff) / Decimal(full) + Decimal(mult)
    return Decimal(mult - n - 1)


def main():
    print("T46 -- what the arms pass discriminates (ratio only; no money is predicted here)")
    print()
    hdr = (f"{'capture':<14} {'freq':<7} {'every':>5} {'period':>6} "
           f"{'R1=every':>9} {'R2 (pinned)':>22} {'R3':>22} {'R4':>22}  verdict")
    print(hdr)
    print("-" * len(hdr))

    totals = {"R1": 0, "R3": 0, "R4": 0, "rows": 0}
    per_capture = {}

    for payload in PAYLOADS:
        doc = json.loads(payload.read_text(), parse_float=Decimal)
        for c in doc["captures"]:
            if c.get("observed") is None:
                print(f"{c['id']:<14} {c['inputs']['repaymentFrequencyType']:<7} "
                      f"{c['inputs']['repaymentEvery']:>5}      -   "
                      f"THREW: {c['error']}")
                per_capture[c["id"]] = "THREW -- no ratio exists"
                continue
            unit = c["inputs"]["repaymentFrequencyType"]
            every = c["inputs"]["repaymentEvery"]
            start = d(c["inputs"]["scheduleGenerationStartDate"])
            sep = {"R1": 0, "R3": 0, "R4": 0}
            rows = 0
            for p in c["observed"]["periods"]:
                if p["type"] != "REPAYMENT":
                    continue
                rows += 1
                totals["rows"] += 1
                f, du = d(p["fromDate"]), d(p["dueDate"])
                r2 = period_ratio(start, f, du, unit, every, "R2")
                r3 = period_ratio(start, f, du, unit, every, "R3")
                r4 = period_ratio(start, f, du, unit, every, "R4")
                r1 = Decimal(every)
                v = []
                if r1 != r2:
                    sep["R1"] += 1
                    totals["R1"] += 1
                    v.append("R1 separated")
                if r3 != r2:
                    sep["R3"] += 1
                    totals["R3"] += 1
                    v.append("R3 separated")
                if r4 != r2:
                    sep["R4"] += 1
                    totals["R4"] += 1
                    v.append("R4 separated")
                if v:
                    print(f"{c['id']:<14} {unit:<7} {every:>5} {p['periodNumber']:>6} "
                          f"{str(r1):>9} {str(r2):>22} {str(r3):>22} {str(r4):>22}  "
                          + ", ".join(v))
            per_capture[c["id"]] = (f"{rows} periods; separates R1 on {sep['R1']}, "
                                    f"R3 on {sep['R3']}, R4 on {sep['R4']}")

    print()
    print("per-capture summary")
    for k in per_capture:
        print(f"  {k:<14} {per_capture[k]}")
    print()
    print(f"TOTALS over {totals['rows']} repayment periods in both T46 passes:")
    print(f"  periods where R1 (RepaymentEvery) differs from the pinned R2 : {totals['R1']}")
    print(f"  periods where R3 (no month-end special case) differs from R2 : {totals['R3']}")
    print(f"  periods where R4 (naive whole-units, no special case) != R2  : {totals['R4']}")


if __name__ == "__main__":
    main()
