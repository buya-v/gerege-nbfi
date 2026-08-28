#!/usr/bin/env python3
"""
T278 - DOMAIN AUDIT.  The seven cells are the easy half.  This file grades the
question the review actually exists to answer:

    is the RE-WORDED law TRUE ABOUT MAIN over the WHOLE DOMAIN IT GOVERNS,
    not merely over the cells that motivated the edit?

T264's finding against the cloud T241 was that a correction measured one of two
laws and affirmed the other sound WITHOUT TESTING IT ON THE DOMAIN IT HAD JUST
WRITTEN.  So this file tests every OTHER live statement in `.softhouse/gates.md`
that is law (ii) wearing a different algebraic coat, and it tests the two
downstream claims the correction leaves standing:

  (a)  residual = min(B_minor, n*delta)                 -- gates.md x4, LIVE
  (b)  the conservative region  B_minor < 1.5*n  is a SUPERSET of the failing
       region, so refusing it refuses every failing cell
  (c)  the RECORD figures (largest residual 3000 minor units; largest FULL
       family-B residual 2999; largest failing disbursement 4499)

Integer minor units throughout.  No float, no decimal/fractions/math, no true
division.  Imports only this review's own re-derivation module.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import t278_rederive as R          # this review's own instrument, nothing else


def residual(c):
    """what the borrower still owes as principal at the end of the schedule."""
    return c["B"] - c["principal_sum"]


def residual_law(c):
    """gates.md, four live sites:  residual = min(B_minor, n*delta)."""
    a = c["B"]
    b = c["n"] * c["delta"]
    return a if a < b else b


def in_conservative_region(c):
    """B_minor < 1.5*n , in integers:  2*B < 3*n ."""
    return 2 * c["B"] < 3 * c["n"]


def audit(scope):
    root = R.repo_root()
    os.chdir(root)
    rep, stuck, exceptions = R.census(root, scope)

    print("=" * 78)
    print("T278 DOMAIN AUDIT  scope=%s   stuck cells=%d" % (scope, len(stuck)))
    print("=" * 78)

    # ---------------------------------------------------------------- (a)
    holds = [c for c in stuck if residual(c) == residual_law(c)]
    fails = [c for c in stuck if residual(c) != residual_law(c)]
    over = [c for c in stuck if residual(c) > residual_law(c)]
    print("")
    print("(a) LIVE CLAIM, gates.md :1164 :1891 :2603 :3543 :3679 --")
    print("    'the residual of an unrescued family-B cell IS min(B_minor, n*delta)'")
    print("    holds : %d of %d" % (len(holds), len(stuck)))
    print("    FAILS : %d" % len(fails))
    for c in sorted(fails, key=lambda x: (x["source"], x["n"])):
        print("      %-24s n=%-5d B=%-5d delta=%d  formula says residual=%-5d  "
              "OBSERVED residual=%-5d  (repaid %d)"
              % (c["id"], c["n"], c["B"], c["delta"], residual_law(c),
                 residual(c), c["principal_sum"]))
    print("    cells where OBSERVED residual EXCEEDS the formula (unsafe "
          "direction): %d" % len(over))
    print("    -> the formula is therefore an UPPER BOUND that holds, but the")
    print("       EQUALITY asserted in the file is FALSE on %d cells." % len(fails))
    print("    exception set of the residual form == exception set of law (ii)? %s"
          % (sorted(c["id"] for c in fails) == sorted(c["id"] for c in exceptions)))

    # ---------------------------------------------------------------- (b)
    failing = [c for c in stuck if residual(c) > 0]
    clean = [c for c in stuck if residual(c) == 0]
    failing_outside = [c for c in failing if not in_conservative_region(c)]
    clean_inside = [c for c in clean if in_conservative_region(c)]
    print("")
    print("(b) CONSERVATIVE REGION  B_minor < 1.5*n  (integers: 2B < 3n)")
    print("    stuck cells that do NOT fully amortize : %d" % len(failing))
    print("    stuck cells that DO fully amortize     : %d" % len(clean))
    print("    FAILING cells OUTSIDE the region (would be a HOLE): %d"
          % len(failing_outside))
    for c in failing_outside[:20]:
        print("      HOLE %-24s n=%-5d B=%-5d residual=%d"
              % (c["id"], c["n"], c["B"], residual(c)))
    print("    clean cells INSIDE the region (over-refusal, expected of a "
          "superset): %d" % len(clean_inside))
    print("    all seven law-(ii) exceptions inside the region? %s"
          % all(in_conservative_region(c) for c in exceptions))
    print("    -> superset claim %s"
          % ("HOLDS on this scope" if not failing_outside else "IS BROKEN"))

    # ---------------------------------------------------------------- (c)
    if failing:
        mx = max(residual(c) for c in failing)
        winners = [c["id"] for c in failing if residual(c) == mx]
        fullb_fail = [c for c in failing if R.full_family_b(c)]
        mxf = max(residual(c) for c in fullb_fail) if fullb_fail else 0
        fwin = [c["id"] for c in fullb_fail if residual(c) == mxf]
        mxd = max(c["B"] for c in failing)
        dwin = [c["id"] for c in failing if c["B"] == mxd]
        print("")
        print("(c) RECORD FIGURES, re-measured from the principal column")
        print("    largest unamortized residual      : %d minor units  %s"
              % (mx, winners))
        print("    largest FULL family-B residual    : %d minor units  %s"
              % (mxf, fwin))
        print("    largest FAILING disbursement      : %d minor units  %s"
              % (mxd, dwin))

    # ------------------------------------------------- law (ii) exception set
    print("")
    print("(d) law (ii) exception set on this scope: %d  %s"
          % (len(exceptions), sorted(c["id"] for c in exceptions)))
    print("    amounts repaid, in id order above    : %s"
          % [c["principal_sum"] for c in sorted(exceptions, key=lambda x: x["id"])])
    return rep, stuck, exceptions


def i1q_trap(scope):
    """Independently reproduce T277's FU-T277-4 claim, with MY instrument."""
    root = R.repo_root()
    os.chdir(root)
    good, gstuck, gexc = R.census(root, scope, False)
    bad, bstuck, bexc = R.census(root, scope, True)
    print("")
    print("=" * 78)
    print("T278 vs FU-T277-4 : taking I1q from repayment row 1's `interest` field")
    print("=" * 78)
    print("  correctly computed  : delta histogram %s , law (ii) fails on %d"
          % (good["deltaHistogram"], good["lawII_fails_allStuck"]))
    print("  I1q read from row 1 : delta histogram %s , law (ii) fails on %d"
          % (bad["deltaHistogram"], bad["lawII_fails_allStuck"]))
    print("  all stuck cells forced to delta=0 by that route? %s"
          % (list(bad["deltaHistogram"].keys()) == ["0"]))
    print("  T277's claim: 'forces delta = 0 on all 296 and refutes law (ii) on "
          "183 cells'")
    print("  T278 measures: %s cells at delta=0, law (ii) 'refuted' on %d"
          % (bad["deltaHistogram"].get("0"), bad["lawII_fails_allStuck"]))


def main():
    scope = sys.argv[1] if len(sys.argv) > 1 else "t229corpus"
    if scope == "--trap":
        i1q_trap("t229corpus")
        return 0
    audit(scope)
    return 0


if __name__ == "__main__":
    sys.exit(main())
