#!/usr/bin/env python3
"""T207 -- plant a corpus into a SCRATCH directory for the red battery.

  python3 plant-corrupt.py <scratch-dir> corrupt|clean|both

`corrupt`  one capture-shaped response carrying money literals that GENUINELY change value
           under a binary-double round trip.  Every literal is a legal `numeric(19,6)` value,
           i.e. a shape Fineract's own schema permits it to emit
           [VERIFIED: `LoanProductRelatedDetail.java:61-62` `scale = 6, precision = 19`, cited
           in T186 §2.2].  Nothing here is exotic; that is the point.
`clean`    the same shape with the corpus's real literals, which do NOT change value.

The file is written as TEXT, never via `json.dump`, so the literals reach disk exactly as
written and are not themselves reshaped by a float on the way in.  Writes ONLY under the
scratch dir it is given, and refuses a target inside the repo.
"""
import os
import sys

CORRUPT = """{
  "periods": [
    {"period": 1, "principalDue": 1234567890123.456789, "interestDue": 1200000.000000},
    {"period": 2, "principalDue": 9999999999999.999999, "interestDue": 0.10}
  ],
  "totalPrincipalDisbursed": 9007199254740993.00,
  "currency": {"code": "MNT", "decimalPlaces": 2}
}
"""

CLEAN = """{
  "periods": [
    {"period": 1, "principalDue": 1200000.00, "interestDue": 13158.10},
    {"period": 2, "principalDue": 102517.60, "interestDue": 112082.40}
  ],
  "totalPrincipalDisbursed": 1162502.50,
  "currency": {"code": "MNT", "decimalPlaces": 2}
}
"""

# A response whose MONEYISH leaves are BARE JSON NUMBERS rather than strings -- the exact
# condition `cells()` drops silently, and which the real corpus happens not to contain.
BARE_NUMBERS = """{
  "periods": [
    {"period": 1, "principalDue": 1200000.00, "interestDue": 13158.10},
    {"period": 2, "principalDue": 102517.60, "interestDue": 112082.40}
  ],
  "totalPrincipalDisbursed": 1162502.50,
  "currency": {"code": "MNT", "decimalPlaces": 2}
}
"""


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    d, which = os.path.abspath(argv[0]), argv[1]
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        *([os.pardir] * 5)))
    if d.startswith(repo + os.sep):
        print("REFUSING: %s is inside the repo (%s). Plant into a scratch dir." % (d, repo))
        return 9
    os.makedirs(d, exist_ok=True)
    wrote = []
    if which in ("corrupt", "both"):
        p = os.path.join(d, "PLANTED-value-corrupt.json")
        open(p, "w").write(CORRUPT)
        wrote.append(p)
    if which in ("clean", "both"):
        p = os.path.join(d, "PLANTED-clean.json")
        open(p, "w").write(CLEAN)
        wrote.append(p)
    if which == "bare":
        p = os.path.join(d, "PLANTED-bare-numbers-exact.json")
        open(p, "w").write(BARE_NUMBERS)
        wrote.append(p)
    for p in wrote:
        print(p)
    return 0 if wrote else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
