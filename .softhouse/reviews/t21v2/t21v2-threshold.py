#!/usr/bin/env python3
"""
T21-v2 AUDIT — test the PASS3-REPORT claim that "precision is load-bearing, but only
above a size threshold".

This uses MY OWN re-derivation model (t21v2-rederive.py), which reproduces the pinned
oracle exactly on all 12 pass-3 captures. It LOCATES candidates cheaply. NOTHING here is
an oracle observation: every headline candidate is then re-run against the running oracle
in T21v2Probe.java and only the oracle's answer is quoted in the audit.
"""
import datetime
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t21v2-rederive.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

START = datetime.date(2024, 1, 1)


def differs(P, n, rate):
    a = rd.derive(P, n, rate, 12, START)
    b = rd.derive(P, n, rate, 19, START)
    if a["total_interest"] != b["total_interest"] or a["total_repayment"] != b["total_repayment"]:
        return True
    for x, y in zip(a["periods"], b["periods"]):
        if x["prin"] != y["prin"] or x["int"] != y["int"] or x["out"] != y["out"]:
            return True
    return False


def first_divergent(n, rate, lo, hi):
    for P in range(lo, hi + 1):
        if differs(P, n, rate):
            return P
    return None


SHAPES = (("C-00 / P-00 shape  6 x 7.0%", 6, "7.0"),
          ("D-01 / P-01 shape 18 x 18.5%", 18, "18.5"),
          ("P-MNT-50M shape   36 x 16.8%", 36, "16.8"),
          ("P-MNT-5M shape    18 x 18.5%", 18, "18.5"))

if __name__ == "__main__":
    print("smallest p12-vs-p19 divergent principal, exhaustive upward scan (MODEL-LOCATED, not observed)")
    for label, n, rate in SHAPES[:3]:
        P = first_divergent(n, rate, 1, 200000)
        print(f"  {label:<30} smallest divergent principal <= 200000: {P}")

    print("\nfirst five divergent principals for 36 x 16.8% (MODEL-LOCATED)")
    found = []
    for P in range(1, 2000):
        if differs(P, 36, "16.8"):
            found.append(P)
            if len(found) == 5:
                break
    print("  ", found)

    print("\nfirst five divergent principals for 6 x 7.0% (MODEL-LOCATED)")
    found = []
    for P in range(1, 200000):
        if differs(P, 6, "7.0"):
            found.append(P)
            if len(found) == 5:
                break
    print("  ", found)
