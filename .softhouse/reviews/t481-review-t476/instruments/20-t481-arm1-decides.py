#!/usr/bin/env python3
"""T481 -- CAN ARM 1 DECIDE ANYTHING? THE HAND-BUILT ATTACK T476 ASKED FOR.

T476's handoff §2.4 and §11 name this as the thing to attack first:

    "ARM 1 earns zero catches on any matrix I could build -- if the SUPERSET CONTROL can't
     fail for a reason I missed, the guarantee is decoration."

`10-t481-matrix-and-arm1.py` re-derives that over 1,992 generated cases and agrees: ARM 1
decides NONE of them. A generated matrix, however, is still an enumeration -- so this file
stops enumerating and CONSTRUCTS, from the shape of the code, the two families where ARM 1
must differ from the other arms:

  * ARM 1 reads PHYSICAL lines; every other arm reads CONTINUATION-JOINED logical ones. So a
    payload whose CLAIM is complete on the first physical line and whose TAG is on the second
    is untagged to ARM 1 and tagged to everything else.
  * ARM 1 is a LEXICAL rule and it runs over a .py that PARSES. The AST arm marks a docstring
    INERT; ARM 1 does not know what a docstring is. So a `print(`-prefixed line inside a
    docstring is a payload to ARM 1 and to nothing else.

Both are answers to "is ARM 1 load-bearing". Which DIRECTION they point in is the finding.

NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103): the grader path is assembled from S
and the repo and ref are REQUIRED arguments.

  python3 20-t481-arm1-decides.py <repo> <ref-T476> [<ref-T455> <ref-T467>]

EXIT 0  the constructed cases behaved as recorded (whatever that behaviour turns out to be:
        this file RECORDS the verdicts, it does not presuppose them).
EXIT 3  REFUSED: could not measure.
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
        "emitted_payload", "printed_payloads", "tagged_blocks", "grade_binding")


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git failed\n")
        sys.exit(3)
    return p.stdout


def lift(repo, ref, need_arm1=True):
    src = git(repo, "show", "%s:%s" % (ref, GRADER)).decode("utf-8", "replace")
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
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<%s>" % ref, "exec"), ns)
    if need_arm1 and "emitter_payloads" not in ns:
        sys.stderr.write("REFUSED: ARM 1 is not present at %s\n" % ref)
        sys.exit(3)
    return ns


def main():
    if len(sys.argv) not in (3, 5):
        sys.stderr.write("REFUSED: usage: <repo> <ref-T476> [<ref-T455> <ref-T467>]\n")
        return 3
    repo, ref = sys.argv[1:3]
    full = lift(repo, ref)
    noarm = lift(repo, ref)
    noarm["emitter_payloads"] = lambda text: []
    TAG, FC = full["TAG"], full["FALSE_CLAIMS"]
    S1 = "There is no " + FC[3] + "."
    GOOD_SH = '  echo "  [%s] %s"\n' % (TAG, S1)
    GOOD_PY = 'print("  [%s] %s")\n' % (TAG, S1)

    def grade(ns, text, rel):
        u, q, p = ns["grade_binding"](text, rel)
        return bool(p)

    # ---- the constructed cases. Each says what a READER of the output actually sees. ----
    cases = [
        # id, rel, text, what the reader sees, is flagging it CORRECT?
        ("C1  continuation: CLAIM on line 1, TAG printed on line 2", "fixture.sh",
         GOOD_SH + '  echo "%s \\\n  [%s]"\n' % (S1, TAG),
         "the claim AND the tag, on one printed line", False),
        ("C2  continuation: CLAIM on line 1, TAG on line 2, tag ALSO in a trailing comment",
         "fixture.sh",
         GOOD_SH + '  echo "%s \\\n  [%s]"  # %s\n' % (S1, TAG, TAG),
         "the claim AND the tag", False),
        ("C3  continuation: CLAIM on line 1, NOTHING but text on line 2 (a real abuse)",
         "fixture.sh",
         GOOD_SH + '  echo "%s \\\n  and more."  # %s\n' % (S1, TAG),
         "the claim, untagged", True),
        ("D1  a `print(`-prefixed line INSIDE A FUNCTION DOCSTRING", "fixture.py",
         GOOD_PY + 'def _f():\n    """doc\nprint("%s")\n    """\n    return 1\n' % S1,
         "nothing: a docstring is not executed", False),
        ("D2  a `print(`-prefixed line inside a MODULE docstring", "fixture.py",
         '"""doc\nprint("%s")\n"""\n' % S1 + GOOD_PY,
         "nothing: a docstring is not executed", False),
        ("D3  a `print(`-prefixed line inside a docstring, TAGGED in that docstring",
         "fixture.py",
         GOOD_PY + 'def _f():\n    """doc [%s]\nprint("%s")\n    """\n    return 1\n'
         % (TAG, S1),
         "nothing", False),
        ("E1  a real live print of the claim, untagged (the calibration: a KNOWN positive)",
         "fixture.py", GOOD_PY + 'print("%s")  # %s\n' % (S1, TAG),
         "the claim, untagged", True),
        ("E2  a correctly tagged live print (the calibration: a KNOWN negative)",
         "fixture.py", GOOD_PY + 'print("[%s] %s")\n' % (TAG, S1),
         "the claim WITH its tag", False),
    ]
    print("=== ARM 1 UNWIRED vs WIRED, on CONSTRUCTED cases ===")
    print("  ref under test: %s" % ref)
    print()
    print("  %-70s %-8s %-8s %s" % ("case", "WITH", "WITHOUT", "ARM 1 DECIDES IT"))
    decided = []
    for cid, rel, text, sees, should in cases:
        a = grade(full, text, rel)
        b = grade(noarm, text, rel)
        mark = "YES" if a != b else "-"
        if a != b:
            decided.append((cid, a, b, should, sees))
        print("  %-70s %-8s %-8s %s"
              % (cid[:70], "FLAG" if a else "clear", "FLAG" if b else "clear", mark))
    print()
    print("=== WHAT ARM 1 DECIDES, AND IN WHICH DIRECTION ===")
    if not decided:
        print("  ARM 1 decides NONE of the constructed cases either.")
    for cid, a, b, should, sees in decided:
        direction = "A CATCH ARM 1 EARNS" if should else "A FALSE POSITIVE ARM 1 CAUSES"
        print("  %s" % cid)
        print("      the reader of the output sees: %s" % sees)
        print("      flagging it is %s  ->  %s"
              % ("CORRECT" if should else "WRONG", direction))
    print()
    earns = [d for d in decided if d[3]]
    costs = [d for d in decided if not d[3]]
    print("  ARM 1 earns %d catch(es) here and causes %d false positive(s)."
          % (len(earns), len(costs)))
    print()
    print("=== THE CALIBRATION (P-72): this instrument must be able to say both words ===")
    print("  E1, a known POSITIVE, is flagged by the shipped rule: %s"
          % grade(full, cases[6][2], cases[6][1]))
    print("  E2, a known NEGATIVE, is clear under the shipped rule:  %s"
          % (not grade(full, cases[7][2], cases[7][1])))
    if not grade(full, cases[6][2], cases[6][1]) or grade(full, cases[7][2], cases[7][1]):
        print("REFUSED: the instrument itself is not calibrated; its negatives mean nothing.")
        return 3

    # ---- IS ANY OF THIS A REGRESSION? Only measurable against the two earlier refs. ----
    if len(sys.argv) == 5:
        print()
        print("=== THE SAME CASES AT ALL THREE REFS -- is any of it NEW? ===")
        others = [("T455", sys.argv[3]), ("T467", sys.argv[4]), ("T476", ref)]
        ns3 = {}
        for nm, rf in others:
            n = lift(repo, rf, need_arm1=False)
            gb = n["grade_binding"]
            k = len(inspect.signature(gb).parameters)
            n["g"] = (lambda t, r, gb=gb: gb(t)) if k == 1 else (lambda t, r, gb=gb: gb(t, r))
            ns3[nm] = n
        print("  %-58s %-7s %-7s %s" % ("case", "T455", "T467", "T476"))
        for cid, rel, text, sees, should in cases:
            row = []
            for nm, _ in others:
                try:
                    row.append("FLAG" if ns3[nm]["g"](text, rel)[2] else "clear")
                except Exception as exc:
                    row.append("RAISE:" + type(exc).__name__)
            print("  %-58s %-7s %-7s %s" % (cid[:58], row[0], row[1], row[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
