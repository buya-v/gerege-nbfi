#!/usr/bin/env python3
"""T327 -- P-72 CALIBRATION OF THE RESIDUE RULE.

P-72: "a sweep is an INSTRUMENT; calibrate it on a known positive before you report its negatives."
`invariant-minor-units.py` reported "residue beyond 2 digits found: NONE" over the captured bytes.
A rule that has never refused anything is indistinguishable from a rule that CANNOT refuse -- P-22,
"a guard, a canary, or a control that cannot fail is worse than none, because it is believed".

This drives the rule RED on synthetic tokens that must be refused, and green on the real ones.
Exit 0 only if every known negative converts and every known positive is refused.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("inv", os.path.join(HERE, "invariant-minor-units.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

rc = 0

print("KNOWN NEGATIVES -- must convert cleanly:")
for t in ["250000.250000", "100000.370000", "350000.620000", "1000000", "0.01", "-5.50"]:
    try:
        print("   ok      %-16s -> %d minor units" % (t, m.to_minor(t)))
    except ValueError as e:
        print("   *** FAIL  %-16s was REFUSED but should convert: %s ***" % (t, e))
        rc = 1

print("")
print("KNOWN POSITIVES -- must be REFUSED, never rounded:")
for t in ["250000.250001", "0.005", "1.239", "100.00000001"]:
    try:
        v = m.to_minor(t)
        print("   *** FAIL  %-16s was ACCEPTED as %d -- the residue rule is vacuous ***" % (t, v))
        rc = 1
    except ValueError as e:
        print("   REFUSED %-16s %s" % (t, e))

print("")
if rc == 0:
    print("The rule fires on a known positive and does not fire on the captured bytes.")
    print("'residue beyond 2 digits found: NONE' is therefore a MEASUREMENT, not a default.")
else:
    print("CALIBRATION FAILED -- do not trust the NONE.")
sys.exit(rc)
