#!/usr/bin/env python3
"""How far apart, in currency, are the oracle's EMI FOLD and the closed-form pow?

The sweep found ZERO separating shapes for M1..M4 over 40,001 on-lattice MNT
loans. This measures WHY, rather than concluding it from a null result: it
re-derives the level installment in exact rational arithmetic at the production
MathContext (19, HALF_UP) both ways and prints the gap in minor units, alongside
the distance to the nearest half-minor-unit rounding boundary -- the only place a
gap that small could ever become a payable difference.

Exact rationals only (fractions.Fraction). No floating point.

    python3 .softhouse/handoff/T61-sweep/emi-magnitude.py
"""
from fractions import Fraction as F

PREC = 19
SCALE = 19


def dec_exp(x):
    """e such that 10^(e-1) <= |x| < 10^e."""
    assert x != 0
    n, d = abs(x.numerator), x.denominator
    e = len(str(n)) - len(str(d))
    if F(n, d) >= F(10) ** e:
        e += 1
    return e


def round_half_up_int(x):
    n, d = abs(x.numerator), x.denominator
    q, r = divmod(n, d)
    if 2 * r >= d:
        q += 1
    return -q if x < 0 else q


def round_scale(x, scale):
    if x == 0:
        return F(0)
    m = F(10) ** scale
    return F(round_half_up_int(x * m), 1) / m


def rsig(x, prec=PREC):
    if x == 0:
        return F(0)
    return round_scale(x, prec - dec_exp(x))


def rate_factor(rate_frac, days_in_month=30, days_in_year=360, mult=1,
                actual_days=30, calc_days=30):
    """rateFactorByRepaymentPeriod [ProgressiveEMICalculator.java:1950-1962]."""
    fr = rsig(F(days_in_month) * mult)
    fr = rsig(fr / days_in_year)
    v = rsig(rate_frac * fr)
    v = rsig(v * actual_days)
    v = rsig(v / calc_days)
    return round_scale(v, SCALE)


def emi_fold(g, n, principal_major):
    """The oracle: TWO folds, no pow [PEC:1817-1828, fnValue at :1991-1993]."""
    rfn = F(1)
    for _ in range(n):
        rfn = rsig(rfn * g)
    fn = F(1)
    for _ in range(n - 1):
        fn = rsig(rsig(fn * g) + 1)
    return rsig(rsig(rfn * principal_major) / fn), rfn, fn


def emi_closed(g, n, principal_major):
    """The textbook: (1+r)^n rounded ONCE, fn = ((1+r)^n - 1)/r."""
    r = g - 1
    rfn = rsig(g ** n)
    fn = F(n) if r == 0 else rsig(rsig(rfn - 1) / r)
    return rsig(rsig(rfn * principal_major) / fn), rfn, fn


def sci(x, digits=3):
    """Render an exact rational in scientific notation WITHOUT touching a float.

    These magnitudes are in minor currency units, so binary floating point is
    forbidden here as everywhere else in this program -- and it would be
    self-defeating besides, since the whole point is to measure a quantity around
    1e-11 that a double would round away.
    """
    if x == 0:
        return "0"
    e = dec_exp(x) - 1
    mant = x / (F(10) ** e)
    scaled = round_half_up_int(mant * (F(10) ** digits))
    s = str(scaled).rjust(digits + 1, "0")
    return "%s.%se%s%02d" % (s[:-digits], s[-digits:], "+" if e >= 0 else "-", abs(e))


def main():
    print("MathContext (19, HALF_UP); FIXED_30_360; monthly; RepaymentEvery 1; on-lattice.")
    print("Every number below is exact rational arithmetic. Money is minor units.\n")
    print("%-26s %-4s %-22s %-22s %s" %
          ("annual rate", "n", "EMI gap (minor units)", "dist to .5 boundary", "would a cent move?"))
    print("-" * 108)
    for num, den, label in ((27, 125, "21.6%"), (21, 125, "16.8%"), (7, 100, "7.0%"),
                            (37, 200, "18.5%"), (3, 10, "30.0%")):
        rate = rsig(F(num, den))
        r = rate_factor(rate)
        g = 1 + r
        for n in (6, 12, 18, 36, 60, 120, 360):
            p = F(120000000, 100)  # MNT 1,200,000.00 in major units
            a, _, _ = emi_fold(g, n, p)
            b, _, _ = emi_closed(g, n, p)
            gap_minor = abs(a - b) * 100
            # distance from the true EMI's minor-unit value to the nearest tie
            m = a * 100
            frac = m - int(m)
            dist = abs(frac - F(1, 2))
            moves = "YES" if gap_minor >= dist and gap_minor > 0 else "no"
            print("%-26s %-4d %-22s %-22s %s"
                  % (label, n, sci(gap_minor), sci(dist), moves))
    print("\nThe gap is the SIZE OF THE PERTURBATION; the boundary distance is how far the")
    print("true value sits from the only place a perturbation of that size could change a")
    print("payable amount. A cent moves only when gap >= dist.")


if __name__ == "__main__":
    main()
