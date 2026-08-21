#!/usr/bin/env python3
"""T83 STEP 4 — run the Go port on the SAME inputs and compare cell for cell.

    python3 .softhouse/capture/t83-nonamortizing/src/run-port.py

The port is built and run on a SCRATCH COPY of the tree under /tmp. Nothing in
nexus/ is modified: `t83port.go.txt` is copied in as `cmd/t83port/main.go` in the
scratch copy only. This task changes no Go logic.

THE CONTROL IS LOAD-BEARING (T58's precedent, reused by T61 and T64). The report
carries `calibrationMismatches` — the number of graded money cells on which the
port disagrees with the capture on the two RIG CALIBRATION shapes, which are
already-promoted parity vectors. If that is not zero, the port is broken on
already-graded ground and no divergence measured on novel ground means anything.

Money is int64 minor units. There is no floating point in this file.

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program; nothing here opens a database connection.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAP = os.path.join(HERE, "..", "out", "capture-t83-raw.json")
OUTDIR = os.path.join(HERE, "..", "out")
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"


def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e


def minor(text):
    """Exact major-unit decimal text -> int64 minor units. No float, ever."""
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        sys.exit("OVER-SCALED wire text %r -- a significant digit beyond the currency "
                 "scale is a finding, never a rounding opportunity" % text)
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac)
    return -v if neg else v


def run_port():
    scratch = "/tmp/t83port"
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    d = os.path.join(scratch, "nexus", "cmd", "t83port")
    os.makedirs(d)
    shutil.copy(os.path.join(HERE, "t83port.go.txt"), os.path.join(d, "main.go"))
    p = subprocess.run(["go", "run", "./cmd/t83port"], cwd=os.path.join(scratch, "nexus"),
                       env=env(), capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("port run failed:\n%s" % p.stderr[:4000])
    res = json.loads(p.stdout)
    shutil.rmtree(scratch, ignore_errors=True)
    return {r["case"]: r for r in res}


def observed_cells(cap):
    """The graded MONEY cells of a capture case, as (row_index, field) -> minor."""
    cells = {}
    for i, p in enumerate(cap["observed"]["periods"]):
        cells[(i, "principal_minor")] = minor(p["principal"])
        if p.get("interest") is not None:
            cells[(i, "interest_minor")] = minor(p["interest"])
        if p.get("balance") is not None:
            cells[(i, "outstanding_principal_minor")] = minor(p["balance"])
    return cells


def main():
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
    port = run_port()

    missing = [i for i in caps if i not in port]
    if missing:
        sys.exit("the port program did not answer %d capture ids, e.g. %r" % (len(missing), missing[:5]))

    report = []
    cal_mismatch = 0
    for cid, cap in caps.items():
        pr = port[cid]
        obs = observed_cells(cap)
        entry = {"case": cid, "cells": len(obs)}
        if pr.get("error"):
            entry.update({"portRefused": True, "portError": pr["error"], "mismatches": None})
            report.append(entry)
            continue
        rows = pr["rows"]
        if len(rows) != len(cap["observed"]["periods"]):
            entry.update({"rowCountPort": len(rows), "rowCountOracle": len(cap["observed"]["periods"]),
                          "mismatches": None, "rowCountDiffers": True})
            report.append(entry)
            continue
        diffs = [{"row": i, "field": f, "oracle": w, "port": rows[i][f]}
                 for (i, f), w in sorted(obs.items()) if rows[i][f] != w]
        last = len(rows) - 1
        entry.update({
            "portRefused": False,
            "mismatches": len(diffs),
            "diffs": diffs,
            "oracleFinalRowOutstandingMinor": obs[(last, "outstanding_principal_minor")],
            "portFinalRowOutstandingMinor": rows[last]["outstanding_principal_minor"],
            "portAmortizesToZero": rows[last]["outstanding_principal_minor"] == 0,
            "oracleAmortizesToZero": obs[(last, "outstanding_principal_minor")] == 0,
        })
        if cid.startswith("P-CAL-"):
            cal_mismatch += len(diffs)
        report.append(entry)

    sweeps = [e for e in report if e["case"].startswith("T83-SW-")]
    diverge = [e for e in sweeps if e.get("mismatches")]
    both_zero = [e for e in sweeps if e.get("oracleAmortizesToZero") and e.get("portAmortizesToZero")]
    oracle_only = [e for e in sweeps if e.get("oracleAmortizesToZero") is False
                   and e.get("portAmortizesToZero") is True]

    # is every divergence confined to the outstanding-principal column?
    off_balance = []
    for e in diverge:
        for d in e.get("diffs", []):
            if d["field"] != "outstanding_principal_minor":
                off_balance.append((e["case"], d))

    summary = {
        "note": "The Go port run on the SAME inputs as the committed T83 capture. No port logic "
                "was changed; the program was compiled into a scratch copy of the tree.",
        "portSource": ".softhouse/capture/t83-nonamortizing/src/t83port.go.txt",
        "captureRef": ".softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json",
        "calibrationMismatchCells": cal_mismatch,
        "calibrationNote": "cells on which the port disagrees with the ALREADY-PROMOTED parity "
                           "vectors T64-ZP-A / T64-ZP-B. If this is not 0, nothing measured on "
                           "novel ground means anything.",
        "sweepCases": len(sweeps),
        "sweepCasesWithAnyMismatch": len(diverge),
        "sweepCasesWhereBothAmortize": len(both_zero),
        "sweepCasesWhereOnlyThePortAmortizes": len(oracle_only),
        "portRefusedAny": [e["case"] for e in report if e.get("portRefused")],
        "everyDivergenceConfinedToOutstandingColumn": not off_balance,
        "divergencesOutsideOutstandingColumn": off_balance[:20],
        "cases": report,
    }
    outp = os.path.join(OUTDIR, "port-vs-oracle.json")
    with open(outp, "w") as f:
        json.dump(summary, f, indent=1)
        f.write("\n")

    print("calibration mismatch cells (must be 0): %d" % cal_mismatch)
    print("sweep cases: %d; with any cell mismatch: %d" % (len(sweeps), len(diverge)))
    print("cases where the ORACLE does not amortize but the PORT does: %d" % len(oracle_only))
    print("every divergence confined to the outstanding-principal column: %s"
          % summary["everyDivergenceConfinedToOutstandingColumn"])
    print("port refused: %r" % summary["portRefusedAny"])
    print("wrote %s" % outp)
    return 0 if cal_mismatch == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
