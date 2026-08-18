#!/usr/bin/env python3
"""
T26 independent re-derivation of the Fineract progressive-loan schedule,
INCLUDING the EMI re-adjust smoothing loop
`ProgressiveEMICalculator.checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`.

NOT RUN AGAINST A LIVE ORACLE. No Fineract instance is reachable in this
sandbox (no Docker, no PostgreSQL on :5432). Every number this script emits is
a re-derivation FROM THE PINNED SOURCE at commit 426a23544. Where the script
prints an "ORACLE" line, that value is quoted from an observation ALREADY
COMMITTED by task T23 at
`.softhouse/reviews/t23-probe/t23-probe2-output.txt`; nothing here is a new
observation and nothing here may be promoted to a vector.

Written from scratch for T26. It deliberately does NOT reuse
`.softhouse/capture/out/t21-probe-rederive.py` (T23 found that script's guard
model defective) nor `.softhouse/reviews/t23-probe/t23_rederive.py`.

Source of every rule modelled below (pinned checkout, PROGRESSIVE generator):

  rate factor          ProgressiveEMICalculator.java:1950-1963
                       (four mc-qualified ops, then setScale(precision) -> a
                       DECIMAL-PLACE quantization, not a significant-digit one)
  1 + rateFactor       RepaymentPeriod.java:216-218  (exact BigDecimal.add,
                       no MathContext)
  product of (1+rf)    ProgressiveEMICalculator.java:1816-1820 (multiply at mc)
  fn recurrence        ProgressiveEMICalculator.java:1822-1828, :1991-1993
                       fn1 = 1; fn_k = 1 + fn_{k-1} * (1 + rf_k)
                       (.skip(1) => the recurrence is applied n-1 times)
  EMI                  ProgressiveEMICalculator.java:1838-1841
                       prod * balance / fn, at mc, then Money scale 2
  per-period interest  InterestPeriod.java:145-158  balance * rf / L * L at mc
  interest cap         RepaymentPeriod.java:272-286 (min with the EMI)
  principal            RepaymentPeriod.java:345-350 (balancing, clamped >= 0)
  final residual       ProgressiveEMICalculator.java:1160-1219, diff at
                       :1202-1203, applied at :1205
  re-adjust loop       ProgressiveEMICalculator.java:1258-1308
  loop guard           EmiAdjustment.java:31-36 + Money.copy(double)
                       (Money.java:220-222 REPLACES the amount)
  adjustment magnitude EmiAdjustment.java:38-40  emiDifference / max(1, n - u)
                       via Money.dividedBy(long) (Money.java:352-358)
  adoption test        EmiAdjustment.java:46-48  |new diff| < |old diff|
  iteration cap        ProgressiveEMICalculator.java:1307-1308 (adjustCounter<=3)

Production MathContext is (19, HALF_UP) -- MoneyHelper.java:35, :91-93.
"""

from decimal import Decimal, localcontext, ROUND_HALF_UP
from datetime import date
import calendar

PRECISION = 19
ROUNDING = ROUND_HALF_UP
MINOR_DIGITS = 2
CENT = Decimal(1).scaleb(-MINOR_DIGITS)


def money(x):
    """Money(currency, amount, mc) -> setScale(decimalPlaces, mode). Money.java:52."""
    return x.quantize(CENT, rounding=ROUNDING)


def mc(f):
    """Run f under the oracle's threaded MathContext (19, HALF_UP)."""
    with localcontext() as ctx:
        ctx.prec = PRECISION
        ctx.rounding = ROUNDING
        return f()


def add_months_clamped(d, k):
    """LocalDate.plusMonths -- DefaultScheduledDateGenerator.java:320-321."""
    m = d.month - 1 + k
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def month_end_reanchor(d, seed):
    """DefaultScheduledDateGenerator.java:168-176 (monthly arm only)."""
    if seed.day > 28 and d.day >= 28:
        return date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def due_dates(start, seed, n, every=1):
    """DefaultScheduledDateGenerator.java:55-73 -- contiguous periods,
    FromDate_1 == scheduleStartDate."""
    out = []
    last = start
    for _ in range(n):
        nxt = month_end_reanchor(add_months_clamped(last, every), seed)
        out.append((last, nxt))
        last = nxt
    return out


def rate_factor(annual_pct, actual_days, calc_days):
    """ProgressiveEMICalculator.java:1318-1320 then :1950-1963, fixed 30/360."""
    def go():
        nominal = Decimal(annual_pct) / Decimal(100)
        frac = (Decimal(30) * Decimal(1)) / Decimal(360)
        v = nominal * frac
        v = v * Decimal(actual_days)
        v = v / Decimal(calc_days)
        return v
    v = mc(go)
    # setScale(mc.getPrecision(), mc.getRoundingMode()) -- a SCALE, not a precision
    return v.quantize(Decimal(1).scaleb(-PRECISION), rounding=ROUNDING)


def level_emi(principal, rfs):
    """ProgressiveEMICalculator.java:1816-1841."""
    plus1 = [Decimal(1) + r for r in rfs]          # exact, RepaymentPeriod.java:216-218

    def prod():
        acc = Decimal(1)
        for v in plus1:
            acc = acc * v
        return acc

    def fn():
        acc = Decimal(1)
        for v in plus1[1:]:                        # .skip(1)
            acc = Decimal(1) + acc * v
        return acc

    p = mc(prod)
    f = mc(fn)
    return money(mc(lambda: p * principal / f))


def split(principal, rfs, emis, lengths):
    """Per-period interest-first / principal-balancing split.
    InterestPeriod.java:145-158; RepaymentPeriod.java:272-286, :345-350, :389-403."""
    bal = money(principal)
    rows = []
    for rf, emi, L in zip(rfs, emis, lengths):
        calc_int = money(mc(lambda: bal * rf / Decimal(L) * Decimal(L)))
        due_int = min(calc_int, emi)
        due_prin = max(Decimal(0), emi - due_int)
        bal = max(Decimal(0), bal - due_prin)
        rows.append({"principal": due_prin, "interest": due_int, "emi": emi, "outstanding": bal})
    return rows


def apply_residual(principal, rows):
    """ProgressiveEMICalculator.java:1160-1219. diff at :1202-1203, applied :1205.
    Target is the last not-fully-paid period = the last one on a fresh schedule."""
    total_int = sum((r["interest"] for r in rows), Decimal(0))
    total_emi = sum((r["emi"] for r in rows), Decimal(0))
    diff = money(principal) + total_int - total_emi
    rows[-1]["emi"] = rows[-1]["emi"] + diff
    return diff


def rebuild(principal, rfs, emis, lengths):
    rows = split(principal, rfs, emis, lengths)
    apply_residual(principal, rows)
    # re-split only the last row: its EMI moved, interest is unchanged
    last = rows[-1]
    last["principal"] = max(Decimal(0), last["emi"] - last["interest"])
    prev_bal = rows[-2]["outstanding"] if len(rows) > 1 else money(principal)
    last["outstanding"] = max(Decimal(0), prev_bal - last["principal"])
    return rows


def should_be_adjusted(rows):
    """EmiAdjustment.shouldBeAdjusted -- EmiAdjustment.java:31-36.

    lowerHalf = floor(n / 2.0)                    (n = number of RELATED periods)
    fires iff lowerHalf > 0
          AND emiDifference != 0
          AND |emiDifference| * 100  >  Money(amount = lowerHalf)

    Money.copy(double) REPLACES the amount (Money.java:220-222), so the
    right-hand side is `lowerHalf` CURRENCY UNITS flat -- it does NOT scale
    the EMI. In int64 minor units the test is
        |lastEMI - penultEMI|_minor * 100 > floor(n/2) * 10^MINOR_DIGITS
    """
    n = len(rows)
    lower_half = n // 2
    emi_diff = rows[-1]["emi"] - rows[-2]["emi"] if n > 1 else Decimal(0)
    fires = lower_half > 0 and emi_diff != 0 and abs(emi_diff) * 100 > Decimal(lower_half)
    return fires, emi_diff, rows[-2]["emi"] if n > 1 else rows[-1]["emi"]


def readjust_loop(principal, rfs, lengths, rows, verbose=True):
    """checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods -- :1258-1308.

    NOTE FOR THE REVIEW: none of the body modelled below is specified in
    DEC-1 revision 3 or in contract.go. Only the GUARD is. This function is
    written from the Java source, not from the contract.
    """
    n = len(rows)
    counter = 1
    while counter <= 3:
        fires, emi_diff, original = should_be_adjusted(rows)
        if not fires:
            if verbose:
                print(f"    iter {counter}: guard does not fire "
                      f"(|diff|={abs(emi_diff)} x100={abs(emi_diff)*100} vs {n//2})")
            break
        # uncountablePeriods == 0 on a freshly generated (unpaid) schedule
        # -- ProgressiveEMICalculator.java:2027-2031
        divisor = max(1, n - 0)
        adjustment = money(mc(lambda: emi_diff / Decimal(divisor)))   # Money.dividedBy(long)
        adjusted = original + adjustment                              # EmiAdjustment.adjustedEmi
        # applyInstallmentAmountInMultiplesOf is a no-op at multiple == null/0
        if adjusted == original:
            if verbose:
                print(f"    iter {counter}: adjusted == original, break")
            break
        new_rows = rebuild(principal, rfs, [adjusted] * n, lengths)
        _, new_diff, _ = should_be_adjusted(new_rows)
        if not (abs(new_diff) < abs(emi_diff)):                       # hasLessEmiDifference
            if verbose:
                print(f"    iter {counter}: new |diff|={abs(new_diff)} not < "
                      f"{abs(emi_diff)}, break (adjustment discarded)")
            break
        if verbose:
            print(f"    iter {counter}: guard FIRES |diff|={abs(emi_diff)}; "
                  f"EMI {original} -> {adjusted}; new |diff|={abs(new_diff)}")
        rows = new_rows
        counter += 1
    return rows


def generate(principal_major, n, annual_pct, start=date(2024, 1, 1), with_loop=True, verbose=True):
    principal = Decimal(principal_major)
    periods = due_dates(start, start, n)
    lengths = [(d - f).days for f, d in periods]
    rfs = [rate_factor(annual_pct, L, L) for L in lengths]
    emi = level_emi(principal, rfs)
    rows = rebuild(principal, rfs, [emi] * n, lengths)
    if with_loop:
        rows = readjust_loop(principal, rfs, lengths, rows, verbose=verbose)
    return rows


def report(principal_major, n, annual_pct, oracle_note):
    print(f"\n=== MNT {principal_major} / {n} x {annual_pct}% ===")
    no_loop = generate(principal_major, n, annual_pct, with_loop=False, verbose=False)
    print(f"  WITHOUT the re-adjust loop: level EMI {no_loop[0]['emi']}, "
          f"final EMI {no_loop[-1]['emi']}, total interest "
          f"{sum((r['interest'] for r in no_loop), Decimal(0))}")
    print("  WITH the re-adjust loop:")
    looped = generate(principal_major, n, annual_pct, with_loop=True, verbose=True)
    print(f"  -> level EMI {looped[0]['emi']}, final EMI {looped[-1]['emi']}, "
          f"total interest {sum((r['interest'] for r in looped), Decimal(0))}")
    print(f"  ORACLE (committed T23 observation, NOT taken by T26): {oracle_note}")


if __name__ == "__main__":
    print(__doc__)
    print("=" * 78)
    print("Re-derivation only. No live oracle was contacted.")
    print("=" * 78)

    # Fineract's own shipped conformance shape.
    report(100, 6, "7.0", "final installment 17.00 after a -0.01 residual")

    # The two cases DEC-1 rev 3 sec 4.3 cites as tripping the guard.
    report(1014632, 6, "7.0",
           "level 172574.64, final 172574.62, total interest 20815.82 "
           "(t23-probe2-output.txt line 4)")
    report(127704, 36, "16.8",
           "level 4540.30, final 4540.06, total interest 35746.56 "
           "(t23-probe2-output.txt line 12)")
