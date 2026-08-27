#!/usr/bin/env python3
"""T117 PASS 2 — generate the case list and the REGISTERED PREDICTION for the principal-extent probe.

Writes:
  ../prediction-pass2.json    predicted outcome per case, registered BEFORE any pass-2 observation
  /tmp/t117p2-cases.java      the cases.add(...) block spliced into CaptureT117P2.java
  /tmp/t117p2-ids.json        the exact id list run-t117-pass2.sh requires, in order

WHY PASS 2 EXISTS. Pass 1 refuted the registered prediction that the failing principal cannot
exceed one minor unit: family B was observed at B = 3 and B = 5 minor units (MNT 0.03, MNT 0.05).
It therefore established that "family B is sub-minor-unit dust" is false, and established NO upper
bound at all — B = 5 is simply the largest principal pass 1 was asked to try. The question the
gate write-up actually turns on is *how far up it goes*, so pass 2 asks the same seam for larger
principals: an odd ladder up to MNT 1,200,000.01, an even control ladder, and a contiguous
B = 6..20 run at one term to see the odd/even structure directly.

No float is constructed anywhere in this file. Every money quantity is an INTEGER count of MINOR
UNITS; the rate is a decimal STRING handed verbatim to BigDecimal on the Java side (P-25).

Emission order is scrambled by a fixed recorded permutation; every tenant id is distinct from
T83's, T84's, T100's and T117 pass 1's.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RATE = "600.0"

# n values at which BOTH B = 3 and B = 5 were observed family B in pass 1
FAMB_TERMS = [108, 121, 150, 250, 1000]

# odd principals in MINOR UNITS. 100000001 = MNT 1,000,000.01; 120000001 = MNT 1,200,000.01,
# i.e. the program's standard ordinary-loan control amount plus one minor unit.
ODD_LADDER = [7, 9, 11, 21, 51, 101, 501, 1001, 10001, 100001, 1000001, 100000001, 120000001]
EVEN_CTRL = [100, 1000, 10000, 100000]

seen = set()
CASES = []


def add(b, n, leg, basis):
    if (b, n) in seen:
        return False
    seen.add((b, n))
    CASES.append(("R600p0-N%d-B%d" % (n, b), n, b, leg, basis))
    return True


# leg OL — the odd ladder. Does family B reach a commercially recognisable amount?
for b in ODD_LADDER:
    for n in FAMB_TERMS:
        add(b, n, "OL", "odd-principal ladder — how far up does family B go?")

# leg BC — contiguous B = 6..20 at one term, to show the odd/even structure directly
for b in range(6, 21):
    add(b, 150, "BC", "contiguous principal sweep B=6..20 at n=150")

# leg EC — even control at large principals
for b in EVEN_CTRL:
    for n in (150, 250):
        add(b, n, "EC", "even-principal control at large B")

# leg RP — reproduce two pass-1 FAMILY B cells under new tenant ids
add(5, 104, "RP", "pass-1 family-B cell re-asked under a new tenant id")
add(3, 300, "RP", "pass-1 CLEAN cell at odd B re-asked under a new tenant id")

import random  # noqa: E402

SCRAMBLE_SEED = 20260821 + 2
_rng = random.Random(SCRAMBLE_SEED)
_rng.shuffle(CASES)


def predict(n, b, leg):
    """Registered prediction for one pass-2 cell. Integer arithmetic only.

    Basis: pass 1 observed family B on 122 of 122 cells whose limit quantity B*r is a HALF-INTEGER
    number of minor units and on none whose B*r is an integer. At 600.0 % r = 1/2 exactly, so that
    condition is exactly "B is odd". It is NECESSARY but NOT SUFFICIENT — 62 pass-1 cells with odd
    B were clean — and which n fall in a family-B band varies with B, so no per-cell call is safe.
    The predictions below are therefore stated per-B over the five terms, not per cell.
    """
    if b % 2 == 0:
        return False, None, "high", "B even -> B*r is an integer, no half-minor-unit tie"
    if leg == "RP":
        return (n == 104), ("B" if n == 104 else None), "high", "reproduces a pass-1 cell"
    conf = "high" if b <= 101 else "moderate"
    return True, "B", conf, ("odd B -> B*r is a half-integer; predicted family B at this term, "
                             "though pass 1 shows some odd-B terms are clean")


pred, java, ids = {}, [], []
for tail, n, b, leg, basis in CASES:
    rid = "T117P2-" + tail
    fails, fam, conf, why = predict(n, b, leg)
    ids.append(rid)
    pred[rid] = {"annualRate": RATE, "n": n, "B_minor": b, "leg": leg,
                 "predictedFails": fails, "predictedFamily": fam, "predictedNotFamilyB": fam != "B",
                 "confidence": conf, "basis": basis, "reasoning": why}
    java.append(
        '        cases.add(prodDates("%s", "T117 pass 2 principal-extent probe (%s) — %s", '
        'LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), '
        '%d, new BigDecimal("%s"), "%s"));' % (rid, leg, basis, b, n, RATE, rid.lower().replace('-', '_')))

assert len(set(ids)) == len(ids), "duplicate case id"

summary = {
    "task": "T117", "pass": 2, "gate": "G-8", "scrambleSeed": SCRAMBLE_SEED,
    "caseCount": len(ids),
    "legs": {L: sum(1 for c in CASES if c[3] == L) for L in ("OL", "BC", "EC", "RP")},
    "predictedFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] == "B"),
    "predictedNotFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] != "B"),
    "largestPrincipalAsked_minor": max(c[2] for c in CASES),
}
json.dump({"summary": summary, "cases": pred},
          open(os.path.join(ROOT, 'prediction-pass2.json'), 'w'), indent=1, sort_keys=True)
open('/tmp/t117p2-cases.java', 'w').write("\n".join(java) + "\n")
json.dump(ids, open('/tmp/t117p2-ids.json', 'w'))
print(json.dumps(summary, indent=1))
