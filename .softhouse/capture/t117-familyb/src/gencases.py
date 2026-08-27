#!/usr/bin/env python3
"""T117 — generate the case list and the REGISTERED PREDICTION for the family-B extent probe.

Writes:
  ../prediction.json      predicted outcome per case, registered BEFORE any observation exists
  /tmp/t117-cases.java    the cases.add(...) block spliced into CaptureT117.java
  /tmp/t117-ids.json      the exact id list run-t117.sh requires the capture to carry, in order

No float is constructed anywhere in this file. Every money quantity is an INTEGER count of MINOR
UNITS and every rate is a decimal STRING handed verbatim to BigDecimal on the Java side (P-25).

WHAT THE PROBE ASKS (task T117, gate G-8, T101's suggested probe carried forward by T112):

  (i)  is family B a HALF-LINE in n (every n above some threshold) or a BOUNDED ISLAND?
       -> 600.0 % p.a., MNT 0.01 (B = 1 minor unit), n = 300..1000, which is entirely above the
          largest n ever asked at the family-B shape (250, by T100).
  (ii) can the FAILING PRINCIPAL exceed ONE MINOR UNIT?
       -> 600.0 % p.a., B = 2..5 minor units, across the whole family-B n range and above it.

Emission order is scrambled by a FIXED, RECORDED permutation so that a reproduction of this
capture is not a reproduction of a natural sweep order, and every tenant id is distinct from
T83's (`cap_t83_*`), T84's (`t84_*`) and T100's (`t100_*`).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RATE = "600.0"                 # decimal string, handed verbatim to new BigDecimal("600.0")

# ---------------------------------------------------------------------------------------------
# The four legs. Each entry is (id-tail, n, B in MINOR UNITS, leg, basis).
# ---------------------------------------------------------------------------------------------
CASES = []

# leg CTRL — two cells ALREADY in the committed corpus, re-asked under new tenant ids. These are
# not calibrations of the rig (the two P-CAL-* cases are); they are re-asks of the phenomenon.
CASES.append(("CTRL-R600p0-N103-B1", 103, 1, "CTRL",
              "T84 measured CLEAN at this shape; re-asked under a new tenant id"))
CASES.append(("CTRL-R600p0-N250-B1", 250, 1, "CTRL",
              "T100 measured FAMILY B at this shape, the largest n ever asked at it; re-asked"))

# leg NC — contiguous n, 300..400, B = 1. A 101-long contiguous block far above every n ever asked
# at the family-B shape. A bounded island with an upper edge inside this block would show as a
# clean cell here.
for n in range(300, 401):
    CASES.append(("NC-R600p0-N%d-B1" % n, n, 1, "NC", "contiguous n sweep 300..400"))

# leg NL — ladder n = 410, 420, ... 1000, B = 1. Coverage of the rest of the requested range.
for n in range(410, 1001, 10):
    CASES.append(("NL-R600p0-N%d-B1" % n, n, 1, "NL", "ladder n 410..1000 step 10"))

# leg NT — contiguous n, 995..999, B = 1. A second contiguous block at the TOP of the requested
# range, so contiguity is tested at both ends and not only at 300..400.
for n in range(995, 1000):
    CASES.append(("NT-R600p0-N%d-B1" % n, n, 1, "NT", "contiguous n sweep 995..999"))

# leg BS — the principal question. B = 2..5 minor units across the family-B n range and above it.
BS_TERMS = [104, 108, 121, 150, 250, 300, 500, 1000]
for b in (2, 3, 4, 5):
    for n in BS_TERMS:
        CASES.append(("BS-R600p0-N%d-B%d" % (n, b), n, b, "BS",
                      "principal sweep B=2..5 at 600.0 percent — can the failing principal exceed 1 minor unit?"))

# ---------------------------------------------------------------------------------------------
# Deterministic scramble. random.Random(20260821) with this exact call sequence IS the recorded
# permutation; it is reproducible from this file alone and involves no float.
# ---------------------------------------------------------------------------------------------
import random  # noqa: E402  (imported here so the seeding is adjacent to its use)

SCRAMBLE_SEED = 20260821
_rng = random.Random(SCRAMBLE_SEED)
_rng.shuffle(CASES)

# ---------------------------------------------------------------------------------------------
# The prediction. See ../PREDICTION.md for the reasoning; this file carries the per-case call.
# ---------------------------------------------------------------------------------------------


def predict(n, b):
    """Registered prediction for one cell. Integer arithmetic only."""
    if b == 1:
        if n <= 103:
            return False, None, "high"
        return True, "B", "high"
    # b >= 2 at 600.0 %: predicted NOT family B, and predicted clean at moderate confidence only.
    return False, None, "moderate"


pred, java, ids = {}, [], []
for tail, n, b, leg, basis in CASES:
    rid = "T117-" + tail
    fails, fam, conf = predict(n, b)
    ids.append(rid)
    pred[rid] = {
        "annualRate": RATE,
        "n": n,
        "B_minor": b,
        "leg": leg,
        "predictedFails": fails,
        "predictedFamily": fam,
        "predictedNotFamilyB": fam != "B",
        "confidence": conf,
        "basis": basis,
    }
    java.append(
        '        cases.add(prodDates("%s", "T117 family-B extent probe (%s) — %s", '
        'LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), '
        '%d, new BigDecimal("%s"), "%s"));' % (rid, leg, basis, b, n, RATE, rid.lower().replace('-', '_')))

assert len(set(ids)) == len(ids), "duplicate case id"

summary = {
    "task": "T117",
    "gate": "G-8",
    "scrambleSeed": SCRAMBLE_SEED,
    "caseCount": len(ids),
    "legs": {
        "CTRL": sum(1 for c in CASES if c[3] == "CTRL"),
        "NC": sum(1 for c in CASES if c[3] == "NC"),
        "NL": sum(1 for c in CASES if c[3] == "NL"),
        "NT": sum(1 for c in CASES if c[3] == "NT"),
        "BS": sum(1 for c in CASES if c[3] == "BS"),
    },
    "predictedFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] == "B"),
    "predictedNotFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] != "B"),
}

json.dump({"summary": summary, "cases": pred}, open(os.path.join(ROOT, 'prediction.json'), 'w'),
          indent=1, sort_keys=True)
open('/tmp/t117-cases.java', 'w').write("\n".join(java) + "\n")
json.dump(ids, open('/tmp/t117-ids.json', 'w'))
print(json.dumps(summary, indent=1))
