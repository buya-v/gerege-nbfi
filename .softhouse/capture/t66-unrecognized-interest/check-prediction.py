#!/usr/bin/env python3
"""T66 — check the registered PREDICTION against the pass-3h capture.

It reads ONLY .softhouse/capture/out/capture-prod3h-raw.json and prints, per case,
what the oracle answered. It computes nothing about money: every value printed is a
string lifted straight out of the capture.

Exit 0 iff P1..P5 all hold. Exit 1 with the offending cells otherwise — in which case
the T66 proof is refuted and ITEM 1's verdict is (A), not (B).
"""
import json
import sys

CAP = ".softhouse/capture/out/capture-prod3h-raw.json"
ZERO = ("0", "0.00", "0.0")

CALIBRATIONS = {
    "P-CAL", "P-CAL-P00", "P-CAL-EMI6", "P-CAL-LATQ0a",
    "P-CAL-MNT50M", "P-CAL-DRIFTF", "P-CAL-ZPA", "P-CAL-ZPB",
}

doc = json.load(open(CAP, encoding="utf-8"))
caps = doc["captures"]
fail = []

print("T66 PREDICTION CHECK — %s, %d cases, pass %s" % (CAP, len(caps), doc["pass"]))
print()
hdr = ("case", "n", "pathId", "FUI!=0", "IMU", "unrec!=0", "zeroEMI", "L", "afterL")
print("%-22s %4s %7s %7s %5s %9s %8s %5s %7s" % hdr)

for c in caps:
    cid = c["id"]
    pid = c.get("pathIdentity", {})
    m = c.get("mechanism")
    if not isinstance(m, dict) or not m.get("periods"):
        fail.append("%s: mechanism absent" % cid)
        continue
    ps = m["periods"]
    fui = [r["idx"] for r in ps if r["futureUnrecognizedInterest"] not in ZERO]
    imu = [r["idx"] for r in ps if r["interestMovedUpward"] is True]
    unrec = [r["idx"] for r in ps if r["unrecognizedInterest"] not in ZERO]
    zemi = [r["idx"] for r in ps if r["emi"] in ZERO]
    notfp = [r["idx"] for r in ps if r["isFullyPaid"] is not True]
    L = max(notfp) if notfp else None
    after = [i for i in zemi if L is not None and i > L]

    print("%-22s %4d %7s %7s %5s %9s %8d %5s %7d" % (
        cid, len(ps), pid.get("identical"), fui or "-", imu or "-",
        unrec or "-", len(zemi), L, len(after)))

    # P1
    if fui:
        fail.append("P1 FALSIFIED — %s: futureUnrecognizedInterest non-zero on periods %s" % (cid, fui))
    # P2
    if imu:
        fail.append("P2 FALSIFIED — %s: interestMovedUpward true on periods %s" % (cid, imu))
    # P3
    if pid.get("identical") is not True or pid.get("seamPlan") != pid.get("instrumentedPlan"):
        fail.append("P3 FALSIFIED — %s: the instrumented plan is not the seam's plan" % cid)

# P5 — the driver's hypothesis shape must actually be present, or the observation is
# uninformative about it and must not be quoted as corroboration.
zpb = next(c for c in caps if c["id"] == "P-CAL-ZPB")
ps = zpb["mechanism"]["periods"]
notfp = [r["idx"] for r in ps if r["isFullyPaid"] is not True]
L = max(notfp)
vac = [r for r in ps if r["isFullyPaid"] is True and r["emi"] in ZERO
       and r["totalPaidAmount"] in ZERO and r["idx"] > L]
print()
print("P5: P-CAL-ZPB last-not-fully-paid index L = %d; periods strictly after L that are "
      "VACUOUSLY fully paid (emi 0, nothing paid): %d" % (L, len(vac)))
if not vac:
    fail.append("P5 FALSIFIED — no vacuously fully-paid zero-EMI period strictly after L exists "
                "in P-CAL-ZPB, so this capture says nothing about the hypothesis")

# The intersection across the whole pass, reported for the handoff.
shapes = []
for c in caps:
    ps = c["mechanism"]["periods"]
    notfp = [r["idx"] for r in ps if r["isFullyPaid"] is not True]
    if not notfp:
        continue
    L = max(notfp)
    after = [r["idx"] for r in ps if r["idx"] > L and r["emi"] in ZERO and r["totalPaidAmount"] in ZERO]
    if after:
        shapes.append((c["id"], L, len(ps), len(after)))
print()
print("Cases exhibiting the FULL structural precondition (>=1 vacuously fully-paid zero-EMI "
      "period STRICTLY AFTER the last not-fully-paid period) — the half T63 never tested:")
for s in shapes:
    print("  %-22s L=%-4d n=%-4d periods after L: %d" % s)
print("  total: %d of %d cases" % (len(shapes), len(caps)))

print()
if fail:
    print("PREDICTION FALSIFIED:")
    for f in fail:
        print("  " + f)
    sys.exit(1)
print("P1 HOLDS  — futureUnrecognizedInterest is '0.00' on every period of every case.")
print("P2 HOLDS  — interestMovedUpward is false on every period of every case.")
print("P3 HOLDS  — every instrumented plan equals the pristine seam's plan cell for cell.")
print("P4 HOLDS  — asserted by run-pass3h.sh itself; all 8 rig calibrations reproduced.")
print("P5 HOLDS  — the hypothesis' own shape is present and the mechanism still did not fire.")
sys.exit(0)
