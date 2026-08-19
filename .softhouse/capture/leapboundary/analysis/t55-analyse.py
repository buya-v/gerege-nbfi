#!/usr/bin/env python3
"""T55 -- discrimination, invariants and branch re-derivation for the leap-boundary captures.

CONTACTS NO ORACLE.  Reads only the raw responses committed under ../out/.

Three jobs:

 1. EXACT-TEXT SIDECARS.  Fineract's REST layer serialises BigDecimal as a JSON *number*
    (finding T44-X1), so the raw bytes are float-shaped on the wire.  Every raw file gets a
    `*-exact.json` sidecar in which every number is a JSON STRING carrying the literal
    characters that were on the wire, produced with json.loads(text, parse_float=str,
    parse_int=str) so no binary double is ever constructed.  All comparison and all
    re-derivation runs off the sidecars, never off the raw floats.

 2. DISCRIMINATION.  For every pair of captures that differ ONLY in the product's day-count
    setting, a FULL-CELL comparison: every period row, every field, plus the plan totals.
    Reports cells compared, cells differing (INCLUDING the zeroes -- a proven zero is the
    result, not a gap) and the largest difference in MINOR UNITS.

 3. BRANCH RE-DERIVATION.  A cell difference proves the setting is honoured.  It does not by
    itself prove WHICH branch ran.  For each period this recomputes both candidate readings
    at the ratified MathContext(19, HALF_UP) -- the partial-period arm
    (ProgressiveEMICalculator.java:1526-1530 -> calculatePeriodFractions :1548-1568 ->
    rateFactorByRepaymentPartialPeriod :1969-1980) and the plain ACT/ACT branch
    (:1533-1535 -> rateFactorByRepaymentPeriod :1950-1963) -- from the OBSERVED opening
    balance and the OBSERVED dates, and reports which one the oracle's OBSERVED interest
    matches.  The balances, dates and interests are OBSERVATIONS; the two candidate columns
    are RE-DERIVATIONS and are labelled as such.

NO FLOAT.  decimal.Decimal only, constructed from exact decimal text.  Money differences are
reported in integer MINOR UNITS (MNT has 2 decimal places, ISO 4217 496).
"""
import json
import os
import sys
from calendar import isleap
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, os.pardir, "out")

# Ratified production MathContext.  MoneyHelper.PRECISION = 19 is a compile-time constant
# [VERIFIED: fineract-core/.../MoneyHelper.java:35, :91-93]; the mode is the tenant's, HALF_UP
# (RoundingMode ordinal 4) [asserted by the preconditions gate, out/preconditions.txt].
PREC = 19
ROUND = ROUND_HALF_UP
MINOR = Decimal("0.01")          # MNT minor unit
SCALE19 = Decimal("1E-19")

fails = []


def bad(msg):
    fails.append(msg)
    print("  FAIL  " + msg)


# ---------------------------------------------------------------- 1. exact-text sidecars
def sidecars():
    print("== exact-text sidecars ==")
    n = 0
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith("-raw.json"):
            continue
        with open(os.path.join(OUT, fn)) as fh:
            text = fh.read()
        # parse_float=str / parse_int=str: the number NEVER becomes a Python float or int.
        doc = json.loads(text, parse_float=str, parse_int=str)
        side = fn[:-len("-raw.json")] + "-exact.json"
        with open(os.path.join(OUT, side), "w") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        # assert the sidecar carries ZERO bare JSON numbers
        with open(os.path.join(OUT, side)) as fh:
            body = fh.read()
        reloaded = json.loads(body)
        if _has_number(reloaded):
            bad("%s contains a bare JSON number" % side)
        n += 1
    print("  %d sidecars written, all with ZERO bare JSON numbers" % n)
    return n


def _has_number(o):
    if isinstance(o, bool):
        return False
    if isinstance(o, (int, float)):
        return True
    if isinstance(o, dict):
        return any(_has_number(v) for v in o.values())
    if isinstance(o, list):
        return any(_has_number(v) for v in o)
    return False


def load(cid):
    with open(os.path.join(OUT, cid + "-exact.json")) as fh:
        return json.load(fh)


# ---------------------------------------------------------------- cells
MONEYISH = (
    "principalDue", "principalOriginalDue", "principalOutstanding", "principalPaid",
    "principalLoanBalanceOutstanding", "interestDue", "interestOriginalDue",
    "interestOutstanding", "interestPaid", "feeChargesDue", "penaltyChargesDue",
    "totalOriginalDueForPeriod", "totalDueForPeriod", "totalPaidForPeriod",
    "totalOutstandingForPeriod", "totalActualCostOfLoanForPeriod", "totalOverdue",
    "totalInstallmentAmountForPeriod", "totalCredits",
    "totalInterestCharged", "totalPrincipalDisbursed", "totalPrincipalExpected",
    "totalPrincipalPaid", "totalRepaymentExpected", "totalOutstanding",
    "totalFeeChargesCharged", "totalPenaltyChargesCharged", "principalDisbursed",
)


def cells(doc):
    """Flatten a response into name -> exact text.  Every period row, every field, plus totals."""
    c = {}
    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        if isinstance(v, (str, bool)):
            c["plan." + k] = str(v)
    for i, p in enumerate(doc.get("periods", [])):
        pref = "row%d." % i
        for k, v in sorted(p.items()):
            if isinstance(v, list):          # date arrays -> yyyy-mm-dd
                c[pref + k] = "-".join("%02d" % int(x) for x in v)
            elif isinstance(v, (str, bool)):
                c[pref + k] = str(v)
    return c


def diff(a_id, b_id):
    A, B = cells(load(a_id)), cells(load(b_id))
    keys = sorted(set(A) | set(B))
    d = []
    worst = 0
    worst_cell = None
    for k in keys:
        av, bv = A.get(k), B.get(k)
        if av != bv:
            d.append((k, av, bv))
            fld = k.split(".", 1)[1]
            if fld in MONEYISH and av is not None and bv is not None:
                try:
                    delta = abs((Decimal(av) - Decimal(bv)) / MINOR)
                    if delta > worst:
                        worst, worst_cell = delta, k
                except Exception:
                    pass
    return len(keys), d, worst, worst_cell


# ---------------------------------------------------------------- 3. branch re-derivation
def d_(x):
    return Decimal(str(x))


def as_date(a):
    y, m, dd = (int(x) for x in a.split("-"))
    return date(y, m, dd)


def year_len(y):
    return 366 if isleap(y) else 365


def contains_feb29(frm, due):
    """isPeriodContainsFeb29 [VERIFIED: ProgressiveEMICalculator.java:1330-1340] --
    DateUtils.isDateInRangeFromExclusiveToInclusive(leapDay, from, due): from < leapDay <= due."""
    for y in range(frm.year, due.year + 1):
        if isleap(y):
            ld = date(y, 2, 29)
            if frm < ld <= due:
                return True
    return False


def arm_factor(rate, frm, due):
    """calculatePeriodFractions [VERIFIED: :1548-1568] with the 31-December boundary
    (isInterestRecognitionOnDisbursementDate = false on products 3/4/7, asserted in
    PostgreSQL), then rateFactorByRepaymentPartialPeriod [VERIFIED: :1969-1980]."""
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        cum = Decimal(0)
        segs = []
        actual = frm
        y = frm.year
        endy = due.year
        while y <= endy:
            fdue = due if y == endy else date(y, 12, 31)
            days = (fdue - actual).days
            cum = cum + (Decimal(days) / Decimal(year_len(y)))
            segs.append((y, days, year_len(y)))
            actual = fdue
            y += 1
        rf = rate * cum          # ONE.multiply(cum) is exact; interestRate.multiply(ifp, mc)
    return rf.quantize(SCALE19, rounding=ROUND), segs


def plain_factor(rate, frm, due, days_in_year):
    """rateFactorByRepaymentPeriod(rate, actualDaysInPeriod, ONE, daysInYear, ONE, ONE)
    [VERIFIED: :1950-1963], reached from :1533-1535 when daysInMonthType == ACTUAL."""
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND
        ifp = (Decimal((due - frm).days) * Decimal(1)) / Decimal(days_in_year)
        rf = rate * ifp
    return rf.quantize(SCALE19, rounding=ROUND)


def days_in_year_for(strategy, frm, p_from, p_due):
    """getNumberOfDays [VERIFIED: :1346-1353] for daysInYearType ACTUAL."""
    n = year_len(frm.year)
    if n == 366 and strategy == "FEB_29_PERIOD_ONLY":
        n = 366 if contains_feb29(p_from, p_due) else 365
    return n


def arm_entered(strategy, frm, due, p_from, p_due):
    """partialPeriodCalculationNeeded [VERIFIED: :1505-1507] for daysInYearType ACTUAL."""
    if due.year - frm.year <= 0:
        return False
    if strategy == "FEB_29_PERIOD_ONLY" and not contains_feb29(p_from, p_due):
        return False
    return True


RATE = Decimal("21.6") / Decimal(100)     # calcNominalInterestRatePercentage [:1318-1320]
STRATEGY = {"p7": "UNSET", "p3": "FULL_LEAP_YEAR", "p4": "FEB_29_PERIOD_ONLY"}


def rederive(cid):
    """For each repayment period: re-derive both candidate readings from the OBSERVED opening
    balance and OBSERVED dates, and say which the OBSERVED interest matches.

    Only the FIRST interest period of a repayment period is modelled here.  On a single
    disbursement at the schedule start every repayment period after the first has exactly one
    interest period, so the model is exact for those; period 1 carries a zero-length interest
    period at the disbursement date in addition, which does not change the factor.  Periods
    where the model does not reproduce EITHER candidate are reported as UNATTRIBUTED, never
    quietly dropped."""
    doc = load(cid)
    strat = STRATEGY[cid.rsplit("-", 1)[1]]
    rows = []
    bal = None
    for p in doc["periods"]:
        if "period" not in p:                     # the disbursement row
            bal = Decimal(p["principalLoanBalanceOutstanding"])
            continue
        frm, due = as_date(p["fromDate"]), as_date(p["dueDate"])
        obs = Decimal(p["interestOriginalDue"])
        entered = arm_entered(strat, frm, due, frm, due)
        af, segs = arm_factor(RATE, frm, due)
        pf = plain_factor(RATE, frm, due, days_in_year_for(strat, frm, frm, due))
        with localcontext() as ctx:
            ctx.prec = PREC
            ctx.rounding = ROUND
            ai = (bal * af).quantize(MINOR, rounding=ROUND)
            pi = (bal * pf).quantize(MINOR, rounding=ROUND)
        verdict = ("ARM" if obs == ai else "") + ("PLAIN" if obs == pi else "")
        if obs == ai == pi:
            verdict = "COINCIDE"
        elif not verdict:
            verdict = "UNATTRIBUTED"
        rows.append(dict(period=p["period"], frm=frm, due=due, days=(due - frm).days,
                         bal=bal, obs=obs, arm_i=ai, plain_i=pi, arm_f=af, plain_f=pf,
                         segs=segs, entered=entered, verdict=verdict,
                         f29=contains_feb29(frm, due)))
        bal = Decimal(p["principalLoanBalanceOutstanding"])
    return rows


# ---------------------------------------------------------------- invariants
def invariants(cid):
    """Property invariants, per capture.  A violation is REPORTED as a finding, not discarded."""
    doc = load(cid)
    res = []
    disb = None
    periods = []
    for p in doc["periods"]:
        if "period" not in p:
            disb = Decimal(p["principalLoanBalanceOutstanding"])
        else:
            periods.append(p)

    # I1 principal portions sum to principal exactly
    sp = sum((Decimal(p["principalOriginalDue"]) for p in periods), Decimal(0))
    res.append(("I1 principal portions sum to principal exactly",
                sp == disb, "sum=%s principal=%s" % (sp, disb)))
    # I2 closing balance exactly zero
    last = Decimal(periods[-1]["principalLoanBalanceOutstanding"])
    res.append(("I2 closing balance exactly zero", last == 0, "closing=%s" % last))
    # I3 period splits sum to the period total
    ok3, det3 = True, []
    for p in periods:
        parts = sum((Decimal(p.get(k, "0")) for k in
                     ("principalOriginalDue", "interestOriginalDue", "feeChargesDue",
                      "penaltyChargesDue")), Decimal(0))
        tot = Decimal(p["totalOriginalDueForPeriod"])
        if parts != tot:
            ok3 = False
            det3.append("row%s parts=%s total=%s" % (p["period"], parts, tot))
    res.append(("I3 period splits sum to the period total", ok3, "; ".join(det3) or "all rows"))
    # I4 due dates strictly monotonic
    ds = [as_date(p["dueDate"]) for p in periods]
    res.append(("I4 due dates strictly monotonic", all(b > a for a, b in zip(ds, ds[1:])),
                " ".join(str(x) for x in ds)))
    # I5 interest portions sum to totalInterestCharged
    si = sum((Decimal(p["interestOriginalDue"]) for p in periods), Decimal(0))
    ti = Decimal(doc["totalInterestCharged"])
    res.append(("I5 interest portions sum to totalInterestCharged", si == ti,
                "sum=%s total=%s" % (si, ti)))
    # I6 every money cell has at most 2 decimal places (MNT minor unit)
    ok6, det6 = True, []
    for k, v in cells(doc).items():
        fld = k.split(".", 1)[1]
        if fld in MONEYISH:
            try:
                exp = -Decimal(v).as_tuple().exponent
            except Exception:
                continue
            if exp > 2:
                ok6 = False
                det6.append("%s=%s" % (k, v))
    res.append(("I6 every money cell is at most 2 dp (MNT minor unit)", ok6,
                "; ".join(det6) or "all cells"))
    # I7 balance recursion: opening - principalDue == closing, row by row
    ok7, det7 = True, []
    b = disb
    for p in periods:
        c = Decimal(p["principalLoanBalanceOutstanding"])
        if b - Decimal(p["principalOriginalDue"]) != c:
            ok7 = False
            det7.append("row%s %s-%s!=%s" % (p["period"], b, p["principalOriginalDue"], c))
        b = c
    res.append(("I7 balance recursion opening - principalDue == closing", ok7,
                "; ".join(det7) or "all rows"))
    return res


# ---------------------------------------------------------------- shapes
SHAPES = [
    # id,          what the shape is for
    ("LB-LEAPIN",   "365 -> 366 crossing in period 2 (ANCHOR: same shape as T48's T48B-PUREB)"),
    ("LB-LEAPOUT",  "366 -> 365 crossing in period 2 (NEW: no captured PAIR held this direction)"),
    ("LB-NONLEAP",  "365 -> 365 crossing in period 2 (CONTROL for T48-N4: must be 0 cells)"),
    ("LB-DEC15IN",  "365 -> 366, 16-day first segment"),
    ("LB-DEC15OUT", "366 -> 365, 16-day first segment"),
    ("LB-DEC15NL",  "365 -> 365, 16-day first segment (CONTROL)"),
    ("LB-DEC31",    "first segment is ZERO days; from-date year is leap"),
    ("LB-F29CROSS", "crossing period CONTAINS 29 Feb 2024 -> FEB_29_PERIOD_ONLY takes the arm too"),
    ("LB-MULTI3",   "ONE period spanning TWO 31-Dec boundaries, NO 29 Feb in the period"),
    ("LB-MULTI3F",  "ONE period spanning TWO 31-Dec boundaries, CONTAINS 29 Feb 2024"),
    ("LB-HALFYR",   "semi-annual: period 1 crosses and contains 29 Feb; period 2 starts in the leap year"),
]

PAIRS = [("p7", "p4", "UNSET (arm live) vs FEB_29_PERIOD_ONLY"),
         ("p3", "p4", "FULL_LEAP_YEAR vs FEB_29_PERIOD_ONLY"),
         ("p7", "p3", "UNSET vs FULL_LEAP_YEAR (must be identical: FULL_LEAP_YEAR is the default reading)")]


def main():
    sidecars()

    print()
    print("=" * 100)
    print("DISCRIMINATION TABLE -- full-cell comparison.  Zeroes are results, not gaps.")
    print("=" * 100)
    print("%-12s %-38s %7s %7s %14s  %s" %
          ("shape", "pair", "cells", "differ", "max minor u", "largest-diff cell"))
    table = []
    for sid, _why in SHAPES:
        for a, b, label in PAIRS:
            n, d, worst, wc = diff("%s-%s" % (sid, a), "%s-%s" % (sid, b))
            table.append((sid, "%s vs %s" % (a, b), label, n, len(d), worst, wc, d))
            print("%-12s %-38s %7d %7d %14s  %s" %
                  (sid, "%s vs %s  (%s)" % (a, b, label.split(" (")[0]), n, len(d),
                   worst if d else "-", wc or "-"))
    print()
    for sid, pair, _label, n, nd, worst, wc, d in table:
        if pair != "p7 vs p4":
            continue
        print("-- %s  %s : %d of %d cells differ%s" %
              (sid, pair, nd, n, ("" if nd == 0 else ", max %s minor units at %s" % (worst, wc))))
        for k, av, bv in d[:8]:
            print("     %-42s %-16s | %-16s" % (k, av, bv))
        if len(d) > 8:
            print("     ... %d more" % (len(d) - 8))

    # p7 vs p3 must be identical everywhere: an UNSET strategy reads as the FULL_LEAP_YEAR
    # behaviour because getNumberOfDays only special-cases FEB_29_PERIOD_ONLY [:1349].
    for sid, pair, _l, n, nd, _w, _wc, _d in table:
        if pair == "p7 vs p3" and nd != 0:
            bad("%s: p7 vs p3 differ on %d of %d cells -- UNSET and FULL_LEAP_YEAR must coincide"
                % (sid, nd, n))

    print()
    print("=" * 100)
    print("BRANCH RE-DERIVATION -- balances/dates/interest are OBSERVED; the two candidate")
    print("columns are RE-DERIVED at MathContext(19, HALF_UP) from the cited source.")
    print("=" * 100)
    for sid, why in SHAPES:
        print()
        print("### %s -- %s" % (sid, why))
        for suf in ("p7", "p3", "p4"):
            cid = "%s-%s" % (sid, suf)
            print("  %s  [strategy %s]" % (cid, STRATEGY[suf]))
            print("    %-3s %-24s %5s %14s %14s %14s %14s  %-12s %s" %
                  ("per", "from -> due", "days", "opening bal", "OBS interest",
                   "ARM re-deriv", "PLAIN re-deriv", "verdict", "segments d/len"))
            for r in rederive(cid):
                segtxt = " + ".join("%d/%d" % (d, l) for _y, d, l in r["segs"]) if r["entered"] or len(r["segs"]) > 1 else "-"
                print("    %-3s %s -> %s %5d %14s %14s %14s %14s  %-12s %s" %
                      (r["period"], r["frm"], r["due"], r["days"], r["bal"], r["obs"],
                       r["arm_i"], r["plain_i"], r["verdict"], segtxt))
                if r["verdict"] == "UNATTRIBUTED":
                    bad("%s period %s matches NEITHER candidate reading (obs=%s arm=%s plain=%s)"
                        % (cid, r["period"], r["obs"], r["arm_i"], r["plain_i"]))
                # the predicted branch must be the observed branch
                want = "ARM" if r["entered"] else "PLAIN"
                if r["verdict"] not in (want, "COINCIDE"):
                    bad("%s period %s: source predicts %s, observation says %s"
                        % (cid, r["period"], want, r["verdict"]))

    print()
    print("=" * 100
          )
    print("INVARIANTS -- per capture")
    print("=" * 100)
    allok = True
    for sid, _why in SHAPES:
        for suf in ("p7", "p3", "p4"):
            cid = "%s-%s" % (sid, suf)
            res = invariants(cid)
            st = "PASS" if all(ok for _n, ok, _d in res) else "FAIL"
            if st == "FAIL":
                allok = False
            print("  %-16s %s   " % (cid, st) + ", ".join(
                "%s=%s" % (n.split()[0], "ok" if ok else "VIOLATED") for n, ok, _d in res))
            for n, ok, det in res:
                if not ok:
                    bad("%s INVARIANT VIOLATED -- %s : %s" % (cid, n, det))
    if allok:
        print("  all 33 captures: I1 I2 I3 I4 I5 I6 I7 all PASS")

    print()
    if fails:
        print("T55 ANALYSIS FAILED -- %d breach(es):" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("== T55 analysis PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
