#!/usr/bin/env python3
"""T175 -- build a SCRATCH corpus for the red probe of t55-analyse.py:352 (invariant I6).

Copies the committed `../out/*-exact.json` sidecars into a scratch directory (the committed
corpus is NEVER touched), then plants ONE defect chosen so that:

  * it is a REAL breach of the money non-negotiable -- the cell carries THREE decimal places,
    which I6 exists to catch; and
  * its text does not parse as a `Decimal`, so I6's `except Exception: continue` at :352
    discards it and the invariant passes WITHOUT ever looking at it.

The planted text is a thousands-separated amount, `"1,200,000.000"`.  That is exactly the shape
a locale-formatted or spreadsheet-round-tripped money field takes, it is three decimal places
in MNT (minor unit 2), and `Decimal("1,200,000.000")` raises `InvalidOperation`.  A defect that
is both real and unparseable is the one the swallow makes invisible; a defect that is real and
parseable would already be caught, and one that is unparseable but not a real breach would not
prove anything about money.

A second mode plants a parseable 3-dp value as a CONTROL, to show the original's I6 is not
simply broken -- it catches what it can parse, and only what it can parse.

Usage:
    python3 plant.py <scratch-dir> unparseable-3dp    # the swallowed defect
    python3 plant.py <scratch-dir> parseable-3dp      # the control the original DOES catch
    python3 plant.py <scratch-dir> clean              # untouched copy
Writes only inside <scratch-dir>.  Constructs no float.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "out"))

TARGET_CAPTURE = "LB-LEAPIN-p7-exact.json"
TARGET_FIELD = "totalRepaymentExpected"     # a plan-level MONEYISH cell; in I6's domain

# WHY THIS FIELD AND NOT `totalInterestCharged`.  The first draft of this probe planted in
# `totalInterestCharged` and the ORIGINAL CRASHED rather than swallowing: invariant I5 reads
# `Decimal(doc["totalInterestCharged"])` at t55-analyse.py:342, outside any try, and I5 runs
# before I6.  `field-census.py` enumerates the whole surface: of 32 cell plants in this
# capture, 24 are SWALLOWED SILENTLY, 8 crash on an unguarded Decimal() elsewhere, and 0 are
# reported by I6.  `totalRepaymentExpected` is in the swallowed 24 -- and it is the plan-level
# total a reader would quote.

PLANTS = {
    "clean": None,
    # Decimal() raises InvalidOperation on this, so t55-analyse.py:352 swallows it.
    "unparseable-3dp": "1,200,000.000",
    # Decimal() accepts this, so the ORIGINAL's I6 does catch it -- the control.
    "parseable-3dp": "1200000.000",
}


def main(argv):
    if len(argv) != 2 or argv[1] not in PLANTS:
        sys.stderr.write(__doc__)
        return 2
    scratch, mode = os.path.abspath(argv[0]), argv[1]
    if os.path.exists(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)
    n = 0
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith("-exact.json"):
            continue
        shutil.copy2(os.path.join(OUT, fn), os.path.join(scratch, fn))
        n += 1
    value = PLANTS[mode]
    if value is not None:
        p = os.path.join(scratch, TARGET_CAPTURE)
        with open(p) as fh:
            doc = json.load(fh)
        before = doc[TARGET_FIELD]
        doc[TARGET_FIELD] = value
        with open(p, "w") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print("PLANTED  %s  %s: %r -> %r" % (TARGET_CAPTURE, TARGET_FIELD, before, value))
    else:
        print("PLANTED  nothing -- clean copy")
    print("scratch corpus: %s  (%d sidecar files copied from %s)" % (scratch, n, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
