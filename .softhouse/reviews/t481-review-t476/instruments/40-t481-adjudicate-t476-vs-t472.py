#!/usr/bin/env python3
"""T481 -- THE TWO PLACES T476 CONTRADICTS T472, ADJUDICATED ON MY OWN DRIVE.

Both parties drove their claim; neither holds a presumption. These are the two:

  7.1  T476: "f-strings are not a blind family. `ast.walk` descends into JoinedStr, so an
       f-string carrying the claim CONTIGUOUSLY was already caught at T467; T472's A4 is
       blind because {chr(72)} is COMPUTED, i.e. it is the runtime family."
       -> driven here at all three refs, together with the case that separates the two
       explanations: an f-string split by a STATIC interpolation, where nothing is computed
       at runtime and the bytes ARE all in the source. If that case is blind at T467 too,
       then "computed at runtime" is not the whole reason, and the honest statement is
       "SPLIT by an interpolation", of which computed values are one cause.

  7.2  T476: "T467's wrapped-payload mitigation is FALSE, not merely untested -- predicate 1
       does not de-wrap UNTAGGED claims; W2/W3 are invisible to BOTH predicates at T467."
       -> driven here, with the tag in each of the three places that matter.

NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103).

  python3 40-t481-adjudicate-t476-vs-t472.py <repo> <T455> <T467> <T476>
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


def lift(repo, ref):
    p = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, GRADER)],
                       capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: could not read the grader at %s\n" % ref)
        sys.exit(3)
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
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<%s>" % ref, "exec"), ns)
    gb = ns["grade_binding"]
    n = len(inspect.signature(gb).parameters)
    ns["g"] = (lambda t, r: gb(t)) if n == 1 else (lambda t, r: gb(t, r))
    return ns


def main():
    if len(sys.argv) != 5:
        sys.stderr.write("REFUSED: usage: <repo> <T455> <T467> <T476>\n")
        return 3
    repo = sys.argv[1]
    refs = [("T455", sys.argv[2]), ("T467", sys.argv[3]), ("T476", sys.argv[4])]
    ns = {n: lift(repo, r) for n, r in refs}
    TAG, FC = ns["T476"]["TAG"], ns["T476"]["FALSE_CLAIMS"]
    S1 = "There is no " + FC[3] + "."
    W = S1.split()
    H1, H2 = " ".join(W[:5]), " ".join(W[5:])
    GOOD_PY = 'print("  [%s] %s")\n' % (TAG, S1)
    GOOD_SH = '  echo "  [%s] %s"\n' % (TAG, S1)

    def row(label, rel, text, expect_note=""):
        cells = []
        for n, _ in refs:
            try:
                u, q, p = ns[n]["g"](text, rel)
                cells.append(("P1+P2" if (u and p) else "P1" if u else "P2" if p else "clear"))
            except Exception as exc:
                cells.append("RAISE:" + type(exc).__name__)
        print("  %-58s %-7s %-7s %-7s %s"
              % (label[:58], cells[0], cells[1], cells[2], expect_note))
        return cells

    print("=== 7.1  THE F-STRING DISAGREEMENT ===")
    print("  cells report WHICH predicate fires: P1 = binding (an untagged line states the")
    print("  claim), P2 = printed (a payload states it untagged), clear = neither.")
    print()
    print("  %-58s %-7s %-7s %-7s" % ("case", "T455", "T467", "T476"))
    # F1: the claim CONTIGUOUS inside an f-string, tag in a trailing comment.
    row("F1  f-string, claim CONTIGUOUS, tag in trailing comment", "fixture.py",
        GOOD_PY + 'print(f"%s")  # %s\n' % (S1, TAG),
        "<- T476 says T467 already caught this")
    # F2: T472's A4 -- split by a COMPUTED interpolation.
    row("F2  f-string split by a COMPUTED value {chr(72)}", "fixture.py",
        GOOD_PY + 'print(f"There is no %s")  # %s\n'
        % (FC[3].replace("head", "{chr(72)}EAD").replace("HEAD", "{chr(72)}EAD") + ".", TAG),
        "<- T472's A4")
    # F3: THE CASE THAT SEPARATES THE TWO EXPLANATIONS -- split by a STATIC interpolation.
    # MY FIRST DRAFT WROTE `.replace("HEAD", ...)` AND THE PATTERN TABLE IS LOWERCASE, so the
    # replacement never fired and F3 silently re-tested F1 -- it reported a number for a case
    # it was not running. Repaired here, and the assertion below REFUSES unless the text this
    # case grades actually contains an interpolation.
    _f3 = 'print(f"There is no %s")  # %s\n' % (FC[3].replace("head", "{%r}EAD" % "H") + ".",
                                                TAG)
    if "{'H'}" not in _f3:
        sys.stderr.write("REFUSED: F3 carries no interpolation; it would measure F1.\n")
        return 3
    row("F3  f-string split by a STATIC interpolation {'H'}", "fixture.py",
        GOOD_PY + _f3, "<- nothing computed; bytes all in source")
    # F4: the same claim in a plain str -- the calibration.
    row("F4  the same claim in a plain str (calibration)", "fixture.py",
        GOOD_PY + 'print("%s")  # %s\n' % (S1, TAG), "<- known POSITIVE")
    print()

    print("=== 7.2  T467's WRAPPED-PAYLOAD MITIGATION ===")
    print("  T467 §9: 'a claim WRAPPED across two payloads -- predicate 1 de-wraps contiguous")
    print("  tagged blocks and does see it.' Driven, with the tag in each place that matters.")
    print()
    print("  %-58s %-7s %-7s %-7s" % ("case", "T455", "T467", "T476"))
    row("W1  wrapped over a continuation, tag on BOTH lines", "fixture.sh",
        GOOD_SH + '  echo "%s \\\n  %s"  # %s\n  # %s\n' % (H1, H2, TAG, TAG))
    row("W2  wrapped over a continuation, tag on the SECOND line only", "fixture.sh",
        GOOD_SH + '  echo "%s \\\n  %s"  # %s\n' % (H1, H2, TAG))
    row("W3  wrapped over a continuation, NO tag anywhere", "fixture.sh",
        GOOD_SH + '  echo "%s \\\n  %s"\n' % (H1, H2))
    row("W4  wrapped over two SEPARATE commands, no tag (declared open)", "fixture.sh",
        GOOD_SH + '  echo "%s"\n  echo "%s"\n' % (H1, H2))
    print()
    print("  READ W3: if T467 is 'clear' there, its declared mitigation is FALSE and not")
    print("  merely untested, because the sentence reaches the reader with no tag anywhere")
    print("  in the file and neither predicate says so.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
