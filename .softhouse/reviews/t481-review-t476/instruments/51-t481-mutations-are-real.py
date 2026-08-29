#!/usr/bin/env python3
"""T481 -- PROVE THE THREE MUTATIONS OF 50-t481-control-can-fail.sh ARE NOT NO-OPS.

50-... reports that mutations M2 and M3 leave the SUPERSET CONTROL GREEN. A green control on
a mutation that never applied is not a finding, it is a broken instrument -- this lineage has
already recorded one drive that reported an INVERTED finding because its mutation silently
failed to apply (T476's own PYANCHOR defect). So the mutations are re-applied here IN MEMORY
and the arm's BEHAVIOUR is measured before and after: a mutation that does not change what
`emitter_payloads` returns is REFUSED, not reported.

  python3 51-t481-mutations-are-real.py <repo> <ref-T476>

EXIT 0  all three mutations demonstrably change the arm.
EXIT 3  REFUSED: one of them is a no-op, and 50-...'s numbers for it mean nothing.
"""
import ast
import subprocess
import sys

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"

EDITS = {
    "M1": ("    out = list(emitter_payloads(text))\n",
           "    out = []\n"),
    "M2": ("    out = []\n    for i, line in enumerate(text.split(\"\\n\"), 1):\n",
           "    out = []\n    for i, line in enumerate([], 1):\n"),
    "M3": ("        if stripped.startswith(\"echo \") or stripped.startswith(\"echo\\t\") \\\n"
           "                or stripped.startswith(\"print(\"):\n",
           "        if stripped.startswith(\"echo \"):\n"),
}
WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "printed_payloads", "tagged_blocks", "grade_binding")


def ns_from(src, tag):
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
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), tag, "exec"), ns)
    return ns


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
    base = ns_from(src, "<base>")
    probe = ('  echo "a claim"  # t\n'
             '  echo\ta second one\n'
             'print("a third")  # t\n'
             '  printf "not this one"\n')
    b_arm = base["emitter_payloads"](probe)
    print("  BASE  emitter_payloads sees %d payload(s): %s"
          % (len(b_arm), [x[0] for x in b_arm]))
    if len(b_arm) != 3:
        sys.stderr.write("REFUSED: the base arm does not see the three probe lines; the "
                         "probe, not the mutation, is what would be measured.\n")
        return 3
    ok = True
    for m in ("M1", "M2", "M3"):
        old, new = EDITS[m]
        if old not in src:
            print("  %s  REFUSED: anchor absent" % m)
            ok = False
            continue
        mut = ns_from(src.replace(old, new, 1), "<%s>" % m)
        m_arm = mut["emitter_payloads"](probe)
        # M1 does not touch the arm itself; it removes the SEEDING. Measure the union there.
        if m == "M1":
            # THE PROBE MUST BE A .py THAT PARSES. On SHELL text the lexical arm reproduces
            # ARM 1's payloads byte for byte, so unwiring ARM 1 changes the union by NOTHING
            # there -- measured, and it is the same fact that makes the shell half of the
            # SUPERSET CONTROL unable to fail. Using a .sh probe here would have reported M1
            # as a no-op when it is not one.
            pyprobe = 'print("a claim")  # t\nx = 1\n'
            base_u = set(base["printed_payloads"](pyprobe, "fixture.py"))
            mut_u = set(mut["printed_payloads"](pyprobe, "fixture.py"))
            sh_b = set(base["printed_payloads"](probe, "fixture.sh"))
            sh_m = set(mut["printed_payloads"](probe, "fixture.sh"))
            changed = base_u != mut_u
            print("  M1    union payloads on a .py  %d -> %d   CHANGED: %s"
                  % (len(base_u), len(mut_u), changed))
            print("        union payloads on a .sh  %d -> %d   CHANGED: %s"
                  " <- the shell arm already reproduces ARM 1 exactly"
                  % (len(sh_b), len(sh_m), sh_b != sh_m))
        else:
            changed = [x[0] for x in m_arm] != [x[0] for x in b_arm]
            print("  %s    arm sees %d payload(s): %s   CHANGED: %s"
                  % (m, len(m_arm), [x[0] for x in m_arm], changed))
        if not changed:
            print("        REFUSED: %s is a NO-OP; any verdict reported for it is void." % m)
            ok = False
    print()
    if not ok:
        print("RESULT: at least one mutation is a no-op. REFUSED.")
        return 3
    print("RESULT: all three mutations demonstrably change the arm or the union. EXIT 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
