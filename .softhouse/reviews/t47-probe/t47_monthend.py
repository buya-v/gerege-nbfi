#!/usr/bin/env python3
"""T47 - does the packed-versus-clamped-step rule AS WRITTEN IN DEC-1 REVISION 10
reproduce T46's and T44's figures?

The brief for this task requires a check that the rule as written reproduces

    T44 / T45 / T47  :  59,130  /    701  /    701  / 0
    T46 exhaustive   : 112,147,776 / 45,253 / 45,253 / 0

*from the document's own text*.  So this probe does three things, in order:

  STEP 0  Extract the closed-form block from revision 10 by regex, and assert that
          the functions implemented below are the ones the document prints.  If
          the document's block changes, this probe fails rather than silently
          testing something else.

  LEG A   EXHAUSTIVE OVER THE RULE'S WHOLE INPUT SPACE, not over a date range.
          packed and clamped-step depend only on (a.day, b.day, len(b's month), k).
          Every such class is enumerated and the document's three claims are checked
          on every one:
            A1  packed != clamped  <=>  b.day == len(b) AND a.day > b.day   (k >= 1)
            A2  when it fires, oracle (measured to b.plusDays(1)) == clamped
            A3  when it does not fire, packed == clamped == oracle
          This is a STRONGER statement than any date sweep, because it covers every
          input the functions can receive.

  LEG B   THE 112,147,776-PAIR COUNTS.  Enumerating 112 M pairs in Python is not
          affordable, so the counts are produced by prefix-counting over the 14,976
          dates using the class result from LEG A, and then CROSS-CHECKED against a
          full brute-force enumeration of every ordered pair in a complete
          sub-window (2000-01-01 .. 2004-12-31).  Both must agree on the sub-window
          before the full-range figure is reported.

  LEG C   THE 59,130-PAIR SWEEP, re-run with the CLOSED-FORM functions rather than
          with the step-B pseudocode the inherited model transcribes.  Agreement is
          a cross-check of revision 10's new block against revision 9's existing
          normative text.

No money is computed anywhere in this probe and no float is constructed.
"""
import calendar
import os
import re
import sys
from datetime import date, timedelta

DOC = "docs/adr/DEC-1-schedule-generator-adapter.md"
LO = date(2000, 1, 1)
HI = date(2040, 12, 31)
SUB_HI = date(2004, 12, 31)          # complete sub-window for the brute-force cross-check


# --------------------------------------------------------------------------
# the two functions, transcribed from revision 10's closed-form block
# --------------------------------------------------------------------------
def pm(y, m):
    """proleptic month, exactly as the document writes it: d.year * 12 + d.month"""
    return y * 12 + m


def lenmonth(y, m):
    return calendar.monthrange(y, m)[1]


def packed_cf(a, b):
    """packed(a, b) = k - [a.day > b.day], for k >= 1.

    At k == 0 Java's ChronoUnit.MONTHS.between truncates toward zero and returns 0,
    which the document records as the one boundary where the closed form's floor
    disagrees.  Both branches are implemented so the probe tests what the document says.
    """
    k = pm(b.year, b.month) - pm(a.year, a.month)
    if k == 0:
        return 0
    return k - (1 if a.day > b.day else 0)


def clamped_cf(a, b):
    """clamped(a, b) = k - [min(a.day, len(b)) > b.day]"""
    k = pm(b.year, b.month) - pm(a.year, a.month)
    return k - (1 if min(a.day, lenmonth(b.year, b.month)) > b.day else 0)


def fires(a, b):
    """the predicate at ProgressiveEMICalculator.java:1432"""
    return lenmonth(b.year, b.month) == b.day and a.day > b.day


def oracle_cf(a, b):
    """:1425-1436 -- packed, measured to b.plusDays(1) when the predicate fires"""
    return packed_cf(a, b + timedelta(days=1)) if fires(a, b) else packed_cf(a, b)


# --------------------------------------------------------------------------
# STEP 0 -- tie the implementation to the document's own text
# --------------------------------------------------------------------------
def step0():
    print("=" * 78)
    print("STEP 0  The rule AS WRITTEN in DEC-1 revision 10")
    print("=" * 78)
    text = open(DOC, encoding="utf-8").read()
    want = [
        "packed(a, b) = k − [a.day > b.day]",
        "clamped(a, b) = k − [min(a.day, len(b)) > b.day]",
        "packed(a, b) != clamped(a, b)  <=>  b.day == len(b)  AND  a.day > b.day",
    ]
    blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    hit = [b for b in blocks if all(w in b for w in want)]
    if len(hit) != 1:
        print("  FAIL: revision 10's closed-form block was not found exactly once")
        print("        (found %d).  This probe tests the document, so it stops here."
              % len(hit))
        return False
    print("  found revision 10's closed-form block, verbatim:")
    for line in hit[0].strip("\n").splitlines():
        print("    | " + line)
    print()
    print("  the functions below are that block, transcribed:")
    print("    packed(a, b)  = pm(b) - pm(a) - [a.day > b.day]            (k >= 1)")
    print("    clamped(a, b) = pm(b) - pm(a) - [min(a.day, len(b)) > b.day]")
    print("    fires(a, b)   = len(b's month) == b.day and a.day > b.day  (:1432)")
    print("    oracle(a, b)  = packed(a, b + 1 day) if fires else packed(a, b)  (:1433/:1435)")
    print()
    # the document also states one worked pair; check it
    a, b = date(2000, 1, 29), date(2001, 2, 28)
    ok = (packed_cf(a, b), clamped_cf(a, b), oracle_cf(a, b)) == (12, 13, 13)
    print("  the worked pair the document prints, seed=2000-01-29 from=2001-02-28:")
    print("    packed=%d clamped=%d oracle=%d   -> %s"
          % (packed_cf(a, b), clamped_cf(a, b), oracle_cf(a, b),
             "MATCHES the document (12 / 13 / 13)" if ok else "DOES NOT MATCH"))
    print()
    return ok


# --------------------------------------------------------------------------
# LEG A -- exhaustive over the rule's whole input space
# --------------------------------------------------------------------------
def leg_a():
    print("=" * 78)
    print("LEG A  EXHAUSTIVE over the rule's whole input space (not a date range)")
    print("=" * 78)
    # (a.day, b.day, len(b's month), k).  Concrete carrier months are chosen so that
    # len(b's month) takes each of its four values; k is exercised at 0 and at 1..14,
    # and packed/clamped depend on k only through k itself, additively.
    carriers = {28: (2001, 2), 29: (2000, 2), 30: (2001, 4), 31: (2001, 1)}
    classes = 0
    diverge = 0
    bad_a1 = bad_a2 = bad_a3 = 0
    witnesses = []
    for lb, (by, bm) in carriers.items():
        for bday in range(1, lb + 1):
            b = date(by, bm, bday)
            for k in range(0, 15):
                # walk k months back from b's month for a's month
                am_total = pm(by, bm) - k
                ay, am = divmod(am_total - 1, 12)
                am += 1
                la = lenmonth(ay, am)
                for aday in range(1, la + 1):
                    a = date(ay, am, aday)
                    classes += 1
                    p, c, o = packed_cf(a, b), clamped_cf(a, b), oracle_cf(a, b)
                    f = fires(a, b)
                    if k >= 1:
                        # A1 -- divergence iff the :1432 predicate
                        if (p != c) != f:
                            bad_a1 += 1
                            if len(witnesses) < 5:
                                witnesses.append(("A1", a, b, p, c, o, f))
                        if p != c:
                            diverge += 1
                    if f:
                        # A2 -- when it fires, the oracle equals clamped-step
                        if o != c:
                            bad_a2 += 1
                            if len(witnesses) < 5:
                                witnesses.append(("A2", a, b, p, c, o, f))
                    else:
                        # A3 -- when it does not fire, all three agree (k >= 1)
                        if k >= 1 and not (p == c == o):
                            bad_a3 += 1
                            if len(witnesses) < 5:
                                witnesses.append(("A3", a, b, p, c, o, f))
    print("  (a.day, b.day, len(b's month), k) classes exercised : %d" % classes)
    print("  classes where packed != clamped (k >= 1)            : %d" % diverge)
    print("  A1 violations  packed != clamped  <=>  :1432 fires  : %d" % bad_a1)
    print("  A2 violations  fires => oracle == clamped           : %d" % bad_a2)
    print("  A3 violations  not fires => packed == clamped == oracle : %d" % bad_a3)
    for w in witnesses:
        print("    WITNESS %s a=%s b=%s packed=%d clamped=%d oracle=%d fires=%s" % w)
    ok = bad_a1 == bad_a2 == bad_a3 == 0
    print("  => %s" % ("PASS -- the document's equivalence holds on EVERY input class"
                       if ok else "FAIL"))
    print()
    return ok


# --------------------------------------------------------------------------
# LEG B -- the 112,147,776-pair counts
# --------------------------------------------------------------------------
def all_dates(lo, hi):
    out = []
    d = lo
    while d <= hi:
        out.append(d)
        d += timedelta(days=1)
    return out


def counts_by_prefix(dates):
    """firing / divergence counts over all ordered pairs a <= b, computed by
    prefix-counting on day-of-month.  Uses LEG A's result that both quantities
    depend only on (a.day, b.day, len(b)) and, for a <= b, coincide."""
    n = len(dates)
    total = n * (n + 1) // 2
    seen = [0] * 32                       # seen[dd] = how many a <= current b have a.day == dd
    firing = 0
    diverging = 0
    both_cross_a = 0                      # fires AND packed == clamped
    both_cross_b = 0                      # not fires AND packed != clamped
    oracle_ne_clamped = 0
    oracle_ne_packed = 0
    for b in dates:
        seen[b.day] += 1                  # a == b is an ordered pair too
        lb = lenmonth(b.year, b.month)
        if lb == b.day:
            cnt = sum(seen[dd] for dd in range(b.day + 1, 32))
            firing += cnt
            diverging += cnt
            oracle_ne_packed += cnt
            # a <= b with a.day > b.day == len(b) forces a's month < b's month, so k >= 1
            # and LEG A gives packed != clamped and oracle == clamped on every one.
        # both_cross_* and oracle_ne_clamped stay 0 by LEG A; the sub-window
        # brute force below is what checks that, rather than this loop asserting it.
    return dict(total=total, firing=firing, diverging=diverging,
                cross_fires_but_equal=both_cross_a,
                cross_not_fires_but_differs=both_cross_b,
                oracle_ne_clamped=oracle_ne_clamped,
                oracle_ne_packed=oracle_ne_packed)


def brute(dates):
    """every ordered pair, functions evaluated directly.  Used on the sub-window only."""
    total = firing = diverging = xa = xb = onec = onep = 0
    n = len(dates)
    for i in range(n):
        a = dates[i]
        for j in range(i, n):
            b = dates[j]
            total += 1
            p, c, o = packed_cf(a, b), clamped_cf(a, b), oracle_cf(a, b)
            f = fires(a, b)
            if f:
                firing += 1
            if p != c:
                diverging += 1
            if f and p == c:
                xa += 1
            if (not f) and p != c:
                xb += 1
            if o != c:
                onec += 1
            if o != p:
                onep += 1
    return dict(total=total, firing=firing, diverging=diverging,
                cross_fires_but_equal=xa, cross_not_fires_but_differs=xb,
                oracle_ne_clamped=onec, oracle_ne_packed=onep)


def leg_b():
    print("=" * 78)
    print("LEG B  the 112,147,776-pair counts, 2000-01-01 .. 2040-12-31")
    print("=" * 78)
    sub = all_dates(LO, SUB_HI)
    print("  cross-check on the complete sub-window %s .. %s (%d dates):"
          % (LO, SUB_HI, len(sub)))
    bb = brute(sub)
    pb = counts_by_prefix(sub)
    agree = bb == pb
    for key in ("total", "firing", "diverging", "cross_fires_but_equal",
                "cross_not_fires_but_differs", "oracle_ne_clamped", "oracle_ne_packed"):
        print("    %-30s brute=%-12d prefix=%-12d %s"
              % (key, bb[key], pb[key], "ok" if bb[key] == pb[key] else "MISMATCH"))
    print("    => %s" % ("the prefix method reproduces direct enumeration exactly"
                         if agree else "FAIL -- the prefix method is not equivalent"))
    print()
    if not agree:
        return False

    full = counts_by_prefix(all_dates(LO, HI))
    want = dict(total=112147776, firing=45253, diverging=45253,
                cross_fires_but_equal=0, cross_not_fires_but_differs=0,
                oracle_ne_clamped=0, oracle_ne_packed=45253)
    labels = {
        "total": "ordered date pairs swept",
        "firing": "the :1432 predicate FIRES",
        "diverging": "packed != clamped",
        "cross_fires_but_equal": "fires AND packed == clamped",
        "cross_not_fires_but_differs": "does NOT fire AND packed != clamped",
        "oracle_ne_clamped": "k_oracle != k_clamped",
        "oracle_ne_packed": "k_oracle != k_packed",
    }
    ok = True
    print("  full range, against the figures DEC-1 revision 10 prints:")
    for key in ("total", "firing", "diverging", "cross_fires_but_equal",
                "cross_not_fires_but_differs", "oracle_ne_clamped", "oracle_ne_packed"):
        good = full[key] == want[key]
        ok &= good
        print("    %-38s computed=%-12d document=%-12d %s"
              % (labels[key], full[key], want[key], "MATCH" if good else "MISMATCH"))
    print("  => %s" % ("PASS -- revision 10's table is reproduced digit for digit"
                       if ok else "FAIL"))
    print()
    return ok


# --------------------------------------------------------------------------
# LEG C -- the 59,130-pair sweep with the closed-form functions
# --------------------------------------------------------------------------
def leg_c():
    """The 59,130-pair sweep, with the CLOSED-FORM functions substituted for the
    step-B pseudocode.  Boundaries and the seed come from the inherited from-text
    model (section 4.2's re-anchor and calculateSeedDate), which is what T44 and
    T45 used; re-transcribing section 4.2 here would test that transcription and
    not the month-end rule."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from t47_model_inherited import repayment_boundaries, calculate_seed_date

    print("=" * 78)
    print("LEG C  the 59,130-pair sweep, re-run with the CLOSED-FORM functions")
    print("       (boundaries + seed from the inherited section-4.2 model, as T44/T45)")
    print("=" * 78)
    swept = firing = r3 = r4 = 0
    d = date(2023, 1, 1)
    while d <= date(2025, 12, 30):
        for terms in (6, 12, 36):
            for rp_from, rp_due in repayment_boundaries(d, d, terms, 1):
                swept += 1
                sd = calculate_seed_date(d, rp_from, rp_due, 1)
                if fires(sd, rp_from):
                    firing += 1
                kp = packed_cf(sd, rp_from)
                kc = clamped_cf(sd, rp_from)
                ko = oracle_cf(sd, rp_from)
                if ko != kp:
                    r3 += 1
                if ko != kc:
                    r4 += 1
        d += timedelta(days=1)
    want = (59130, 701, 701, 0)
    got = (swept, firing, r3, r4)
    print("  (ScheduleStartDate, repayment period) pairs swept : %d" % swept)
    print("  periods on which the :1432 predicate FIRES        : %d" % firing)
    print("  periods where k_oracle != k_packed                : %d" % r3)
    print("  periods where k_oracle != k_clamped               : %d" % r4)
    print("  document / T44 / T45 figures                      : %s" % (want,))
    ok = got == want
    print("  => %s" % ("PASS -- the closed-form block and the step-B pseudocode agree, "
                       "and both reproduce T44's sweep"
                       if ok else "FAIL -- %s" % (got,)))
    print()
    return ok


def main():
    print("T47 MONTH-END RULE CHECK -- DEC-1 revision 10")
    print("no money is computed here and no float is constructed")
    print()
    ok = step0()
    ok = leg_a() and ok
    ok = leg_b() and ok
    ok = leg_c() and ok
    print("=" * 78)
    print("OVERALL: %s" % ("PASS" if ok else "FAIL"))
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    if not os.path.exists(DOC):
        sys.exit("run from the repository root")
    sys.exit(main())
