"""
T38 -- DEC-1 revision 7, transcribed from the DOCUMENT TEXT ALONE.

This file is the from-text spec check the ADR holds itself to: revision 7's
normative sections (2.1, 4.1, 4.1.1 including the new periodRatio subsection,
4.2, 4.3, 4.3.1, 4.3.2 including the corrected step 4 and the three membership
rules) are transcribed here as a runnable model.  Nothing is read from the
Fineract source while writing THIS file; the source re-derivation lives in the
ADR and in t38_periodratio.py.

*** NO LIVE ORACLE WAS CONTACTED BY THIS TASK. ***
Every number this file computes is a RE-DERIVATION.  Every expectation it is
checked against is TRANSCRIBED from a capture file already committed on main.

Exact arithmetic only: `Decimal` under an explicit context, and integer minor
units.  NO float appears anywhere on a money path.

Structural note, disclosed rather than hidden: the dataclass layout, the
`round_mc`/`set_scale`/`to_minor` helpers and the capture-file plumbing follow
the same conventions as `.softhouse/reviews/t34-probe/t34_model.py`, so that the
two models are comparable cell for cell.  Every money rule below was
re-transcribed from revision 7's text, and the four rules revision 7 changes
(periodRatio, the pre-disbursement balance, the [from,due) attachment rule and
the disbursement-row balance) are implemented here and NOT in T34's model.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext

# --- 4.1: the tenant MathContext -------------------------------------------
# The production MathContext is (19, HALF_UP); RateFactorScale == SignificantDigits.
SIG = 19
RATE_FACTOR_SCALE = 19
MINOR_DIGITS = 2
MINOR = 10 ** MINOR_DIGITS


def round_mc(x: Decimal, sig: int = SIG) -> Decimal:
    """Round to `sig` SIGNIFICANT decimal digits under HALF_UP (4.1)."""
    with localcontext() as ctx:
        ctx.prec = sig
        ctx.rounding = ROUND_HALF_UP
        return +x


def set_scale(x: Decimal, scale: int) -> Decimal:
    """setScale(scale, HALF_UP) -- a DECIMAL-PLACE quantization (4.1)."""
    return x.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)


def to_minor(x: Decimal) -> int:
    """The currency layer: a quantity becomes money when it is scaled to
    Currency.MinorUnitDigits decimal places under Rounding.Mode (4.1)."""
    return int(set_scale(x, MINOR_DIGITS) * MINOR)


def days(a: date, b: date) -> int:
    return (b - a).days


# --- 4.2: civil-date stepping ----------------------------------------------

def plus_months(d: date, k: int) -> date:
    """Add k calendar months, clamping the day to the target month's length.
    This is also what `LocalDate.plusMonths` does, and 4.1.1's periodRatio walk
    relies on the same clamping."""
    y = d.year + (d.month - 1 + k) // 12
    m = (d.month - 1 + k) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months_between(a: date, b: date) -> int:
    """Whole months from a to b (ChronoUnit.MONTHS.between), signed, truncated
    toward zero.  Used by 4.1.1's periodRatio."""
    k = (b.year - a.year) * 12 + (b.month - a.month)
    if k > 0 and plus_months(a, k) > b:
        k -= 1
    elif k < 0 and plus_months(a, k) < b:
        k += 1
    return k


def re_anchor(stepped: date, seed: date) -> date:
    """4.2 step 2 (monthly only): if the SEED day > 28 and the stepped day >= 28,
    set the day to min(days in target month, seed day).  The seed is the
    DISBURSEMENT date."""
    if seed.day > 28 and stepped.day >= 28:
        return date(stepped.year, stepped.month,
                    min(calendar.monthrange(stepped.year, stepped.month)[1], seed.day))
    return stepped


def repayment_boundaries(start: date, seed: date, n: int, every: int) -> list[tuple[date, date]]:
    """4.2.  Boundaries are stepped from ScheduleStartDate; the month-end
    re-anchor seed is the DISBURSEMENT date."""
    out = []
    prev = start
    for _ in range(n):
        nxt = re_anchor(plus_months(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# --- 4.1.1: periodRatio (NEW in revision 7) --------------------------------

def calculate_seed_date(schedule_start: date, rp_from: date, rp_due: date, every: int) -> date:
    """4.1.1, `calculateSeedDate`.

    Walk k = 1, 2, ... from ScheduleStartDate until `ScheduleStartDate + k months`
    is NOT before the repayment period's DueDate.  The seed is ScheduleStartDate
    if and only if BOTH:
      (a) that landing date equals the period's DueDate, AND
      (b) landing date MINUS RepaymentEvery months equals the period's FromDate.
    Otherwise the seed is the repayment period's own FromDate.
    """
    k = 1
    while True:
        cand = plus_months(schedule_start, k)
        k += 1
        if not (cand < rp_due):
            break
    if cand == rp_due and plus_months(cand, -every) == rp_from:
        return schedule_start
    return rp_from


def period_ratio(schedule_start: date, rp_from: date, rp_due: date, every: int) -> Decimal:
    """4.1.1, `calculatePeriodRatio` for MONTHS.  Returns an exact Decimal.

    The ONLY MathContext-rounded step is the final division; the addition of the
    whole-period count is exact.
    """
    seed = calculate_seed_date(schedule_start, rp_from, rp_due, every)

    # k: whole months from the seed to the period's FromDate, with the month-end
    # special case -- when FromDate is the last day of its month AND the seed's
    # day-of-month is later than FromDate's, measure to FromDate + 1 day instead.
    last_day_of_from_month = calendar.monthrange(rp_from.year, rp_from.month)[1]
    if last_day_of_from_month == rp_from.day and seed.day > rp_from.day:
        k = months_between(seed, rp_from + timedelta(days=1))
    else:
        k = months_between(seed, rp_from)

    m = k + 1
    cursor = rp_from
    while cursor < rp_due:
        cursor = plus_months(seed, m)
        if not (cursor > rp_due):
            m += 1
        else:
            full = cursor
            m = m - k - 1
            base = plus_months(seed, m)
            frac = round_mc(Decimal(days(base, rp_due)) / Decimal(days(base, full)))
            return frac + Decimal(m)
    return Decimal(m - k - 1)


# --- 4.1 / 4.1.1: the rate factor ------------------------------------------

def rate_factor(rate_pct: Decimal, multiplier: Decimal,
                span_from: date, span_due: date,
                rp_from: date, rp_due: date,
                ratio_one: bool = False) -> Decimal:
    """4.1's snippet with 4.1.1's day counts and multipliers:

        interestFractionPerPeriod = 30 .multiply(<multiplier>, mc) .divide(360, mc)
        return rate .multiply(fraction, mc) .multiply(actual, mc)
                    .divide(calculated, mc) .setScale(RateFactorScale, mode)

    4.1.1: actual     = whole days across THE SPAN the factor is computed over
           calculated = whole days of the ENCLOSING REPAYMENT PERIOD
           guard: exactly ZERO when calculated == 0
           <multiplier> = RepaymentEvery for `rateFactor`
                          periodRatio   for `rateFactorTillPeriodDueDate`
    """
    calculated = days(rp_from, rp_due)
    if calculated == 0:
        return Decimal(0)
    actual = calculated if ratio_one else days(span_from, span_due)
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
        """2.1: g = 1 + the SUM of the interest periods' rate factors, every
        addition EXACT (no MathContext)."""
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
    sig: int = SIG


# --- 4.3.2: the three date-membership rules --------------------------------

def membership_interest_model(D: date, periods, idx: int) -> bool:
    """M1 -- the INTEREST MODEL's balance-change membership.
    [FromDate, DueDate] inclusive at both ends for the FIRST repayment period;
    (FromDate, DueDate] -- from-exclusive, due-inclusive -- for every later one."""
    p = periods[idx]
    return (p.frm <= D <= p.due) if idx == 0 else (p.frm < D <= p.due)


def membership_attachment(D: date, periods, idx: int) -> bool:
    """M3 -- the GENERATOR's disbursement-attachment membership.
    [FromDate, DueDate) -- from-inclusive, DUE-EXCLUSIVE."""
    p = periods[idx]
    return p.frm <= D < p.due


def segment(req: Request):
    """4.2 boundaries + 4.3.2's interest-period segmentation, which uses M1."""
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    periods = [RepaymentPeriod(f, d) for f, d in bounds]
    for p in periods:
        p.interest_periods = [InterestPeriod(p.frm, p.due, p.frm, p.due)]

    D = req.disb
    target = None
    for idx in range(len(periods)):
        if membership_interest_model(D, periods, idx):
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


def attachment_index(req: Request, periods) -> int:
    """M3: the index of the repayment period whose half-open window contains the
    disbursement date.  Inside the graded domain this is also the index of the
    FIRST RELATED repayment period (4.3.1)."""
    for idx in range(len(periods)):
        if membership_attachment(req.disb, periods, idx):
            return idx
    raise ValueError("disbursement outside every half-open repayment window")


def apply_rate_factors(req: Request, periods, till_multiplier="periodRatio",
                       ratio_one: bool = False) -> None:
    """4.1.1's two call sites.  `till_multiplier` selects the reading under test:
       "periodRatio"    -- revision 7 (normative)
       "repaymentEvery" -- the reading revision 6 wrote (P0-T34-1)
    """
    for p in periods:
        if till_multiplier == "periodRatio":
            m_till = period_ratio(req.start, p.frm, p.due, req.every)
        elif till_multiplier == "repaymentEvery":
            m_till = Decimal(req.every)
        else:
            raise ValueError(till_multiplier)
        for ip in p.interest_periods:
            ip.rate_factor = rate_factor(req.rate_pct, Decimal(req.every),
                                         ip.frm, ip.due, p.frm, p.due, ratio_one)
            ip.rate_factor_till_due = rate_factor(req.rate_pct, m_till,
                                                  ip.frm, p.due, p.frm, p.due,
                                                  ratio_one)


def first_related(req: Request, periods, target: int) -> int:
    """4.3.1: index of the first RELATED repayment period, via M1 + M2."""
    if periods[target].due == req.disb:
        eff = periods[target + 1].due if target + 1 < len(periods) else periods[target].due
    else:
        eff = periods[target].due
    for idx, p in enumerate(periods):
        if not (p.due < eff):
            return idx
    raise ValueError("no related period")


def level_installment(periods, first_rel: int, balance_minor: int) -> int:
    """2.1: fn1 = 1, fn_k = 1 + fn_{k-1} * g_k; installment = prod(g) * balance / fn.
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


def _split_one(p: RepaymentPeriod, balance_in_minor: int, textbook: bool) -> tuple[int, int]:
    """4.3.2's interest computation for one repayment period.
    Returns (calculated due interest in minor units, amount disbursed in this
    period's interest periods in minor units).
    `textbook` selects the wrong reading `round_mc(B x rateFactor)`."""
    b = Decimal(balance_in_minor) / Decimal(MINOR)
    total_t3 = Decimal(0)
    disbursed_here = 0
    for ip in p.interest_periods:
        if ip.length_till_period_due == 0:
            t3 = Decimal(0)
        elif textbook:
            t3 = round_mc(b * ip.rate_factor_till_due)
        else:
            t1 = round_mc(b * ip.rate_factor_till_due)
            t2 = round_mc(t1 / Decimal(ip.length_till_period_due))
            t3 = round_mc(t2 * Decimal(ip.length))
        total_t3 += t3
        if ip.disbursed_minor:
            disbursed_here += ip.disbursed_minor
            b = b + Decimal(ip.disbursed_minor) / Decimal(MINOR)
    return max(0, to_minor(total_t3)), disbursed_here


def split_rows(req: Request, periods, first_rel: int, attach: int, emi_minor: int,
               textbook: bool = False, whole_principal_prerow: bool = False) -> None:
    """4.3.2 'From interest period to row', steps 1-4, over every row.

    Step 4 (CORRECTED in revision 7, P0-T37-1) separates TWO quantities that
    revision 6 conflated:

      (a) the CARRIED-FORWARD balance the next repayment period computes on --
          max(0, balance carried in + amounts disbursed in this period under M1
          - PrincipalMinor);
      (b) the EMITTED OutstandingPrincipalMinor -- equal to (a) from the
          ATTACHMENT period (M3's half-open owner) onward, and exactly ZERO on
          every repayment row before it, because such a row is emitted from a
          model in which the disbursement has not yet been registered.

    `whole_principal_prerow=True` selects revision 6's literal step-4 reading,
    which emits (a) on the pre-disbursement row too -- i.e. the whole principal.
    """
    carry = 0
    for idx, p in enumerate(periods):
        p.emi_minor = emi_minor if idx >= first_rel else 0
        calc, disbursed_here = _split_one(p, carry, textbook)
        p.interest_minor = min(calc, p.emi_minor)
        p.principal_minor = max(0, p.emi_minor - p.interest_minor)
        carry_next = max(0, carry + disbursed_here - p.principal_minor)
        if idx < attach and not whole_principal_prerow:
            p.outstanding_minor = 0
        else:
            p.outstanding_minor = carry_next
        carry = carry_next


def apply_residual_and_recompute(req: Request, periods, first_rel: int, attach: int,
                                 textbook: bool = False,
                                 whole_principal_prerow: bool = False) -> None:
    """4.3: diff = disbursed + sum(dueInterest) - sum(installments); lastEmi += diff.
    4.3.2 step 5: the final row's SPLIT is then recomputed from steps 2-4."""
    total_interest = sum(p.interest_minor for p in periods)
    total_emi = sum(p.emi_minor for p in periods)
    diff = req.principal_minor + total_interest - total_emi
    last = periods[-1]
    last.emi_minor += diff
    idx = len(periods) - 1
    # The carried-forward balance into the last period, which for a
    # pre-attachment predecessor is NOT that row's emitted value.
    carry = 0
    for j, q in enumerate(periods[:-1]):
        _c, dh = _split_one(q, carry, textbook)
        carry = max(0, carry + dh - q.principal_minor)
    calc, disbursed_here = _split_one(last, carry, textbook)
    last.interest_minor = min(calc, last.emi_minor)
    last.principal_minor = max(0, last.emi_minor - last.interest_minor)
    carry_next = max(0, carry + disbursed_here - last.principal_minor)
    if idx < attach and not whole_principal_prerow:
        last.outstanding_minor = 0
    else:
        last.outstanding_minor = carry_next


def build(req: Request, emi_minor: int, first_rel: int, attach: int, **opts):
    till = opts.get("till_multiplier", "periodRatio")
    textbook = opts.get("textbook", False)
    prerow = opts.get("whole_principal_prerow", False)
    ratio_one = opts.get("ratio_one", False)
    periods, _ = segment(req)
    apply_rate_factors(req, periods, till, ratio_one)
    split_rows(req, periods, first_rel, attach, emi_minor, textbook, prerow)
    apply_residual_and_recompute(req, periods, first_rel, attach, textbook, prerow)
    return periods


def generate(req: Request, till_multiplier: str = "periodRatio",
             textbook: bool = False, whole_principal_prerow: bool = False,
             wrong_n: bool = False, ratio_one: bool = False,
             no_adoption: bool = False, run_loop: bool = True):
    """The whole 4.3 / 4.3.1 / 4.3.2 pipeline.  Keyword switches select the wrong
    readings the from-text check must discriminate."""
    opts = dict(till_multiplier=till_multiplier, textbook=textbook,
                whole_principal_prerow=whole_principal_prerow,
                ratio_one=ratio_one)
    periods0, target = segment(req)
    apply_rate_factors(req, periods0, till_multiplier, ratio_one)
    first_rel = first_related(req, periods0, target)
    attach = attachment_index(req, periods0)
    emi = level_installment(periods0, first_rel, req.principal_minor)
    rows = build(req, emi, first_rel, attach, **opts)
    if not run_loop:
        return rows

    # 4.3.1's loop.  n is |relatedRepaymentPeriods|; `wrong_n` reads
    # NumberOfRepayments instead (P0-T29-1).
    n = req.n if wrong_n else len(rows) - first_rel
    adjust_counter = 1
    while True:
        if n < 2:
            break
        i_pen = first_rel + (len(rows) - first_rel) - 2
        i_last = first_rel + (len(rows) - first_rel) - 1
        original = rows[i_pen].emi_minor
        emi_difference = rows[i_last].emi_minor - original
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
        trial = build(req, adjusted, first_rel, attach, **opts)
        new_difference = trial[i_last].emi_minor - trial[i_pen].emi_minor
        if not no_adoption and not (abs(new_difference) < abs(emi_difference)):
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
