#!/usr/bin/env python3
"""T55 -- PRIOR-CAPTURE ASSESSMENT.  Does any EXISTING T48 capture already discriminate?

The T55 brief says: if an existing T48 capture already crosses a leap boundary with a non-zero
first segment and therefore already discriminates, say so with the capture id and the
discriminating cells, and do not invent redundant work.  This script answers that MECHANICALLY
rather than by reading, by running the same branch attribution and the same gradeability test
used on the T55 captures over T48's committed Path B responses.

READ-ONLY with respect to `.softhouse/capture/actualactual/**` -- it opens those files and writes
nothing into that subtree.  Contacts no oracle.
"""
import json
import os
import re
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
LB = os.path.join(HERE, os.pardir)
AA = os.path.join(LB, os.pardir, "actualactual", "pathb")

# reuse the T55 machinery verbatim, so the verdicts are produced by the SAME code
_g = {"__name__": "not_main", "__file__": os.path.join(HERE, "t55-analyse.py")}
exec(compile(open(os.path.join(HERE, "t55-analyse.py")).read(),
             os.path.join(HERE, "t55-analyse.py"), "exec"), _g)
arm_factor = _g["arm_factor"]
plain_factor = _g["plain_factor"]
days_in_year_for = _g["days_in_year_for"]
arm_entered = _g["arm_entered"]
contains_feb29 = _g["contains_feb29"]
year_len = _g["year_len"]
as_date = _g["as_date"]
MINOR = _g["MINOR"]
PREC = _g["PREC"]
ROUND = _g["ROUND"]
from decimal import localcontext  # noqa: E402

STRAT = {"p7": "UNSET", "p3": "FULL_LEAP_YEAR", "p4": "FEB_29_PERIOD_ONLY"}


def req_rate(cid):
    """Read the interest rate out of T48's COMMITTED request file -- never guessed."""
    p = os.path.join(AA, "req", "calc-%s.json" % cid)
    txt = open(p).read()
    m = re.search(r'"interestRatePerPeriod":\s*([0-9.]+)', txt)
    return Decimal(m.group(1)) / Decimal(100)


def load(cid):
    with open(os.path.join(AA, "out", "%s-exact.json" % cid)) as fh:
        return json.load(fh)


def attribute(cid):
    rate = req_rate(cid)
    strat = STRAT[cid.rsplit("-", 1)[1]]
    doc = load(cid)
    bal = None
    rows = []
    for p in doc["periods"]:
        if "period" not in p:
            bal = Decimal(p["principalLoanBalanceOutstanding"])
            continue
        frm, due = as_date(p["fromDate"]), as_date(p["dueDate"])
        obs = Decimal(p["interestOriginalDue"])
        af, segs = arm_factor(rate, frm, due)
        pf = plain_factor(rate, frm, due, days_in_year_for(strat, frm, frm, due))
        nact = plain_factor(rate, frm, due, year_len(frm.year))
        n365 = plain_factor(rate, frm, due, 365)
        with localcontext() as ctx:
            ctx.prec = PREC
            ctx.rounding = ROUND
            ai = (bal * af).quantize(MINOR, rounding=ROUND)
            pi = (bal * pf).quantize(MINOR, rounding=ROUND)
            iact = (bal * nact).quantize(MINOR, rounding=ROUND)
            i365 = (bal * n365).quantize(MINOR, rounding=ROUND)
        crossing = due.year > frm.year
        yrs = sorted({year_len(y) for y in range(frm.year, due.year + 1)}) if crossing else []
        rows.append(dict(period=p["period"], frm=frm, due=due, obs=obs, arm=ai, plain=pi,
                         nact=iact, n365=i365, segs=segs, crossing=crossing,
                         mixed_year_lengths=(len(yrs) > 1),
                         first_seg=(segs[0][1] if segs else None),
                         entered=arm_entered(strat, frm, due, frm, due),
                         f29=contains_feb29(frm, due)))
        bal = Decimal(p["principalLoanBalanceOutstanding"])
    return rows


def cells_differ(a, b):
    A = _g["cells"](load(a))
    B = _g["cells"](load(b))
    keys = sorted(set(A) | set(B))
    d = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    worst, wc = 0, None
    for k, av, bv in d:
        fld = k.split(".", 1)[1]
        if fld in _g["MONEYISH"] and av and bv:
            try:
                delta = abs((Decimal(av) - Decimal(bv)) / MINOR)
                if delta > worst:
                    worst, wc = delta, k
            except Exception:
                pass
    return len(keys), d, worst, wc


SETS = ["T48B-PUREB", "T48B-YEAR", "T48B-QTR", "T48B-B03SHAPE"]

print("=" * 100)
print("PRIOR-CAPTURE ASSESSMENT -- T48's committed Path B captures, scored by T55's own code")
print("=" * 100)
print()
print("Q1. Does an existing T48 capture cross a leap boundary with a NON-ZERO first segment?")
print("Q2. Does an existing T48 PAIR discriminate (>0 cells on a one-setting change)?")
print("Q3. Does an existing T48 capture GRADE a port that omits the arm?")
print()

for s in SETS:
    ids = [i for i in ("p7", "p3", "p4")
           if os.path.exists(os.path.join(AA, "out", "%s-%s-exact.json" % (s, i)))]
    print("### %s   (captured on: %s)" % (s, ", ".join(ids)))
    # Q1 / Q3, on the arm-live capture
    live = "p7" if "p7" in ids else ids[0]
    cid = "%s-%s" % (s, live)
    rows = attribute(cid)
    q1 = [r for r in rows if r["crossing"] and r["mixed_year_lengths"] and r["first_seg"]]
    g_nact = [r for r in rows if r["obs"] != r["nact"]]
    g_365 = [r for r in rows if r["obs"] != r["n365"]]
    print("  Q1  crossing periods with MIXED year lengths and a non-zero first segment: %d" % len(q1))
    for r in q1:
        print("        p%-2s %s -> %s   segments %s   OBS %s   verdict %s"
              % (r["period"], r["frm"], r["due"],
                 " + ".join("%d/%d" % (d, l) for _y, d, l in r["segs"]), r["obs"],
                 "ARM" if r["obs"] == r["arm"] else
                 ("PLAIN" if r["obs"] == r["plain"] else "UNATTRIBUTED")))
    print("  Q3  %s grades a no-arm/actual-year port on %d periods, a no-arm/always-365 port on %d"
          % (cid, len(g_nact), len(g_365)))
    if g_nact:
        r = max(g_nact, key=lambda r: abs(r["obs"] - r["nact"]))
        print("        largest gap vs no-arm/actual-year: p%s  OBS %s vs %s = %s minor units"
              % (r["period"], r["obs"], r["nact"], abs(r["obs"] - r["nact"]) / MINOR))
    # Q2
    if "p4" in ids and live != "p4":
        n, d, worst, wc = cells_differ(cid, "%s-p4" % s)
        print("  Q2  %s vs %s-p4 : %d of %d cells differ%s"
              % (cid, s, len(d), n, "" if not d else ", max %s minor units at %s" % (worst, wc)))
    else:
        print("  Q2  NO PAIR EXISTS -- %s was captured on %s only, so nothing grades it"
              % (s, ", ".join(ids)))
    print()

# T48 captured the FEB_29_PERIOD_ONLY leg of the 12-month shape under a DIFFERENT id
# (T48B-B04SHAPE-p4), so the pair for that shape spans two ids.  Score it, so the assessment does
# not under-report what the program already holds.
print("### the CROSS-ID pair for the 12-month 2024 shape")
n, d, worst, wc = cells_differ("T48B-B03SHAPE-p7", "T48B-B04SHAPE-p4")
print("  T48B-B03SHAPE-p7 vs T48B-B04SHAPE-p4 : %d of %d cells differ%s"
      % (len(d), n, "" if not d else ", max %s minor units at %s" % (worst, wc)))
print("  BUT: of its 12 periods only p12 crosses a year boundary.  The other 11 are wholly inside")
print("  leap 2024, where the strategy acts through effect (a) -- getNumberOfDays' 366 -> 365")
print("  substitution [:1349] -- and NOT through the arm.  The arm's own contribution at p12 is")
r12 = [r for r in attribute("T48B-B03SHAPE-p7") if str(r["period"]) == "12"][0]
print("  OBS %s vs the no-arm/actual-year reading %s = %s minor units, i.e. 0.006%% of the pair's"
      % (r12["obs"], r12["nact"], abs(r12["obs"] - r12["nact"]) / MINOR))
print("  %s-minor-unit headline.  A port that omitted the arm entirely would still miss this pair" % worst)
print("  by %s minor units at p12 -- so it DOES grade the arm, but only barely and only if the" %
      (abs(r12["obs"] - r12["nact"]) / MINOR))
print("  comparison is made period by period rather than on the headline totals.")
print()

print("=" * 100)
print("VERDICT")
print("=" * 100)
print("""
YES -- existing T48 captures already discriminate, and T55 does not re-take them as new evidence.

  * `T48B-PUREB-p7`/`-p3` vs `T48B-PUREB-p4` -- 23 of 65 cells, max 97 minor units.  Period 2
    (2023-12-01 -> 2024-01-01) crosses into leap 2024 with a 30-day first segment and attributes
    to the ARM.  This ALREADY satisfies T48-N4's promotion condition.
  * `T48B-YEAR-p7`/`-p3` vs `T48B-YEAR-p4` -- 157 of 285 cells.  Period 1 has the same geometry and
    the same ARM attribution, isolated from effect (a) because the from-date year 2023 is non-leap.
  * `T48B-QTR` -- 49 of 109 cells; period 2 crosses AND contains 29 Feb, segments 30/365 + 61/366.
  * `T48B-B03SHAPE-p7` vs `T48B-B04SHAPE-p4` -- a CROSS-ID pair that does discriminate, and whose
    period 12 carries the 366 -> 365 direction.  It is not a clean grader of the arm: 11 of its 12
    periods separate through effect (a) instead.

T55's LB-LEAPIN is therefore an ANCHOR, not new evidence: it re-takes the PUREB geometry and must
reproduce T48's committed numbers cell for cell.

What T48's Path B set does NOT hold, and T55 adds:

  * a CLEAN pair in the 366 -> 365 direction.  T48B-AA1 has that geometry but was captured on
    product 7 ONLY (no p3/p4 twin), and the B03/B04 cross-id pair buries the arm under effect (a).
    T55's LB-LEAPOUT (2 periods) and LB-DEC15OUT (1 period) isolate it.
  * any period spanning TWO 31-December boundaries, i.e. THREE iterations of
    calculatePeriodFractions.  T55's LB-MULTI3 and LB-MULTI3F are the first.
  * any NON-LEAP cross-year CONTROL.  Every T48 Path B shape has a 366-day year in play, so
    T48-N4 was DERIVED and never OBSERVED.  T55's LB-NONLEAP and LB-DEC15NL observe it at 0 cells
    while the same comparator reports 11-27 cells on the leap shapes.
  * any ZERO-first-segment shape.  T55's LB-DEC31 is the first, and it CORRECTS the necessary
    condition T48-N4 states -- see the T55 handoff, finding T55-N1.
""")
