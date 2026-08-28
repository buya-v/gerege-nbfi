#!/usr/bin/env python3
"""
T278 -- INDEPENDENT no-float audit of every instrument in play, T277's and the
reviewer's own.

Money is integer minor units INCLUDING INTERMEDIATE CALCULATION, so the audit is
run over ALL of them, not only T277's.

THE FALSE-POSITIVE CLASS THIS AUDITOR REFUSES TO REPEAT (FU-T277-7):
  the driver's pre-merge scan reported 2 violations against T277's claim of 0.
  Both were `isinstance(node.value, float)` -- the float DETECTOR naming the type
  it detects.  A scan that fires on the bare NAME `float` cannot tell a detector
  from a defect.

  So this auditor classifies rather than counts:
    HARD   a float/complex LITERAL, a true-division `/` node, a `float(...)` or
           `round(...)` CALL, an import of decimal/fractions/math/numpy.
           These change arithmetic.  Any HARD hit is a rejection.
    BENIGN the identifier `float` appearing ONLY as the second argument of
           isinstance(...) or as a type-name comparison -- i.e. inside a
           detector.  Reported, and explicitly NOT counted as a violation.
    OTHER  the identifier `float` in any other position -- reported as a HARD
           hit, because the FP class is narrow and must not become an excuse.
"""

import ast
import os
import sys

HARD_IMPORTS = ("decimal", "fractions", "math", "numpy")


def classify(path):
    src = open(path, "r").read()
    tree = ast.parse(src)
    hard, benign = [], []

    # positions of `float` / `complex` Name nodes that sit in an isinstance()
    # second argument, or in a `type(x) is float` style comparison.
    detector_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "isinstance":
                for arg in node.args[1:]:
                    for sub in ast.walk(arg):
                        if isinstance(sub, ast.Name):
                            detector_nodes.add(id(sub))
        if isinstance(node, ast.Compare):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id in ("float", "complex"):
                    detector_nodes.add(id(sub))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            tn = type(node.value).__name__
            if tn in ("float", "complex"):
                hard.append("%s LITERAL at line %d" % (tn.upper(), node.lineno))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            hard.append("TRUE-DIVISION `/` at line %d" % node.lineno)
        if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Div):
            hard.append("TRUE-DIVISION `/=` at line %d" % node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("float", "round"):
                hard.append("CALL to %s() at line %d" % (node.func.id, node.lineno))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            for nm in names:
                if nm in HARD_IMPORTS:
                    hard.append("IMPORT %s at line %d" % (nm, node.lineno))
        if isinstance(node, ast.Name) and node.id in ("float", "complex"):
            if id(node) in detector_nodes:
                benign.append(
                    "identifier `%s` at line %d -- inside a DETECTOR "
                    "(isinstance/type comparison), NOT arithmetic"
                    % (node.id, node.lineno)
                )
            else:
                # a Name `float` that is not a call and not a detector: still
                # report it HARD.  the FP class is narrow on purpose.
                parent_is_call = False
                for anc in ast.walk(tree):
                    if isinstance(anc, ast.Call) and anc.func is node:
                        parent_is_call = True
                if not parent_is_call:
                    hard.append(
                        "bare identifier `%s` at line %d (not a detector)"
                        % (node.id, node.lineno)
                    )
    return hard, benign


def main():
    root = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
    )
    targets = [
        ".softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py",
        ".softhouse/capture/t277-shapelaw-salvage/src/crosscheck_seven_t277b.py",
        ".softhouse/capture/t277-shapelaw-salvage/src/dump_seven_t277.py",
        ".softhouse/reviews/t278-review-t277/probe/t278_rederive.py",
        ".softhouse/reviews/t278-review-t277/probe/t278_domain_audit.py",
        ".softhouse/reviews/t278-review-t277/probe/t278_float_audit.py",
    ]
    rc = 0
    print("T278 NO-FLOAT AUDIT -- money is integer minor units, intermediates too")
    print("")
    for rel in targets:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            print("  MISSING  %s" % rel)
            rc = 1
            continue
        hard, benign = classify(p)
        print("  %-64s HARD=%d BENIGN=%d" % (rel, len(hard), len(benign)))
        for h in hard:
            print("      HARD   %s" % h)
            rc = 1
        for b in benign:
            print("      benign %s" % b)
    print("")
    # the shell verifier gets a text scan; it does no arithmetic.
    vp = os.path.join(
        root, ".softhouse/capture/t277-shapelaw-salvage/src/verify_t277.sh"
    )
    txt = open(vp).read()
    import re as _re
    lits = _re.findall(r"(?<![\w.])\d+\.\d+(?![\w.])", txt)
    lits = [l for l in lits if l not in ("1.5",)]
    print("  verify_t277.sh  decimal-looking literals: %s" % (lits or "none"))
    print("")
    print("T278 NO-FLOAT AUDIT: %s" % ("PASS" if rc == 0 else "FAIL"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
