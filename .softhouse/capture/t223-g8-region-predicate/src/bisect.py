#!/usr/bin/env python3
"""T223 scratch: bisect, in the EMULATOR only, the term at which E_q drops below I_1 for a given
(rate, B). Prints; asserts nothing. Exact arithmetic (Decimal/Fraction); no float."""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emi_mechanism import predict  # noqa: E402


def below(rate, n, b):
    p = predict(rate, n, b)
    return p["emiQuantizedMinor"] < Fraction(p["i1ExactMinorNum"], p["i1ExactMinorDen"])


if __name__ == "__main__":
    rate, b = sys.argv[1], int(sys.argv[2])
    lo, hi = int(sys.argv[3]), int(sys.argv[4])
    for n in range(lo, hi + 1):
        p = predict(rate, n, b)
        i1 = Fraction(p["i1ExactMinorNum"], p["i1ExactMinorDen"])
        e = p["emiQuantizedMinor"]
        print("n=%-6d E_q=%-6d %s I1=%-8s raw=%s" %
              (n, e, "<" if e < i1 else ("=" if e == i1 else ">"), str(i1), p["emiRaw"]))
