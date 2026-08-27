#!/usr/bin/env python3
"""T66 — print the mechanism rows around the last not-fully-paid period, for the five
cases that exhibit the full structural precondition. Every value is a string lifted from
the capture; nothing here is computed."""
import json

d = json.load(open(".softhouse/capture/out/capture-prod3h-raw.json", encoding="utf-8"))
byid = {c["id"]: c for c in d["captures"]}
ZERO = ("0", "0.00", "0.0")

for cid in ("P-CAL-ZPB", "T66-M-R12000", "T66-M-DRIFT-R2400", "T66-M-DRIFT-R12000",
            "T66-M-FLOOR-HR", "T66-M-DISB-ON-DUE"):
    ps = byid[cid]["mechanism"]["periods"]
    notfp = [r["idx"] for r in ps if r["isFullyPaid"] is not True]
    L = max(notfp) if notfp else None
    lo = max(0, (L or 0) - 2)
    show = list(range(lo, min(len(ps), (L or 0) + 4)))
    if len(ps) - 1 not in show:
        show.append(len(ps) - 1)
    print("=== %s   (n=%d, last-not-fully-paid L=%s)" % (cid, len(ps), L))
    print("    idx  emi        calcDueInt  dueInt     unrec   FUI     IMU    balance      paid  fullyPaid")
    for i in show:
        r = ps[i]
        mark = " <- L" if i == L else ("" if i <= (L or 0) else " (after L)")
        print("    %-4d %-10s %-11s %-10s %-7s %-7s %-6s %-12s %-5s %s%s" % (
            r["idx"], r["emi"], r["calculatedDueInterest"], r["dueInterest"],
            r["unrecognizedInterest"], r["futureUnrecognizedInterest"],
            r["interestMovedUpward"], r["outstandingLoanBalance"],
            r["totalPaidAmount"], r["isFullyPaid"], mark))
    print()
