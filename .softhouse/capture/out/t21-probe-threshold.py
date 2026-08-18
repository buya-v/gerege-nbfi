#!/usr/bin/env python3
"""
T21 AUDIT PROBE — search for the p12-vs-p19 divergence threshold.

This uses my re-derivation model (t21-probe-rederive.py), which matched the pinned
oracle EXACTLY on all 12 pass-3 captures, to LOCATE candidate divergences cheaply.
Nothing found here is asserted as oracle output. Every headline candidate is then
re-run against the live oracle in T21Probe.java and only the oracle's answer is quoted.
"""
import datetime, sys
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t21-probe-rederive.py"))
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)

START = datetime.date(2024, 1, 1)


def differs(P, n, rate):
    a = rd.derive(P, n, rate, 12, START)
    b = rd.derive(P, n, rate, 19, START)
    if a["emi"] != b["emi"] or a["total_interest"] != b["total_interest"]:
        return True
    for x, y in zip(a["periods"], b["periods"]):
        if x["prin"] != y["prin"] or x["int"] != y["int"] or x["out"] != y["out"] or x["emi"] != y["emi"]:
            return True
    return False


def scan(label, n, rate, lo_exp, hi_exp):
    print(f"\n### {label}: n={n} rate={rate}%  — first divergence per decade (model-located)")
    for e in range(lo_exp, hi_exp + 1):
        base = 10 ** e
        found = []
        # sample 200 principals across the decade
        step = max(1, (10 * base - base) // 200)
        for P in range(base, 10 * base, step):
            if differs(P, n, rate):
                found.append(P)
                if len(found) >= 3:
                    break
        total = 0
        cnt = 0
        for P in range(base, 10 * base, step):
            cnt += 1
            if differs(P, n, rate):
                total += 1
        pct = 100.0 * total / cnt if cnt else 0
        print(f"  1e{e:<2}  divergent {total:>3}/{cnt:<3} sampled ({pct:5.1f}%)   first: {found[:3]}")


def bisect_first(n, rate, lo, hi):
    """Smallest principal in [lo,hi] that diverges, scanning upward (not a true bisect:
    the property is not monotone, so a linear scan is the honest instrument)."""
    for P in range(lo, hi + 1):
        if differs(P, n, rate):
            return P
    return None


if __name__ == "__main__":
    scan("C-00 shape (6 x 7.0%)", 6, "7.0", 2, 10)
    scan("D-01 shape (18 x 18.5%)", 18, "18.5", 2, 10)
    scan("MNT-50M shape (36 x 16.8%)", 36, "16.8", 2, 10)

    print("\n### smallest divergent principal by exhaustive upward scan")
    for label, n, rate, lo, hi in (
        ("6 x 7.0%", 6, "7.0", 1, 400000),
        ("18 x 18.5%", 18, "18.5", 1, 400000),
        ("36 x 16.8%", 36, "16.8", 1, 400000),
    ):
        P = bisect_first(n, rate, lo, hi)
        print(f"  {label:<12} smallest divergent principal <= {hi}: {P}")
