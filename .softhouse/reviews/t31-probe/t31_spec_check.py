#!/usr/bin/env python3
"""
T31 -- FROM-TEXT SPEC CHECK of DEC-1 **revision 5**.

*** NOT RUN AGAINST A LIVE ORACLE. ***
No Fineract instance is reachable in this sandbox (no Docker, no PostgreSQL).
Every expected value below is QUOTED from an observation ALREADY COMMITTED
under `.softhouse/reviews/t23-probe/` (the list and the expectations are taken
from `.softhouse/reviews/t29-probe/t29_validate.py`; the MODEL below is not).
Nothing here is a new oracle observation and nothing here may be promoted to
the vector store.

WHAT THIS FILE IS
-----------------
A literal transcription of DEC-1 **revision 5**'s normative text -- and of
NOTHING ELSE -- into a runnable schedule generator in exact integer minor units:

  ADR section 2.1          the recurrence, the interest-first / principal-
                           balancing split, the final-period residual
  ADR section 4.1          the two rounding senses, the exact 1 + rateFactor,
                           the currency layer
  ADR section 4.2          the month-end step and re-anchor to the disbursement
  ADR section 4.3          the final-period residual `diff`
  ADR section 4.3.1        the related-repayment-period definition, the effective
                           due date, and the EMI re-adjust loop, steps 1-8
  ADR section 4.3.2        THE PER-PERIOD INTEREST COMPUTATION (new in rev 5)
  ADR section 4.9          fixed 30/360, monthly

It is written against the revision-5 text only; the pinned Java was consulted
when WRITING that text, not when writing this script.

WHAT IT PROVES
--------------
  (A) The corrected text still reproduces all 13 already-committed observations.
  (B) The corrected text DISCRIMINATES: the two readings re-review T29 found
      revision 4 could not exclude --
        * `n == NumberOfRepayments` (P0-T29-1), and
        * the textbook `interest = balance * rateFactor` (P0-T29-2)
      -- each return DIFFERENT money from the revision-5 text on the shapes T29
      cited.  A specification that cannot tell the wrong answer from the right
      one has not been fixed.

MONEY REPRESENTATION
--------------------
Every monetary quantity is a Python `int` in MINOR UNITS.  `Decimal` is used
only for the dimensionless intermediates DEC-1 explicitly says are NOT money
(the per-period rate factor, the `fn` recurrence, and the three mc-rounded
operations of section 4.3.2, whose operands are exact decimals).  There is no
float32/float64/float literal or cast anywhere in this file.
"""

from decimal import Decimal, localcontext, ROUND_HALF_UP
from datetime import date
import calendar

# --- the Run-1 graded domain (ADR section 3.1) ----------------------------
SIG = 19   # Rounding.SignificantDigits
RFS = 19   # Rounding.RateFactorScale
MUD = 2    # Currency.MinorUnitDigits
UNIT = 10 ** MUD


# ==========================================================================
# ADR section 4.1 -- the two rounding senses
# ==========================================================================
def round_mc(x: Decimal) -> Decimal:
    """Round to SIG SIGNIFICANT DIGITS under Rounding.Mode (HALF_UP).

    This is the `round_mc(.)` of ADR section 4.3.2 and the `mc` of section 4.1.
    """
    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_UP
        return +x                     # unary plus applies the context rounding


def mul_mc(a: Decimal, b: Decimal) -> Decimal:
    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_UP
        return a * b


def div_mc(a: Decimal, b: Decimal) -> Decimal:
    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_UP
        return a / b


def to_money(x: Decimal) -> int:
    """A quantity BECOMES MONEY: setScale(MinorUnitDigits, Rounding.Mode)
    (ADR section 4.3.2 step 1; Money.java:40-53, scale at :52).  Returns
    int64 minor units."""
    with localcontext() as c:
        c.prec = 60
        c.rounding = ROUND_HALF_UP
        return int((x * UNIT).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def half_up_div_int(num: int, den: int) -> int:
    """ADR section 4.3.1 step 3's closed form, in pure integers:
    sign(x) * (2|x| + d) / (2d)  -- nearest, ties away from zero."""
    assert den > 0
    s = -1 if num < 0 else 1
    return s * ((2 * abs(num) + den) // (2 * den))


# ==========================================================================
# ADR section 4.2 -- repayment period boundaries, monthly
# ==========================================================================
def add_months(d: date, k: int) -> date:
    m = d.month - 1 + k
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def reanchor(d: date, seed: date) -> date:
    """Step 2: monthly AND seed day > 28 AND stepped day >= 28."""
    if seed.day > 28 and d.day >= 28:
        return date(d.year, d.month,
                    min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def windows(start: date, seed: date, n: int, every: int = 1):
    out, prev = [], start
    for _ in range(n):
        nxt = reanchor(add_months(prev, every), seed)
        out.append((prev, nxt))
        prev = nxt
    return out


# ==========================================================================
# ADR section 4.1 / 4.9 -- the per-period rate factor, fixed 30/360, monthly
#   interestFraction = 30 * repaymentEvery / 360            @mc
#   rf = rate * interestFraction @mc * actualDays @mc / calcDays @mc
#        then setScale(RateFactorScale, Rounding.Mode)
# ==========================================================================
def rate_factor(rate_num: int, rate_den: int, actual_days: int, calc_days: int,
                every: int = 1) -> Decimal:
    if calc_days == 0:
        return Decimal(0)
    r = div_mc(Decimal(rate_num), Decimal(rate_den))          # nominal / 100
    frac = div_mc(mul_mc(Decimal(30), Decimal(every)), Decimal(360))
    v = mul_mc(r, frac)
    v = mul_mc(v, Decimal(actual_days))
    v = div_mc(v, Decimal(calc_days))
    with localcontext() as c:
        c.prec = 60
        c.rounding = ROUND_HALF_UP
        return v.quantize(Decimal(1).scaleb(-RFS), rounding=ROUND_HALF_UP)


# ==========================================================================
# ADR section 4.3.1 -- RELATED REPAYMENT PERIODS (the P0-T29-1 definition)
# ==========================================================================
def first_related_index(wins, disb: date):
    """The effective due date, then the related suffix, exactly as ADR
    section 4.3.1's "Related repayment periods" block defines them:

      1. find the repayment period CONTAINING the disbursement --
         [FromDate, DueDate] inclusive for the FIRST period,
         (FromDate, DueDate] for every later one;
      2. if that period's DueDate EQUALS the disbursement date, the effective
         due date is the NEXT period's DueDate, else the matched period's own.

    related = periods whose DueDate is not before the effective due date, so the
    index returned is the index of the first related period.  `None` means the
    request is outside the graded domain (disbursement on/after the last due
    date, or before the schedule start) -- refused, never answered.
    """
    hit = None
    for i, (f, d) in enumerate(wins):
        inside = (f <= disb <= d) if i == 0 else (f < disb <= d)
        if inside:
            hit = i
            break
    if hit is None:
        return None
    if wins[hit][1] == disb:                       # step 2: push to the next
        return hit + 1 if hit + 1 < len(wins) else None
    return hit


# ==========================================================================
# ADR section 2.1 -- the level installment, over the RELATED periods only
#   (section 4.3.1: "computed over, and written to, the related periods only")
# ==========================================================================
def level_installment(balance_minor: int, rfs) -> int:
    plus1 = [Decimal(1) + r for r in rfs]          # EXACT, no MathContext

    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_UP
        prod = Decimal(1)
        for v in plus1:
            prod = prod * v
        fn = Decimal(1)
        for v in plus1[1:]:
            fn = Decimal(1) + fn * v
        emi = prod * (Decimal(balance_minor) / UNIT) / fn
    return to_money(emi)


# ==========================================================================
# ADR section 4.3.2 -- THE PER-PERIOD INTEREST COMPUTATION (new in revision 5)
# ==========================================================================
def interest_of_interest_period(balance_minor: int, rf_till_due: Decimal,
                                length: int, length_till_due: int,
                                textbook: bool = False) -> Decimal:
    """Section 4.3.2, transcribed literally:

        if lengthTillPeriodDueDate == 0 { interest := 0 }
        else {
          B  := outstanding principal balance carried into this interest period
          t1 := round_mc( B  * rateFactorTillPeriodDueDate )   # operation (1)
          t2 := round_mc( t1 / lengthTillPeriodDueDate    )    # operation (2)
          t3 := round_mc( t2 * length                     )    # operation (3)
          interest := t3
        }

    `textbook=True` is the READING THE SPEC MUST EXCLUDE -- the single
    `round_mc(B * rateFactor)` that revision 4's prose licensed.  It exists in
    this file only so the discrimination check below can run it.
    """
    if length_till_due == 0:
        return Decimal(0)
    b = Decimal(balance_minor) / UNIT
    t1 = mul_mc(b, rf_till_due)                          # operation (1)
    if textbook:
        return t1
    t2 = div_mc(t1, Decimal(length_till_due))            # operation (2)
    t3 = mul_mc(t2, Decimal(length))                     # operation (3)
    return t3


def build(disbursed_minor: int, periods, first_rel: int, emi_of,
          textbook: bool = False):
    """Section 4.3.2 "From interest period to row", steps 1-4.

    `periods` is a list of (from, due, length, rateFactorTillPeriodDueDate).
    Inside the graded domain the segmentation table of section 4.3.2 says every
    interest period carrying a NON-ZERO balance has lengthTillPeriodDueDate ==
    length and spans the whole repayment window, and every segment where they
    differ carries a zero balance and contributes exactly zero -- so one
    balance-carrying segment per repayment period reproduces the partition for
    the two shapes the corpus samples (disbursement on a FromDate, or on a
    DueDate).  The third shape -- a disbursement strictly inside a period -- is
    ungraded and deliberately not exercised here.
    """
    rows = []
    bal = 0
    for i, (f, d, L, rf) in enumerate(periods):
        if i == first_rel:
            bal += disbursed_minor          # the amount enters the LATER segment
        emi = emi_of(i)
        # step 1: sum the interest periods' t3, THEN make it money, clamp at 0
        t3_sum = interest_of_interest_period(bal, rf, L, L, textbook)
        calc_int = max(0, to_money(t3_sum))
        due_int = min(calc_int, emi)        # step 2: cap at the installment
        due_prin = max(0, emi - due_int)    # step 3: balancing remainder
        bal = max(0, bal - due_prin)        # step 4: clamped roll-forward
        rows.append({"emi": emi, "interest": due_int, "principal": due_prin,
                     "outstanding": bal, "from": f, "due": d})
    return rows


# ==========================================================================
# ADR section 4.3 -- the final-period residual
# ==========================================================================
def apply_residual(disbursed_minor: int, rows):
    tot_int = sum(r["interest"] for r in rows)
    tot_emi = sum(r["emi"] for r in rows)
    diff = disbursed_minor + tot_int - tot_emi     # every sum at CURRENCY scale
    last = rows[-1]
    last["emi"] += diff
    last["principal"] = max(0, last["emi"] - last["interest"])
    prev = rows[-2]["outstanding"] if len(rows) > 1 else disbursed_minor
    last["outstanding"] = max(0, prev - last["principal"])
    return diff


def rebuild(disbursed_minor, periods, first_rel, level_minor,
            related_only=True, textbook=False):
    """Section 4.3.1 step 6: `adjusted` is written onto exactly the RELATED
    periods; rows before the first related period keep their ZERO installment.

    `related_only=False` is the READING THE SPEC MUST EXCLUDE -- revision 4's
    "inside the graded domain that is ALL n periods".
    """
    if related_only:
        emi_of = (lambda i: level_minor if i >= first_rel else 0)
    else:
        emi_of = (lambda i: level_minor)
    rows = build(disbursed_minor, periods, first_rel, emi_of, textbook)
    apply_residual(disbursed_minor, rows)
    return rows


# ==========================================================================
# ADR section 4.3.1 -- the EMI re-adjust loop, steps 1-8, transcribed literally
# `rows` is INDEXED OVER THE RELATED PERIODS (revision 5).
# ==========================================================================
def readjust(disbursed_minor, periods, first_rel, rows, n,
             related_only=True, textbook=False, trace=None):
    adjust_counter = 1                                             # :1262
    while True:
        # 1. the pair                                    :1266 -> :1778-1789
        if n < 2:
            break
        original = rows[-2]["emi"]
        emi_difference = rows[-1]["emi"] - original                # SIGNED

        # 2. guard, all three conjuncts            EmiAdjustment.java:31-36
        lower_half = n // 2
        if not (lower_half > 0
                and emi_difference != 0
                and abs(emi_difference) * 100 > lower_half * UNIT):
            break

        # 3. magnitude; uncountablePeriods counted over the RELATED list
        uncountable = 0        # nothing is paid on a schedule this contract generates
        d = max(1, n - uncountable)
        adjustment = half_up_div_int(emi_difference, d)

        # 4. candidate (the installment-multiple pass is the identity here)
        adjusted = original + adjustment

        # 5. no-change break
        if adjusted == original:
            break

        # 6. trial rebuild -- RELATED periods only
        trial = rebuild(disbursed_minor, periods, first_rel, adjusted,
                        related_only, textbook)

        # 7. adoption test, strict; failure DISCARDS
        new_difference = trial[-1]["emi"] - trial[-2]["emi"]
        if not (abs(new_difference) < abs(emi_difference)):
            break

        # 8. adopt, bound
        if trace is not None:
            trace.append(f"ADOPT#{adjust_counter} {original}->{adjusted}")
        rows = trial
        adjust_counter += 1
        if adjust_counter > 3:
            break
    return rows


# ==========================================================================
# whole-schedule generation, from the revision-5 text
# ==========================================================================
def generate(principal_major, n_rep, rate_pct, start=date(2024, 1, 1),
             disb=None, reading="spec"):
    """reading:
         "spec"        -- DEC-1 revision 5 exactly as written
         "wrong_n"     -- revision 4's reading in full: `n == NumberOfRepayments`
                          AND step 6's "inside the graded domain that is ALL n
                          periods"
         "wrong_n_only"-- ONLY the value of `n` is wrong; the overwrite set stays
                          the related periods.  This is T29's experiment A
                          isolation, and it is the arm that shows `n` alone moves
                          money while the corpus stays blind.
         "textbook"    -- `interest = round_mc(balance * rateFactor)`
    """
    principal_minor = int(Decimal(str(principal_major)) * UNIT)
    disb = disb or start
    wins = windows(start, disb, n_rep)
    first_rel = first_related_index(wins, disb)
    if first_rel is None:
        return None                       # refused: outside the graded domain
    num, den = Decimal(str(rate_pct)).as_integer_ratio()

    textbook = (reading == "textbook")
    periods = []
    for i, (f, d) in enumerate(wins):
        L = (d - f).days
        rf = rate_factor(num, den * 100, L, L) if i >= first_rel else Decimal(0)
        periods.append((f, d, L, rf))

    rel_rfs = [p[3] for p in periods[first_rel:]]
    level = level_installment(principal_minor, rel_rfs)

    if reading == "wrong_n":
        rows = rebuild(principal_minor, periods, first_rel, level,
                       related_only=False, textbook=textbook)
        return readjust(principal_minor, periods, first_rel, rows,
                        n_rep, related_only=False, textbook=textbook)

    rows = rebuild(principal_minor, periods, first_rel, level,
                   related_only=True, textbook=textbook)
    n = n_rep if reading == "wrong_n_only" else n_rep - first_rel
    return readjust(principal_minor, periods, first_rel, rows, n,
                    related_only=True, textbook=textbook)


def f(m):
    return f"{m // 100}.{abs(m) % 100:02d}"


def triple(rows):
    rel = [x for x in rows if x["emi"] != 0]
    return (f(rel[0]["emi"]), f(rows[-1]["emi"]),
            f(sum(x["interest"] for x in rows)))


# ==========================================================================
# (A) the 13 already-committed observations
#     expectations quoted from .softhouse/reviews/t29-probe/t29_validate.py,
#     whose provenance is .softhouse/reviews/t23-probe/.  NOT re-taken.
# ==========================================================================
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

# (B) the shapes T29 cited as separating the two readings.  These are
# RE-DERIVED CANDIDATE SHAPES TO CAPTURE, never observations; nothing below
# compares them against an oracle value, only the readings against each other.
WRONG_N_SHAPES = [
    (10548069, 6, "16.8", date(2024, 1, 1), date(2024, 2, 1)),
    (1222552,  6, "18.5", date(2024, 1, 1), date(2024, 2, 1)),
    (13549647, 6, "21.6", date(2024, 1, 1), date(2024, 2, 1)),
]
TEXTBOOK_SHAPES = [
    (13202,   6, "16.8", date(2024, 1, 1),  None),
    (3924149, 6, "16.8", date(2024, 1, 31), None),
    (1814727, 6, "21.6", date(2024, 1, 31), None),
]


if __name__ == "__main__":
    print("T31 spec check -- DEC-1 REVISION 5 transcribed from its own text")
    print("NO LIVE ORACLE WAS CONTACTED. Expectations are quoted from committed")
    print("captures; every figure printed for an UNCAPTURED shape is a")
    print("RE-DERIVATION and must never be promoted to the vector store.\n")

    print("(A) reproduction of the 13 already-committed observations")
    print("-" * 72)
    ok = bad = 0
    for p, n, r, disb, expect, prov in CASES:
        got = triple(generate(p, n, r, disb=disb))
        good = got == expect
        ok, bad = ok + good, bad + (not good)
        tag = "  disb=" + str(disb) if disb else ""
        print(f"  {'PASS' if good else 'FAIL'}  P={p:<9} n={n:<3} {r:>5}%{tag:<18}"
              f"  level/final/interest = {got}")
        if not good:
            print(f"        expected {expect}   [{prov}]")
    print(f"\n  {ok} pass, {bad} fail, out of {len(CASES)}\n")

    print("(B1) DISCRIMINATION -- does revision 5's text EXCLUDE `n == NumberOfRepayments`?")
    print("     (P0-T29-1; shapes are T29's re-derived candidates, not observations)")
    print("-" * 72)
    d1 = 0
    for p, n, r, start, disb in WRONG_N_SHAPES:
        a = triple(generate(p, n, r, start=start, disb=disb, reading="spec"))
        b = triple(generate(p, n, r, start=start, disb=disb, reading="wrong_n"))
        c = triple(generate(p, n, r, start=start, disb=disb, reading="wrong_n_only"))
        differs = a != b and a != c
        d1 += differs
        print(f"  {'EXCLUDED' if differs else 'NOT EXCLUDED'}  P={p:<9} n={n} {r:>5}%"
              f"  disb={disb}")
        print(f"        revision 5              : {a}")
        print(f"        rev 4 in full           : {b}")
        print(f"        `n` alone (T29 expt A)  : {c}")
    print(f"\n  BOTH wrong-`n` readings FAIL the revision-5 spec on {d1}/{len(WRONG_N_SHAPES)} shapes\n")

    print("(B2) DISCRIMINATION -- does revision 5's text EXCLUDE `balance * rateFactor`?")
    print("     (P0-T29-2; shapes are T29's re-derived candidates, not observations)")
    print("-" * 72)
    d2 = 0
    for p, n, r, start, disb in TEXTBOOK_SHAPES:
        a = triple(generate(p, n, r, start=start, disb=disb, reading="spec"))
        b = triple(generate(p, n, r, start=start, disb=disb, reading="textbook"))
        differs = a != b
        d2 += differs
        print(f"  {'EXCLUDED' if differs else 'NOT EXCLUDED'}  P={p:<9} n={n} {r:>5}%"
              f"  start={start}")
        print(f"        revision 5 (3 ops) : {a}")
        print(f"        textbook (1 op)    : {b}")
    print(f"\n  the textbook reading FAILS the revision-5 spec on {d2}/{len(TEXTBOOK_SHAPES)} shapes\n")

    print("(C) CONTROL -- how much of each wrong reading the CORPUS can see.")
    print("    `n` alone and the textbook reading both reproduce all 13, which is")
    print("    exactly why the corpus cannot grade either P0 (T29 sections 2.3, 3.3).")
    print("    Revision 4's reading IN FULL is caught at 12/13 -- by Q0b -- because")
    print("    its step-6 'ALL n periods' also overwrites the pre-disbursement row.")
    print("-" * 72)
    for label, reading in (("rev4 full", "wrong_n"),
                           ("`n` alone", "wrong_n_only"),
                           ("textbook", "textbook")):
        agree = sum(1 for p, n, r, disb, expect, _ in CASES
                    if triple(generate(p, n, r, disb=disb, reading=reading)) == expect)
        print(f"  {label:<10}: reproduces {agree}/{len(CASES)} committed observations")

    print()
    verdict = (bad == 0 and d1 == len(WRONG_N_SHAPES) and d2 == len(TEXTBOOK_SHAPES))
    print("VERDICT:", "SPEC CHECK PASSES" if verdict else "SPEC CHECK FAILS")
    raise SystemExit(0 if verdict else 1)
