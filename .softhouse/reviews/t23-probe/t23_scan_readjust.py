#!/usr/bin/env python3
"""
T23 — locate a request INSIDE DEC-1's stated graded domain on which the EMI re-adjust loop's
guard (EmiAdjustment.shouldBeAdjusted, EmiAdjustment.java:31-36) evaluates TRUE.

Model-located only; every headline candidate is then put to the pinned oracle.
Guard, read correctly from source: |lastEmi - penultimateEmi| * 100 > Money(floor(n/2)).
"""
import datetime
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t23_rederive.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

START = datetime.date(2024, 1, 1)

shapes = [(6, "7.0"), (6, "21.6"), (12, "21.6"), (18, "18.5"), (36, "16.8")]

for n, rate in shapes:
    hits = []
    for P in range(1000, 60000000, 7919):     # ~7.6k samples per shape, prime step
        d = rd.derive(P, n, rate, START)
        if d["readjust_guard"]:
            hits.append((P, d["emi"], d["emi_diff"]))
            if len(hits) >= 5:
                break
    print(f"n={n:<3} rate={rate:<6} threshold=|gap|>{n//2/100:.2f}   hits: {hits}")
