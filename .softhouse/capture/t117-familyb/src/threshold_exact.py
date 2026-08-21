#!/usr/bin/env python3
"""T117 — the zero-EMI threshold quantity B*a(r,n), in EXACT RATIONAL ARITHMETIC (P-25).

No float is constructed on any decision path. `fractions.Fraction` throughout; the only
float() calls are in the DISPLAY column, and they are labelled as display and are not read
by any comparison.

a(r, n) = r / (1 - (1+r)^-n),  r = annual/100/12,  B in INTEGER MINOR UNITS.
T83 registered the closed form "the cell fails iff B*a(r,n) < 1/2" as a HYPOTHESIS; T100/T101
refuted it on 22 family-B cells. This script does not decide anything about the oracle — it
only reports where each swept (B, n) sits relative to the 1/2 threshold, so the prediction
in ../PREDICTION.md can be stated in exact terms rather than approximate ones.
"""
import json
import sys
from fractions import Fraction


def rate_monthly(annual_pct_str):
    """Exact monthly rate from a decimal-string annual percentage. No float."""
    return Fraction(annual_pct_str) / 100 / 12


def annuity_factor(r, n):
    return r / (1 - (1 + r) ** (-n))


def main():
    r = rate_monthly("600.0")
    rows = []
    for n in (103, 104, 105, 106, 107, 121, 250, 300, 400, 500, 700, 1000):
        for B in (1, 2, 3, 4, 5):
            v = B * annuity_factor(r, n)
            gap = v - Fraction(1, 2)
            rows.append({
                "annualRate": "600.0",
                "n": n,
                "B_minor": B,
                "B_times_a_minus_half_sign": ("+" if gap > 0 else ("0" if gap == 0 else "-")),
                "B_times_a_numerator_bits": v.numerator.bit_length(),
                "B_times_a_display_only_float": float(v),
                "gap_display_only_float": float(gap),
                "closed_form_predicts": ("FAIL" if gap < 0 else "CLEAN"),
            })
    print(json.dumps({
        "note": "exact Fraction arithmetic; the two *_display_only_float keys are for human reading "
                "and are read by nothing",
        "r_monthly_exact": "%d/%d" % (r.numerator, r.denominator),
        "rows": rows,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
