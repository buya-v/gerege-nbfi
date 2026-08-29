#!/usr/bin/env python3
"""T481 -- THE FALLBACK CATCHES SyntaxError AND ValueError. IS THAT THE WHOLE SET?

T476 closed one member of this class: `ast.parse` raises ValueError, not SyntaxError, on a
NUL byte, so a guarded .py containing one used to take the grader down by traceback. T472
reasoned it; T476 drove it and widened the except clause to `(SyntaxError, ValueError)`.

The question this file asks is the next one, and nobody in the lineage has asked it: is
`(SyntaxError, ValueError)` the complete set of things `ast.parse` raises on input a guarded
.py could contain? A grader that crashes on a corpus member has not graded it, and this is
the SAME defect one file over -- twice now.

The probes are inputs, not theories. Each is fed to the SHIPPED `printed_payloads` through
`grade_binding`, exactly as the live arm feeds it, and what escapes is reported by type.

  python3 80-t481-fallback-exhaustive.py <repo> <ref>

EXIT 0  measured. EXIT 1  something escaped the fallback. EXIT 3  REFUSED.
"""
import ast
import inspect
import subprocess
import sys

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"
WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "printed_payloads", "tagged_blocks", "grade_binding")


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("REFUSED: usage: <repo> <ref>\n")
        return 3
    repo, ref = sys.argv[1:3]
    p = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, GRADER)],
                       capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: could not read the grader\n")
        return 3
    src = p.stdout.decode("utf-8", "replace")
    tree, pieces = ast.parse(src), []
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in WANT:
            pieces.append(ast.get_source_segment(src, node))
    ns = {}
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<ref>", "exec"), ns)
    gb = ns["grade_binding"]
    n = len(inspect.signature(gb).parameters)
    grade = (lambda t, r: gb(t)) if n == 1 else (lambda t, r: gb(t, r))

    claim = "There is no " + ns["FALSE_CLAIMS"][3] + "."
    probes = [
        ("P1  a NUL byte (the one T476 closed)", 'print("%s")\nx = "\x00"\n' % claim),
        ("P2  a lone surrogate", 'print("%s")\nx = "\ud800"\n' % claim),
        ("P3  a stray form feed inside an identifier position", 'print("%s")\n\x0cx = 1\n' % claim),
        ("P4  200 nested parentheses", 'print("%s")\nx = ' % claim + "(" * 200 + "1" + ")" * 200 + "\n"),
        ("P5  2000 nested parentheses", 'print("%s")\nx = ' % claim + "(" * 2000 + "1" + ")" * 2000 + "\n"),
        ("P6  2000 nested list displays", 'print("%s")\nx = ' % claim + "[" * 2000 + "]" * 2000 + "\n"),
        ("P7  a 5000-deep chain of unary minus", 'print("%s")\nx = ' % claim + "-" * 5000 + "1\n"),
        ("P8  plain unparseable text (the SyntaxError baseline)", 'print("%s")\nthis is ( not python\n' % claim),
        ("P9  a lone BOM then valid code", '﻿print("%s")\n' % claim),
        ("P10 a null in a comment", 'print("%s")  # \x00\n' % claim),
    ]
    bad = []
    print("  ref: %s" % ref)
    print("  %-52s %-22s %s" % ("probe", "ast.parse raises", "grade_binding"))
    for label, text in probes:
        try:
            ast.parse(text)
            praise = "-"
        except BaseException as exc:
            praise = type(exc).__name__
        try:
            u, q, pr = grade(text, "fixture.py")
            got = "graded (P2 fires: %s)" % bool(pr)
        except BaseException as exc:
            got = "ESCAPED: " + type(exc).__name__
            bad.append((label, type(exc).__name__))
        print("  %-52s %-22s %s" % (label[:52], praise, got))
    print()
    if bad:
        print("  A GRADER THAT CRASHES ON A CORPUS MEMBER HAS NOT GRADED IT. Escapes:")
        for label, exc in bad:
            print("    %s  ->  %s" % (label, exc))
        print("  This is the F-T464-2 shape: fail-CRASH, not fail-closed, at the file level.")
        print("  It fails closed at the RUNNER (a traceback is a section-10 move and")
        print("  run-all.sh FAILs), which is why the severity is bounded -- but the")
        print("  except clause `(SyntaxError, ValueError)` is stated as the complete set")
        print("  and it is not.")
        return 1
    print("  Nothing escaped the fallback on these probes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
