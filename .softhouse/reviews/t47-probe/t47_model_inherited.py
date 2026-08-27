"""
T41 -- DEC-1 REVISION 8, transcribed from the DOCUMENT TEXT ALONE.

This is the from-text spec check the ADR holds itself to.  Revision 8's
normative sections are transcribed here as a runnable model:

  2.1     the fn recurrence and the SUMMED growth factor
  4.1     the two senses of the MathContext integer
  4.1.1   the two day counts, the two call sites' two multipliers, periodRatio
          (seed, the month-end special case in step B, the walk in step C), and
          revision 8's narrowing: the days-in-month argument is 30 at BOTH call
          sites unconditionally
  4.1.2   WHICH MathContext is in force -- the THREADED one on Path A.  This
          model therefore takes (SIG, mode) as the THREADED context and never
          reads a tenant-global one; see `assert_threaded_context`.
  4.2     civil-date stepping and the month-end re-anchor on Disbursement.Date
  4.3     the final-period residual
  4.3.1   the EMI re-adjust loop, over the RELATED periods
  4.3.2   the per-period interest (three separately rounded operations), the
          FOUR date-membership rules, and step 4a/4b
  4.5     OutstandingPrincipalMinor, including the disbursement row
  4.5.1   charges: NOT carried.  A charge moves no cell this model computes --
          that is decision C-1/C-2's observed premise and t41_discriminate.py
          tests it directly against the captures.

*** NO LIVE ORACLE WAS CONTACTED BY THIS TASK. ***
Every number this file computes is a RE-DERIVATION from revision 8's text.
Every expectation it is checked against is TRANSCRIBED from a capture file
already committed on main, quoted by capture id.

Exact arithmetic only: `Decimal` under an explicit context, and integer minor
units.  NO float appears anywhere on a money path; capture files are loaded with
`parse_float=Decimal`.

Disclosed rather than hidden, exactly as T38 disclosed the same about T34: the
dataclass layout, the round_mc/set_scale/to_minor helpers and the capture-file
plumbing follow T38's conventions so the two models are comparable cell for
cell.  Every MONEY RULE below was re-transcribed by this task from revision 8's
text, and where revision 8's sentence is unchanged from revision 7's, agreement
with T38's model is a second independent reading of the same sentence rather
than a copy -- t41_validate.py reports that cross-check explicitly.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext

# --- 4.1 / 4.1.2: the THREADED MathContext ---------------------------------
# 4.1: the production MathContext is (19, HALF_UP) and RateFactorScale ==
# SignificantDigits, because the oracle derives both from one integer.
# 4.1.2: on Path A the arithmetic in force is the THREADED context.  This model
# has no ambient context at all -- which is the point: if the ambient one
# mattered inside the graded domain, a model without it could not reproduce the
# captures.
SIG = 19
RATE_FACTOR_SCALE = 19
MINOR_DIGITS = 2
MINOR = 10 ** MINOR_DIGITS


def assert_threaded_context(cap_inputs) -> str | None:
    """4.1.2, made executable.  A capture is admissible to this model only if its
    THREADED MathContext is (19, HALF_UP).  The AMBIENT MoneyHelper context is
    recorded by the capture and deliberately NOT consulted here; returning a
    reason string means 'skip and say why'."""
    if cap_inputs.get("mathContextPrecision") != SIG:
        return f"threaded precision {cap_inputs.get('mathContextPrecision')}, not {SIG}"
    if cap_inputs.get("mathContextRoundingMode") != "HALF_UP":
        return f"threaded mode {cap_inputs.get('mathContextRoundingMode')}, not HALF_UP"
    return None


def round_mc(x: Decimal, sig: int = SIG) -> Decimal:
    """4.1, sense 1: round to `sig` SIGNIFICANT decimal digits under HALF_UP."""
    with localcontext() as ctx:
        ctx.prec = sig
        ctx.rounding = ROUND_HALF_UP
        return +x


def set_scale(x: Decimal, scale: int) -> Decimal:
    """4.1, sense 2: setScale(scale, mode) -- a DECIMAL-PLACE quantization.
    `setScale` takes a scale, not a precision; that is the whole of 4.1."""
    return x.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)


def to_minor(x: Decimal) -> int:
    """4.3.2 step 1: a quantity becomes money exactly once, when it is scaled to
    Currency.MinorUnitDigits places under Rounding.Mode."""
    return int(set_scale(x, MINOR_DIGITS) * MINOR)


def days(a: date, b: date) -> int:
    return (b - a).days


def m2s(v: int) -> str:
    neg = v < 0
    a = abs(v)
    return ("-" if neg else "") + f"{a // MINOR}.{a % MINOR:02d}"


# --- 4.2: civil dates, stepping, and the month-end re-anchor ----------------

def plus_months(d: date, k: int) -> date:
    """4.2 step 1 / 4.1.1: LocalDate month arithmetic, which CLAMPS the
    day-of-month to the target month's length."""
    y = d.year + (d.month - 1 + k) // 12
    m = (d.month - 1 + k) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def months_between(a: date, b: date) -> int:
    """4.1.1 step B: `DateUtils.getExactDifference(a, b, MONTHS)`, which is
    `ChronoUnit.MONTHS.between` [DateUtils.java:308-317] and therefore Java's
    `LocalDate.monthsUntil`:

        packed = prolepticMonth * 32 + dayOfMonth
        result = (packed_b - packed_a) / 32          # truncated toward zero

    *** T41 FINDING F-1.  Revision 8's phrase "whole months ... truncated toward
    zero" admits a SECOND reading -- "the largest k with a + k months <= b" --
    and the two are NOT the same function.  They differ exactly when `plusMonths`
    would CLAMP, i.e. when b is the last day of its month and a's day-of-month is
    strictly greater: MONTHS.between(2024-01-31, 2024-02-29) is 0 under the
    packed rule and 1 under the clamped-step rule.  That is EXACTLY the condition
    step B's month-end special case tests, so the two readings agree on every
    input WHILE the special case is present -- which is why a model using the
    wrong one still reproduces every committed cell -- and disagree the moment it
    is dropped.  This model transcribes the PACKED rule, because that is what the
    cited routine does and because T39's 116-of-116 observation that the special
    case is load-bearing is only possible under it.  ***
    """
    p1 = (a.year * 12 + a.month - 1) * 32 + a.day
    p2 = (b.year * 12 + b.month - 1) * 32 + b.day
    diff = p2 - p1
    q = abs(diff) // 32
    return q if diff >= 0 else -q


def re_anchor(stepped: date, seed: date) -> date:
    """4.2 step 2, monthly only.  If the SEED day-of-month > 28 AND the stepped
    date's day >= 28, set the day to min(days in target month, seed day).
    THE SEED IS THE DISBURSEMENT DATE (LoanApplicationTerms.java:583-589), which
    is why 4.2 documents the rule on Disbursement.Date."""
    if seed.day > 28 and stepped.day >= 28:
        return date(stepped.year, stepped.month,
                    min(calendar.monthrange(stepped.year, stepped.month)[1], seed.day))
    return stepped


def repayment_boundaries(start: date, seed: date, n: int, every: int):
    """4.2: boundaries are stepped from ScheduleStartDate; the re-anchor seed is
    Disbursement.Date.  That ASYMMETRY BETWEEN TWO SEEDS is 4.1.1's whole
    mechanism, because calculateSeedDate reads the schedule start instead."""
    out = []
    prev = start
    for _ in range(n):
        nxt = re_anchor(plus_months(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# --- 4.1.1: periodRatio ----------------------------------------------------

def calculate_seed_date(schedule_start: date, rp_from: date, rp_due: date,
                        every: int) -> date:
    """4.1.1 step A.  Walk k = 1, 2, 3 ... until ScheduleStartDate + k months is
    NOT BEFORE the repayment period's DueDate; call it L.  The seed is
    ScheduleStartDate iff BOTH conjuncts hold -- L == DueDate AND
    L - RepaymentEvery months == FromDate -- otherwise the period's own
    FromDate.  A reading that keeps only the first conjunct is wrong."""
    k = 1
    while True:
        L = plus_months(schedule_start, k)
        k += 1
        if not (L < rp_due):
            break
    both = (L == rp_due) and (plus_months(L, -every) == rp_from)
    return schedule_start if both else rp_from


def period_ratio(schedule_start: date, rp_from: date, rp_due: date, every: int,
                 month_end_case: bool = True) -> Decimal:
    """4.1.1 steps A-C for MONTHS.

    `month_end_case=False` selects the reading with step B's four month-end
    lines omitted -- the most plausible mis-port, and DEC-1 section 8 item 3f's
    wrong reading.
    """
    seed = calculate_seed_date(schedule_start, rp_from, rp_due, every)

    # Step B.  k is the whole months from the seed to the period's FromDate,
    # EXCEPT for the month-end special case: when FromDate is the LAST DAY of
    # its month AND the seed's day-of-month is STRICTLY LATER than FromDate's,
    # k is measured to FromDate.plusDays(1).
    last_day = calendar.monthrange(rp_from.year, rp_from.month)[1]
    if month_end_case and last_day == rp_from.day and seed.day > rp_from.day:
        k = months_between(seed, rp_from + timedelta(days=1))
    else:
        k = months_between(seed, rp_from)

    # Step C.  The division is the ONLY MathContext-rounded operation; the
    # addition of the whole-period count is EXACT and carries no MathContext.
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
            return frac + Decimal(m)          # EXACT addition
    return Decimal(m - k - 1)


# --- 4.1 / 4.1.1: the rate factor ------------------------------------------

DAYS_IN_MONTH = Decimal(30)   # 4.1.1, revision 8: THIRTY AT BOTH CALL SITES,
                              # unconditionally -- :1537 is consumed only from
                              # the case DAYS_30 arm at :1536, where :1508
                              # yields the literal 30, the same literal :1413
                              # passes.  One constant, not two.
DAYS_IN_YEAR = Decimal(360)   # 4.9: DayCountFixed30Over360


def rate_factor(rate_pct: Decimal, multiplier: Decimal,
                span_from: date, span_due: date,
                rp_from: date, rp_due: date,
                ratio_one: bool = False) -> Decimal:
    """4.1's snippet, with 4.1.1's day counts and multipliers.

        interestFractionPerPeriod = 30 .multiply(<multiplier>, mc) .divide(360, mc)
        rateFactor = rate .multiply(fraction, mc)
                          .multiply(actualDaysInPeriod, mc)
                          .divide(calculatedDaysInPeriod, mc)
                          .setScale(RateFactorScale, mode)

    4.1.1:  actual     = whole days across THE SPAN the factor is computed over
            calculated = whole days of the ENCLOSING REPAYMENT PERIOD, never the
                         span's own length
            guard      = exactly BigDecimal.ZERO when calculated == 0
            multiplier = RepaymentEvery for `rateFactor`
                         periodRatio   for `rateFactorTillPeriodDueDate`

    `ratio_one=True` selects the deleted ratio-is-always-1 reading (P0-T32-1).
    """
    calculated = days(rp_from, rp_due)
    if calculated == 0:
        return Decimal(0)                                  # exact zero guard
    actual = calculated if ratio_one else days(span_from, span_due)
    rate = round_mc(rate_pct / Decimal(100))               # 4.8
    frac = round_mc(round_mc(DAYS_IN_MONTH * multiplier) / DAYS_IN_YEAR)
    x = round_mc(rate * frac)
    x = round_mc(x * Decimal(actual))
    x = round_mc(x / Decimal(calculated))
    return set_scale(x, RATE_FACTOR_SCALE)                 # the SCALE sense


# --- model structures ------------------------------------------------------

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
    interest_periods: list = field(default_factory=list)
    emi_minor: int = 0
    interest_minor: int = 0
    principal_minor: int = 0
    outstanding_minor: int = 0

    @property
    def growth_factor(self) -> Decimal:
        """2.1 / P1-T32-1: g = 1 + the SUM of the interest periods' rate
        factors, every addition EXACT and carrying no MathContext."""
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


# --- 4.3.2: the FOUR date-membership rules ---------------------------------
# M4 governs CHARGES and this contract carries none, so it is stated in the ADR
# and not implemented here.  M1, M2 and M3 all bear on the schedule.

def in_period_M1(D: date, periods, idx: int) -> bool:
    """M1 -- the INTEREST MODEL's balance-change membership.
    [FromDate, DueDate] inclusive at BOTH ends for the FIRST repayment period;
    (FromDate, DueDate] -- from-EXCLUSIVE, due-inclusive -- for every later one.
    Revision 8 records that the 'is first' input here is the period's own
    STRUCTURAL property, not a counter -- which is what distinguishes M1
    from M4."""
    p = periods[idx]
    return (p.frm <= D <= p.due) if idx == 0 else (p.frm < D <= p.due)


def in_period_M3(D: date, periods, idx: int) -> bool:
    """M3 -- [FromDate, DueDate), from-inclusive, DUE-EXCLUSIVE.  Decides in
    which period's iteration the disbursement is registered and the
    disbursement row emitted, and is 4.6's ordering window key."""
    p = periods[idx]
    return p.frm <= D < p.due


def segment(req: Request, collapse_M3_into_M1: bool = False):
    """4.2's boundaries plus 4.3.2's interest-period segmentation, which uses M1.

    Inside the graded domain the only balance change is the single disbursement,
    so exactly three shapes occur:
      D on period j's FromDate -> a ZERO-LENGTH [From, From] holding the amount,
                                  then [From, Due] carrying it as balance
      D on period j's DueDate  -> ONE interest period, unchanged; the amount is
                                  recorded on it and enters period j+1's balance
      D strictly inside        -> [From, D] with a ZERO balance, then [D, Due]
                                  carrying the amount

    `collapse_M3_into_M1=True` selects the wrong reading that reuses 4.6's
    ordering window key for this segmentation.
    """
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    periods = [RepaymentPeriod(f, d) for f, d in bounds]
    for p in periods:
        p.interest_periods = [InterestPeriod(p.frm, p.due, p.frm, p.due)]

    D = req.disb
    pred = in_period_M3 if collapse_M3_into_M1 else in_period_M1
    target = next((i for i in range(len(periods)) if pred(D, periods, i)), None)
    if target is None:
        raise ValueError("disbursement outside every repayment period (3.1 refuses it)")

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


def m3_owner(req: Request, periods) -> int:
    """M3's owner period.  4.3.2: inside the graded domain this index IS the
    first RELATED repayment period, in all three rows of 4.3.1's table."""
    for i in range(len(periods)):
        if in_period_M3(req.disb, periods, i):
            return i
    raise ValueError("disbursement outside every half-open window (4.6 refuses it)")


def first_related(req: Request, periods, target: int) -> int:
    """4.3.1 / M2.  The effective due date is the matched period's own DueDate,
    or the NEXT period's if the disbursement falls exactly on it; the related
    periods are those whose DueDate is NOT BEFORE it."""
    p = periods[target]
    if p.due == req.disb:
        eff = periods[target + 1].due if target + 1 < len(periods) else p.due
    else:
        eff = p.due
    for i, q in enumerate(periods):
        if not (q.due < eff):
            return i
    raise ValueError("no related period")


def apply_rate_factors(req: Request, periods, till_multiplier="periodRatio",
                       ratio_one: bool = False, month_end_case: bool = True) -> None:
    """4.1.1's TWO call sites and their TWO multipliers.

      rateFactor                  -> RepaymentEvery   (the fn recurrence)
      rateFactorTillPeriodDueDate -> periodRatio      (the per-period interest)

    periodRatio is computed PER REPAYMENT PERIOD, so every interest period
    inside one repayment period shares it.
    """
    for p in periods:
        if till_multiplier == "periodRatio":
            m_till = period_ratio(req.start, p.frm, p.due, req.every, month_end_case)
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


def level_installment(periods, first_rel: int, balance_minor: int) -> int:
    """2.1: fn_1 = 1, fn_k = 1 + fn_{k-1} * g_k; installment = PROD(g) * balance / fn.
    Not the closed-form annuity formula.
    4.3.1: computed over, and written to, the RELATED periods only."""
    rel = periods[first_rel:]
    fn = Decimal(1)
    prod = Decimal(1)
    for i, p in enumerate(rel):
        g = p.growth_factor
        prod = round_mc(prod * g)
        if i > 0:
            fn = round_mc(Decimal(1) + round_mc(fn * g))
    bal = Decimal(balance_minor) / Decimal(MINOR)
    return to_minor(round_mc(round_mc(prod * bal) / fn))


def _due_interest(p: RepaymentPeriod, balance_in_minor: int, textbook: bool):
    """4.3.2's interest computation for ONE repayment period.

    Three separately MathContext-rounded operations, IN THIS ORDER:
        t1 = round_mc(B  * rateFactorTillPeriodDueDate)
        t2 = round_mc(t1 / lengthTillPeriodDueDate)
        t3 = round_mc(t2 * length)
    with an exact-zero short circuit when lengthTillPeriodDueDate == 0.
    Operations 2 and 3 cancel ALGEBRAICALLY and NOT NUMERICALLY.

    Step 1: sum the t3 values, convert to money EXACTLY ONCE, clamp at zero.
    `textbook=True` selects the collapsed round_mc(B * rateFactor) reading.
    """
    b = Decimal(balance_in_minor) / Decimal(MINOR)
    total = Decimal(0)
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
        total += t3
        if ip.disbursed_minor:
            # 4.3.2: the amount enters the balance of the LATER segment.
            disbursed_here += ip.disbursed_minor
            b = b + Decimal(ip.disbursed_minor) / Decimal(MINOR)
    return max(0, to_minor(total)), disbursed_here


def split_rows(req: Request, periods, first_rel: int, owner: int, emi_minor: int,
               textbook: bool = False, whole_principal_prerow: bool = False) -> None:
    """4.3.2 'From interest period to row', steps 2-4.

      2. cap:       InterestMinor  = min(calculated due interest, installment)
      3. balancing: PrincipalMinor = max(0, installment - InterestMinor)
      4a. carried forward: max(0, carried in + disbursed in this period under M1
                               - PrincipalMinor)
      4b. EMITTED OutstandingPrincipalMinor: EXACTLY ZERO on every repayment row
          before M3's owner period, else the carried-forward value.

    `whole_principal_prerow=True` selects revision 6's literal step-4 reading,
    which emits the carried-forward value on the pre-disbursement row too --
    i.e. the whole principal (P0-T37-1).
    """
    carry = 0
    for i, p in enumerate(periods):
        p.emi_minor = emi_minor if i >= first_rel else 0
        calc, disbursed_here = _due_interest(p, carry, textbook)
        p.interest_minor = min(calc, p.emi_minor)
        p.principal_minor = max(0, p.emi_minor - p.interest_minor)
        nxt = max(0, carry + disbursed_here - p.principal_minor)
        p.outstanding_minor = nxt if (i >= owner or whole_principal_prerow) else 0
        carry = nxt


def apply_residual(req: Request, periods, first_rel: int, owner: int,
                   textbook: bool = False, whole_principal_prerow: bool = False) -> None:
    """4.3: diff = SUM disbursed + SUM dueInterest - SUM installments, signed;
    lastEmi += diff, every SUM accumulated at CURRENCY SCALE.
    4.3.2 step 5: the final row's SPLIT is then recomputed from steps 2-4 --
    split every row, THEN absorb the residual, never the reverse."""
    diff = (req.principal_minor
            + sum(p.interest_minor for p in periods)
            - sum(p.emi_minor for p in periods))
    last = periods[-1]
    last.emi_minor += diff
    carry = 0
    for q in periods[:-1]:
        _c, dh = _due_interest(q, carry, textbook)
        carry = max(0, carry + dh - q.principal_minor)
    calc, dh = _due_interest(last, carry, textbook)
    last.interest_minor = min(calc, last.emi_minor)
    last.principal_minor = max(0, last.emi_minor - last.interest_minor)
    nxt = max(0, carry + dh - last.principal_minor)
    i = len(periods) - 1
    last.outstanding_minor = nxt if (i >= owner or whole_principal_prerow) else 0


def _build(req: Request, emi_minor: int, first_rel: int, owner: int, **o):
    periods, _ = segment(req, o.get("collapse_M3_into_M1", False))
    apply_rate_factors(req, periods, o.get("till_multiplier", "periodRatio"),
                       o.get("ratio_one", False), o.get("month_end_case", True))
    split_rows(req, periods, first_rel, owner, emi_minor,
               o.get("textbook", False), o.get("whole_principal_prerow", False))
    apply_residual(req, periods, first_rel, owner,
                   o.get("textbook", False), o.get("whole_principal_prerow", False))
    return periods


def generate(req: Request, **o):
    """The whole 4.3 / 4.3.1 / 4.3.2 pipeline.  Keyword switches select the
    wrong readings the from-text check must discriminate:

      till_multiplier="repaymentEvery"  P0-T34-1  (now OBSERVED, T39)
      month_end_case=False              T39 N-2   (now OBSERVED, T39)
      ratio_one=True                    P0-T32-1
      textbook=True                     P0-T29-2
      wrong_n=True                      P0-T29-1
      whole_principal_prerow=True       P0-T37-1
      no_adoption=True                  section 8 item 3a
      run_loop=False                    section 8 item 3
      collapse_M3_into_M1=True          the inert membership collapse
    """
    run_loop = o.pop("run_loop", True)
    wrong_n = o.pop("wrong_n", False)
    no_adoption = o.pop("no_adoption", False)

    periods0, target = segment(req, o.get("collapse_M3_into_M1", False))
    apply_rate_factors(req, periods0, o.get("till_multiplier", "periodRatio"),
                       o.get("ratio_one", False), o.get("month_end_case", True))
    first_rel = first_related(req, periods0, target)
    owner = m3_owner(req, periods0)
    emi = level_installment(periods0, first_rel, req.principal_minor)
    rows = _build(req, emi, first_rel, owner, **o)
    if not run_loop:
        return rows

    # --- 4.3.1: the EMI re-adjust loop, in exact integer minor units --------
    n = req.n if wrong_n else len(rows) - first_rel
    adjust_counter = 1
    while True:
        if n < 2:
            break                                        # degenerate pair
        i_pen, i_last = len(rows) - 2, len(rows) - 1
        original = rows[i_pen].emi_minor
        emi_difference = rows[i_last].emi_minor - original
        lower_half = n // 2                              # floor(n/2)
        if not (lower_half > 0
                and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * MINOR):
            break                                        # guard, three conjuncts
        d = max(1, n)                                    # uncountablePeriods == 0
        sgn = 1 if emi_difference > 0 else -1
        adjustment = sgn * ((2 * abs(emi_difference) + d) // (2 * d))   # HALF_UP
        adjusted = original + adjustment
        if adjusted == original:
            break                                        # no-change break
        trial = _build(req, adjusted, first_rel, owner, **o)
        new_difference = trial[i_last].emi_minor - trial[i_pen].emi_minor
        if not no_adoption and not (abs(new_difference) < abs(emi_difference)):
            break                                        # STRICT adoption test:
                                                         # failure DISCARDS
        rows = trial
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return rows


def totals(rows):
    ti = sum(p.interest_minor for p in rows)
    tp = sum(p.principal_minor for p in rows)
    return tp, ti, tp + ti
