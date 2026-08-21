#!/usr/bin/env python3
"""T159 — case list + REGISTERED PREDICTION for the INDEPENDENT re-observation of T117.

T159 is the independent review of T117. T117's most consequential claim is that
**no upper bound is established** on the unamortized residual, because "the largest
failing principal tracks the largest term asked" and nothing above n = 1000 was ever
asked. That is a statement about the SHAPE OF T117'S PROBE SET, and it could be an
artefact of it. This probe attacks it directly, at the live reference oracle
(Fineract), on the pinned image, through the same Path A embeddable seam.

Four legs:

  TERM  n > 1000 — the region NOBODY has ever asked. B in {1, 501, 1001, 10001} at
        n in {1200, 1500, 2000, 3000}, plus B = 100001 and B = 1000001 at n = 3000.
        If B = 1001 becomes family B at some n <= 3000, the trend CONTINUES and the
        residual is unbounded in B given enough term. If it stays clean, the trend
        BREAKS and MNT 5.01 may be near a real ceiling.

  PRIN  principals strictly BETWEEN 501 and 1001 minor units at n = 1000 — the gap
        T117's ladder jumped straight over (odd only; T117 observed 16/16 even-B
        cells clean, and zero family-B cells at even B).

  BAND  B = 1, the band boundaries T117 reports at n = 361/362/363/364 and
        n = 390/391 and n = 400/401. A boundary off by one changes the claim's shape.
        These cells are ALSO committed pass-1 cells, so they double as byte-identity
        re-asks under fresh tenant ids.

  REP   straight re-asks of committed pass-2 cells under tenant ids disjoint from
        T117's, including the MNT 5.01 headline cell and the three PARTIAL B = 11
        cells that falsify a sentence standing in gates.md.

MONEY DISCIPLINE (P-25). No float is constructed anywhere in this file. Every money
quantity is an INTEGER count of MINOR UNITS and reaches Java as
`new BigDecimal(<int>).movePointLeft(2)`; the rate is a decimal STRING handed
verbatim to `new BigDecimal("600.0")`.

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product and this probe opens no database connection at all.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RATE = "600.0"

CASES = []
seen = set()


def add(b, n, leg, basis):
    if (b, n) in seen:
        return False
    seen.add((b, n))
    CASES.append(("R600p0-N%d-B%d" % (n, b), n, b, leg, basis))
    return True


# --- leg TERM: above n = 1000, which no probe in this program has ever asked ------
for b in (1, 501, 1001, 10001):
    for n in (1200, 1500, 2000, 3000):
        add(b, n, "TERM", "n > 1000 — never asked before; does the failing principal keep tracking the term?")
add(100001, 3000, "TERM", "n > 1000 at a large principal")
add(1000001, 3000, "TERM", "n > 1000 at a large principal")

# --- leg PRIN: odd principals between 501 and 1001 at n = 1000 -------------------
for b in (503, 551, 601, 701, 751, 801, 901, 999):
    add(b, 1000, "PRIN", "odd principal in the 501..1001 gap T117's ladder jumped over")
for b in (601, 801, 999):
    add(b, 2000, "PRIN", "odd principal in the 501..1001 gap, at a term above 1000")

# --- leg BAND: B = 1 boundary cells ---------------------------------------------
for n in (360, 361, 362, 363, 364, 365, 389, 390, 391, 392, 393, 399, 400, 401):
    add(1, n, "BAND", "band boundary re-ask at B = 1 — is the boundary where T117 says it is?")

# --- leg REP: byte-identity re-asks of committed pass-2 cells --------------------
add(501, 1000, "REP", "THE HEADLINE CELL — MNT 5.01 residual, re-asked under a fresh tenant id")
for n in (108, 121, 150):
    add(11, n, "REP", "PARTIAL-amortization cell — re-asked under a fresh tenant id")

_rng = random.Random(20260821 + 159)
_rng.shuffle(CASES)


def predict(n, b, leg):
    """T159's registered prediction. Integer arithmetic only; no float anywhere.

    BASIS, re-derived by T159 from T117's RAW captures (not from T117's analysis):
    at 600.0 % the monthly rate is exactly 1/2, family B was observed only at ODD B,
    and the first failing term among the five T117 asked grows with B --
    B <= 51 fail at n = 108 (the smallest term asked), B = 101 first at n = 250,
    B = 501 first at n = 1000, and B >= 1001 at none of the five. The observed
    brackets are therefore 101 in (150, 250] and 501 in (250, 1000], which is
    consistent with a threshold term of ORDER 2*B. If that order is real, B = 1001
    should turn family B somewhere around n = 2000 and B = 10001 not until n of
    order 20000 -- far above anything asked here.

    COUNTER-HYPOTHESIS this probe can also confirm: the tie direction is NOT a
    function of "B odd" (T117 already showed necessary-not-sufficient), and B = 1001
    at n = 1000 emits an EMI of 5.01 = ceil(1001/2) while B = 501 at n = 1000 emits
    2.50 = floor(501/2). If the tie direction is essentially arbitrary in n, the
    n > 1000 region will show family B and clean interleaved with no term threshold
    at all, and "the largest failing principal tracks the largest term asked" is an
    ARTEFACT of a five-point ladder, not a trend.
    """
    if leg == "REP":
        return True, "B", "high", "committed family-B cell; must reproduce byte-identically"
    if leg == "BAND":
        # T117's reported bands at B = 1: famB on 300-361 and 364-390, clean on
        # 362-363 and 391-400.
        clean = n in (362, 363) or 391 <= n <= 400
        return (not clean), (None if clean else "B"), "high", \
            "T117's reported band structure at B = 1, taken at face value and re-asked"
    if b % 2 == 0:
        return False, None, "high", "B even -> B*r is an integer, no half-minor-unit tie"
    if leg == "TERM":
        if b == 1:
            return True, "B", "moderate", "B = 1 is family B at n = 1000; predicted to continue above it"
        if b == 501:
            return True, "B", "moderate", "B = 501 is family B at n = 1000; predicted to continue above it"
        if b == 1001:
            return (n >= 2000), ("B" if n >= 2000 else None), "low", \
                "THE DECISIVE PREDICTION: if the threshold term is of order 2*B, B = 1001 turns " \
                "family B at n ~ 2000 and is clean at n = 1200 and n = 1500"
        return False, None, "low", "threshold term of order 2*B would be far above n = 3000 here"
    if leg == "PRIN":
        if n == 1000:
            # order-2B threshold: B <= 500 would already have failed; 501..1001 is
            # exactly the bracket where n = 1000 stops being enough.
            return (b <= 601), ("B" if b <= 601 else None), "low", \
                "order-2*B threshold puts the n = 1000 cutoff somewhere near B ~ 500-600"
        return True, "B", "low", "n = 2000 should be past the order-2*B threshold for B < 1001"
    raise AssertionError("unclassified leg %s" % leg)


pred, java, ids = {}, [], []
for tail, n, b, leg, basis in CASES:
    rid = "T159-" + tail
    fails, fam, conf, why = predict(n, b, leg)
    ids.append(rid)
    pred[rid] = {"annualRate": RATE, "n": n, "B_minor": b, "leg": leg,
                 "predictedFails": fails, "predictedFamily": fam,
                 "predictedNotFamilyB": fam != "B",
                 "confidence": conf, "basis": basis, "reasoning": why}
    java.append(
        '        cases.add(prodDates("%s", "T159 independent re-observation of T117 (%s) — %s", '
        'LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(%d).movePointLeft(2), '
        '%d, new BigDecimal("%s"), "%s"));' % (rid, leg, basis, b, n, RATE, rid.lower().replace('-', '_')))

assert len(set(ids)) == len(ids), "duplicate case id"

summary = {
    "task": "T159", "reviews": "T117", "gate": "G-8", "scrambleSeed": 20260821 + 159,
    "caseCount": len(ids),
    "legs": {L: sum(1 for c in CASES if c[3] == L) for L in ("TERM", "PRIN", "BAND", "REP")},
    "largestTermAsked": max(c[1] for c in CASES),
    "largestPrincipalAsked_minor": max(c[2] for c in CASES),
    "predictedFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] == "B"),
    "predictedNotFamilyB": sum(1 for v in pred.values() if v["predictedFamily"] != "B"),
    "decisiveCells": ["T159-R600p0-N%d-B1001" % n for n in (1200, 1500, 2000, 3000)],
}
json.dump({"summary": summary, "cases": pred},
          open(os.path.join(ROOT, 'prediction-t159.json'), 'w'), indent=1, sort_keys=True)
open('/tmp/t159-cases.java', 'w').write("\n".join(java) + "\n")
json.dump(ids, open('/tmp/t159-ids.json', 'w'))
print(json.dumps(summary, indent=1))
