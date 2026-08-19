#!/usr/bin/env python3
"""
T44 audit - the Path B captures serialise money as BARE JSON NUMBERS. Measure, rather than
assert, what a consumer that reads them through a binary float would lose.

For every bare non-integer number in the charges payloads:
  * does float(s) round-trip back to the same decimal text?
  * does Decimal(repr(float(s))) differ from Decimal(s)?
The text is never converted to a float on the money path used for the VERDICT - the floats
constructed here exist only to characterise the hazard, and are labelled as such.
"""
import json, sys, glob
from decimal import Decimal

seen = {}


def hook(s):
    seen[s] = seen.get(s, 0) + 1
    return Decimal(s)


paths = []
for pat in sys.argv[1:]:
    paths.extend(sorted(glob.glob(pat, recursive=True)))
for p in paths:
    try:
        json.load(open(p), parse_float=hook)
    except Exception:
        pass

print("T44 - float round-trip hazard on the Path B (charges) raw captures")
print(f"  distinct bare non-integer literals: {len(seen)}")
print(f"  total occurrences               : {sum(seen.values())}")
print()

# HAZARD CHARACTERISATION ONLY - these floats never touch an audit verdict.
lossy_text, lossy_value, max_scale = [], [], 0
for s in seen:
    max_scale = max(max_scale, -Decimal(s).as_tuple().exponent)
    f = float(s)                      # deliberate: the thing a careless consumer would do
    if repr(f) != s:
        lossy_text.append((s, repr(f)))
    if Decimal(repr(f)) != Decimal(s):
        lossy_value.append((s, repr(f)))

print(f"  max decimal scale seen                    : {max_scale}")
print(f"  literals whose float repr() != the text   : {len(lossy_text)}")
print(f"  literals whose float VALUE != the decimal : {len(lossy_value)}")
print()
for label, lst in (("text-lossy", lossy_text), ("VALUE-lossy", lossy_value)):
    if lst:
        print(f"  {label} examples:")
        for s, r in lst[:12]:
            print(f"    {s!r:>18}  ->  {r}")
        print()
if not lossy_value:
    print("  => no literal changes VALUE on a float round-trip at these magnitudes and scales,")
    print("     so no committed charges number is corrupted TODAY. The hazard is structural:")
    print("     the wire format is float-shaped, so a consumer that does not force exact")
    print("     decimal parsing violates the money rule by construction, and would corrupt")
    print("     a value as soon as a magnitude or a scale grows.")
