#!/usr/bin/env python3
"""T251 THE LOAD-BEARING CHECK: did any obligation move in H-10?

G-14 requires revision 7 to be an EVIDENTIAL correction. T247 reports that at
L827-830 it separated a fact clause from two obligations welded into the same
sentence and moved only the fact. This re-derives that claim character by
character rather than reading T247's summary of it.

Method:
  1. Assert H-10's `— BEFORE —` block is byte-identical to the live ADR at the
     lines it claims (if it is not, the whole hunk is measured against a text
     that no longer exists).
  2. Reduce BEFORE and AFTER to their NORMATIVE content by deleting the single
     clause T247 says it moved, then compare. Anything that differs after that
     deletion is an obligation that moved and T247 did not declare.
"""
import os
import re
import sys
import difflib

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")
LINES = open(ADR, encoding="utf-8").read().split("\n")

BEFORE = "\n".join(LINES[827 - 1:830])

# H-10's AFTER, transcribed verbatim from REVISION-7-PROPOSED.md L668-676.
AFTER = """**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context. **Revisions 1–6 added "and grades none of them today"; REVISION 7 CORRECTS
THAT CLAUSE AND ONLY THAT CLAUSE — it grades I-1 and I-2, on four vectors, and grades I-3, I-4 and
I-5 by nothing** [MEASURED by `T247` at `9b6c596`]. **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope — **unchanged by revision 7, and unchanged BY the six vectors**: a vector is a
snapshot of oracle output and cannot observe the absence of a write, so no growth of this corpus
will ever discharge them."""

# The two obligations T247 declares UNTOUCHED.
OBLIGATIONS = [
    "DEC-2 **obliges** I-1 through I-5 on any implementation of the\nGL/accounting context",
    "**I-3 and I-4 must be enforced by a\nharness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement\nrather than a hope",
]


def norm(s):
    """Collapse whitespace so a re-wrap is not mistaken for an edit."""
    return re.sub(r"\s+", " ", s).strip()


def main():
    print("COMMIT:", os.popen("git -C %s rev-parse HEAD" % ROOT).read().strip())
    print("\n=== 1. Is H-10's BEFORE byte-identical to the live ADR L827-830? ===")
    quoted = """**The rule this table encodes:** DEC-2 **obliges** I-1 through I-5 on any implementation of the
GL/accounting context, and **grades none of them today.** **I-3 and I-4 must be enforced by a
harness-level source guard, not by a vector**, and DEC-2 states that as a normative requirement
rather than a hope."""
    if quoted == BEFORE:
        print("  YES — byte-identical (%d chars)." % len(BEFORE))
    else:
        print("  NO — H-10 is measured against text that is not there:")
        for d in difflib.unified_diff(BEFORE.split("\n"), quoted.split("\n"),
                                      "live ADR", "H-10 BEFORE", lineterm=""):
            print("   ", d)
        return 1

    print("\n=== 2. Are both declared obligations present, verbatim, in BOTH? ===")
    ok = True
    for i, ob in enumerate(OBLIGATIONS, 1):
        b = norm(ob) in norm(BEFORE)
        a = norm(ob) in norm(AFTER)
        print("  obligation %d: BEFORE=%-5s AFTER=%-5s  %r" % (i, b, a, norm(ob)[:70]))
        if not (b and a):
            ok = False
    print("  ->", "BOTH OBLIGATIONS CARRIED FORWARD VERBATIM" if ok else "AN OBLIGATION MOVED")

    print("\n=== 3. Residue: what is in AFTER that is NOT one of the obligations? ===")
    residue = norm(AFTER)
    for ob in OBLIGATIONS:
        residue = residue.replace(norm(ob), "█OBLIGATION█")
    print("  ", residue)

    print("\n=== 4. Residue: what was in BEFORE that is NOT one of the obligations? ===")
    rb = norm(BEFORE)
    for ob in OBLIGATIONS:
        rb = rb.replace(norm(ob), "█OBLIGATION█")
    print("  ", rb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
