#!/usr/bin/env python3
"""
T29 -- THE FROM-TEXT TRANSCRIPTION EXPERIMENT.

WHAT THIS IS
------------
This file is the answer to DEC-1 revision 4's central claim: that
sections 4.3 / 4.3.1 / 2.1 / 4.1 / 4.2, plus contract.go's `Period` doc,
determine the money on their own -- so that two independent implementers
reading ONLY DEC-1 produce byte-identical schedules.

To test that, the EMI re-adjust loop below (`readjust_loop_AS_TEXT`) was
transcribed FROM THE DOCUMENT TEXT ALONE, in exact integer MINOR UNITS,
without consulting the Java while transcribing, and without reusing
`.softhouse/reviews/t26-probe/t26_rederive.py` or
`.softhouse/reviews/t28-probe/t28_spec_check.py` (T28's spec-check imports
T26's machinery, so a shared-dependency error could not be detected by it;
this file shares nothing with either).

The surrounding schedule machinery (rate factor, EMI recurrence, split,
final-period residual) is transcribed the same way, from DEC-1 sections 2.1,
4.1, 4.2, 4.3 and 4.9. Where DEC-1 gives a `file:line`, that citation is
recorded in the docstring -- but the CODE follows the document's own prose,
which is the thing under test.

*** NOT RUN AGAINST A LIVE ORACLE. ***
No Fineract instance is reachable in this sandbox (no Docker, no PostgreSQL).
Every number this script prints is either (a) a re-derivation from the pinned
source at 426a23544, or (b) quoted from an observation ALREADY COMMITTED under
`.softhouse/reviews/t23-probe/`. Nothing here is a new oracle observation and
nothing here may be promoted to the vector store.

MONEY REPRESENTATION
--------------------
Every monetary quantity below is a Python `int` in MINOR UNITS (MNT/USD
cents). Decimal is used ONLY for the two intermediate quantities DEC-1
explicitly says are not money -- the per-period rate factor (section 4.1: a
quantized decimal) and the products of the `fn` recurrence (section 2.1) --
exactly as DEC-1 section 4.1 and contract.go's `Rounding` doc require. No
float32/float64 appears anywhere.
"""

from decimal import Decimal, localcontext, ROUND_HALF_UP
from datetime import date
import calendar

# ---------------------------------------------------------------------------
# Rounding policy. DEC-1 section 4.1: the production MathContext is
# (19, HALF_UP); SignificantDigits == RateFactorScale == 19; MinorUnitDigits 2.
# ---------------------------------------------------------------------------
SIG_DIGITS = 19
RATE_FACTOR_SCALE = 19
MINOR_DIGITS = 2
SCALE = 10 ** MINOR_DIGITS


def at_mc(fn):
    """Evaluate fn() at the threaded MathContext (SignificantDigits, HALF_UP)."""
    with localcontext() as ctx:
        ctx.prec = SIG_DIGITS
        ctx.rounding = ROUND_HALF_UP
        return fn()


def to_minor(x: Decimal) -> int:
    """Decimal -> int64 minor units, HALF_UP, ties away from zero.

    DEC-1 section 4.1 / contract.go Rounding: "Currency-scale rounding happens
    where a quantity becomes money" (Money.java:40-53).
    """
    scaled = x * SCALE
    q = scaled.quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(q)


def div_round_half_up(num: int, den: int) -> int:
    """Exact-integer nearest-integer division, ties AWAY FROM ZERO.

    This is the closed form DEC-1 section 4.3.1 step 3 writes out verbatim:
        sign(x) * (2*|x| + d) // (2*d)
    It is stated here in integer arithmetic only, as the document requires.
    """
    assert den > 0
    sign = -1 if num < 0 else 1
    a = abs(num)
    return sign * ((2 * a + den) // (2 * den))


# ---------------------------------------------------------------------------
# Dates. DEC-1 section 4.2 -- step + month-end re-anchor to the DISBURSEMENT
# seed (DefaultScheduledDateGenerator.java:128-129, :168-176, :311-333).
# ---------------------------------------------------------------------------
def add_months_clamped(d: date, k: int) -> date:
    m = d.month - 1 + k
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def reanchor(d: date, seed: date) -> date:
    if seed.day > 28 and d.day >= 28:
        return date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def period_windows(start: date, seed: date, n: int, every: int = 1):
    out, prev = [], start
    for _ in range(n):
        nxt = reanchor(add_months_clamped(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# ---------------------------------------------------------------------------
# Rate factor. DEC-1 section 4.1 + section 4.9 (fixed 30/360, monthly).
# Four mc-qualified ops, then a quantization to RateFactorScale DECIMAL PLACES
# (ProgressiveEMICalculator.java:1950-1963).
# ---------------------------------------------------------------------------
def rate_factor(annual_pct: Decimal, actual_days: int, calc_days: int) -> Decimal:
    def go():
        nominal = annual_pct / Decimal(100)          # :1318-1320
        frac = (Decimal(30) * Decimal(1)) / Decimal(360)
        v = nominal * frac
        v = v * Decimal(actual_days)
        v = v / Decimal(calc_days)
        return v
    v = at_mc(go)
    return v.quantize(Decimal(1).scaleb(-RATE_FACTOR_SCALE), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Level installment. DEC-1 section 2.1: the RECURRENCE, never the closed form.
#   fn1 = 1 ; fn_k = 1 + fn_{k-1} * (1 + rf_k)   (:1822-1828, :1991-1993)
#   EMI = PROD(1+rf) * balance / fn              (:1816-1820, :1838-1841)
#   1 + rf is EXACT, with no MathContext         (RepaymentPeriod.java:216-218)
# ---------------------------------------------------------------------------
def level_installment_minor(balance_minor: int, rfs) -> int:
    plus1 = [Decimal(1) + r for r in rfs]

    def prod():
        acc = Decimal(1)
        for v in plus1:
            acc = acc * v
        return acc

    def fn():
        acc = Decimal(1)
        for v in plus1[1:]:
            acc = Decimal(1) + acc * v
        return acc

    p = at_mc(prod)
    f = at_mc(fn)
    bal = Decimal(balance_minor) / SCALE
    return to_minor(at_mc(lambda: p * bal / f))


# ---------------------------------------------------------------------------
# The per-period split. DEC-1 section 2.1 + contract.go Period.PrincipalMinor:
# interest first, capped at the installment; principal is the non-negative
# balancing remainder; the outstanding roll-forward is clamped at zero.
# (RepaymentPeriod.java:272-286, :345-350, :389-403; InterestPeriod.java:145-158)
# ---------------------------------------------------------------------------
def split(balance_minor: int, rfs, emis_minor, lengths):
    bal = balance_minor
    rows = []
    for rf, emi, L in zip(rfs, emis_minor, lengths):
        b = Decimal(bal) / SCALE
        calc_int = to_minor(at_mc(lambda: b * rf / Decimal(L) * Decimal(L)))
        due_int = min(calc_int, emi)
        due_prin = max(0, emi - due_int)
        bal = max(0, bal - due_prin)
        rows.append({"emi": emi, "interest": due_int, "principal": due_prin, "outstanding": bal})
    return rows


# ---------------------------------------------------------------------------
# The final-period residual. DEC-1 section 4.3, verbatim:
#   diff    = SUM disbursed + SUM capitalizedIncome + creditedPrincipal
#             + SUM dueInterest - SUM installments      (accumulated at
#                                                        CURRENCY SCALE)
#   lastEmi = lastEmi + diff                            (:1202-1205, :1210)
# The period's principal then falls out as installment - interest (:345-350).
# ---------------------------------------------------------------------------
def apply_final_period_residual(disbursed_minor: int, rows):
    total_int = sum(r["interest"] for r in rows)
    total_emi = sum(r["emi"] for r in rows)
    diff = disbursed_minor + total_int - total_emi
    rows[-1]["emi"] += diff
    rows[-1]["principal"] = max(0, rows[-1]["emi"] - rows[-1]["interest"])
    prev_bal = rows[-2]["outstanding"] if len(rows) > 1 else disbursed_minor
    rows[-1]["outstanding"] = max(0, prev_bal - rows[-1]["principal"])
    return diff


def build(disbursed_minor: int, rfs, level_minor: int, lengths):
    rows = split(disbursed_minor, rfs, [level_minor] * len(rfs), lengths)
    apply_final_period_residual(disbursed_minor, rows)
    return rows


# ===========================================================================
#  THE EXPERIMENT: DEC-1 section 4.3.1 steps 1-8, transcribed from the TEXT.
#  `n_text` is what the document says n is:
#     "n is the number of related repayment periods, which inside the graded
#      domain is NumberOfRepayments (ProgressiveLoanInterestScheduleModel
#      .java:191-194)"                     -- ADR section 4.3.1, and verbatim
#                                             in contract.go's Period doc.
#  Everything else is the text's own step order.
# ===========================================================================
def readjust_loop_AS_TEXT(disbursed_minor, rfs, lengths, rows, n_text, trace=None):
    adjust_counter = 1                                              # :1262
    while True:
        # 1. the pair
        if n_text < 2:
            break
        original = rows[n_text - 2]["emi"]
        emi_difference = rows[n_text - 1]["emi"] - original          # SIGNED

        # 2. guard -- all three conjuncts
        lower_half = n_text // 2
        if not (lower_half > 0
                and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * SCALE):
            if trace is not None:
                trace.append(f"guard no-fire |d|={emi_difference} lowerHalf={lower_half}")
            break

        # 3. magnitude -- uncountablePeriods is 0 on a generated schedule
        uncountable = sum(1 for r in rows if 0 > original)           # == 0, per the text
        d = max(1, n_text - uncountable)
        adjustment = div_round_half_up(emi_difference, d)

        # 4. candidate (installment multiple is the identity in the graded domain)
        adjusted = original + adjustment

        # 5. break on no change
        if adjusted == original:
            break

        # 6. trial rebuild
        trial = build(disbursed_minor, rfs, adjusted, lengths)

        # 7. adoption test -- strict, failure DISCARDS
        new_difference = trial[n_text - 1]["emi"] - trial[n_text - 2]["emi"]
        if not (abs(new_difference) < abs(emi_difference)):
            if trace is not None:
                trace.append(f"adoption fails |new|={new_difference} |old|={emi_difference}")
            break

        # 8. adopt, bound
        if trace is not None:
            trace.append(f"ADOPT iter {adjust_counter}: {original} -> {adjusted} "
                         f"(|d| {abs(emi_difference)} -> {abs(new_difference)})")
        rows = trial
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return rows


# ===========================================================================
#  The SOURCE-FAITHFUL loop. Identical body, but `n` is the count of RELATED
#  repayment periods actually passed to
#  checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods at
#  ProgressiveEMICalculator.java:749, i.e.
#     getRelatedRepaymentPeriods(getEffectiveRepaymentDueDate(...))
#     -- ProgressiveLoanInterestScheduleModel.java:191-198,
#        ProgressiveEMICalculator.java:250-263, :146-151
#  and `rows` is that same related SUFFIX (the list getEmiAdjustment scans at
#  :1779-1785 and whose size EmiAdjustment.numberOfRelatedPeriods() returns).
# ===========================================================================
def readjust_loop_AS_SOURCE(disbursed_minor, rfs, lengths, related_rows, trace=None):
    n = len(related_rows)
    return readjust_loop_AS_TEXT(disbursed_minor, rfs, lengths, related_rows, n, trace)


# ---------------------------------------------------------------------------
# Whole-schedule generation.
#   disb_on_period: 0 => disbursement on ScheduleStartDate (all N periods are
#                        related). j>0 => disbursement dated exactly on period
#                        j's due date, which the graded domain admits
#                        (ScheduleStartDate <= D < last due date) and which
#                        DEC-1 sections 4.2 / 4.6 both cite as OBSERVED.
# ---------------------------------------------------------------------------
def generate(principal_major, N, annual_pct, start=date(2024, 1, 1),
             disb_on_period=0, which="source", trace=None):
    principal_minor = int(round(principal_major * SCALE))
    wins = period_windows(start, start, N)
    seed = start if disb_on_period == 0 else wins[disb_on_period - 1][1]
    if disb_on_period:                       # re-anchor month-end on the real seed
        wins = period_windows(start, seed, N)
    related = wins[disb_on_period:]
    lengths = [(d - f).days for f, d in related]
    rfs = [rate_factor(Decimal(str(annual_pct)), L, L) for L in lengths]
    level = level_installment_minor(principal_minor, rfs)
    rows = build(principal_minor, rfs, level, lengths)
    if which == "none":
        return rows
    if which == "source":
        return readjust_loop_AS_SOURCE(principal_minor, rfs, lengths, rows, trace)
    # "text": the document says n == NumberOfRepayments, so an implementer
    # reading DEC-1 alone uses N here, not len(related).
    return readjust_loop_AS_TEXT(principal_minor, rfs, lengths, rows, N, trace)


def fmt(m):
    return f"{m // 100}.{abs(m) % 100:02d}"


def show(tag, rows):
    ti = sum(r["interest"] for r in rows)
    print(f"    {tag}: level={fmt(rows[0]['emi'])} final={fmt(rows[-1]['emi'])} "
          f"totalInterest={fmt(ti)}")


if __name__ == "__main__":
    print(__doc__)
    print("=" * 78)
    print("PART 1 -- does the TEXT ALONE reproduce the committed observations?")
    print("(observations quoted from .softhouse/reviews/t23-probe/, NOT re-taken)")
    print("=" * 78)

    cases = [
        (100, 6, "7.0", 0, "t23 / DEC-1 4.3: final installment 17.00 after a -0.01 residual"),
        (1014632, 6, "7.0", 0, "t23-probe2 line 4: level 172574.64, final 172574.62, interest 20815.82"),
        (127704, 36, "16.8", 0, "t23-probe2 line 12: level 4540.30, final 4540.06, interest 35746.56"),
        (1200000, 6, "21.6", 0, "t23-probe Q0a: level 212787.28, final 212787.30, interest 76723.70"),
        (1200000, 6, "21.6", 1, "t23-probe Q0b: level 253114.12, final 253114.10, interest 65570.58"),
    ]
    for p, n, r, j, note in cases:
        print(f"\n--- {p} / {n} x {r}%  disbursement on "
              f"{'ScheduleStartDate' if j == 0 else f'period {j} due date'} ---")
        tr_t, tr_s = [], []
        show("no loop      ", generate(p, n, r, disb_on_period=j, which="none"))
        show("AS TEXT   n=N", generate(p, n, r, disb_on_period=j, which="text", trace=tr_t))
        show("AS SOURCE n=|related|", generate(p, n, r, disb_on_period=j, which="source", trace=tr_s))
        for t in tr_t:
            print(f"        text  : {t}")
        for t in tr_s:
            print(f"        source: {t}")
        print(f"      COMMITTED OBSERVATION: {note}")
