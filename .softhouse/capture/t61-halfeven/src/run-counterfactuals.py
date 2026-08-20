#!/usr/bin/env python3
"""Measure the M7 counterfactual against what the reference oracle OBSERVED.

This directory contains NO oracle observation. Every observed number used here is
read from `.softhouse/capture/out/capture-prod3f-raw.json`. What this produces is
the *other* half of a `graded_against` claim: the value a named wrong
implementation emits, and therefore the margin.

THE CONTROL IS THE LOAD-BEARING PART (T58's precedent). The report carries
`baselineMismatches` -- the number of graded money cells on which the UNMUTATED
port disagrees with the capture's observed value. A counterfactual model whose
unmutated form did not reproduce the oracle would be measuring its own defect and
calling it a margin.

Mutations are applied to scratch copies under /tmp, never to the committed tree.

    python3 .softhouse/capture/t61-halfeven/src/run-counterfactuals.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program; nothing here opens a connection of any kind.
Money is int64 minor units and there is no floating point in this file.
"""
import importlib.util, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAP = os.path.join(ROOT, ".softhouse/capture/out/capture-prod3f-raw.json")
OUTDIR = os.path.join(ROOT, ".softhouse/capture/t61-halfeven/out")
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"
MUT = "M7"

spec = importlib.util.spec_from_file_location(
    "t61mut", os.path.join(ROOT, ".softhouse/handoff/T61-mutations.py"))
t61mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t61mut)


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


def build_and_run(tag, mutate):
    scratch = "/tmp/t61cf-" + tag
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    d = os.path.join(scratch, "nexus", "cmd", "t61cf")
    os.makedirs(d)
    shutil.copy(os.path.join(HERE, "t61cf.go.txt"), os.path.join(d, "main.go"))
    if mutate:
        _, _, patches, _ = t61mut.BY_ID[MUT]
        for path, old, new in patches:
            rel = os.path.relpath(path, os.path.join(ROOT, "nexus"))
            tgt = os.path.join(scratch, "nexus", rel)
            src = open(tgt).read()
            if src.count(old) != 1:
                sys.exit("ANCHOR MISS applying %s to %s" % (MUT, rel))
            open(tgt, "w").write(src.replace(old, new))
    p = subprocess.run(["go", "run", "./cmd/t61cf"], cwd=os.path.join(scratch, "nexus"),
                       env=env(), capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("%s run failed:\n%s" % (tag, p.stderr[:3000]))
    shutil.rmtree(scratch, ignore_errors=True)
    return {r["case"]: r["rows"] for r in json.loads(p.stdout)}


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


FIELD_OF = {"principal_minor": "Principal", "interest_minor": "Interest",
            "outstanding_principal_minor": "Outstanding"}
GO_KEY = {"principal_minor": "principal_minor", "interest_minor": "interest_minor",
          "outstanding_principal_minor": "outstanding_principal_minor"}


def main():
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
    base = build_and_run("base", False)
    mut = build_and_run(MUT.lower(), True)

    report = []
    for cid in ("T61-HE-A", "T61-HE-B", "T61-HE-C"):
        obs = observed_cells(caps[cid])
        b, m = base[cid], mut[cid]
        if len(b) != len(caps[cid]["observed"]["periods"]):
            sys.exit("%s: row count %d vs observed %d"
                     % (cid, len(b), len(caps[cid]["observed"]["periods"])))
        baseline_mismatches, divergent = [], []
        for (i, field), want in sorted(obs.items()):
            got_base = b[i][GO_KEY[field]]
            got_mut = m[i][GO_KEY[field]]
            if got_base != want:
                baseline_mismatches.append(
                    {"row": i, "field": field, "observed": want, "value": got_base})
            if got_mut != want:
                divergent.append({"row": i, "field": field, "observed": want,
                                  "value": got_mut, "delta": abs(want - got_mut)})
        date_divergent = []
        for i in range(len(b)):
            for k in ("from_date", "due_date"):
                if b[i][k] != m[i][k]:
                    date_divergent.append("period[%d].%s observed %s, counterfactual %s"
                                          % (i, k, b[i][k], m[i][k]))
        report.append({
            "case": cid,
            "captureRef": ".softhouse/capture/out/capture-prod3f-raw.json",
            "cells": len(obs),
            "baselineMismatches": len(baseline_mismatches),
            "baselineMismatchDetail": baseline_mismatches,
            "mutation": MUT,
            "mutationName": t61mut.BY_ID[MUT][1],
            "nDivergentCells": {MUT: len(divergent)},
            "maxMargin": {MUT: max([d["delta"] for d in divergent], default=0)},
            "divergent": {MUT: divergent},
            "dateDivergent": {MUT: date_divergent},
        })

    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, "t61-counterfactuals-pass3f.json")
    open(path, "w").write(json.dumps(report, indent=2) + "\n")

    total_cells = sum(r["cells"] for r in report)
    total_base = sum(r["baselineMismatches"] for r in report)
    print("wrote %s" % os.path.relpath(path, ROOT))
    print("%d cases, %d graded money cells, baselineMismatches %d"
          % (len(report), total_cells, total_base))
    for r in report:
        print("  %-10s cells %-4d %s: %d divergent, max margin %d minor"
              % (r["case"], r["cells"], MUT, r["nDivergentCells"][MUT], r["maxMargin"][MUT]))
    if total_base:
        sys.exit("CONTROL FAILED: the UNMUTATED port disagrees with the oracle on %d cells. "
                 "Nothing this report calls a margin may be believed." % total_base)


if __name__ == "__main__":
    main()
