#!/usr/bin/env python3
"""T45 - prove mechanically WHICH normative blocks revision 9 touched.

Revision 9 is an erratum. The claim it needs to support before any replay is meaningful is:
*the sentences a from-text model reads are unchanged, so a model transcribed from revision 8's
text is also a correct transcription of revision 9's text.*

This extracts the normative blocks a model reads -- every fenced code block, plus the graded
domain predicate -- from revision 8 (git show main:...) and from revision 9 (working tree),
and diffs them block by block. Anything that moved is printed in full.
"""
import difflib
import re
import subprocess
import sys

DOC = "docs/adr/DEC-1-schedule-generator-adapter.md"
FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)


def blocks(text):
    return [b.strip("\n") for b in FENCE.findall(text)]


def graded_domain(text):
    """Section 3.1's predicate block, however it is fenced or indented."""
    i = text.find("### 3.1")
    j = text.find("### 3.2")
    return text[i:j]


def main():
    old = subprocess.run(["git", "show", f"main:{DOC}"],
                         capture_output=True, text=True).stdout
    new = open(DOC).read()

    print("T45 NORMATIVE-BLOCK DIFF - revision 8 (main) against revision 9 (working tree)")
    print()

    ob, nb = blocks(old), blocks(new)
    print(f"fenced normative blocks: revision 8 = {len(ob)}, revision 9 = {len(nb)}")

    oset, nset = set(ob), set(nb)
    removed = [b for b in ob if b not in nset]
    added = [b for b in nb if b not in oset]
    print(f"  blocks present in 8 and REMOVED in 9 : {len(removed)}")
    print(f"  blocks ADDED in 9                    : {len(added)}")
    print(f"  blocks unchanged                     : {len(oset & nset)}")
    print()

    for b in removed:
        print("--- REMOVED (present in revision 8, absent in revision 9) ---")
        print(b)
        print()
    for b in added:
        print("+++ ADDED (absent in revision 8, present in revision 9) +++")
        print(b)
        print()

    og, ng = graded_domain(old), graded_domain(new)
    print("=" * 78)
    print("Section 3.1 (the graded-domain predicate), byte comparison:")
    if og == ng:
        print("  IDENTICAL -- no graded-domain predicate moves in revision 9.")
    else:
        print("  *** CHANGED ***")
        for line in difflib.unified_diff(og.split("\n"), ng.split("\n"),
                                         "rev8 3.1", "rev9 3.1", lineterm=""):
            print("  " + line)
    print()

    print("=" * 78)
    print("VERDICT")
    if not removed and og == ng:
        print("  No normative block that existed in revision 8 was removed or altered, and")
        print("  section 3.1 is byte-identical. Every block added in revision 9 is NEW")
        print("  specification (listed above), not a change to an existing rule.")
        print("  => A model transcribed from revision 8's arithmetic text is a correct")
        print("     transcription of revision 9's arithmetic text.")
        return 0
    print("  Normative content MOVED. Read the diff above before trusting any replay.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
