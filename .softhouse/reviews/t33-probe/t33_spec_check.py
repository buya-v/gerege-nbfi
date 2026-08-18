#!/usr/bin/env python3
"""T33 -- DEC-1 **REVISION 6** transcribed literally from its own text, and run.

WHAT THIS IS.  A from-text transcription of the corrected contract:
`docs/adr/DEC-1-schedule-generator-adapter.md` revision 6 (sections 2.1, 3.1,
4.1, 4.1.1 (NEW), 4.2, 4.3, 4.3.1, 4.3.2, 4.5, 4.6) together with the doc
comments of `nexus/internal/apps/loanschedule/contract/contract.go`.  It is
written from the TEXT, in exact decimal / integer minor units.  THERE IS NO
FLOAT ANYWHERE ON A MONEY PATH -- no float32/float64/big.Float equivalent; the
only `float` in this file would be a syntax error.

*** NO LIVE ORACLE WAS CONTACTED.  NOTHING HERE IS AN OBSERVATION. ***
The thirteen expectations in CASES are quoted verbatim from
`.softhouse/reviews/t32-probe/t32_validate.py`, which quotes them from capture
files already committed under `.softhouse/reviews/t23-probe/`.  Only those
EXPECTATIONS are re-used; the model below is this task's own.  Every figure this
script prints for an UNCAPTURED shape is a RE-DERIVATION from the pinned
checkout `426a23544` and a *candidate shape to capture* (DEC-1 section 8 items
3b / 3d).  None of them may be promoted to the vector store.

WHAT IT PROVES.
  (A) revision 6's text reproduces all 13 committed observations digit-for-digit;
  (B) revision 6's text DISCRIMINATES the three readings prior rounds found, each
      of which reproduces the corpus 13/13 and is therefore invisible to it:
        B1  the RATIO-IS-ALWAYS-1 reading of the rate factor's day counts
            -- the clause revision 6 deletes from contract.go (P0-T32-1);
        B2  the textbook `balance x rateFactor` interest (section 4.3.2);
        B3  the wrong-`n` reading, `n = NumberOfRepayments` (section 4.3.1).
      Each must return DIFFERENT MONEY from revision 6's text on the shapes the
      corresponding review cited.  A specification that cannot tell the wrong
      answer from the right one has not been fixed.
  (C) informational: the growth-factor composition P1-T32-1 corrects
      (`1 + SUM rateFactor` vs `1 + rateFactor(whole period)`) is measured
      INERT on today's graded domain, which is why T32 graded it P1 and not P0.
"""

from __future__ import annotations

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
                  n_reading: str, number_of_repayments: int) -> None:
    """DEC-1 section 4.3.1, steps 1-8, verbatim, in whole minor units.

    `n` is the RELATED-period count (revision 5, P0-T29-1).  `n_reading ==
    "numberofrepayments"` isolates the wrong reading: the pair is still the last
    two related rows and the rebuild is still scoped to the related periods, but
    the guard threshold floor(n/2) and the divisor max(1, n - uncountable) read
    NumberOfRepayments.  Kept only to be falsified.
    """
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
        if not (abs(new_difference) < abs(emi_difference)):
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


# ------------------------------------------------------------- generation

def generate(principal_major, n, annual_pct, start=date(2024, 1, 1), disb=None,
             day_counts="spec", interest_reading="spec",
             composition="sum", n_reading="spec"):
    """One GenerateRequest, per DEC-1 revision 6, inside the graded domain."""
    d = disb or start
    amount = Decimal(principal_major)
    rate = Decimal(annual_pct)

    rps = build_periods(start, n, 1, d)

    # whole-period rate factors, captured BEFORE segmentation, for the
    # "singular" growth-factor control only (P1-T32-1's rejected wording).
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
    readjust_loop(rps, related, amount, interest_reading, n_reading, n)
    return rps


def summarise(rps):
    """(level installment, final installment, total interest) at currency scale."""
    rel = [rp for rp in rps if rp.emi != 0]
    tot = ZERO
    for rp in rps:
        tot = xadd(tot, rp.interest)
    fmt = lambda x: f"{set_scale(x, MINOR):.2f}"                       # noqa: E731
    return (fmt(rel[0].emi) if rel else "0.00", fmt(rps[-1].emi), fmt(tot))


# ===========================================================================
# (A) the THIRTEEN COMMITTED OBSERVATIONS.  Expectations quoted verbatim from
# .softhouse/reviews/t32-probe/t32_validate.py, which quotes the capture files
# under .softhouse/reviews/t23-probe/.  NOT re-taken from any oracle.
# ===========================================================================

CASES = [
    (100,      6,  "7.0",  None, ("17.01", "17.00", "2.05"),
     "shipped fixture / DEC-1 4.3 observed (-0.01 residual)"),
    (1014632,  6,  "7.0",  None, ("172574.64", "172574.62", "20815.82"),
     "t23-probe2-output.txt CASE P=1014632"),
    (127704,  36, "16.8",  None, ("4540.30", "4540.06", "35746.56"),
     "t23-probe2-output.txt CASE P=127704"),
    (135623,   6,  "7.0",  None, ("23067.56", "23067.59", "2782.39"),
     "t23-probe2-output.txt CASE P=135623"),
    (2345024,  6,  "7.0",  None, ("398855.60", "398855.63", "48109.63"),
     "t23-probe2-output.txt CASE P=2345024"),
    (167299,   6, "21.6",  None, ("29665.91", "29665.94", "10696.49"),
     "t23-probe2-output.txt CASE P=167299"),
    (64352,   12, "21.6",  None, ("6010.61", "6010.55", "7775.26"),
     "t23-probe2-output.txt CASE P=64352"),
    (1000,    18, "18.5",  None, ("64.04", "64.14", "152.82"),
     "t23-probe2-output.txt CASE P=1000"),
    (246489,  18, "18.5",  None, ("15786.24", "15786.14", "37663.22"),
     "t23-probe2-output.txt CASE P=246489"),
    (16838,   36, "16.8",  None, ("598.65", "598.46", "4713.21"),
     "t23-probe2-output.txt CASE P=16838"),
    (40595,   36, "16.8",  None, ("1443.28", "1443.47", "11363.27"),
     "t23-probe2-output.txt CASE P=40595"),
    (1200000,  6, "21.6",  None, ("212787.28", "212787.30", "76723.70"),
     "t23-probe-output.txt Q0a"),
    (1200000,  6, "21.6", date(2024, 2, 1), ("253114.12", "253114.10", "65570.58"),
     "t23-probe-output.txt Q0b -- disbursement ON repayment 1's due date"),
]

# (B) the shapes each review cited as separating a reading.  RE-DERIVED
# CANDIDATE SHAPES TO CAPTURE, never observations; nothing below compares them
# against an oracle value, only the readings against each other.
#
# B1: strictly-inside-a-period disbursements (T32 section 4.3; DEC-1 8/3d).
INSIDE_SHAPES = [
    (1200000,  6, "21.6", date(2024, 1, 1), date(2024, 1, 15)),
    (1014632,  6,  "7.0", date(2024, 1, 1), date(2024, 1, 15)),
    (127704,  36, "16.8", date(2024, 1, 1), date(2024, 1, 20)),
    (1200000,  6, "21.6", date(2024, 1, 1), date(2024, 2, 10)),
    (50000000, 12, "18.5", date(2024, 1, 1), date(2024, 1, 2)),
]
# B2: the interest round-trip (T29; DEC-1 8/3b).
TEXTBOOK_SHAPES = [
    (13202,   6, "16.8", date(2024, 1, 1),  None),
    (3924149, 6, "16.8", date(2024, 1, 31), None),
    (1814727, 6, "21.6", date(2024, 1, 31), None),
]
# B3: the wrong `n` (T29; DEC-1 8/3c).
WRONG_N_SHAPES = [
    (10548069, 6, "16.8", date(2024, 1, 1), date(2024, 2, 1)),
    (1222552,  6, "18.5", date(2024, 1, 1), date(2024, 2, 1)),
    (13549647, 6, "21.6", date(2024, 1, 1), date(2024, 2, 1)),
]


def part_a() -> int:
    print("(A) DEC-1 REVISION 6 as transcribed, vs the 13 COMMITTED observations")
    bad = 0
    for p, n, r, disb, expect, prov in CASES:
        got = summarise(generate(p, n, r, disb=disb))
        ok = got == expect
        bad += (not ok)
        print(f"  {'PASS' if ok else 'FAIL'}  P={p:<9} n={n:<3} {r:>5}%"
              f"{('  disb=' + str(disb)) if disb else '':<20}  {got}")
        if not ok:
            print(f"        expected {expect}   [{prov}]")
    print(f"  => {len(CASES) - bad} pass, {bad} fail, out of {len(CASES)}\n")
    return bad


def _corpus_agreement(**kw) -> int:
    return sum(1 for p, n, r, disb, expect, _ in CASES
               if summarise(generate(p, n, r, disb=disb, **kw)) == expect)


def part_b(label, shapes, kw, note) -> int:
    print(f"(B) {label}")
    print(f"    {note}")
    agree = _corpus_agreement(**kw)
    print(f"    reproduces {agree}/{len(CASES)} committed observations"
          f"  -> the corpus is {'BLIND to it' if agree == len(CASES) else 'able to see it'}")
    diverge = 0
    for p, n, r, start, disb in shapes:
        spec = summarise(generate(p, n, r, start=start, disb=disb))
        wrong = summarise(generate(p, n, r, start=start, disb=disb, **kw))
        d = spec != wrong
        diverge += d
        tag = "DISCRIMINATED" if d else "not separated"
        ds = f" disb={disb}" if disb else ""
        print(f"    {tag:<14} MNT {p:>10,} / {n:<3} x {r:>5}%  start={start}{ds}")
        print(f"                   revision 6 : {spec[0]:>14} / {spec[1]:>14} / {spec[2]:>15}")
        print(f"                   the reading: {wrong[0]:>14} / {wrong[1]:>14} / {wrong[2]:>15}")
    print(f"    => the reading FAILS revision 6 on {diverge}/{len(shapes)} cited shapes\n")
    return diverge


def part_c() -> int:
    print("(C) informational -- P1-T32-1's growth-factor composition")
    diverge = 0
    for p, n, r, start, disb in INSIDE_SHAPES:
        a = summarise(generate(p, n, r, start=start, disb=disb, composition="sum"))
        b = summarise(generate(p, n, r, start=start, disb=disb, composition="singular"))
        diverge += (a != b)
    print(f"    1 + SUM rateFactor  vs  1 + rateFactor(whole period): "
          f"{diverge}/{len(INSIDE_SHAPES)} divergences")
    print("    INERT on today's graded domain -- which is why T32 graded the")
    print("    wording defect P1 and not P0.  Revision 6 states the true form")
    print("    anyway, because it stops being inert under interest pauses,")
    print("    mid-term rate changes or multi-tranche (DEC-1 6.2, 6.3).\n")
    return diverge


if __name__ == "__main__":
    print("T33 spec check -- DEC-1 REVISION 6 transcribed from its own text")
    print("NO LIVE ORACLE WAS CONTACTED.  Expectations are quoted from committed")
    print("captures; every figure printed for an UNCAPTURED shape is a")
    print("RE-DERIVATION and must never be promoted to the vector store.")
    print("Exact decimal / integer minor units throughout; no float anywhere.\n")

    bad = part_a()

    d1 = part_b(
        "B1 -- the RATIO-IS-ALWAYS-1 reading of the day counts (P0-T32-1)",
        INSIDE_SHAPES, {"day_counts": "ratio1"},
        "the clause revision 6 DELETES from contract.go:317-321; DEC-1 8/3d")
    d2 = part_b(
        "B2 -- the textbook `balance x rateFactor` interest (P0-T29-2)",
        TEXTBOOK_SHAPES, {"interest_reading": "textbook"},
        "the reading DEC-1 4.3.2 exists to exclude; DEC-1 8/3b")
    d3 = part_b(
        "B3 -- the wrong-`n` reading, n = NumberOfRepayments (P0-T29-1)",
        WRONG_N_SHAPES, {"n_reading": "numberofrepayments"},
        "n isolated in the guard threshold and the divisor; DEC-1 8/3c")

    part_c()

    ok = (bad == 0
          and d1 == len(INSIDE_SHAPES)
          and d2 == len(TEXTBOOK_SHAPES)
          and d3 == len(WRONG_N_SHAPES))
    print("=" * 74)
    print(f"(A) 13 committed observations reproduce : {'YES' if bad == 0 else 'NO'}")
    print(f"(B1) ratio-is-1 reading discriminated   : {d1}/{len(INSIDE_SHAPES)}")
    print(f"(B2) textbook reading discriminated     : {d2}/{len(TEXTBOOK_SHAPES)}")
    print(f"(B3) wrong-`n` reading discriminated    : {d3}/{len(WRONG_N_SHAPES)}")
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    print("=" * 74)
    raise SystemExit(0 if ok else 1)
