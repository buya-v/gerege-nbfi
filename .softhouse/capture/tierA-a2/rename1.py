#!/usr/bin/env python3
"""Preserve the FIRST attempt at the product-mapping batch under `attempt1-`.

Why this exists rather than a silent overwrite: attempt 1 was refused 400 on
EVERY payload, including the ones meant to be valid, because MY payload omitted
`isInterestRecalculationEnabled` — a defect in the request, not a finding about
the A2 slice. Those refusals are still real observations from the oracle and are
kept verbatim; they are simply not evidence about product-to-account mapping.
Deleting them would be editing the record.
"""
import os, glob

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
n = 0
for p in glob.glob(os.path.join(OUT, "A2-prod-06*")):
    b = os.path.basename(p)
    os.rename(p, os.path.join(OUT, "attempt1-" + b))
    n += 1
print("preserved", n, "files under attempt1-")
