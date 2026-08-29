#!/usr/bin/env python3
"""T481 -- THE VACUITY CONTROL'S PUBLISHED CARDINAL, AFTER THE UNION.

The regenerated transcript moves one number that is not a new check:

    VACUITY CONTROL ... emitted tagged quotation lines: 2   ->   8

The check itself is `> 0` and is unaffected. Its printed DETAIL is not: `_emitted_tagged`
increments once per PAYLOAD, and the union offers one source line as several payloads (whole
code text under two comment rules, plus each quoted segment). Commit `0d15e5c7` recognised
exactly this and deduped the reported SITES for `printed_untagged` -- and did not dedupe this
counter, whose label still says "lines".

This file measures both readings on the four guarded files, so the difference is a number and
not an inference.

  python3 95-t481-vacuity-cardinal.py <repo> <ref-T467> <ref-T476>
"""
import ast
import inspect
import subprocess
import sys

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"
CORRECTED = (S + "/reviews/A2-11/verify-capture-integrity.py",
             S + "/reviews/A2-11/run-all.sh",
             S + "/capture/t393-t382-conditions/instruments/10-drive-conditions.sh",
             S + "/capture/t393-t382-conditions/instruments/12-relaunder-manifest.py")
WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "printed_payloads", "tagged_blocks", "grade_binding")


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo] + list(a), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git failed\n")
        sys.exit(3)
    return p.stdout


def lift(repo, ref):
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
    return ns


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("REFUSED: usage: <repo> <ref-T467> <ref-T476>\n")
        return 3
    repo, r467, r476 = sys.argv[1:4]
    for label, ref in (("T467", r467), ("T476", r476)):
        ns = lift(repo, ref)
        pp = ns["printed_payloads"]
        n = len(inspect.signature(pp).parameters)
        TAG = ns["TAG"]
        payloads = lines = 0
        for rel in CORRECTED:
            text = git(repo, "show", "%s:%s" % (ref, rel)).decode("utf-8", "replace")
            seen = set()
            got = pp(text, rel) if n == 2 else pp(text)
            for lineno, pl in got:
                if ns["states_a_false_claim"](pl) and TAG in pl:
                    payloads += 1
                    seen.add((rel, lineno))
            lines += len(seen)
        print("  %-5s  as the file counts it (per PAYLOAD): %d      distinct SOURCE LINES: %d"
              % (label, payloads, lines))
    print()
    print('  The transcript prints the first number under the words "quotation LINES".')
    return 0


if __name__ == "__main__":
    sys.exit(main())
