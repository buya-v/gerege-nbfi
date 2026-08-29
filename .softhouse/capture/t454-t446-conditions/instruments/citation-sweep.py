#!/usr/bin/env python3
"""
T454 -- THE INBOUND CITATION SWEEP, RUN TWO PINS DEEP.  [From T446's LOW-2.]

T445 checked ONE citation (`patterns.md:3426`) and concluded that its commit moved no pin.
T446 swept the whole repository and found 16 `conformance.sh:NNNN` citations pointing above
the first line T445 moved -- ALL SIXTEEN ALREADY ROTTED, so T445's conclusion survived BY
LUCK rather than by the evidence it offered.  This sweep is the same one, run for T454's own
commit, and it RESOLVES each citation on BOTH trees instead of counting them.

  * a citation that resolved BEFORE and no longer resolves is a pin THIS COMMIT BROKE;
  * a citation that was already rotted stays rotted and is reported as such -- it is not
    evidence that nothing moved;
  * "resolves" is decided by whether the cited line is non-blank and non-comment, which is
    the weakest test that can distinguish a live pin from a dead one without knowing what
    each citation meant.

IT MUST NOT PRINT A NEGATIVE IT DID NOT MEASURE:
  * the corpus is asserted reachable and non-empty (exit 3 otherwise);
  * the matcher is calibrated on a citation KNOWN to be present in the corpus before any
    count is reported (exit 2 if the calibration misses);
  * "zero citations" and "could not search" have different exit codes.

usage: citation-sweep.py <repo root> <old rev> <new rev>
"""

import re
import subprocess
import sys

PAT = re.compile(r'conformance\.sh:(\d+)')


def git(root, *args):
    # errors="replace": this corpus contains files that are not valid UTF-8, and a decode
    # crash midway through a sweep is an instrument that stopped rather than one that
    # measured.  The pattern searched for is pure ASCII, so replacement cannot create or
    # destroy a match.
    r = subprocess.run(["git", "-C", root] + list(args),
                       capture_output=True, text=True,
                       errors="replace")
    return r.returncode, r.stdout


def main():
    if len(sys.argv) != 4:
        print("usage: citation-sweep.py <repo root> <old rev> <new rev>")
        return 3
    root, old, new = sys.argv[1], sys.argv[2], sys.argv[3]

    rc, files = git(root, "ls-files")
    if rc != 0 or not files.strip():
        print("CORPUS UNREACHABLE OR EMPTY: git ls-files rc=%d, %d bytes" % (rc, len(files)))
        return 3
    paths = [f for f in files.split("\n") if f]
    print("T454 INBOUND CITATION SWEEP")
    print("corpus            : %d tracked files" % len(paths))
    print("revisions         : %s -> %s" % (old, new))

    olds = {}
    news = {}
    for rev, dest in ((old, olds), (new, news)):
        rc, blob = git(root, "show", "%s:.softhouse/conformance.sh" % rev)
        if rc != 0 or not blob:
            print("CANNOT READ .softhouse/conformance.sh AT %s" % rev)
            return 3
        dest["lines"] = blob.split("\n")
    print("conformance.sh    : %d lines at %s, %d lines at %s"
          % (len(olds["lines"]), old, len(news["lines"]), new))

    # ONE `git grep` over the tree at <new rev>, not ten thousand `git show`s.  git grep's
    # exit code carries the three facts this instrument needs to keep apart: 0 = matches,
    # 1 = a MEASURED zero, >1 = an ERROR that must never be read as zero.
    rc, hits = git(root, "grep", "-n", "-I", "-E", "conformance[.]sh:[0-9]+", new)
    if rc > 1:
        print("SEARCH ERROR: git grep exited %d. A search that errored has not reported"
              " zero. REFUSED." % rc)
        return 3
    cites = []
    for line in hits.split("\n"):
        if not line:
            continue
        # "<rev>:<path>:<lineno>:<text>"
        parts = line.split(":", 3)
        if len(parts) < 4:
            continue
        f = parts[1]
        for m in PAT.finditer(parts[3]):
            cites.append((f, int(m.group(1))))
    if not cites:
        print("CALIBRATION MISSED: not one `conformance.sh:NNNN` citation in a corpus that is")
        print("known to carry hundreds. The matcher or the corpus is broken. REFUSED.")
        return 2
    print("citations found   : %d occurrences, %d distinct line numbers"
          % (len(cites), len({n for _, n in cites})))

    def resolves(lines, n):
        if n < 1 or n > len(lines):
            return False
        s = lines[n - 1].strip()
        return bool(s) and not s.startswith("#")

    # The first line this commit changed, measured from the diff rather than typed.
    rc, diff = git(root, "diff", "-U0", "%s..%s" % (old, new), "--", ".softhouse/conformance.sh")
    if rc != 0:
        print("CANNOT DIFF the harness between %s and %s" % (old, new))
        return 3
    firsts = [int(m.group(1)) for m in re.finditer(r'^@@ -(\d+)', diff, re.M)]
    if not firsts:
        print("NO HUNKS in the harness diff: this commit moved no line of it. Nothing to sweep.")
        return 0
    first = min(firsts)
    print("first changed line: %d (measured from the diff, not typed)" % first)

    above = [(f, n) for f, n in cites if n >= first]
    print("citations at or below that line (i.e. MOVED by this commit): %d" % len(above))
    print("")
    print("%-72s %-7s %-9s %s" % ("citing file", "line", "before", "after"))
    broke = 0
    already = 0
    for f, n in sorted(set(above)):
        b = resolves(olds["lines"], n)
        a = resolves(news["lines"], n)
        if b and not a:
            broke += 1
        if not b:
            already += 1
        print("%-72s %-7d %-9s %s" % (f[:72], n,
                                      "resolves" if b else "ROTTED",
                                      "resolves" if a else "ROTTED"))
    print("")
    print("citations this commit BROKE (resolved before, rotted after) : %d" % broke)
    print("citations ALREADY ROTTED before this commit                 : %d" % already)
    print("")
    print("READING: 'already rotted' is not a defence. It is the reason the remedy is to cite")
    print("by RULE ID and SENTENCE and never by line number -- which is what T445 did to this")
    print("file's outbound patterns.md citations and what T454's handoff does for its own.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
