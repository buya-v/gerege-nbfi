#!/usr/bin/env python3
"""Measure the T64 counterfactuals against what the reference oracle OBSERVED.

This directory contains NO oracle observation. Every observed number used here is
read from `.softhouse/capture/out/capture-prod3g-raw.json`. What this produces is
the *other* half of a `graded_against` claim: the value a named wrong
implementation emits, and therefore the margin.

THE CONTROL IS THE LOAD-BEARING PART (T58's precedent, reused by T61). The report
carries `baselineMismatches` -- the number of graded money cells on which the
UNMUTATED port disagrees with the capture's observed value. A counterfactual model
whose unmutated form did not reproduce the oracle would be measuring its own
defect and calling it a margin.

Mutations are applied to scratch copies under /tmp, never to the committed tree.

    python3 .softhouse/capture/t64-zeroprincipal/src/run-counterfactuals.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program; nothing here opens a connection of any kind.
Money is int64 minor units and there is no floating point in this file.
"""
import importlib.util, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAP = os.path.join(ROOT, ".softhouse/capture/out/capture-prod3g-raw.json")
OUTDIR = os.path.join(ROOT, ".softhouse/capture/t64-zeroprincipal/out")
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"
CASES = ("T64-ZP-A", "T64-ZP-B", "T64-ZP-C", "T64-ZP-D")

spec = importlib.util.spec_from_file_location("t64mut", os.path.join(HERE, "T64-mutations.py"))
t64mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t64mut)


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


def build_and_run(tag, mid):
    scratch = "/tmp/t64cf-" + tag
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    d = os.path.join(scratch, "nexus", "cmd", "t64cf")
    os.makedirs(d)
    shutil.copy(os.path.join(HERE, "t64cf.go.txt"), os.path.join(d, "main.go"))
    if mid:
        _, _, patches, _ = t64mut.BY_ID[mid]
        for path, old, new in patches:
            rel = os.path.relpath(path, os.path.join(ROOT, "nexus"))
            tgt = os.path.join(scratch, "nexus", rel)
            src = open(tgt).read()
            if src.count(old) != 1:
                sys.exit("ANCHOR MISS applying %s to %s (%d occurrences)"
                         % (mid, rel, src.count(old)))
            open(tgt, "w").write(src.replace(old, new))
    p = subprocess.run(["go", "run", "./cmd/t64cf"], cwd=os.path.join(scratch, "nexus"),
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


def main():
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
    base = build_and_run("base", None)
    muts = {m[0]: build_and_run(m[0].lower(), m[0]) for m in t64mut.MUTATIONS}

    report, total_base = [], 0
    for cid in CASES:
        obs = observed_cells(caps[cid])
        b = base[cid]
        if len(b) != len(caps[cid]["observed"]["periods"]):
            sys.exit("%s: row count %d vs observed %d"
                     % (cid, len(b), len(caps[cid]["observed"]["periods"])))
        baseline = [{"row": i, "field": f, "observed": w, "value": b[i][f]}
                    for (i, f), w in sorted(obs.items()) if b[i][f] != w]
        total_base += len(baseline)

        divergent, ndiv, maxm, names = {}, {}, {}, {}
        for mid, m in muts.items():
            rows = m[cid]
            d = []
            if len(rows) != len(b):
                # a row-count change is itself a divergence, and a large one
                d.append({"row": -1, "field": "row_count", "observed": len(b),
                          "value": len(rows), "delta": abs(len(b) - len(rows))})
            else:
                for (i, f), w in sorted(obs.items()):
                    if rows[i][f] != w:
                        d.append({"row": i, "field": f, "observed": w, "value": rows[i][f],
                                  "delta": abs(w - rows[i][f])})
            divergent[mid] = d
            ndiv[mid] = len(d)
            maxm[mid] = max([x["delta"] for x in d], default=0)
            names[mid] = t64mut.BY_ID[mid][1]

        report.append({
            "case": cid,
            "captureRef": ".softhouse/capture/out/capture-prod3g-raw.json",
            "cells": len(obs),
            "baselineMismatches": len(baseline),
            "baselineMismatchDetail": baseline,
            "mutationNames": names,
            "nDivergentCells": ndiv,
            "maxMargin": maxm,
            "divergent": divergent,
        })

    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, "t64-counterfactuals-pass3g.json")
    open(path, "w").write(json.dumps(report, indent=2) + "\n")

    print("wrote %s" % os.path.relpath(path, ROOT))
    print("%d cases, %d graded money cells, baselineMismatches %d"
          % (len(report), sum(r["cells"] for r in report), total_base))
    for r in report:
        print("  %-10s cells %-5d" % (r["case"], r["cells"]))
        for mid in sorted(r["nDivergentCells"]):
            print("      %-34s %4d divergent, max margin %d minor"
                  % (mid, r["nDivergentCells"][mid], r["maxMargin"][mid]))
    if total_base:
        sys.exit("CONTROL FAILED: the UNMUTATED port disagrees with the oracle on %d cells. "
                 "Nothing this report calls a margin may be believed." % total_base)


if __name__ == "__main__":
    main()
