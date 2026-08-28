#!/usr/bin/env python3
"""T145 -- PER-SITE CLASSIFICATION of every unguarded json.load against T207's ruling.

T207 held that a float-derived predicate MAY gate on the oracle-facing wire, response leg,
because the non-negotiable bans a float from CARRYING A VALUE, not from BEING MEASURED. So
"add parse_float everywhere" is the wrong instrument. This classifies each site by what the
loaded object is actually DONE WITH, using the AST, and reports the population per class.

The classes were not chosen a priori: two of them were DISCOVERED by the differential sweep,
where the blanket repair broke a script rather than fixing it.

  C1 ROUNDTRIP-WRITER   the same module also json.dump()s. Converting to Decimal makes
                        json.dump raise TypeError and can leave a TRUNCATED artefact on
                        disk -- MEASURED, not predicted, at pathb/t22-probe/mkreq.py and
                        mkcalc.py, which wrote a half-finished request body. For a REQUEST
                        body this is also exactly what T186 rule A1 protects by other means
                        (repr(float(tok)) == tok, live at conformance.sh:997).
                        VERDICT: PERMITTED. DO NOT CONVERT.

  C2 FLOAT-DETECTOR     the module tests isinstance(x, float) / (int, float) / type is float.
                        The unguarded load IS the instrument: reading without parse_float is
                        the only way to learn which tokens were bare JSON numbers. Converting
                        makes the detector structurally unable to fire -- P-22. MEASURED at
                        charges/bin/t48-analyse.py, whose leaf population fell 218 -> 80 and
                        whose zero-bare-numbers guard went silent while still exiting 0.
                        VERDICT: PERMITTED, AND CONVERTING IT IS A REGRESSION.

  C3 CARRIES-VALUE      an arithmetic operator, sum(), round(), abs(), min/max or a float()
                        cast is applied somewhere in the module AND the module reads a file
                        from the money-float hazard set. This is the class the non-negotiable
                        actually names. VERDICT: THE REAL FIX.

  C4 STRUCTURAL         none of the above: the module only indexes, counts, prints or
                        string-compares. parse_float would be inert. VERDICT: CHURN.

A module can fall in more than one class; the report gives both the per-class file counts
and the disjoint priority assignment C3 > C2 > C1 > C4, and says which it is using.
"""
import ast
import json
import os
import subprocess
import sys

ARITH = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
ARITH_FUNCS = {"sum", "round", "abs", "min", "max", "fsum", "mean", "median"}


class Scan(ast.NodeVisitor):
    def __init__(self):
        self.dump = False
        self.detector = []
        self.arith = []
        self.floatcast = []

    def visit_Call(self, n):
        f = n.func
        if isinstance(f, ast.Attribute) and f.attr in ("dump", "dumps"):
            v = f.value
            if isinstance(v, ast.Name) and v.id in ("json", "simplejson"):
                self.dump = True
        if isinstance(f, ast.Name):
            if f.id == "float":
                self.floatcast.append(n.lineno)
            if f.id in ARITH_FUNCS:
                self.arith.append(n.lineno)
            if f.id == "isinstance" and len(n.args) == 2:
                if "float" in ast.dump(n.args[1]):
                    self.detector.append(n.lineno)
        self.generic_visit(n)

    def visit_BinOp(self, n):
        if isinstance(n.op, ARITH):
            self.arith.append(n.lineno)
        self.generic_visit(n)

    def visit_Compare(self, n):
        # `type(x) is float`
        if "float" in ast.dump(n):
            for c in n.comparators:
                if isinstance(c, ast.Name) and c.id == "float":
                    self.detector.append(n.lineno)
        self.generic_visit(n)


def money_float_files(root):
    """Files from the corpus census that carry a bare JSON float under a money-ish key."""
    p = os.path.join(root, ".softhouse/capture/t145-analysis-float/out/corpus-float-census.txt")
    names = set()
    take = False
    for line in open(p, encoding="utf-8", errors="replace"):
        if line.startswith("==== THE HAZARD SET"):
            take = True
            continue
        if line.startswith("==== float-bearing but NOT"):
            break
        if take and line.startswith("  .softhouse/"):
            names.add(os.path.basename(line.split("   (")[0].strip()))
    return names


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    here = os.path.dirname(os.path.abspath(__file__))
    census = json.load(open(os.path.join(here, "..", "out", "census.json")))
    unguarded = [h for h in census["hits"] if not h["guarded"]]
    files = sorted({h["file"] for h in unguarded})
    hazard_basenames = money_float_files(root)
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True).stdout.strip()

    print("SELECTOR (sites)   : out/census.json, hits with guarded=false")
    print("SELECTOR (classes) : ast walk of the WHOLE module -- json.dump present (C1);")
    print("                     isinstance(_, float)/(int,float) or `is float` (C2);")
    print("                     a BinOp arithmetic op / sum,round,abs,min,max / float()")
    print("                     cast AND a filename literal in the money-float hazard set (C3)")
    print("SELECTOR (hazard)  : basenames from out/corpus-float-census.txt HAZARD SET")
    print("REV: %s" % rev)
    print("UNGUARDED SITES: %d in %d files" % (len(unguarded), len(files)))
    print()

    rows = []
    for rel in files:
        src = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        s = Scan()
        s.visit(ast.parse(src))
        # does this module name a hazard-set file, or glob into a capture out/ dir?
        touches_hazard = any(b in src for b in hazard_basenames) or \
            (("glob" in src or "iterdir" in src or "listdir" in src) and "out" in src)
        nsites = sum(1 for h in unguarded if h["file"] == rel)
        rows.append({
            "file": rel, "sites": nsites,
            "C1": s.dump,
            "C2": bool(s.detector),
            "C3": bool(s.arith or s.floatcast) and touches_hazard,
            "detector_lines": sorted(set(s.detector)),
            "floatcast_lines": sorted(set(s.floatcast)),
            "hazard": touches_hazard,
        })

    def pri(r):
        return "C3" if r["C3"] else "C2" if r["C2"] else "C1" if r["C1"] else "C4"

    for r in rows:
        r["class"] = pri(r)

    print("==== OVERLAPPING membership (a module can be in several) ====")
    for c, lab in (("C1", "ROUNDTRIP-WRITER  -- DO NOT CONVERT"),
                   ("C2", "FLOAT-DETECTOR    -- CONVERTING IT IS A REGRESSION"),
                   ("C3", "CARRIES-VALUE     -- THE REAL FIX")):
        f = [r for r in rows if r[c]]
        print("  %s %-45s files=%-4d sites=%d"
              % (c, lab, len(f), sum(r["sites"] for r in f)))
    print()
    print("==== DISJOINT assignment, priority C3 > C2 > C1 > C4 ====")
    for c in ("C3", "C2", "C1", "C4"):
        f = [r for r in rows if r["class"] == c]
        print("  %s files=%-4d sites=%d" % (c, len(f), sum(r["sites"] for r in f)))
    print()
    print("==== C3 -- THE CANDIDATE CARRY SET (the only class where parse_float is the fix) ====")
    for r in sorted([r for r in rows if r["class"] == "C3"], key=lambda x: -x["sites"]):
        print("  %-78s sites=%-3d float()@%s"
              % (r["file"], r["sites"], r["floatcast_lines"] or "-"))
    print()
    print("==== C2 -- FLOAT DETECTORS. Converting these SILENCES them (P-22). ====")
    for r in sorted([r for r in rows if r["C2"]], key=lambda x: x["file"]):
        print("  %-78s sites=%-3d isinstance-float@%s"
              % (r["file"], r["sites"], r["detector_lines"]))
    return 0


sys.exit(main())
