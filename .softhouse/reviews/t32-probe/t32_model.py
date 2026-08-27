#!/usr/bin/env python3
"""T32 -- an INDEPENDENT transcription of DEC-1 revision 5 into a runnable model.

WRITTEN FROM THE DOCUMENT TEXT (docs/adr/DEC-1-schedule-generator-adapter.md
revision 5 + nexus/.../contract.go).  It deliberately does NOT reuse
.softhouse/capture/out/t21-probe-rederive.py (retracted), t29_rederive.py or
t31_spec_check.py.

*** NO LIVE ORACLE WAS CONTACTED.  Nothing in this file is an observation. ***
Every expected value used by t32_validate.py is quoted from a capture file
already committed under .softhouse/reviews/t23-probe/.

All money is exact-decimal / integer minor units.  There is no float anywhere.

--------------------------------------------------------------------------
WHERE THE TEXT IS SILENT (recorded, because that is the experiment's output)
--------------------------------------------------------------------------
G-1  DEC-1 section 4.1 prints the oracle's rate-factor snippet with the names
     `actualDaysInPeriod` and `calculatedDaysInPeriod` and NEVER DEFINES EITHER.
     Section 4.3.2 says only "the section 4.1 rate factor computed over
     [interest period FromDate, repayment period DueDate]".  contract.go
     (DayCountFixed30Over360) additionally asserts the ratio is "exactly 1 ...
     every period in the graded domain".  Two readings therefore exist:
        DAYS_TEXT   : both day counts are taken from the span the rate factor
                      is "computed over"  ->  ratio == 1 always
        DAYS_SOURCE : actualDaysInPeriod  = days(interest-period FromDate, span end)
                      calculatedDaysInPeriod = days(REPAYMENT period FromDate,
                                                    REPAYMENT period DueDate)
     They coincide for every shape the corpus samples and DIVERGE for a
     disbursement dated strictly inside a repayment period.  Selected by the
     `days_reading` argument.
G-2  The text never says how a repayment period carrying MORE THAN ONE interest
     period contributes a single growth factor to the fn recurrence.  Modelled
     as 1 + SUM(rateFactor of each interest period), exact addition.
G-3  The text does not state the rounding of the fn recurrence's own addition
     (only that `1 + rateFactor` is exact).  Modelled at the MathContext.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, Context, ROUND_HALF_UP

# ---------------------------------------------------------------- arithmetic

PRECISION = 19          # Rounding.SignificantDigits (production, ratified)
RATE_SCALE = 19         # Rounding.RateFactorScale   (constrained == above)
MINOR = 2               # Currency.MinorUnitDigits   (MNT / USD)

MC = Context(prec=PRECISION, rounding=ROUND_HALF_UP)   # the threaded MathContext
EXACT = Context(prec=400, rounding=ROUND_HALF_UP)      # "no MathContext at all"


def mul(a: Decimal, b: Decimal) -> Decimal:
    return MC.multiply(a, b)


def div(a: Decimal, b: Decimal) -> Decimal:
    return MC.divide(a, b)


def madd(a: Decimal, b: Decimal) -> Decimal:
    return MC.add(a, b)


def eadd(a: Decimal, b: Decimal) -> Decimal:
    """Exact addition -- DEC-1 4.1: `1 + rateFactor` carries no MathContext."""
    return EXACT.add(a, b)


def set_scale(x: Decimal, s: int) -> Decimal:
    """BigDecimal.setScale(s, HALF_UP)."""
    return EXACT.quantize(x, Decimal(1).scaleb(-s))


def money(x: Decimal) -> Decimal:
    """Money.of(currency, x, mc) -- the constructor's setScale(decimals, mode)."""
    return set_scale(x, MINOR)


ZERO = Decimal(0)
UNIT = Decimal(1).scaleb(-MINOR)          # one minor unit as a decimal


# ------------------------------------------------------------------- dates

def _clamp_add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def due_dates(start: date, n: int, every: int, seed: date) -> list[date]:
    """DEC-1 4.2, monthly only: step-with-clamp, then the seed re-anchor."""
    out = [start]
    for _ in range(n):
        nxt = _clamp_add_months(out[-1], every)
        if seed.day > 28 and nxt.day >= 28:
            nxt = nxt.replace(day=min(calendar.monthrange(nxt.year, nxt.month)[1], seed.day))
        out.append(nxt)
    return out


def days(a: date, b: date) -> int:
    return (b - a).days


# ------------------------------------------------------------------ model

@dataclass
class InterestPeriod:
    frm: date
    due: date
    disbursed: Decimal = ZERO       # amount registered ON this interest period
    balance_in: Decimal = ZERO      # outstandingLoanBalance carried in
    rate_factor: Decimal = ZERO     # for the fn recurrence
    rf_till_due: Decimal = ZERO     # for the interest computation


@dataclass
class RepaymentPeriod:
    frm: date
    due: date
    ips: list[InterestPeriod] = field(default_factory=list)
    emi: Decimal = ZERO
    interest: Decimal = ZERO
    principal: Decimal = ZERO
    outstanding: Decimal = ZERO
    related: bool = False


# ------------------------------------------------------- rate factor (4.1)

def rate_factor(annual_pct: Decimal, span_from: date, span_to: date,
                rp: RepaymentPeriod, days_reading: str) -> Decimal:
    """DEC-1 4.1, fixed 30/360, monthly, RepaymentEvery == 1.

    interestFractionPerPeriod = 30 * repaymentEvery / daysInYear (each op at mc)
    rateFactor = ((rate * fraction) * actualDays / calculatedDays) then
                 setScale(RateFactorScale, mode)
    """
    calculated = (days(span_from, span_to) if days_reading == "text"
                  else days(rp.frm, rp.due))
    if calculated == 0:
        return ZERO
    actual = days(span_from, span_to)
    rate = div(annual_pct, Decimal(100))                       # :1318-1320
    frac = div(mul(Decimal(30), Decimal(1)), Decimal(360))     # 30 * every / 360
    v = mul(rate, frac)
    v = mul(v, Decimal(actual))
    v = div(v, Decimal(calculated))
    return set_scale(v, RATE_SCALE)


# ------------------------------------------------- interest of one row (4.3.2)

def interest_of(ip: InterestPeriod, rp: RepaymentPeriod) -> Decimal:
    ltpdd = days(ip.frm, rp.due)
    if ltpdd == 0:                                             # :146-148
        return ZERO
    b = ip.balance_in                                          # DECLINING_BALANCE :151
    t1 = mul(b, ip.rf_till_due)                                # operation (1)  :155
    t2 = div(t1, Decimal(ltpdd))                               # operation (2)  :156
    t3 = mul(t2, Decimal(days(ip.frm, ip.due)))                # operation (3)  :157
    return t3


def interest_of_textbook(ip: InterestPeriod, rp: RepaymentPeriod) -> Decimal:
    """The reading DEC-1 4.3.2 exists to exclude: one rounded multiplication."""
    if days(ip.frm, rp.due) == 0:
        return ZERO
    return mul(ip.balance_in, ip.rf_till_due)


# ---------------------------------------------------------------- generation

def build_periods(start: date, n: int, every: int, seed: date) -> list[RepaymentPeriod]:
    ds = due_dates(start, n, every, seed)
    return [RepaymentPeriod(frm=ds[i], due=ds[i + 1],
                            ips=[InterestPeriod(ds[i], ds[i + 1])])
            for i in range(n)]


def register_disbursement(rps: list[RepaymentPeriod], d: date, amount: Decimal) -> date:
    """DEC-1 4.3.1 (effective due date) + 4.3.2 (interest-period segmentation).

    Returns the EFFECTIVE DUE DATE.
    """
    # membership: [from, due] inclusive both ends for the FIRST period,
    #             (from, due] for every later one
    idx = None
    for i, rp in enumerate(rps):
        lo_ok = (d >= rp.frm) if i == 0 else (d > rp.frm)
        if lo_ok and d <= rp.due:
            idx = i
            break
    if idx is None:
        raise ValueError("disbursement outside every repayment period")
    rp = rps[idx]

    # segmentation
    hit = next((ip for ip in rp.ips if ip.due == d), None)
    if hit is not None:
        hit.disbursed = EXACT.add(hit.disbursed, amount)
    else:
        prev = [ip for ip in rp.ips if ip.frm <= d][-1]
        original_due = prev.due
        new_due = min(max(d, prev.frm), prev.due)
        prev.due = new_due
        prev.disbursed = EXACT.add(prev.disbursed, amount)
        rp.ips.insert(rp.ips.index(prev) + 1, InterestPeriod(new_due, original_due))

    # effective due date
    if rp.due == d:
        if idx + 1 < len(rps):
            return rps[idx + 1].due
        return rp.due
    return rp.due


def propagate_one(rps: list[RepaymentPeriod], i: int) -> None:
    """InterestPeriod.updateOutstandingLoanBalance for period i, clamped at zero.

    Sequential: period i's balances depend on period i-1's ALREADY COMPUTED
    principal, which is why the split walks the schedule in order.
    """
    rp = rps[i]
    for j, ip in enumerate(rp.ips):
        if j == 0:
            if i == 0:
                ip.balance_in = ZERO
            else:
                prev_rp = rps[i - 1]
                last = prev_rp.ips[-1]
                v = EXACT.add(EXACT.add(last.balance_in, last.disbursed),
                              -prev_rp.principal)
                ip.balance_in = v if v > 0 else ZERO
        else:
            prev = rp.ips[j - 1]
            v = EXACT.add(prev.balance_in, prev.disbursed)
            ip.balance_in = v if v > 0 else ZERO


def propagate_balances(rps: list[RepaymentPeriod]) -> None:
    for i in range(len(rps)):
        propagate_one(rps, i)


def compute_rate_factors(rps: list[RepaymentPeriod], annual_pct: Decimal,
                         days_reading: str) -> None:
    for rp in rps:
        for ip in rp.ips:
            ip.rate_factor = rate_factor(annual_pct, ip.frm, ip.due, rp, days_reading)
            ip.rf_till_due = rate_factor(annual_pct, ip.frm, rp.due, rp, days_reading)


def rate_factor_plus1(rp: RepaymentPeriod) -> Decimal:
    """RepaymentPeriod.calculateRateFactorPlus1 -- 1 + SUM(rf), exact (gap G-2)."""
    acc = Decimal(1)
    for ip in rp.ips:
        acc = eadd(acc, ip.rate_factor)
    return acc


def level_installment(related: list[RepaymentPeriod]) -> Decimal:
    """DEC-1 2.1: the recurrence, then PI(1+rf) * balance / fn."""
    rf_n = Decimal(1)
    for rp in related:
        rf_n = mul(rf_n, rate_factor_plus1(rp))
    fn = Decimal(1)
    for rp in related[1:]:
        fn = madd(Decimal(1), mul(fn, rate_factor_plus1(rp)))
    balance = related[0].ips[0].balance_in
    for ip in related[0].ips:
        balance = EXACT.add(balance, ip.disbursed)
    # initial balance for EMI recalculation = previous outstanding + disbursed here
    if related[0].ips[0].balance_in == ZERO:
        pass
    return money(div(mul(rf_n, balance), fn))


def split(rps: list[RepaymentPeriod], interest_fn) -> None:
    """DEC-1 4.3.2 'From interest period to row', steps 1-4."""
    for i, rp in enumerate(rps):
        propagate_one(rps, i)
        total = ZERO
        for ip in rp.ips:
            total = EXACT.add(total, interest_fn(ip, rp))
        calc = money(total)
        if calc < 0:
            calc = ZERO
        rp.interest = calc if calc < rp.emi else rp.emi        # cap :280
        p = EXACT.add(rp.emi, -rp.interest)                    # :345-350
        rp.principal = p if p > 0 else ZERO
        disbursed_here = ZERO
        for ip in rp.ips:
            disbursed_here = EXACT.add(disbursed_here, ip.disbursed)
        bal_in = rp.ips[0].balance_in
        o = EXACT.add(EXACT.add(bal_in, disbursed_here), -rp.principal)
        rp.outstanding = o if o > 0 else ZERO


def apply_residual(rps: list[RepaymentPeriod], total_disbursed: Decimal) -> None:
    """DEC-1 4.3: diff = SUM disbursed + SUM dueInterest - SUM installments."""
    tot_int = ZERO
    tot_emi = ZERO
    for rp in rps:
        tot_int = EXACT.add(tot_int, rp.interest)
        tot_emi = EXACT.add(tot_emi, rp.emi)
    diff = EXACT.add(EXACT.add(total_disbursed, tot_int), -tot_emi)
    last = rps[-1]
    last.emi = money(EXACT.add(last.emi, diff))


def rebuild(rps: list[RepaymentPeriod], related: list[RepaymentPeriod],
            level: Decimal, total_disbursed: Decimal, interest_fn) -> None:
    for rp in related:
        rp.emi = level
    split(rps, interest_fn)
    apply_residual(rps, total_disbursed)
    split(rps, interest_fn)          # re-derive the last row's split from the new emi


def divide_to_minor(numer: Decimal, d: int) -> Decimal:
    """Money.dividedBy(long): divide at mc, then setScale(minor, HALF_UP).

    DEC-1 4.3.1 consequence 2 gives the exact-integer form; both are exact for
    every amount this contract can express, so the decimal form is used.
    """
    if d == 1:
        return numer
    return money(div(numer, Decimal(d)))


def readjust_loop(rps: list[RepaymentPeriod], related: list[RepaymentPeriod],
                  total_disbursed: Decimal, interest_fn) -> None:
    """DEC-1 4.3.1, steps 1-8, verbatim."""
    n = len(related)
    counter = 1
    while True:
        if n < 2:
            return
        original = related[n - 2].emi
        emi_diff = EXACT.add(related[n - 1].emi, -original)

        lower_half = n // 2
        if not (lower_half > 0 and emi_diff != 0
                and EXACT.multiply(abs(emi_diff), Decimal(100)) > Decimal(lower_half)):
            return

        uncountable = 0                                     # nothing is paid
        d = max(1, n - uncountable)
        adjustment = divide_to_minor(emi_diff, d)
        adjusted = EXACT.add(original, adjustment)          # multiple-rounding = identity
        if adjusted == original:
            return

        import copy as _copy
        trial = _copy.deepcopy(rps)
        trial_related = [rp for rp in trial if rp.related]
        rebuild(trial, trial_related, adjusted, total_disbursed, interest_fn)

        new_diff = EXACT.add(trial_related[n - 1].emi, -trial_related[n - 2].emi)
        if not (abs(new_diff) < abs(emi_diff)):
            return

        for src, dst in zip(trial, rps):
            dst.emi, dst.interest = src.emi, src.interest
            dst.principal, dst.outstanding = src.principal, src.outstanding
            for a, b in zip(src.ips, dst.ips):
                b.balance_in, b.disbursed = a.balance_in, a.disbursed
        related = [rp for rp in rps if rp.related]
        counter += 1
        if counter > 3:
            return


def generate(principal_major: int | Decimal, n: int, annual_pct: str,
             start: date = date(2024, 1, 1), disb: date | None = None,
             days_reading: str = "source", interest_reading: str = "spec"):
    """Return the list of repayment rows, per DEC-1 revision 5."""
    d = disb or start
    amount = Decimal(principal_major)
    rate = Decimal(annual_pct)
    interest_fn = interest_of if interest_reading == "spec" else interest_of_textbook

    rps = build_periods(start, n, 1, d)
    eff_due = register_disbursement(rps, d, amount)
    for rp in rps:
        rp.related = not (rp.due < eff_due)
    related = [rp for rp in rps if rp.related]

    compute_rate_factors(rps, rate, days_reading)
    propagate_balances(rps)

    level = level_installment(related)
    rebuild(rps, related, level, amount, interest_fn)
    readjust_loop(rps, related, amount, interest_fn)
    return rps


def fmt(x: Decimal) -> str:
    return f"{set_scale(x, MINOR):.2f}"


def summarise(rps):
    rel = [rp for rp in rps if rp.emi != 0]
    tot = ZERO
    for rp in rps:
        tot = EXACT.add(tot, rp.interest)
    return (fmt(rel[0].emi) if rel else "0.00", fmt(rps[-1].emi), fmt(tot))
