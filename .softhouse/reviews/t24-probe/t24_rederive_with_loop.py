#!/usr/bin/env python3
"""
T24 — re-derivation of the PROGRESSIVE schedule INCLUDING the EMI re-adjust loop.

Purpose: T23 (.softhouse/reviews/T23-DEC-1-v2-rereview.md §6.1) showed that
checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods runs on EVERY generation and changes the
answer on 7 of 10 ordinary graded-domain requests. Its own model deliberately OMITS the loop.
This model INCLUDES it, so that the normative text T24 writes into DEC-1 §4.3 can be checked
against the oracle rather than asserted.

Every step cites the pinned checkout 426a23544e8426a38ae43ae404670a0a7e85b9eb.
Paths (as they exist in that checkout):
  PEC  = fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/
         ProgressiveEMICalculator.java
  EA   = .../loanproduct/calc/data/EmiAdjustment.java
  RP   = .../loanproduct/calc/data/RepaymentPeriod.java
  M    = fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java
  DSDG = .../loanaccount/loanschedule/domain/DefaultScheduledDateGenerator.java

Pre-loop schedule (unchanged from what DEC-1 §2.1/§4.1/§4.3 already specifies):
  dates        DSDG:128-131 (step) + :168-176 (re-anchor to the seed = disbursement date,
               LoanApplicationTerms.java:583-589)
  rate         PEC:1318-1320   rate/100 under mc
  rate factor  PEC:1956-1958 fraction = daysInMonth*repayEvery/daysInYear (mc)
               PEC:1959-1962 rate*fraction*actual/calc (mc) then .setScale(precision, mode)
  1+rf         RP:216-218 EXACT
  prod, fn     PEC:1816-1820, :1822-1828 / :1991-1993
  EMI          PEC:1838-1841 prod*balance/fn (mc) then currency scale (M:52)
  split        interest = balance*rf at currency scale, capped at EMI; principal = EMI - interest
               clamped at 0 (RP:272-286, :345-350); balance roll-forward clamped at 0 (RP:389-403)
  residual     PEC:1202-1203 diff = disbursed + dueInterest - totalEMI, each sum at currency scale
               PEC:1205/:1210 lastEmi += diff

EMI re-adjust loop (PEC:1258-1308, called unconditionally from PEC:749 inside
calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod when
onlyOnActualModelShouldApply, which is true for a fresh generation because scheduleModel.isEmpty()
— PEC:733-735):

  do (at most 3 iterations, PEC:1262 adjustCounter=1 .. PEC:1307 while adjustCounter <= 3):
    a = getEmiAdjustment(periods)                                        PEC:1778-1789
        on a fresh schedule nothing is paid, so the scan at PEC:1779-1786 stops at the LAST
        period: originalEmi = penultimate period's EMI, emiDifference = last EMI - penultimate EMI
        (which on a fresh schedule is exactly the residual `diff` above),
        uncountablePeriods = 0 (PEC:2027-2031: count of periods whose totalPaidAmount exceeds
        originalEmi; nothing is paid).
    if !a.shouldBeAdjusted(): break                                      EA:31-36
        lowerHalf = floor(n/2.0) where n = number of related repayment periods
        guard = lowerHalf > 0 && emiDifference != 0
                && |emiDifference| * 100  >  Money(amount = lowerHalf)
        NOTE Money.copy(double) (M:220-222 -> M:216-218) REPLACES the amount; it does not scale
        it. So the right-hand side is floor(n/2) CURRENCY UNITS, and the guard has no dependence
        whatever on installmentAmountInMultiplesOf.
    adjusted = applyInstallmentAmountInMultiplesOf(model, a.adjustedEmi())  PEC:1270, :1761-1766
        multiple null/0 -> identity. a.adjustedEmi() = originalEmi + emiDifference/max(1, n-0)
        (EA:38-44; Money.dividedBy(long) M:352-358 divides under the tenant MathContext and
        returns through Money.of, so the quotient lands at currency scale).
    if adjusted == originalEmi: break                                    PEC:1271-1273
    recompute the whole schedule on a deep copy with EMI := adjusted on every period
                                                                        PEC:1275-1288
    if !newGap.hasLessEmiDifference(a): break                            PEC:1289-1291 / EA:46-48
        i.e. adopt only if |new residual| < |old residual|, strictly.
    adopt the new model's EMIs into the actual model                     PEC:1293-1305

This file prints only computed values; every oracle number it is compared against is read from a
raw capture file.
"""
from decimal import Decimal, Context, ROUND_HALF_UP, ROUND_HALF_EVEN
import calendar
import datetime

PRECISION = 19
MODE = ROUND_HALF_UP
CTX = Context(prec=PRECISION, rounding=MODE)


def money(x, digits=2):
    """M:52 — setScale(currency decimal places, tenant rounding mode)."""
    return Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=MODE)


def mul(a, b):
    return CTX.multiply(Decimal(a), Decimal(b))


def div(a, b):
    return CTX.divide(Decimal(a), Decimal(b))


def add_mc(a, b):
    return CTX.add(Decimal(a), Decimal(b))


def set_scale(x, scale):
    return Decimal(x).quantize(Decimal(1).scaleb(-scale), rounding=MODE)


def plus_months(d, n):
    """java.time.LocalDate.plusMonths: clamps the day to the target month's length."""
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def reanchor(d, seed):
    """DSDG:168-176 — monthly only."""
    if seed.day > 28 and d.day >= 28:
        return datetime.date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def due_dates(start, seed, n, every=1):
    out = []
    cur = start
    for _ in range(n):
        cur = reanchor(plus_months(cur, every), seed)
        out.append(cur)
    return out


def rate_factors(dates, annual_rate_pct, every=1, days_in_month=30, days_in_year=360):
    rate = div(Decimal(str(annual_rate_pct)), Decimal(100))          # PEC:1318-1320
    out = []
    for i in range(len(dates) - 1):
        actual = Decimal((dates[i + 1] - dates[i]).days)
        calc = actual
        frac = div(mul(Decimal(days_in_month), Decimal(every)), Decimal(days_in_year))   # PEC:1956-1958
        rf = div(mul(mul(rate, frac), actual), calc)                                     # PEC:1959-1962
        out.append(set_scale(rf, PRECISION))
    return out


def level_emi(principal, rfs, digits=2):
    plus1 = [Decimal(1) + r for r in rfs]                 # RP:216-218 EXACT
    prod = Decimal(1)                                     # PEC:1816-1820
    for p in plus1:
        prod = mul(prod, p)
    fn = Decimal(1)                                       # PEC:1822-1828 / :1991-1993
    for p in plus1[1:]:
        fn = add_mc(Decimal(1), mul(fn, p))
    return money(div(mul(prod, Decimal(principal)), fn), digits)


def schedule_with_emi(principal, rfs, emi, digits=2):
    """Split the schedule under an IMPOSED level installment, then compute the residual.

    Returns (rows, diff) where rows[-1]['emi'] already carries the residual.
    """
    balance = money(Decimal(principal), digits)
    rows = []
    for rf in rfs:
        interest = money(mul(balance, rf), digits)
        if interest > emi:
            interest = emi
        principal_part = emi - interest
        if principal_part < 0:
            principal_part = Decimal(0).quantize(Decimal(1).scaleb(-digits))
        new_balance = balance - principal_part
        if new_balance < 0:
            new_balance = Decimal(0).quantize(Decimal(1).scaleb(-digits))
        rows.append({"emi": emi, "interest": interest, "principal": principal_part,
                     "balance": new_balance})
        balance = new_balance

    total_interest = sum((r["interest"] for r in rows), money(0, digits))
    total_emi = sum((r["emi"] for r in rows), money(0, digits))
    diff = money(Decimal(principal) + total_interest - total_emi, digits)   # PEC:1202-1203

    rows[-1]["emi"] = money(rows[-1]["emi"] + diff, digits)                 # PEC:1205/:1210
    rows[-1]["principal"] = rows[-1]["emi"] - rows[-1]["interest"]          # RP:345-350
    if rows[-1]["principal"] < 0:
        rows[-1]["principal"] = money(0, digits)
    prev_balance = rows[-2]["balance"] if len(rows) > 1 else money(Decimal(principal), digits)
    rows[-1]["balance"] = max(money(0, digits), prev_balance - rows[-1]["principal"])
    return rows, diff


def guard_fires(emi_difference, n, digits=2):
    """EA:31-36. |emiDifference| * 100 > Money(floor(n/2)).

    multipliedBy(100) is M:380-388 under the tenant MathContext; copy(double) is M:220-222,
    which REPLACES the amount, so the threshold is floor(n/2) whole currency units.
    """
    lower_half = Decimal(n // 2)                       # Math.floor(n / 2.0)
    if lower_half <= 0 or emi_difference == 0:
        return False
    lhs = money(mul(abs(emi_difference), Decimal(100)), digits)
    rhs = money(lower_half, digits)
    return lhs > rhs


def adjustment(emi_difference, n, digits=2):
    """EA:38-40 — emiDifference.dividedBy(max(1, n - uncountablePeriods)); uncountable = 0 fresh.

    M:352-358: divide under the tenant MathContext, then Money.of -> currency scale.
    """
    d = max(1, n)
    if d == 1:
        q = Decimal(emi_difference)
    else:
        q = div(Decimal(emi_difference), Decimal(d))
    return money(q, digits)


def derive(principal, n, annual_rate_pct, start, seed=None, digits=2,
           every=1, days_in_month=30, days_in_year=360, apply_loop=True, trace=False):
    seed = seed or start
    dates = [start] + due_dates(start, seed, n, every)
    rfs = rate_factors(dates, annual_rate_pct, every, days_in_month, days_in_year)

    emi = level_emi(principal, rfs, digits)
    rows, diff = schedule_with_emi(principal, rfs, emi, digits)

    steps = []
    if apply_loop:
        counter = 1
        while counter <= 3:                                       # PEC:1262, :1307
            original_emi = emi                                    # penultimate period's EMI
            emi_difference = diff                                 # last EMI - penultimate EMI
            if not guard_fires(emi_difference, n, digits):        # PEC:1267-1269 / EA:31-36
                steps.append(("break:guard", str(emi), str(emi_difference)))
                break
            candidate = money(original_emi + adjustment(emi_difference, n, digits), digits)
            if candidate == original_emi:                         # PEC:1271-1273
                steps.append(("break:no-change", str(emi), str(emi_difference)))
                break
            new_rows, new_diff = schedule_with_emi(principal, rfs, candidate, digits)
            if not (abs(new_diff) < abs(emi_difference)):         # PEC:1289-1291 / EA:46-48
                steps.append(("break:not-better", str(candidate), str(new_diff)))
                break
            emi, rows, diff = candidate, new_rows, new_diff       # PEC:1293-1305
            steps.append(("adopt", str(candidate), str(new_diff)))
            counter += 1

    out = {
        "emi": emi,
        "rows": [dict(r, **{"from": dates[i], "due": dates[i + 1]}) for i, r in enumerate(rows)],
        "diff": diff,
        "total_interest": sum((r["interest"] for r in rows), money(0, digits)),
        "total_repayment": sum((r["emi"] for r in rows), money(0, digits)),
        "term_days": (dates[-1] - dates[0]).days,
        "loop": steps,
    }
    if trace:
        out["trace"] = steps
    return out
