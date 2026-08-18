#!/usr/bin/env python3
"""DEC-1 revision 6 transcribed from its own text, PLUS the wrong readings the
five binding captures (DEC-1 section 8 items 3 / 3a / 3b / 3c / 3d) must separate.

PROVENANCE.  The model body below is COPIED VERBATIM from
`.softhouse/reviews/t33-probe/t33_spec_check.py` lines 38-435 (task T33's from-text
transcription of DEC-1 revision 6), with exactly three additions, each marked
`# T37 EDIT`:

  1. `readjust_loop` gains a `loop_reading` parameter so the EMI re-adjust loop can
     be switched off entirely ("absent") or run without its adoption test
     ("no_adoption") -- the two readings items 3 and 3a exist to separate.
  2. `generate` gains the same parameter and passes it through.
  3. `rows()` is added, returning the FULL per-period split so an observation can be
     compared to a reading row by row, not only on three summary figures.

*** NO LIVE ORACLE IS CONTACTED BY THIS FILE. ***  Everything it computes is a
RE-DERIVATION.  Observations live in ../out/ and come from the pinned oracle only.
Exact decimal / integer minor units throughout; NO FLOAT anywhere on a money path.
"""


import calendar
import copy
from dataclasses import dataclass, field
from datetime import date
from decimal import Context, Decimal, ROUND_HALF_UP

# --------------------------------------------------------------- arithmetic
# DEC-1 section 4.1 / Rounding: the graded domain pins SignificantDigits ==
# RateFactorScale == 19 and Mode == RoundingHalfUp; Currency.MinorUnitDigits==2.

PRECISION = 19       # Rounding.SignificantDigits  (MoneyHelper.java:35, :91-93)
RATE_SCALE = 19      # Rounding.RateFactorScale    (constrained equal, section 4.1)
MINOR = 2            # Currency.MinorUnitDigits    (MNT)

MC = Context(prec=PRECISION, rounding=ROUND_HALF_UP)    # the threaded MathContext
EXACT = Context(prec=500, rounding=ROUND_HALF_UP)       # "no MathContext at all"

ZERO = Decimal(0)
ONE = Decimal(1)


def mul(a: Decimal, b: Decimal) -> Decimal:
    """One `.multiply(x, mc)`."""
    return MC.multiply(a, b)


def div(a: Decimal, b: Decimal) -> Decimal:
    """One `.divide(x, mc)`."""
    return MC.divide(a, b)


def madd(a: Decimal, b: Decimal) -> Decimal:
    return MC.add(a, b)


def xadd(a: Decimal, b: Decimal) -> Decimal:
    """DEC-1 section 2.1: the growth factor's additions carry NO MathContext
    (RepaymentPeriod.java:216-218), and money sums are already at currency
    scale (section 4.3)."""
    return EXACT.add(a, b)


def set_scale(x: Decimal, s: int) -> Decimal:
    """BigDecimal.setScale(s, HALF_UP)."""
    return EXACT.quantize(x, Decimal(1).scaleb(-s))


def money(x: Decimal) -> Decimal:
    """Money.of(currency, x, mc): the constructor's setScale(decimals, mode)
    (Money.java:40-53, scale at :52)."""
    return set_scale(x, MINOR)


def days(a: date, b: date) -> int:
    """DateUtils.getDifferenceInDays -- whole days, exact integer."""
    return (b - a).days


# ------------------------------------------------------------------- dates
# DEC-1 section 4.2, monthly only: step-with-clamp then the seed re-anchor,
# the seed being the DISBURSEMENT date (LoanApplicationTerms.java:583-589).

def _step_month(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def due_dates(start: date, n: int, every: int, seed: date) -> list[date]:
    out = [start]
    for _ in range(n):
        nxt = _step_month(out[-1], every)
        if seed.day > 28 and nxt.day >= 28:                # :168-176
            nxt = nxt.replace(
                day=min(calendar.monthrange(nxt.year, nxt.month)[1], seed.day))
        out.append(nxt)
    return out


# ------------------------------------------------------------------ model

@dataclass
class InterestPeriod:
    frm: date
    due: date
    disbursed: Decimal = ZERO      # amount registered ON this interest period
    balance_in: Decimal = ZERO     # outstanding loan balance carried in
    rate_factor: Decimal = ZERO    # feeds the growth factor (section 2.1)
    rf_till_due: Decimal = ZERO    # feeds the interest (section 4.3.2)


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


# ------------------------------------------- section 4.1 + 4.1.1: rate factor

def rate_factor(annual_pct: Decimal,
                span_from: date, span_to: date,
                rp: RepaymentPeriod,
                day_counts: str) -> Decimal:
    """DEC-1 section 4.1 (the snippet) with section 4.1.1's day counts.

    section 4.1.1, NORMATIVE:
      actualDaysInPeriod     = days across THE SPAN the factor is computed over
                               (ProgressiveEMICalculator.java:1367-1368, :1500-1501)
      calculatedDaysInPeriod = days from the ENCLOSING REPAYMENT PERIOD's FromDate
                               to its DueDate -- NEVER the span's own length
                               (:1369-1370, :1502-1503)
      numerator = actual, denominator = calculated                     (:1961-1962)
      exact-zero guard when calculatedDaysInPeriod == 0                (:1953-1955)

    `day_counts == "ratio1"` selects the reading revision 6 DELETES from
    contract.go -- both day counts taken from the span, so the ratio is
    identically 1.  It exists here only to be falsified.
    """
    actual = days(span_from, span_to)
    if day_counts == "spec":
        calculated = days(rp.frm, rp.due)          # section 4.1.1
    elif day_counts == "ratio1":
        calculated = actual                        # the deleted clause
    else:
        raise ValueError(day_counts)

    if calculated == 0:                            # :1953-1955, exactly zero
        return ZERO

    rate = div(annual_pct, Decimal(100))                        # :1318-1320
    frac = div(mul(Decimal(30), ONE), Decimal(360))             # 30 * every / 360
    v = mul(rate, frac)                                         # .multiply(mc)
    v = mul(v, Decimal(actual))                                 # .multiply(actual, mc)
    v = div(v, Decimal(calculated))                             # .divide(calculated, mc)
    return set_scale(v, RATE_SCALE)                             # setScale(RateFactorScale)


def compute_rate_factors(rps: list[RepaymentPeriod], annual_pct: Decimal,
                         day_counts: str) -> None:
    """The two call sites and their two spans (ProgressiveEMICalculator.java:638-643)."""
    for rp in rps:
        for ip in rp.ips:
            # rateFactor: span = the interest period's own window          :639-640
            ip.rate_factor = rate_factor(annual_pct, ip.frm, ip.due, rp, day_counts)
            # rateFactorTillPeriodDueDate: span = [ip.FromDate, rp.DueDate] :641-642
            ip.rf_till_due = rate_factor(annual_pct, ip.frm, rp.due, rp, day_counts)


# ------------------------------------------ section 2.1: the growth factor

def growth_factor(rp: RepaymentPeriod, composition: str) -> Decimal:
    """DEC-1 section 2.1, corrected in revision 6 (P1-T32-1):

      g_k = 1 + SUM over the repayment period's interest periods of rateFactor,
      every addition EXACT (RepaymentPeriod.java:216-217, no MathContext :216-218).

    `composition == "singular"` is the pre-revision-6 wording, `1 + rateFactor`
    read as one factor for the whole repayment period.  Kept only to measure it.
    """
    if composition == "sum":
        acc = ONE
        for ip in rp.ips:
            acc = xadd(acc, ip.rate_factor)
        return acc
    if composition == "singular":
        # one factor computed over the whole repayment period's window
        return xadd(ONE, rp.ips[0].rate_factor if len(rp.ips) == 1
                    else _whole_period_factor(rp))
    raise ValueError(composition)


_WHOLE_RATE: dict = {}


def _whole_period_factor(rp: RepaymentPeriod) -> Decimal:
    return _WHOLE_RATE[(rp.frm, rp.due)]


# ----------------------------------- section 4.3.2: interest of one period

def interest_of(ip: InterestPeriod, rp: RepaymentPeriod, reading: str) -> Decimal:
    """DEC-1 section 4.3.2, DECLINING_BALANCE (InterestPeriod.java:145-158)."""
    ltpdd = days(ip.frm, rp.due)                    # :164-166
    if ltpdd == 0:                                  # :146-148, exactly zero
        return ZERO
    b = ip.balance_in                               # :151, outstanding balance
    if reading == "textbook":                       # the reading 4.3.2 excludes
        return mul(b, ip.rf_till_due)
    t1 = mul(b, ip.rf_till_due)                     # :155  operation (1)
    t2 = div(t1, Decimal(ltpdd))                    # :156  operation (2)
    t3 = mul(t2, Decimal(days(ip.frm, ip.due)))     # :157  operation (3), length :160-162
    return t3


# --------------------------- section 4.3.2: interest-period segmentation

def build_periods(start: date, n: int, every: int, seed: date) -> list[RepaymentPeriod]:
    ds = due_dates(start, n, every, seed)
    return [RepaymentPeriod(frm=ds[i], due=ds[i + 1],
                            ips=[InterestPeriod(ds[i], ds[i + 1])])
            for i in range(n)]


def register_disbursement(rps: list[RepaymentPeriod], d: date,
                          amount: Decimal) -> date:
    """section 4.3.1 (effective due date) + section 4.3.2 (segmentation).

    Returns the EFFECTIVE DUE DATE.
    """
    # membership: [FromDate, DueDate] inclusive both ends for the FIRST period,
    # (FromDate, DueDate] for every later one   (ProgressiveLoanInterestScheduleModel
    # .java:238-245)
    idx = None
    for i, rp in enumerate(rps):
        lo = (d >= rp.frm) if i == 0 else (d > rp.frm)
        if lo and d <= rp.due:
            idx = i
            break
    if idx is None:
        raise ValueError("disbursement outside every repayment period")
    rp = rps[idx]

    hit = next((ip for ip in rp.ips if ip.due == d), None)
    if hit is not None:                                     # :275-277
        hit.disbursed = xadd(hit.disbursed, amount)
    else:                                                   # :280-296
        prev = [ip for ip in rp.ips if ip.frm <= d][-1]
        original_due = prev.due
        new_due = min(max(d, prev.frm), prev.due)           # :439-442, clamped
        prev.due = new_due
        prev.disbursed = xadd(prev.disbursed, amount)
        rp.ips.insert(rp.ips.index(prev) + 1,
                      InterestPeriod(new_due, original_due))

    # effective due date (ProgressiveEMICalculator.java:250-263)
    if rp.due == d and idx + 1 < len(rps):
        return rps[idx + 1].due
    return rp.due


def propagate_one(rps: list[RepaymentPeriod], i: int) -> None:
    """InterestPeriod.updateOutstandingLoanBalance, clamped at zero.

    The amount enters the balance of the LATER segment, never the earlier one
    (InterestPeriod.java:168-188).
    """
    rp = rps[i]
    for j, ip in enumerate(rp.ips):
        if j == 0:
            if i == 0:
                ip.balance_in = ZERO
            else:
                prev_rp = rps[i - 1]
                last = prev_rp.ips[-1]
                v = xadd(xadd(last.balance_in, last.disbursed), -prev_rp.principal)
                ip.balance_in = v if v > 0 else ZERO
        else:
            prev = rp.ips[j - 1]
            v = xadd(prev.balance_in, prev.disbursed)
            ip.balance_in = v if v > 0 else ZERO


# ------------------------------- section 4.3.2: from interest period to row

def split(rps: list[RepaymentPeriod], interest_reading: str) -> None:
    """section 4.3.2 'From interest period to row', steps 1-4, in schedule order."""
    for i, rp in enumerate(rps):
        propagate_one(rps, i)
        total = ZERO
        for ip in rp.ips:
            total = xadd(total, interest_of(ip, rp, interest_reading))
        calc = money(total)                                  # step 1: sum THEN money
        if calc < 0:
            calc = ZERO                                      # RepaymentPeriod.java:264
        rp.interest = calc if calc < rp.emi else rp.emi      # step 2: cap    :280
        p = xadd(rp.emi, -rp.interest)                       # step 3        :345-350
        rp.principal = p if p > 0 else ZERO
        here = ZERO
        for ip in rp.ips:
            here = xadd(here, ip.disbursed)
        o = xadd(xadd(rp.ips[0].balance_in, here), -rp.principal)
        rp.outstanding = o if o > 0 else ZERO                # step 4, clamp  :399


def apply_residual(rps: list[RepaymentPeriod], total_disbursed: Decimal) -> None:
    """section 4.3: diff = SUM disbursed + SUM dueInterest - SUM installments,
    accumulated at CURRENCY scale, absorbed onto the last period."""
    tot_int = ZERO
    tot_emi = ZERO
    for rp in rps:
        tot_int = xadd(tot_int, rp.interest)
        tot_emi = xadd(tot_emi, rp.emi)
    diff = xadd(xadd(total_disbursed, tot_int), -tot_emi)
    rps[-1].emi = money(xadd(rps[-1].emi, diff))


def rebuild(rps, related, level, total_disbursed, interest_reading) -> None:
    """Level installment onto the RELATED periods only (section 4.3.1), split,
    residual, then section 4.3.2 step 5: the final row's SPLIT recomputed from
    steps 2-4 (revision 6, P2-T32-1)."""
    for rp in related:
        rp.emi = level
    split(rps, interest_reading)
    apply_residual(rps, total_disbursed)
    split(rps, interest_reading)


# ------------------------------------- section 2.1: the level installment

def level_installment(related: list[RepaymentPeriod], composition: str) -> Decimal:
    """fn_1 = 1, fn_k = 1 + fn_(k-1) * g_k;  installment = PROD g_k * balance / fn."""
    prod = ONE
    for rp in related:
        prod = mul(prod, growth_factor(rp, composition))
    fn = ONE
    for rp in related[1:]:
        fn = madd(ONE, mul(fn, growth_factor(rp, composition)))
    balance = related[0].ips[0].balance_in
    for ip in related[0].ips:
        balance = xadd(balance, ip.disbursed)
    return money(div(mul(prod, balance), fn))


# ------------------------------------ section 4.3.1: the EMI re-adjust loop

def divide_to_minor(numer: Decimal, d: int) -> Decimal:
    """Money.dividedBy(long) -- divide at mc, then setScale(minor, mode)
    (Money.java:352-358, :52); short-circuit at d == 1 (:353-355)."""
    if d == 1:
        return numer
    return money(div(numer, Decimal(d)))


def readjust_loop(rps, related, total_disbursed, interest_reading,
                  n_reading: str, number_of_repayments: int,
                  loop_reading: str = "spec") -> None:      # T37 EDIT 1
    """DEC-1 section 4.3.1, steps 1-8, verbatim, in whole minor units.

    `n` is the RELATED-period count (revision 5, P0-T29-1).  `n_reading ==
    "numberofrepayments"` isolates the wrong reading: the pair is still the last
    two related rows and the rebuild is still scoped to the related periods, but
    the guard threshold floor(n/2) and the divisor max(1, n - uncountable) read
    NumberOfRepayments.  Kept only to be falsified.
    """
    # T37 EDIT 1 -- `loop_reading == "absent"` is the reading in which the port never
    # implements checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods at all (DEC-1 8/3);
    # `"no_adoption"` implements it but omits step 7's strict test (DEC-1 8/3a).
    if loop_reading == "absent":
        return
    n = len(related)
    n_arith = n if n_reading == "spec" else number_of_repayments
    counter = 1
    while True:
        # 1. the pair                                          :1266 -> :1778-1789
        if n < 2:
            return
        original = related[n - 2].emi
        emi_difference = xadd(related[n - 1].emi, -original)   # SIGNED       :1783

        # 2. guard, all three conjuncts            :1267-1269, EmiAdjustment.java:31-36
        lower_half = n_arith // 2                              # floor(n/2)      :32
        if not (lower_half > 0
                and emi_difference != 0
                and EXACT.multiply(abs(emi_difference), Decimal(100))
                > Decimal(lower_half)):                        # :34-35, in units
            return

        # 3. adjustment magnitude                 EmiAdjustment.java:38-40, Money:352-358
        uncountable = 0                                        # nothing is paid :2027-2031
        d = max(1, n_arith - uncountable)                      # == n            :39
        adjustment = divide_to_minor(emi_difference, d)

        # 4./5. candidate, and break when it is not a change   :1270-1273
        adjusted = xadd(original, adjustment)
        if adjusted == original:
            return

        # 6. TRIAL rebuild on a copy; related periods only     :1274-1288
        trial = copy.deepcopy(rps)
        trial_related = [rp for rp in trial if rp.related]
        rebuild(trial, trial_related, adjusted, total_disbursed, interest_reading)

        # 7. strict adoption test; failure DISCARDS            :1289-1291, :46-48
        new_difference = xadd(trial_related[n - 1].emi, -trial_related[n - 2].emi)
        if loop_reading != "no_adoption" and \
                not (abs(new_difference) < abs(emi_difference)):   # T37 EDIT 1
            return

        # 8. adopt, then bound the iteration                   :1293-1308
        for src, dst in zip(trial, rps):
            dst.emi, dst.interest = src.emi, src.interest
            dst.principal, dst.outstanding = src.principal, src.outstanding
            for a, b in zip(src.ips, dst.ips):
                b.balance_in, b.disbursed = a.balance_in, a.disbursed
        related = [rp for rp in rps if rp.related]
        counter += 1
        if counter > 3:
            return


# =============================== T37 EDIT 2 ================================
# `generate` copied from t33_spec_check.py with `loop_reading` threaded through.

def generate(principal_major, n, annual_pct, start=date(2024, 1, 1), disb=None,
             day_counts="spec", interest_reading="spec",
             composition="sum", n_reading="spec", loop_reading="spec"):
    """One GenerateRequest, per DEC-1 revision 6, inside the graded domain."""
    d = disb or start
    amount = Decimal(principal_major)
    rate = Decimal(annual_pct)

    rps = build_periods(start, n, 1, d)

    _WHOLE_RATE.clear()
    for rp in rps:
        _WHOLE_RATE[(rp.frm, rp.due)] = rate_factor(rate, rp.frm, rp.due, rp, day_counts)

    eff_due = register_disbursement(rps, d, amount)
    for rp in rps:
        rp.related = not (rp.due < eff_due)
    related = [rp for rp in rps if rp.related]

    compute_rate_factors(rps, rate, day_counts)
    for i in range(len(rps)):
        propagate_one(rps, i)

    level = level_installment(related, composition)
    rebuild(rps, related, level, amount, interest_reading)
    readjust_loop(rps, related, amount, interest_reading, n_reading, n, loop_reading)
    return rps


# =============================== T37 EDIT 3 ================================
# Full per-period rendering, so an OBSERVATION can be compared to a reading row
# by row rather than on three summary figures only.

def _f(x: Decimal) -> str:
    return f"{set_scale(x, MINOR):.2f}"


def rows(rps) -> dict:
    """The reading's schedule in the same shape the capture emits."""
    tot_int = ZERO
    tot_emi = ZERO
    out = []
    for i, rp in enumerate(rps, start=1):
        tot_int = xadd(tot_int, rp.interest)
        tot_emi = xadd(tot_emi, rp.emi)
        out.append({
            "periodNumber": i,
            "fromDate": str(rp.frm),
            "dueDate": str(rp.due),
            "principal": _f(rp.principal),
            "interest": _f(rp.interest),
            "total": _f(rp.emi),
            "balance": _f(rp.outstanding),
        })
    return {
        "totalInterestAmount": _f(tot_int),
        "totalRepaymentAmount": _f(tot_emi),
        "periods": out,
    }


def reading(principal_major, n, annual_pct, start, disb, **kw) -> dict:
    return rows(generate(principal_major, n, annual_pct, start=start, disb=disb, **kw))
