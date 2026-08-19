"""
T34 -- independent re-review of DEC-1 revision 6.

A transcription of DEC-1 revision 6 (docs/adr/DEC-1-schedule-generator-adapter.md,
merge 3a30154) into a runnable model, written from the DOCUMENT TEXT ALONE.
It is deliberately NOT written from the Fineract source and NOT from any earlier
review's probe: the experiment the document itself proposes is "the text alone,
with nothing else supplied, determines the money".

*** NO LIVE ORACLE WAS CONTACTED BY THIS TASK.  NOTHING PRODUCED HERE IS AN
*** OBSERVATION.  Every number this file computes is a RE-DERIVATION.

Exact arithmetic only: Decimal with an explicit context, and integer minor units.
No float appears anywhere on a money path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
import calendar

# --- the tenant MathContext ------------------------------------------------
# DEC-1 4.1: the production MathContext is (19, HALF_UP); RateFactorScale == SignificantDigits.
SIG = 19
RATE_FACTOR_SCALE = 19
MINOR_DIGITS = 2
MINOR = 10 ** MINOR_DIGITS


def round_mc(x: Decimal, sig: int = SIG) -> Decimal:
    """Round to `sig` SIGNIFICANT decimal digits under HALF_UP (DEC-1 4.1)."""
    with localcontext() as ctx:
        ctx.prec = sig
        ctx.rounding = ROUND_HALF_UP
        return +x


def set_scale(x: Decimal, scale: int) -> Decimal:
    """setScale(scale, HALF_UP) -- a DECIMAL-PLACE quantization (DEC-1 4.1)."""
    return x.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)


def to_minor(x: Decimal) -> int:
    """Currency layer: a quantity becomes money when it is scaled to
    Currency.MinorUnitDigits decimal places under Mode (DEC-1 4.1)."""
    return int(set_scale(x, MINOR_DIGITS) * MINOR)


def days(a: date, b: date) -> int:
    return (b - a).days


# --- 4.2 the month-end date rule -------------------------------------------

def add_months_clamped(d: date, k: int) -> date:
    """Step 1: add k calendar months, clamping the day to the target month's length."""
    y = d.year + (d.month - 1 + k) // 12
    m = (d.month - 1 + k) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def re_anchor(stepped: date, seed: date) -> date:
    """Step 2 (monthly only): if the SEED day > 28 and the stepped day >= 28,
    set the day to min(days in target month, seed day)."""
    if seed.day > 28 and stepped.day >= 28:
        return date(stepped.year, stepped.month,
                    min(calendar.monthrange(stepped.year, stepped.month)[1], seed.day))
    return stepped


def repayment_boundaries(start: date, seed: date, n: int, every: int) -> list[tuple[date, date]]:
    """DEC-1 4.2.  Boundaries are stepped from ScheduleStartDate; the month-end
    seed is the DISBURSEMENT date."""
    out = []
    prev = start
    for _ in range(n):
        nxt = re_anchor(add_months_clamped(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# --- 4.1 / 4.1.1 the rate factor -------------------------------------------

def rate_factor(rate_pct: Decimal, multiplier: Decimal,
                span_from: date, span_due: date,
                rp_from: date, rp_due: date) -> Decimal:
    """DEC-1 4.1's snippet plus 4.1.1's day counts, transcribed literally:

        interestFractionPerPeriod = 30 .multiply(<multiplier>, mc) .divide(360, mc)
        return rate .multiply(fraction, mc) .multiply(actual, mc)
                    .divide(calculated, mc) .setScale(RateFactorScale, mode)

    4.1.1: actual     = days across THE SPAN the factor is computed over
           calculated = days of the ENCLOSING REPAYMENT PERIOD
           guard: exactly ZERO when calculated == 0

    DEC-1 4.3.2 writes `<multiplier>` as `RepaymentEvery` for BOTH call sites.
    `multiplier` is a parameter here so that the alternative reading this review
    tests can be swept against it.
    """
    calculated = days(rp_from, rp_due)
    if calculated == 0:
        return Decimal(0)
    actual = days(span_from, span_due)
    rate = round_mc(rate_pct / Decimal(100))
    frac = round_mc(round_mc(Decimal(30) * multiplier) / Decimal(360))
    x = round_mc(rate * frac)
    x = round_mc(x * Decimal(actual))
    x = round_mc(x / Decimal(calculated))
    return set_scale(x, RATE_FACTOR_SCALE)


# --- the schedule model ----------------------------------------------------

@dataclass
class InterestPeriod:
    frm: date
    due: date
    rp_from: date
    rp_due: date
    disbursed_minor: int = 0
    rate_factor: Decimal = Decimal(0)
    rate_factor_till_due: Decimal = Decimal(0)

    @property
    def length(self) -> int:
        return days(self.frm, self.due)

    @property
    def length_till_period_due(self) -> int:
        return days(self.frm, self.rp_due)


@dataclass
class RepaymentPeriod:
    frm: date
    due: date
    interest_periods: list[InterestPeriod] = field(default_factory=list)
    emi_minor: int = 0
    interest_minor: int = 0
    principal_minor: int = 0
    outstanding_minor: int = 0

    @property
    def growth_factor(self) -> Decimal:
        """DEC-1 2.1 (revision 6, P1-T32-1): g = 1 + the SUM of the interest
        periods' rate factors, every addition EXACT."""
        g = Decimal(1)
        for ip in self.interest_periods:
            g = g + ip.rate_factor
        return g


@dataclass
class Request:
    start: date
    disb: date
    principal_minor: int
    n: int
    rate_pct: Decimal
    every: int = 1


def segment(req: Request) -> list[RepaymentPeriod]:
    """Boundaries + DEC-1 4.3.2's interest-period segmentation."""
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    periods = [RepaymentPeriod(f, d) for f, d in bounds]
    for p in periods:
        p.interest_periods = [InterestPeriod(p.frm, p.due, p.frm, p.due)]

    D = req.disb
    target = None
    for idx, p in enumerate(periods):
        inside = (p.frm <= D <= p.due) if idx == 0 else (p.frm < D <= p.due)
        if inside:
            target = idx
            break
    if target is None:
        raise ValueError("disbursement outside every repayment period")

    p = periods[target]
    if D == p.frm:
        p.interest_periods = [
            InterestPeriod(p.frm, p.frm, p.frm, p.due, disbursed_minor=req.principal_minor),
            InterestPeriod(p.frm, p.due, p.frm, p.due),
        ]
    elif D == p.due:
        p.interest_periods[0].disbursed_minor = req.principal_minor
    else:
        p.interest_periods = [
            InterestPeriod(p.frm, D, p.frm, p.due, disbursed_minor=req.principal_minor),
            InterestPeriod(D, p.due, p.frm, p.due),
        ]
    return periods, target


def apply_rate_factors(req: Request, periods, multipliers=None) -> None:
    """multipliers[i] overrides the `rateFactorTillPeriodDueDate` multiplier for
    repayment period i.  None means DEC-1 4.3.2's normative `RepaymentEvery`."""
    for idx, p in enumerate(periods):
        m_till = Decimal(req.every) if multipliers is None else multipliers[idx]
        for ip in p.interest_periods:
            ip.rate_factor = rate_factor(req.rate_pct, Decimal(req.every),
                                         ip.frm, ip.due, p.frm, p.due)
            ip.rate_factor_till_due = rate_factor(req.rate_pct, m_till,
                                                  ip.frm, p.due, p.frm, p.due)


def first_related(req: Request, periods, target: int) -> int:
    """DEC-1 4.3.1: index of the first RELATED repayment period."""
    if periods[target].due == req.disb:
        eff = periods[target + 1].due if target + 1 < len(periods) else periods[target].due
    else:
        eff = periods[target].due
    for idx, p in enumerate(periods):
        if not (p.due < eff):
            return idx
    raise ValueError("no related period")


def level_installment(periods, first_rel: int, balance_minor: int) -> int:
    """DEC-1 2.1: fn1 = 1, fn_k = 1 + fn_{k-1} * g_k; installment = prod(g) * balance / fn.
    4.3.1: computed over the RELATED periods only."""
    rel = periods[first_rel:]
    fn = Decimal(1)
    prod = Decimal(1)
    for i, p in enumerate(rel):
        g = p.growth_factor
        prod = round_mc(prod * g)
        if i > 0:
            fn = round_mc(Decimal(1) + round_mc(fn * g))
    bal = Decimal(balance_minor) / Decimal(MINOR)
    emi = round_mc(round_mc(prod * bal) / fn)
    return to_minor(emi)


def split_rows(periods, first_rel: int, emi_minor: int) -> None:
    """DEC-1 4.3.2 'From interest period to row', steps 1-4, over every row."""
    balance_minor = 0
    for idx, p in enumerate(periods):
        p.emi_minor = emi_minor if idx >= first_rel else 0
        b = Decimal(balance_minor) / Decimal(MINOR)
        total_t3 = Decimal(0)
        disbursed_here = 0
        for ip in p.interest_periods:
            if ip.length_till_period_due == 0:
                t3 = Decimal(0)
            else:
                t1 = round_mc(b * ip.rate_factor_till_due)
                t2 = round_mc(t1 / Decimal(ip.length_till_period_due))
                t3 = round_mc(t2 * Decimal(ip.length))
            total_t3 += t3
            if ip.disbursed_minor:
                disbursed_here += ip.disbursed_minor
                b = b + Decimal(ip.disbursed_minor) / Decimal(MINOR)
        calc = max(0, to_minor(total_t3))
        p.interest_minor = min(calc, p.emi_minor)
        p.principal_minor = max(0, p.emi_minor - p.interest_minor)
        p.outstanding_minor = max(0, balance_minor + disbursed_here - p.principal_minor)
        balance_minor = p.outstanding_minor


def apply_residual_and_recompute(periods, principal_minor: int) -> None:
    """DEC-1 4.3: diff = disbursed + sum(dueInterest) - sum(installments);
    lastEmi += diff.  Then 4.3.2 step 5: the final row's SPLIT is recomputed."""
    total_interest = sum(p.interest_minor for p in periods)
    total_emi = sum(p.emi_minor for p in periods)
    diff = principal_minor + total_interest - total_emi
    last = periods[-1]
    last.emi_minor += diff
    balance_minor = periods[-2].outstanding_minor if len(periods) > 1 else 0
    b = Decimal(balance_minor) / Decimal(MINOR)
    total_t3 = Decimal(0)
    disbursed_here = 0
    for ip in last.interest_periods:
        if ip.length_till_period_due == 0:
            t3 = Decimal(0)
        else:
            t1 = round_mc(b * ip.rate_factor_till_due)
            t2 = round_mc(t1 / Decimal(ip.length_till_period_due))
            t3 = round_mc(t2 * Decimal(ip.length))
        total_t3 += t3
        if ip.disbursed_minor:
            disbursed_here += ip.disbursed_minor
            b = b + Decimal(ip.disbursed_minor) / Decimal(MINOR)
    calc = max(0, to_minor(total_t3))
    last.interest_minor = min(calc, last.emi_minor)
    last.principal_minor = max(0, last.emi_minor - last.interest_minor)
    last.outstanding_minor = max(0, balance_minor + disbursed_here - last.principal_minor)


def build(req: Request, emi_minor: int, first_rel: int, multipliers=None):
    periods, target = segment(req)
    apply_rate_factors(req, periods, multipliers)
    split_rows(periods, first_rel, emi_minor)
    apply_residual_and_recompute(periods, req.principal_minor)
    return periods


def generate(req: Request, multipliers=None, run_loop: bool = True,
             emi_override: int | None = None):
    periods0, target = segment(req)
    apply_rate_factors(req, periods0, multipliers)
    first_rel = first_related(req, periods0, target)
    emi = emi_override if emi_override is not None else \
        level_installment(periods0, first_rel, req.principal_minor)
    rows = build(req, emi, first_rel, multipliers)
    if not run_loop:
        return rows

    n = len(rows) - first_rel
    adjust_counter = 1
    while True:
        if n < 2:
            break
        original = rows[first_rel + n - 2].emi_minor
        emi_difference = rows[first_rel + n - 1].emi_minor - original
        lower_half = n // 2
        if not (lower_half > 0 and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * MINOR):
            break
        d = max(1, n)                       # uncountablePeriods == 0 here
        sgn = 1 if emi_difference > 0 else -1
        adjustment = sgn * ((2 * abs(emi_difference) + d) // (2 * d))
        adjusted = original + adjustment
        if adjusted == original:
            break
        trial = build(req, adjusted, first_rel, multipliers)
        new_difference = (trial[first_rel + n - 1].emi_minor
                          - trial[first_rel + n - 2].emi_minor)
        if not (abs(new_difference) < abs(emi_difference)):
            break
        rows = trial
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return rows


def totals(rows):
    ti = sum(p.interest_minor for p in rows)
    tp = sum(p.principal_minor for p in rows)
    return tp, ti, tp + ti


def m2s(v: int) -> str:
    neg = v < 0
    a = abs(v)
    return ("-" if neg else "") + f"{a // MINOR}.{a % MINOR:02d}"
