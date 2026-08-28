#!/usr/bin/env python3
"""T357 — replace the RETIRED hard-coded worktree root in the five A2-11 scripts that
abort with a traceback (run-all.sh sections 2, 4, 5, 6, 7).

Run once. It asserts each target substring occurs EXACTLY once and refuses otherwise,
so a re-run or a drifted file fails loudly instead of half-patching.

NOTE ON THE COMMENT WORDING, recorded because a guard forced it. T357's first draft of
NOTE wrapped a repo path at end of line, so the line ended `...reviews/` and the next
began `A2-11/...`. Inside this file that appeared in a Python string as the literal two
characters backslash-n, and `bash .softhouse/conformance.sh` REFUSED with exit 2 on
guard_dead_path_frontier: the dead-path census extracted a token that resolved to
nothing. The guard was right. NOTE was reworded so no repo path ends a line, and the
same wording was applied to the five patched files, so this script remains a faithful
producer of exactly what is in them -- verified by re-extracting NOTE from this source
and asserting it occurs verbatim in all five.
"""
import pathlib
import sys

A2 = pathlib.Path(__file__).resolve().parents[2] / "reviews" / "A2-11"

NOTE = (
    "# T357 REPAIR -- was a hard-coded absolute path into the worktree\n"
    "#   /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da\n"
    "# which was RETIRED, so this script aborted with a traceback in every later checkout\n"
    "# and the committed transcript stopped being re-derivable from the script that made\n"
    "# it. Derived from __file__ instead: this file sits three levels below the checkout\n"
    "# root, under reviews/A2-11, so parents[3] IS that root. In the ORIGINAL worktree it\n"
    "# resolved to agent-a3ac3d56d665ff7da, so the substitution is OUTPUT-NEUTRAL there --\n"
    "# it restores the evidence rather than altering it, and that claim is MEASURED in\n"
    "# .softhouse/capture/t357-a2-11-section1-red/ (BEFORE/AFTER, and a diff against the\n"
    "# committed transcript), not asserted. A2_11_ROOT overrides for a cross-checkout run.\n"
)

RETIRED = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da"
DERIVE = 'os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])'

EDITS = {
    "enumerate-corpus.py": (
        'ROOT = "%s"' % RETIRED,
        NOTE + "ROOT = " + DERIVE,
        "import json\n", "import os\nimport pathlib\n"),
    "verify-manifest-independently.py": (
        'ROOT = "%s"' % RETIRED,
        NOTE + "ROOT = " + DERIVE,
        "import hashlib\n", "import os\nimport pathlib\n"),
    "audit-float.py": (
        'ROOT = Path("%s")' % RETIRED,
        NOTE + 'ROOT = Path(os.environ.get("A2_11_ROOT") or Path(__file__).resolve().parents[3])',
        "import ast\n", "import os\n"),
    "prove-resolve7-float-red.py": (
        'RIG = "%s/.softhouse/capture/tierA-a2"' % RETIRED,
        NOTE + 'RIG = (%s) + "/.softhouse/capture/tierA-a2"' % DERIVE,
        "import decimal\n", "import pathlib\n"),
    "prove-a2-7-guards-are-falsifiable.py": (
        'RIG = "%s/.softhouse/capture/tierA-a2"' % RETIRED,
        NOTE + 'RIG = (%s) + "/.softhouse/capture/tierA-a2"' % DERIVE,
        "import os\n", "import pathlib\n"),
}

rc = 0
for fn, (old, new, anchor, imp) in EDITS.items():
    p = A2 / fn
    s = p.read_text()
    if s.count(old) != 1:
        print("REFUSE %-40s target substring occurs %d times, expected 1" % (fn, s.count(old)))
        rc = 1
        continue
    if s.count(anchor) < 1:
        print("REFUSE %-40s import anchor %r not found" % (fn, anchor))
        rc = 1
        continue
    s = s.replace(old, new).replace(anchor, imp + anchor, 1)
    p.write_text(s)
    print("patched %-40s root now derived from __file__" % fn)
sys.exit(rc)
