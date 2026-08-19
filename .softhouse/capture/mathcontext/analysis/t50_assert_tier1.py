#!/usr/bin/env python3
"""
T50 Tier 1 admissibility assertions + the full cell dump.

Reads ONLY the capture payload.  Contacts no oracle, no server, no database.

`patterns.md`, T46-N4: "publish the cells, not the verdict".  So every one of the 2352 cells
is printed, and the verdict is computed from the printed cells rather than asserted beside them.

Exit 0 => admissible.  Exit 1 => BREACH; the runner moves the payload aside and refuses to
publish it.
"""
import json
import sys
from collections import defaultdict

JDK_ORDINALS = ["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]

breaches = []


def breach(msg):
    breaches.append(msg)
    print("BREACH: " + msg)


def ok(msg):
    print("  ok  " + msg)


def main(path):
    with open(path) as fh:
        doc = json.load(fh)

    cases = doc["cases"]
    print("== T50 Tier 1 admissibility ==")
    print("  payload: %s" % path)
    print("  caseCount declared %d, present %d" % (doc["caseCount"], len(cases)))
    if doc["caseCount"] != len(cases):
        breach("declared caseCount %d != cases present %d" % (doc["caseCount"], len(cases)))

    # ---- A0. MoneyHelper.PRECISION, read off the oracle ------------------------------------
    print("  MoneyHelper.PRECISION as read from the oracle: %s" % doc["moneyHelperPrecisionConstant"])
    if doc["moneyHelperPrecisionConstant"] != 19:
        breach("MoneyHelper.PRECISION is %s, expected the compile-time constant 19"
               % doc["moneyHelperPrecisionConstant"])
    else:
        ok("MoneyHelper.PRECISION == 19")

    # ---- A1. THE VACUITY GUARD (patterns.md / T46-N2) --------------------------------------
    canary = doc["ambientCanary"]
    print("  ambientCanary: %s" % canary)
    if "THREW java.lang.IllegalStateException" not in canary or "Rounding mode is not initialized" not in canary:
        breach("the ambient-absence probe is VACUOUS: reading MoneyHelper.getMathContext() on an "
               "uninitialised tenant did not throw IllegalStateException. Every ABSENT case below "
               "proves nothing.")
    else:
        ok("ambient-absence probe is LIVE (uninitialised tenant throws IllegalStateException)")

    # ---- A2. the ordinal -> RoundingMode mapping, read off the oracle -----------------------
    print("  -- ordinal proof, read back out of MoneyHelper --")
    for row in doc["ordinalProof"]:
        o = row["ordinal"]
        print("     ordinal %d -> MoneyHelper %-60s | JDK RoundingMode.values()[%d] = %s"
              % (o, row["moneyHelperRoundingMode"], o, row["jdkRoundingModeValues"]))
        if o <= 6:
            if row["moneyHelperRoundingMode"] != JDK_ORDINALS[o]:
                breach("MoneyHelper maps ordinal %d to %r, not %r"
                       % (o, row["moneyHelperRoundingMode"], JDK_ORDINALS[o]))
    ok("ordinals 0-6 map to UP,DOWN,CEILING,FLOOR,HALF_UP,HALF_DOWN,HALF_EVEN on the oracle's own testimony")

    # ---- A3. per-case attestation, object vs intent -----------------------------------------
    n_att = 0
    n_absent = 0
    n_disagree_axes = 0
    for c in cases:
        i, a = c["inputs"], c["attestation"]
        if a["threadedPrecisionObject"] != i["threadedPrecisionIntent"]:
            breach("%s: threaded precision object %s != intent %s"
                   % (c["id"], a["threadedPrecisionObject"], i["threadedPrecisionIntent"]))
        if a["threadedRoundingModeObject"] != i["threadedRoundingModeIntent"]:
            breach("%s: threaded mode object %s != intent %s"
                   % (c["id"], a["threadedRoundingModeObject"], i["threadedRoundingModeIntent"]))
        if i["ambientRoundingModeOrdinal"] is None:
            n_absent += 1
            if "IllegalStateException" not in a["ambientMathContextObject"]:
                breach("%s: declared ambient ABSENT but MoneyHelper.getMathContext() did not throw: %s"
                       % (c["id"], a["ambientMathContextObject"]))
        else:
            want = "precision=19 roundingMode=%s" % i["ambientRoundingModeIntent"]
            if a["ambientMathContextObject"] != want:
                breach("%s: ambient MathContext object %r != %r"
                       % (c["id"], a["ambientMathContextObject"], want))
            if i["ambientRoundingModeIntent"] != i["threadedRoundingModeIntent"]:
                n_disagree_axes += 1
                if a["ambientEqualsThreadedObject"]:
                    breach("%s: axes declared different but the two MathContext objects are equal" % c["id"])
        n_att += 1
    ok("%d cases attested object-vs-intent, 0 disagreements" % n_att)
    ok("%d cases have ambient ABSENT (uninitialised tenant)" % n_absent)
    ok("%d cases have ambient mode STRICTLY DIFFERENT from threaded mode -- the separation this "
       "task exists to produce, and which no tenant write can create on Path B" % n_disagree_axes)
    if n_disagree_axes == 0:
        breach("no case separates the two axes; the experiment did not happen")

    # ---- A4/A5. the absence probe, per site --------------------------------------------------
    print("  -- absence probe, per site (ambient uninitialised) --")
    by_site = defaultdict(list)
    for c in cases:
        by_site[c["site"]].append(c)
    site_reads_ambient = {}
    for site in sorted(by_site):
        absent = [c for c in by_site[site] if c["inputs"]["ambientRoundingModeOrdinal"] is None]
        threw = [c for c in absent
                 if c["error"] and "IllegalStateException" in c["error"]
                 and "Rounding mode is not initialized" in c["error"]]
        okd = [c for c in absent if c["error"] is None and c["observed"] is not None]
        other = [c for c in absent if c not in threw and c not in okd]
        hyp = by_site[site][0]["hypothesisReadsAmbient"]
        observed_reads = len(threw) == len(absent) and len(absent) > 0
        site_reads_ambient[site] = observed_reads
        print("     %-24s absent=%3d  threw_IllegalState=%3d  completed=%3d  other=%3d "
              "| hypothesis readsAmbient=%s | OBSERVED readsAmbient=%s%s"
              % (site, len(absent), len(threw), len(okd), len(other), hyp, observed_reads,
                 "" if observed_reads == hyp else "   <-- HYPOTHESIS CONTRADICTED BY OBSERVATION"))
        if other:
            breach("%s: %d absent cases neither threw the expected IllegalStateException nor "
                   "completed; first: %s / %s" % (site, len(other), other[0]["id"], other[0]["error"]))
        if len(absent) == 0:
            breach("%s: no absence cases at all" % site)

    # ---- A6. the cell dump and the separation verdict ---------------------------------------
    print()
    print("== CELL DUMP -- every (site, value, ambient, threaded) observation ==")
    print("   columns: site | value | ambient | threaded | intermediate | observed | error")
    grid = defaultdict(dict)
    for c in cases:
        i = c["inputs"]
        amb = "ABSENT" if i["ambientRoundingModeOrdinal"] is None else i["ambientRoundingModeIntent"]
        thr = i["threadedRoundingModeIntent"]
        grid[(c["site"], c["value"])][(amb, thr)] = c
    n_printed = 0
    for key in sorted(grid):
        site, val = key
        for (amb, thr) in sorted(grid[key]):
            c = grid[key][(amb, thr)]
            print("   %-24s %-22s %-10s %-10s %-24s %-24s %s"
                  % (site, val, amb, thr,
                     c["intermediate"] if c["intermediate"] is not None else "-",
                     c["observed"] if c["observed"] is not None else "-",
                     (c["error"] or "-")[:60]))
            n_printed += 1
    print("   %d cells printed" % n_printed)
    if n_printed != len(cases):
        breach("printed %d cells but the payload holds %d cases" % (n_printed, len(cases)))

    # ---- A7. does the observation move with AMBIENT, with THREADED, or with neither? --------
    print()
    print("== SEPARATION -- holding one axis fixed and moving the other (ABSENT cells excluded) ==")
    print("   columns: site | value | #distinct observations | moves-with-ambient | moves-with-threaded")
    summary = {}
    for key in sorted(grid):
        site, val = key
        cells = {k: v for k, v in grid[key].items() if k[0] != "ABSENT"}
        distinct = sorted({c["observed"] for c in cells.values()})
        # moves-with-ambient: exists a threaded value t and two ambients a1,a2 with different observed
        moves_amb = 0
        moves_thr = 0
        thrs = sorted({k[1] for k in cells})
        ambs = sorted({k[0] for k in cells})
        for t in thrs:
            vals = {cells[(a, t)]["observed"] for a in ambs if (a, t) in cells}
            if len(vals) > 1:
                moves_amb += 1
        for a in ambs:
            vals = {cells[(a, t)]["observed"] for t in thrs if (a, t) in cells}
            if len(vals) > 1:
                moves_thr += 1
        summary[key] = (len(distinct), moves_amb, len(thrs), moves_thr, len(ambs), distinct)
        print("   %-24s %-22s distinct=%-3d  ambient moves it in %d/%d threaded columns  "
              "threaded moves it in %d/%d ambient rows"
              % (site, val, len(distinct), moves_amb, len(thrs), moves_thr, len(ambs)))
        print("        distinct observations: %s" % ", ".join(distinct))

    # ---- A8. the NULL CONTROL must not move at all ------------------------------------------
    print()
    print("== NULL CONTROL (V3-noTie-scale2: the arithmetic is exact, no rounding decision exists) ==")
    control_ok = True
    for key in sorted(grid):
        site, val = key
        if val != "V3-noTie-scale2":
            continue
        d = summary[key][0]
        print("   %-24s %-22s distinct=%d" % (site, val, d))
        if d != 1:
            control_ok = False
            breach("null control %s/%s produced %d distinct observations; a shape with no "
                   "rounding decision must not move with either axis" % (site, val, d))
    if control_ok:
        ok("null control is flat on every site: the grid is not simply always-different")

    print()
    if breaches:
        print("== %d BREACH(ES) -- payload NOT admissible ==" % len(breaches))
        return 1
    print("== all admissibility assertions passed ==")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
