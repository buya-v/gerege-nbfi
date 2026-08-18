#!/usr/bin/env python3
"""
T29 -- INDEPENDENT RE-DERIVATION + THE FROM-TEXT TRANSCRIPTION EXPERIMENT.

*** NOT RUN AGAINST A LIVE ORACLE. ***
No Fineract instance is reachable in this sandbox (no Docker, no PostgreSQL).
Every number this script prints is either
  (a) a re-derivation from the pinned source at 426a23544, or
  (b) compared against an observation ALREADY COMMITTED under
      `.softhouse/reviews/t23-probe/`.
Nothing here is a new oracle observation and nothing here may be promoted to
the vector store.

WHAT THIS FILE IS
-----------------
Two models of the progressive-loan schedule generator, in exact integer minor
units:

  * `MODEL_TEXT`   -- the EMI re-adjust loop transcribed from DEC-1 revision 4
                      section 4.3.1 / contract.go's `Period` doc ALONE, taking
                      the document at its word that
                        "n is the number of related repayment periods, which
                         inside the graded domain is NumberOfRepayments"
                      i.e. n == NumberOfRepayments, and that step 6 overwrites
                      "ALL n periods".
  * `MODEL_SOURCE` -- the same loop with `n` and the overwrite set re-derived
                      from the pinned Java:
                        n == relatedRepaymentPeriods.size()
                        (EmiAdjustment.numberOfRelatedPeriods(),
                         ProgressiveEMICalculator.java:732, :749,
                         ProgressiveLoanInterestScheduleModel.java:191-198)
                      and only the RELATED periods are overwritten
                      (ProgressiveEMICalculator.java:1279-1286).

The surrounding machinery (dates, rate factor, EMI recurrence, per-period
split, final-period residual) is written once and shared by both models, so the
ONLY difference between them is the thing under test.

This file shares NO code with `.softhouse/reviews/t26-probe/t26_rederive.py`
or `.softhouse/reviews/t28-probe/t28_spec_check.py` (T28's spec-check imports
T26's machinery, so a shared-dependency error could not be detected by it).
It supersedes the UNVALIDATED attempt-1 WIP scripts in this directory.

MONEY REPRESENTATION
--------------------
Every monetary quantity is a Python `int` in MINOR UNITS. `Decimal` is used
only for the dimensionless intermediates DEC-1 explicitly says are NOT money
(the per-period rate factor and the `fn` recurrence). No float32/float64.
"""

from decimal import Decimal, localcontext, ROUND_HALF_UP
from datetime import date
import calendar

SIG = 19            # Rounding.SignificantDigits  (MoneyHelper.PRECISION)
RFS = 19            # Rounding.RateFactorScale
MUD = 2             # Currency.MinorUnitDigits (MNT / USD)
UNIT = 10 ** MUD


# --------------------------------------------------------------------------
# arithmetic primitives
# --------------------------------------------------------------------------
def mc(fn):
    """Evaluate fn() at the threaded MathContext (SIG significant digits, HALF_UP)."""
    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_UP
        return fn()


def to_money(x: Decimal) -> int:
    """A quantity becomes money: setScale(MUD, HALF_UP) -> int64 minor units.

    Money.java:52 (the Money constructor's setScale under the rounding mode).
    """
    with localcontext() as c:
        c.prec = 60
        c.rounding = ROUND_HALF_UP
        return int((x * UNIT).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def half_up_div(num: int, den: int) -> int:
    """Nearest integer, ties away from zero -- the closed form DEC-1 4.3.1
    step 3 writes out: sign(x) * (2|x| + d) // (2d).  Pure integers."""
    assert den > 0
    s = -1 if num < 0 else 1
    return s * ((2 * abs(num) + den) // (2 * den))


# --------------------------------------------------------------------------
# dates -- DEC-1 section 4.2 (DefaultScheduledDateGenerator.java:128-129,
#          :168-176, :311-333)
# --------------------------------------------------------------------------
def add_months(d: date, k: int) -> date:
    m = d.month - 1 + k
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def reanchor(d: date, seed: date) -> date:
    if seed.day > 28 and d.day >= 28:
        return date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def windows(start: date, seed: date, n: int, every: int = 1):
    out, prev = [], start
    for _ in range(n):
        nxt = reanchor(add_months(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# --------------------------------------------------------------------------
# rate factor -- DEC-1 section 4.1 / contract.go Rounding.RateFactorScale
# ProgressiveEMICalculator.java:1950-1963 via :1536 (DAYS_30 + MONTHS):
#   interestFraction = daysInMonth(30) * repaymentEvery / daysInYear(360)  @mc
#   rf = rate * interestFraction @mc * actualDays @mc / calcDays @mc
#        then setScale(RateFactorScale, mode)
# --------------------------------------------------------------------------
def rate_factor(rate_num: int, rate_den: int, actual_days: int, calc_days: int,
                every: int = 1, apply_day_correction: bool = True) -> Decimal:
    if calc_days == 0:
        return Decimal(0)

    def go():
        # AnnualNominalInterestRate as a percentage decimal / 100 (:1318-1320)
        r = Decimal(rate_num) / Decimal(rate_den)
        frac = (Decimal(30) * Decimal(every)) / Decimal(360)
        v = r * frac
        if apply_day_correction:
            v = v * Decimal(actual_days)
            v = v / Decimal(calc_days)
        return v

    v = mc(go)
    with localcontext() as c:
        c.prec = 60
        c.rounding = ROUND_HALF_UP
        return v.quantize(Decimal(1).scaleb(-RFS), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# level installment -- DEC-1 section 2.1, the RECURRENCE.
#   rateFactorPlus1 = 1 + rf                        EXACT (RepaymentPeriod:216-218)
#   PROD  = reduce(ONE, acc.multiply(v, mc))        (:1816-1820)
#   fn    = periods.skip(1).reduce(ONE, (p,v) -> ONE.add(p.multiply(v,mc), mc))
#   EMI   = PROD * balance / fn   @mc  -> money     (:1838-1841, :1745-1747)
# --------------------------------------------------------------------------
def level_installment(balance_minor: int, rfs) -> int:
    plus1 = [Decimal(1) + r for r in rfs]

    def prod():
        acc = Decimal(1)
        for v in plus1:
            acc = acc * v
        return acc

    def fnres():
        acc = Decimal(1)
        for v in plus1[1:]:
            acc = Decimal(1) + acc * v
        return acc

    p = mc(prod)
    f = mc(fnres)
    bal = Decimal(balance_minor) / UNIT
    return to_money(mc(lambda: p * bal / f))


# --------------------------------------------------------------------------
# the per-period split -- DEC-1 section 2.1 / contract.go Period.PrincipalMinor
#   interest = balance * rf / lengthTillDue * length   @mc -> money
#              (InterestPeriod.java:145-158)
#   dueInterest  = min(calcInterest, emi)              (RepaymentPeriod:272-286)
#   duePrincipal = max(0, emi - dueInterest)           (:345-350)
#   balance roll-forward clamped at zero               (:389-403)
# --------------------------------------------------------------------------
def build(disbursed_minor: int, periods, first_rel: int, emi_of):
    """periods: list of (from,due,length,rf). first_rel: index of the first
    related period (the disbursement lands at its from-date). emi_of(i) gives
    period i's installment in minor units."""
    rows = []
    bal = 0
    for i, (f, d, L, rf) in enumerate(periods):
        if i == first_rel:
            bal += disbursed_minor
        emi = emi_of(i)
        if bal == 0 or rf == 0:
            calc_int = 0
        else:
            b = Decimal(bal) / UNIT
            calc_int = to_money(mc(lambda: b * rf / Decimal(L) * Decimal(L)))
        due_int = min(calc_int, emi)
        due_prin = max(0, emi - due_int)
        bal = max(0, bal - due_prin)
        rows.append({"emi": emi, "interest": due_int, "principal": due_prin,
                     "outstanding": bal, "from": f, "due": d})
    return rows


def apply_residual(disbursed_minor: int, rows):
    """DEC-1 section 4.3 (ProgressiveEMICalculator.java:1160-1219, diff :1202-1203,
    applied :1205).  Every sum is at CURRENCY scale."""
    tot_int = sum(r["interest"] for r in rows)
    tot_emi = sum(r["emi"] for r in rows)
    diff = disbursed_minor + tot_int - tot_emi
    last = rows[-1]
    last["emi"] += diff
    last["principal"] = max(0, last["emi"] - last["interest"])
    prev = rows[-2]["outstanding"] if len(rows) > 1 else disbursed_minor
    last["outstanding"] = max(0, prev - last["principal"])
    return diff


def rebuild(disbursed_minor, periods, first_rel, level_minor, keep_before=True):
    """Build the whole schedule on `level_minor` and re-apply the residual.

    keep_before=True  -> only the RELATED periods carry the level installment
                         (:1279-1286: the from/due-date predicate).
    keep_before=False -> ALL periods carry it (the reading DEC-1 4.3.1 step 6's
                         parenthetical "inside the graded domain that is ALL n
                         periods" licenses when n == NumberOfRepayments).
    """
    if keep_before:
        emi_of = lambda i: level_minor if i >= first_rel else 0
    else:
        emi_of = lambda i: level_minor
    rows = build(disbursed_minor, periods, first_rel, emi_of)
    apply_residual(disbursed_minor, rows)
    return rows


# ==========================================================================
# THE LOOP.  DEC-1 revision 4 section 4.3.1 steps 1-8, transcribed literally.
# `n` and `keep_before` are the only two things the two models disagree about.
# ==========================================================================
def readjust(disbursed_minor, periods, first_rel, rows, n, keep_before, trace=None):
    adjust_counter = 1                                             # :1262
    while True:
        # 1. the pair                              :1266 -> :1778-1789
        if n < 2:
            break
        original = rows[-2]["emi"]
        emi_difference = rows[-1]["emi"] - original                # SIGNED :1783

        # 2. guard, all three conjuncts            EmiAdjustment.java:31-36
        lower_half = n // 2
        if not (lower_half > 0
                and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * UNIT):
            if trace is not None:
                trace.append(f"guard NO: |d|={emi_difference} lowerHalf={lower_half} n={n}")
            break

        # 3. magnitude                             EmiAdjustment.java:38-40
        uncountable = 0        # nothing is paid on a schedule this contract generates
        d = max(1, n - uncountable)
        adjustment = half_up_div(emi_difference, d)

        # 4. candidate                             EmiAdjustment.java:42-44
        adjusted = original + adjustment           # multiple-rounding is the identity

        # 5. no-change break                       :1271-1273
        if adjusted == original:
            if trace is not None:
                trace.append("no-change break")
            break

        # 6. trial rebuild                         :1274-1288
        trial = rebuild(disbursed_minor, periods, first_rel, adjusted, keep_before)

        # 7. adoption test, strict; failure DISCARDS   :1289-1291
        new_difference = trial[-1]["emi"] - trial[-2]["emi"]
        if not (abs(new_difference) < abs(emi_difference)):
            if trace is not None:
                trace.append(f"adoption FAILS |new|={new_difference} |old|={emi_difference}")
            break

        # 8. adopt, bound                          :1293-1306, :1307-1308
        if trace is not None:
            trace.append(f"ADOPT#{adjust_counter} {original}->{adjusted} "
                         f"(|d| {abs(emi_difference)}->{abs(new_difference)})")
        rows = trial
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return rows


# --------------------------------------------------------------------------
# whole-schedule generation
# --------------------------------------------------------------------------
def related_index(n_rep, wins, disb: date):
    """Re-derived from ProgressiveEMICalculator.java:147-151 + :250-263 +
    ProgressiveLoanInterestScheduleModel.java:191-198, :238-245, and
    LoanRepaymentScheduleProcessingWrapper.isInPeriod (:251-254):
    the FIRST period is matched INCLUSIVE-INCLUSIVE, later periods
    from-EXCLUSIVE to-INCLUSIVE; if the matched period's DUE date equals the
    disbursement date the effective due date is the NEXT period's due date.
    Returns the index of the first RELATED period."""
    hit = None
    for i, (f, d) in enumerate(wins):
        inside = (f <= disb <= d) if i == 0 else (f < disb <= d)
        if inside:
            hit = i
            break
    if hit is None:
        return None                       # outside the graded domain (section 4.6)
    if wins[hit][1] == disb:
        if hit + 1 < n_rep:
            return hit + 1
        return None                       # disbursement on the LAST due date: discarded
    return hit


def generate(principal_major, n_rep, rate_pct, start=date(2024, 1, 1),
             disb=None, model="source", trace=None,
             apply_day_correction=True):
    principal_minor = int(Decimal(str(principal_major)) * UNIT)
    disb = disb or start
    wins = windows(start, disb, n_rep)
    first_rel = related_index(n_rep, wins, disb)
    if first_rel is None:
        return None
    num, den = Decimal(str(rate_pct)).as_integer_ratio()
    periods = []
    for i, (f, d) in enumerate(wins):
        L = (d - f).days
        rf = rate_factor(num, den * 100, L, L,
                         apply_day_correction=apply_day_correction) if i >= first_rel else Decimal(0)
        periods.append((f, d, L, rf))

    rel_rfs = [p[3] for p in periods[first_rel:]]
    level = level_installment(principal_minor, rel_rfs)
    rows = rebuild(principal_minor, periods, first_rel, level, keep_before=True)
    if model == "none":
        return rows
    if model == "source":
        n = n_rep - first_rel
        return readjust(principal_minor, periods, first_rel, rows, n, True, trace)
    # "text": DEC-1 4.3.1 says n == NumberOfRepayments and step 6 overwrites
    # "ALL n periods".
    return readjust(principal_minor, periods, first_rel, rows, n_rep, False, trace)


def f(m):
    return f"{m // 100}.{abs(m) % 100:02d}"


def summarize(rows):
    return (f(rows[0]["emi"]), f(rows[-1]["emi"]),
            f(sum(r["interest"] for r in rows)))
