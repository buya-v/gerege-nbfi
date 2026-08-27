#!/usr/bin/env python3
"""T223 scratch scan: where does the emulated instalment E_q fall relative to the exact first-period
interest I_1, as a function of (rate, n, B)? Prints E_q and I_1 only -- it asserts nothing."""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emi_mechanism import predict  # noqa: E402


def show(rate, n, b):
    p = predict(rate, n, b)
    i1 = Fraction(p["i1ExactMinorNum"], p["i1ExactMinorDen"])
    e = p["emiQuantizedMinor"]
    rel = "<" if e < i1 else ("=" if e == i1 else ">")
    print("  rate=%-7s n=%-6d B=%-8d E_q=%-10d %s I1=%-12s  raw=%s"
          % (rate, n, b, e, rel, str(i1), p["emiRaw"]))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        show(args[0], int(args[1]), int(args[2]))
    else:
        print("300.0 %% B=2 (I1 = 0.5 minor):")
        for n in (150, 190, 196, 200, 204, 220, 260, 300, 400, 500, 800, 1200):
            show("300.0", n, 2)
        print("96.0 %% B=25 (I1 = 2.0 minor -- NOT resonant) and B=? resonance:")
        for n in (400, 568, 600, 800, 1200):
            show("96.0", n, 25)
        print("36.0 %% B=50 (I1 = 1.5 minor):")
        for n in (600, 1000, 1480, 1600, 2000, 3000):
            show("36.0", n, 50)
        print("21.6 %% B=250 (I1 = 4.5 minor):")
        for n in (1000, 2000, 2452, 2600, 3000, 4000):
            show("21.6", n, 250)
        print("600.0 %% B=1 boundary re-check:")
        for n in (102, 103, 104, 105):
            show("600.0", n, 1)
