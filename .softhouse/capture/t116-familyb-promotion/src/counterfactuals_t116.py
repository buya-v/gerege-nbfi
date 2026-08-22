#!/usr/bin/env python3
"""T116 — measure named wrong implementations against what the reference oracle OBSERVED, on the
three cells T116 intends to promote. This produces the OTHER half of a `graded_against` claim: the
value a named wrong implementation emits, and therefore the margin.

Derived from the committed .softhouse/capture/t64-zeroprincipal/src/run-counterfactuals.py. That
file is IMPORTED for its mutation set and otherwise not touched (T114's ruling: do not edit a script
that produced committed evidence). T64's six mutations are imported UNCHANGED, and T116 adds exactly
one of its own, in its own file, T116-mutations.py: G8-FINAL-ROW-SETTLES-THE-BALANCE, the reading the
port's own doc comment at emi.go:1832-1842 names as undetectable by the corpus.

THE CONTROL IS THE LOAD-BEARING PART. `baselineMismatches` is the number of graded money cells on
which the UNMUTATED port disagrees with T116's own capture. A counterfactual model whose unmutated
form did not reproduce the oracle would be measuring its own defect and calling it a margin. On the
two family-B cells the control is ALSO the claim under test — "the Go port reproduces family B cell
for cell" — so a non-zero control here is a finding, not a rig failure, and the script says so.

Mutations are applied to scratch copies under /tmp, never to the committed tree.

"The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product in
this program; nothing here opens a connection of any kind. Money is int64 minor units and there is
no floating point in this file.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAP = os.path.join(ROOT, ".softhouse/capture/t116-familyb-promotion/out/capture-t116-raw.json")
OUTDIR = os.path.join(ROOT, ".softhouse/capture/t116-familyb-promotion/out")
T64SRC = os.path.join(ROOT, ".softhouse/capture/t64-zeroprincipal/src")
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"
CASES = ("T116-CLEAN-R600p0-N103-B1", "T116-FAMB-R600p0-N104-B1", "T116-FAMB-R600p0-N108-B1")

def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


# T64's set, imported unchanged, plus T116's one region-specific mutation. The two sets are kept in
# separate files: T64's produced committed evidence and is not edited (T114's ruling).
t64mut = _load("t64mut", os.path.join(T64SRC, "T64-mutations.py"))
t116mut = _load("t116mut", os.path.join(HERE, "T116-mutations.py"))
ALL_MUTATIONS = list(t64mut.MUTATIONS) + list(t116mut.MUTATIONS)
BY_ID = dict(t64mut.BY_ID)
BY_ID.update(t116mut.BY_ID)
assert len(BY_ID) == len(ALL_MUTATIONS), "mutation id collision between the two sets"


def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e


def minor(text):
    """Exact major-unit decimal text -> int64 minor units. No float, ever."""
    text = str(text)
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        sys.exit("OVER-SCALED wire text %r -- a significant digit beyond the currency scale is a "
                 "finding, never a rounding opportunity" % text)
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac)
    return -v if neg else v


def build_and_run(tag, mid):
    scratch = "/tmp/t116cf-" + tag
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    d = os.path.join(scratch, "nexus", "cmd", "t116cf")
    os.makedirs(d)
    shutil.copy(os.path.join(HERE, "t116cf.go.txt"), os.path.join(d, "main.go"))
    if mid:
        _, _, patches, _ = BY_ID[mid]
        for path, old, new in patches:
            rel = os.path.relpath(path, os.path.join(ROOT, "nexus"))
            tgt = os.path.join(scratch, "nexus", rel)
            src = open(tgt).read()
            if src.count(old) != 1:
                sys.exit("ANCHOR MISS applying %s to %s (%d occurrences)" % (mid, rel, src.count(old)))
            open(tgt, "w").write(src.replace(old, new))
    p = subprocess.run(["go", "run", "./cmd/t116cf"], cwd=os.path.join(scratch, "nexus"),
                       env=env(), capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("%s run failed:\n%s" % (tag, p.stderr[:3000]))
    shutil.rmtree(scratch, ignore_errors=True)
    return {r["case"]: r["rows"] for r in json.loads(p.stdout)}


def observed_cells(cap):
    """The graded MONEY cells of a capture case, as (row_index, field) -> integer minor units."""
    cells = {}
    for i, p in enumerate(cap["observed"]["periods"]):
        cells[(i, "principal_minor")] = minor(p["principal"])
        if p.get("interest") is not None:
            cells[(i, "interest_minor")] = minor(p["interest"])
        if p.get("balance") is not None:
            cells[(i, "outstanding_principal_minor")] = minor(p["balance"])
    return cells


def main():
    with open(CAP) as fh:
        caps = {c["id"]: c for c in json.load(fh)["captures"]}
    base = build_and_run("base", None)
    muts = {m[0]: build_and_run(m[0].lower(), m[0]) for m in ALL_MUTATIONS}

    report, total_base = [], 0
    for cid in CASES:
        obs = observed_cells(caps[cid])
        b = base[cid]
        if len(b) != len(caps[cid]["observed"]["periods"]):
            sys.exit("%s: port row count %d vs observed %d"
                     % (cid, len(b), len(caps[cid]["observed"]["periods"])))
        baseline = [{"row": i, "field": f, "observed": w, "value": b[i][f]}
                    for (i, f), w in sorted(obs.items()) if b[i][f] != w]
        total_base += len(baseline)

        divergent, ndiv, maxm, names, widest = {}, {}, {}, {}, {}
        for mid, m in muts.items():
            rows = m[cid]
            d = []
            if len(rows) != len(b):
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
            widest[mid] = max(d, key=lambda x: x["delta"]) if d else None
            names[mid] = BY_ID[mid][1]

        report.append({
            "case": cid,
            "captureRef": ".softhouse/capture/t116-familyb-promotion/out/capture-t116-raw.json",
            "cells": len(obs),
            "rows": len(b),
            "baselineMismatches": len(baseline),
            "baselineMismatchDetail": baseline,
            "mutationNames": names,
            "nDivergentCells": ndiv,
            "maxMargin": maxm,
            "widestCell": widest,
            "divergent": divergent,
        })

    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, "counterfactuals-t116.json")
    with open(path, "w") as fh:
        fh.write(json.dumps(report, indent=1) + "\n")

    print("wrote %s" % os.path.relpath(path, ROOT))
    print("%d cases, %d graded money cells, baselineMismatches %d"
          % (len(report), sum(r["cells"] for r in report), total_base))
    for r in report:
        print("  %-30s rows %-4d money cells %-5d baselineMismatches %d"
              % (r["case"], r["rows"], r["cells"], r["baselineMismatches"]))
        for mid in sorted(r["nDivergentCells"]):
            w = r["widestCell"][mid]
            print("      %-34s %5d divergent, max margin %d minor%s"
                  % (mid, r["nDivergentCells"][mid], r["maxMargin"][mid],
                     ("  [widest row %s %s: observed %s, counterfactual %s]"
                      % (w["row"], w["field"], w["observed"], w["value"])) if w else ""))
    if total_base:
        sys.exit("CONTROL FAILED: the UNMUTATED port disagrees with the oracle on %d cells. "
                 "Nothing this report calls a margin may be believed -- and on the family-B cells "
                 "this is also a REFUTATION of 'the port reproduces family B cell for cell'."
                 % total_base)


if __name__ == "__main__":
    main()
