#!/usr/bin/env python3
"""T362 — re-derive T357's OUTPUT-NEUTRALITY claim independently.

T357 says the five __file__ reroots are output-neutral, and evidences it with its own
diff-sections.py. This does not reuse that tool. It takes the COMMITTED
TRANSCRIPT-A2-11.txt as it stands on main (generated 2026-08-21T08:11:39Z, before any
T357 edit), slices out each section's body, runs the PATCHED script for that section
fresh, and diffs the two.
"""
import difflib
import re
import subprocess
import sys
import os

# Both inputs are passed in; nothing is hard-coded. See the sibling shell scripts
# for how to build the target tree.
#   argv[1]  the committed transcript, e.g.
#            git show main:.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt > /tmp/committed.txt
#   argv[2]  a checkout of main merged with softhouse/T357-a2-11-section1-red
if len(sys.argv) != 3:
    sys.exit("usage: %s <committed TRANSCRIPT-A2-11.txt> <main+T357 checkout>" % sys.argv[0])
COMMITTED = sys.argv[1]
MERGED = sys.argv[2]

SCRIPTS = {
    1: "check-shape.py",
    2: "enumerate-corpus.py",
    3: "verify-double-entry-minor-units.py",
    4: "verify-manifest-independently.py",
    5: "audit-float.py",
    6: "prove-resolve7-float-red.py",
    7: "prove-a2-7-guards-are-falsifiable.py",
}

text = open(COMMITTED, encoding="utf-8").read()
lines = text.splitlines()

# index the section headers of the COMMITTED transcript
hdr = {}
for i, ln in enumerate(lines):
    m = re.match(r"^############ (\d)\. ", ln)
    if m:
        hdr[int(m.group(1))] = i
print("committed transcript: %d lines, section headers at %s"
      % (len(lines), sorted(hdr.items())))


def committed_body(n):
    """Lines strictly between section n's header and its 'exit=' line."""
    start = hdr[n] + 1
    for j in range(start, len(lines)):
        if lines[j].startswith("exit="):
            return lines[start:j], lines[j]
    raise AssertionError("no exit= for section %d" % n)


print()
verdict = {}
for n in sorted(SCRIPTS):
    body, exitline = committed_body(n)
    # committed sections 2 and 8 carry extra prose lines emitted by run-all.sh itself,
    # not by the script; strip nothing — compare exactly and report.
    p = subprocess.run([sys.executable,
                        os.path.join(MERGED, ".softhouse/reviews/A2-11", SCRIPTS[n])],
                       capture_output=True, text=True, cwd=MERGED)
    fresh = (p.stdout + p.stderr).splitlines()
    # drop leading/trailing blank lines on both sides (run-all.sh emits its own blanks)
    def trim(x):
        while x and not x[0].strip():
            x = x[1:]
        while x and not x[-1].strip():
            x = x[:-1]
        return x
    b, f = trim(list(body)), trim(fresh)
    same = (b == f)
    verdict[n] = (same, len(b), len(f), p.returncode, exitline)
    flag = "IDENTICAL" if same else "DIFFERS"
    print("section %d  %-38s %-10s committed=%d lines  fresh=%d lines  "
          "committed %s  fresh exit=%d"
          % (n, SCRIPTS[n], flag, len(b), len(f), exitline, p.returncode))
    if not same:
        d = list(difflib.unified_diff(b, f, "committed", "fresh(T357-patched)", n=1))
        print("        %d diff lines; first 12:" % len(d))
        for ln in d[:12]:
            print("        | " + ln[:190])

print()
print("T357 CLAIMED: sections 1,2,3,6,7 IDENTICAL; 4 and 5 differ (rig has grown).")
got_identical = sorted(n for n, v in verdict.items() if v[0])
print("T362 MEASURED identical:", got_identical)
print("MATCHES T357'S CLAIM" if got_identical == [1, 2, 3, 6, 7]
      else "*** DOES NOT MATCH T357'S CLAIM ***")
