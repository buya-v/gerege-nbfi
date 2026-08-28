#!/usr/bin/env python3
"""T391 -- is today's oracle response for L29/L30/L31 the SAME response T388
recorded?

The comparison is KEY-ORDER-NORMALISED AND NOTHING ELSE. Values are compared as
the characters the oracle emitted: `parse_float=str` and `parse_int=str` keep
every number as its wire token, so `24000.000000` never becomes `24000.0` and a
scale change would be reported as a difference rather than normalised away.

This is T389's re-issue control applied by a second, independent reader. If a
body differs, the difference is PRINTED, not summarised.
"""
import json
import sys


def load(path):
    with open(path, "rb") as fh:
        return json.load(fh, parse_float=str, parse_int=str)


def canon(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


rc = 0
for old, new in zip(sys.argv[1::2], sys.argv[2::2]):
    a, b = load(old), load(new)
    ca, cb = canon(a), canon(b)
    if ca == cb:
        print("IDENTICAL (key-order-normalised): %s == %s" % (old, new))
        continue
    rc = 1
    print("DIFFERENT: %s != %s" % (old, new))
    print("  recorded: %s" % ca)
    print("  today   : %s" % cb)
print("verdict rc=%d" % rc)
sys.exit(rc)
