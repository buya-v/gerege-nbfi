#!/usr/bin/env python3
"""T116 — case list and REGISTERED PREDICTION for the family-B PROMOTION capture (gate G-8, option a).

Writes:
  ../prediction.json     predicted outcome per case, registered BEFORE any observation exists
  /tmp/t116-cases.java   the cases.add(...) block spliced into CaptureT116.java
  /tmp/t116-ids.json     the exact id list run-t116.sh requires the capture to carry, in order

NO FLOAT IS CONSTRUCTED ANYWHERE IN THIS FILE (P-25). Every money quantity is an INTEGER count of
MINOR UNITS; the rate is a decimal STRING handed verbatim to `new BigDecimal("600.0")` on the Java
side. Nothing here divides, and nothing here is read by a comparison after being widened.

WHY THIS PASS EXISTS — task T116 carries an explicit PROMOTION mandate for gate G-8 option (a):
promote a parity vector over the family-B region with an explicit, NARROW invariant exemption.
T116 re-captures the shapes it intends to promote from the live reference oracle rather than
transcribing another task's committed bytes (P-63: a figure in a handoff is evidence of when it was
true, not that it is true).

THE THREE PROBE CELLS, all at 600.0 % p.a., MNT, dp 2, FIXED_30_360, monthly, no down payment:

  n = 103, B = 1 minor unit  -- recorded CLEAN by T84 and by T117's CTRL re-ask. The amortizing
      side of the family-B lower boundary. Promotable WITHOUT any exemption, and its value is
      exactly that: it pins the boundary from below, so the exemption on the cells above it cannot
      be read as "600.0 % is exempt".
  n = 104, B = 1 minor unit  -- the LOWEST family-B cell ever observed. F-T114-1 established that
      the leading (sub-ulp) explanation for family B does NOT reach here: the exact-rational
      residual at n = 104 is +2.4293e-19 = 2.43 ulp at 19 significant digits. The region's cause is
      least understood exactly here.
  n = 108, B = 1 minor unit  -- the cell T100's exemption demo graded: 761 graded cells, 2 ungraded,
      ZERO cell diffs against the Go port, FAIL on exactly two invariants without an exemption.

THIS FILE PREDICTS; IT DOES NOT OBSERVE. The harness asserts nothing and classifies nothing; the
classification is done afterwards by classify_t116.py, reading only the emitted JSON.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RATE = "600.0"   # decimal string, verbatim to BigDecimal; never a float

# (id-tail, n, B in MINOR UNITS, leg, basis)
CASES = [
    ("CLEAN-R600p0-N103-B1", 103, 1, "BOUNDARY-BELOW",
     "the amortizing cell immediately below the family-B lower boundary"),
    ("FAMB-R600p0-N104-B1", 104, 1, "BOUNDARY-AT",
     "the lowest family-B cell ever observed; the sub-ulp explanation does not reach it (F-T114-1)"),
    ("FAMB-R600p0-N108-B1", 108, 1, "GRADED-BY-T100",
     "the family-B cell T100's exemption demo graded at 761 cells / 0 diffs"),
]

# --------------------------------------------------------------------------------------------
# Deterministic scramble, so a reproduction of this capture is not a reproduction of a natural
# sweep order. random.Random(20260822) with this exact call sequence IS the recorded permutation.
# --------------------------------------------------------------------------------------------
import random  # noqa: E402

SCRAMBLE_SEED = 20260822
random.Random(SCRAMBLE_SEED).shuffle(CASES)


def predict(n):
    """Registered prediction for one cell. Integer minor units only; no division anywhere.

    Returns (predictedFamilyB, predictedFinalBalanceMinor, predictedPrincipalRepaidMinor, confidence).
    A family-B cell is predicted to emit `principal 0.00` on EVERY repayment row, so the principal
    repaid is 0 minor units and the balance stays at the disbursed 1 minor unit on every row
    including the last. A clean cell is predicted to repay all 1 minor unit and end at 0.
    """
    if n <= 103:
        return False, 0, 1, "high"
    return True, 1, 0, "high"


pred, java, ids = {}, [], []
for tail, n, b, leg, basis in CASES:
    rid = "T116-" + tail
    famb, bal, repaid, conf = predict(n)
    ids.append(rid)
    pred[rid] = {
        "annualRate": RATE,
        "n": n,
        "B_minor": b,
        "leg": leg,
        "predictedFamilyB": famb,
        "predictedFinalRowBalanceMinor": bal,
        "predictedPrincipalRepaidMinor": repaid,
        "predictedRepaymentRowCount": n,
        "confidence": conf,
        "basis": basis,
    }
    java.append(
        '        cases.add(prodDates("%s", "T116 family-B promotion capture (%s) - %s", '
        'LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), '
        '%d, new BigDecimal("%s"), "%s"));' % (rid, leg, basis, b, n, RATE, rid.lower().replace('-', '_')))

assert len(set(ids)) == len(ids), "duplicate case id"
assert len(ids) == 3, "case count changed without the prediction being revisited"

summary = {
    "task": "T116",
    "gate": "G-8",
    "option": "(a) promote a parity vector with an explicit invariant exemption",
    "scrambleSeed": SCRAMBLE_SEED,
    "caseCount": len(ids),
    "emissionOrder": ids,
    "mathContext": {"precision": 19, "roundingMode": "HALF_UP"},
    "currency": {"code": "MNT", "minorUnitDigits": 2},
    "predictions": pred,
    "registeredBeforeObservation": True,
}
with open(os.path.join(ROOT, "prediction.json"), "w") as fh:
    json.dump(summary, fh, indent=1, sort_keys=True)
    fh.write("\n")
with open("/tmp/t116-cases.java", "w") as fh:
    fh.write("\n".join(java) + "\n")
with open("/tmp/t116-ids.json", "w") as fh:
    json.dump(ids, fh, indent=1)
    fh.write("\n")
print("wrote prediction.json (%d cases), /tmp/t116-cases.java, /tmp/t116-ids.json" % len(ids))
print("emission order: " + ", ".join(ids))
