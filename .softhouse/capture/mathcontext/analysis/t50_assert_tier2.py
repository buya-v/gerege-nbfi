#!/usr/bin/env python3
"""
T50 Tier 2 admissibility assertions + the full cell dump.

Reads ONLY the capture payload.  Contacts no oracle, no server, no database.

Tier 2 differs from Tier 1 in one important way: some legs may LEGITIMATELY FAIL TO RUN (a leg
reached by reflection into a 76-parameter factory can throw before it reaches the site under
test).  A leg that throws is REPORTED, not hidden, and it is not a breach -- what IS a breach is
a leg that throws and is then written up as an observation.  So the exit code turns only on:

  * the vacuity canary being live,
  * per-case object-vs-intent attestation,
  * the null control not moving on any leg that ran,
  * every case being printed.

The per-leg verdicts (ambient-governed / threaded-governed / did not run) are COMPUTED FROM THE
PRINTED CELLS and printed beside their counts.

Exit 0 => admissible.  Exit 1 => BREACH; the runner moves the payload aside.
"""
import collections
import json
import sys

breaches = []


def breach(msg):
    breaches.append(msg)
    print("BREACH: " + msg)


def ok(msg):
    print("  ok  " + msg)


def main(path):
    doc = json.load(open(path))
    cases = doc["cases"]
    print("== T50 Tier 2 admissibility ==")
    print("  payload: %s" % path)
    print("  caseCount declared %d, present %d" % (doc["caseCount"], len(cases)))
    if doc["caseCount"] != len(cases):
        breach("declared caseCount %d != cases present %d" % (doc["caseCount"], len(cases)))

    print("  MoneyHelper.PRECISION as read from the oracle: %s" % doc["moneyHelperPrecisionConstant"])
    if doc["moneyHelperPrecisionConstant"] != 19:
        breach("MoneyHelper.PRECISION is %s, expected 19" % doc["moneyHelperPrecisionConstant"])

    canary = doc["ambientCanary"]
    print("  ambientCanary: %s" % canary)
    if "THREW java.lang.IllegalStateException" not in canary or "Rounding mode is not initialized" not in canary:
        breach("the ambient-absence probe is VACUOUS; every ABSENT case proves nothing")
    else:
        ok("ambient-absence probe is LIVE")

    # ---- per-case attestation ----------------------------------------------------------------
    n_disagree = 0
    for c in cases:
        i, a = c["inputs"], c["attestation"]
        if a["threadedPrecisionObject"] != 19:
            breach("%s: threaded precision object %s != 19" % (c["id"], a["threadedPrecisionObject"]))
        if a["threadedRoundingModeObject"] != i["threadedRoundingModeIntent"]:
            breach("%s: threaded mode object %s != intent %s"
                   % (c["id"], a["threadedRoundingModeObject"], i["threadedRoundingModeIntent"]))
        if i["ambientRoundingModeOrdinal"] is None:
            if "IllegalStateException" not in a["ambientMathContextObject"]:
                breach("%s: declared ambient ABSENT but the ambient read did not throw" % c["id"])
        else:
            want = "precision=19 roundingMode=%s" % i["ambientRoundingModeIntent"]
            if a["ambientMathContextObject"] != want:
                breach("%s: ambient MathContext object %r != %r" % (c["id"], a["ambientMathContextObject"], want))
            if i["ambientRoundingModeIntent"] != i["threadedRoundingModeIntent"]:
                n_disagree += 1
    ok("%d cases attested object-vs-intent" % len(cases))
    ok("%d cases have ambient mode STRICTLY DIFFERENT from threaded mode" % n_disagree)
    if n_disagree == 0:
        breach("no case separates the two axes; the experiment did not happen")

    # ---- per-leg: did it run at all? ----------------------------------------------------------
    print()
    print("== PER-LEG REACHABILITY (a leg that threw is reported, never written up as a result) ==")
    by_leg = collections.defaultdict(list)
    for c in cases:
        by_leg[c["leg"]].append(c)
    ran = {}
    for leg in sorted(by_leg):
        cs = by_leg[leg]
        present = [c for c in cs if c["inputs"]["ambientRoundingModeOrdinal"] is not None]
        absent = [c for c in cs if c["inputs"]["ambientRoundingModeOrdinal"] is None]
        okc = [c for c in present if c["error"] is None]
        errc = [c for c in present if c["error"] is not None]
        abs_threw = [c for c in absent
                     if c["error"] and "IllegalStateException" in c["error"]
                     and "Rounding mode is not initialized" in c["error"]]
        abs_ok = [c for c in absent if c["error"] is None]
        ran[leg] = len(okc) > 0
        print("   %-42s source: %s" % (leg, cs[0]["legSource"]))
        print("      ambient-present: %3d cases, %3d completed, %3d threw" % (len(present), len(okc), len(errc)))
        print("      ambient-ABSENT : %3d cases, %3d completed, %3d threw 'Rounding mode is not initialized'"
              % (len(absent), len(abs_ok), len(abs_threw)))
        if errc:
            print("      first error: %s" % errc[0]["error"][:200])
        if not ran[leg]:
            print("      => LEG DID NOT RUN.  No conclusion is drawn from it.")

    # ---- the cell dump -------------------------------------------------------------------------
    print()
    print("== CELL DUMP -- every (leg, value, ambient, threaded) observation ==")
    grid = collections.defaultdict(dict)
    for c in cases:
        i = c["inputs"]
        amb = "ABSENT" if i["ambientRoundingModeOrdinal"] is None else i["ambientRoundingModeIntent"]
        grid[(c["leg"], c["value"])][(amb, i["threadedRoundingModeIntent"])] = c
    printed = 0
    for key in sorted(grid):
        leg, val = key
        for k in sorted(grid[key]):
            c = grid[key][k]
            print("   %-42s %-24s %-10s %-10s %-40s %s"
                  % (leg, val, k[0], k[1],
                     c["observed"] if c["observed"] is not None else "-",
                     (c["error"] or "-")[:70]))
            printed += 1
    print("   %d cells printed" % printed)
    if printed != len(cases):
        breach("printed %d cells but the payload holds %d cases" % (printed, len(cases)))

    # ---- separation ------------------------------------------------------------------------------
    print()
    print("== SEPARATION -- ABSENT cells excluded; only legs that ran are summarised ==")
    summary = {}
    for key in sorted(grid):
        leg, val = key
        cells = {k: v for k, v in grid[key].items() if k[0] != "ABSENT" and v["error"] is None}
        if not cells:
            print("   %-42s %-24s (no completed cells)" % (leg, val))
            continue
        ambs = sorted({k[0] for k in cells})
        thrs = sorted({k[1] for k in cells})
        distinct = sorted({c["observed"] for c in cells.values()})
        moves_amb = sum(1 for t in thrs if len({cells[(a, t)]["observed"] for a in ambs if (a, t) in cells}) > 1)
        moves_thr = sum(1 for a in ambs if len({cells[(a, t)]["observed"] for t in thrs if (a, t) in cells}) > 1)
        summary[key] = (len(distinct), moves_amb, len(thrs), moves_thr, len(ambs))
        print("   %-42s %-24s distinct=%-3d  ambient moves it in %d/%d threaded columns  "
              "threaded moves it in %d/%d ambient rows"
              % (leg, val, len(distinct), moves_amb, len(thrs), moves_thr, len(ambs)))
        print("        distinct observations: %s" % ", ".join(distinct))

    # ---- null control ------------------------------------------------------------------------------
    print()
    print("== NULL CONTROL (W5-noTie: exact arithmetic, no rounding decision exists) ==")
    for key in sorted(summary):
        leg, val = key
        if val != "W5-noTie":
            continue
        d = summary[key][0]
        print("   %-42s distinct=%d" % (leg, d))
        if d != 1:
            breach("null control on %s produced %d distinct observations" % (leg, d))

    print()
    if breaches:
        print("== %d BREACH(ES) -- payload NOT admissible ==" % len(breaches))
        return 1
    print("== all admissibility assertions passed ==")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
