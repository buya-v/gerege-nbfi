#!/usr/bin/env python3
"""T421, INFORMATIONAL from T406 -- name what moved the printed READ-BUT-NOT-GRADED
numeric census by +18.

The bar prints "N of them are NOT byte-preserved" over numeric tokens found in
CITED capture records outside any recorded-request block. A token is
"byte-preserved" when re-rendering the decoded number reproduces the bytes the
oracle emitted. Fineract emits journal-entry amounts at SCALE 6 (`24000.000000`),
and no ordinary JSON number renderer reproduces six trailing decimals, so every
such amount is counted as not-byte-preserved.

T391 promoted three vectors, each citing one journal-entry body of SIX legs. Six
bodies-worth of legs... no: three bodies, six amount tokens each = 18. This script
COUNTS them rather than asserting them, decoding with parse_float=str so no money
value becomes a float in the act of explaining a census about money values.
"""
import json, os

BODIES = [
    ".softhouse/capture/t391-accrual-promotion/out/T391-A01-je-L29.json",
    ".softhouse/capture/t391-accrual-promotion/out/T391-A02-je-L30.json",
    ".softhouse/capture/t391-accrual-promotion/out/T391-A04-je-L32.json",
]

total = 0
for b in BODIES:
    doc = json.load(open(b), parse_float=str, parse_int=str)
    items = doc["pageItems"]
    # An amount token is NOT byte-preserved when its bytes carry trailing zeros a
    # renderer would drop -- i.e. when the shortest equal decimal differs from the
    # emitted bytes. Decided by STRING SURGERY: strip trailing zeros of the
    # fraction and compare, never by rendering a float.
    notpres = []
    for it in items:
        raw = it["amount"]
        assert isinstance(raw, str), "amount decoded as a number -- parse_float=str failed"
        if "." in raw:
            short = raw.rstrip("0").rstrip(".")
        else:
            short = raw
        if short != raw:
            notpres.append((raw, short))
    print("%-70s legs=%d  amount tokens NOT byte-preserved=%d"
          % (os.path.basename(b), len(items), len(notpres)))
    for raw, short in notpres:
        print("      %s -> %s" % (raw, short))
    total += len(notpres)

print()
print("TOTAL contributed by T391's three cited bodies:", total)
print("The bar prints 104; before T391 it printed", 104 - total, "-- that is the +18.")
