#!/usr/bin/env python3
"""
T466 -- CITATION SWEEP.  Every inbound `conformance.sh:NNNN` citation in the tree is a PIN INTO
A LINE NUMBER, and this task inserts about four hundred lines into that file, so every citation
below the first insertion now points somewhere else.

THE STANDING REMEDY IN THIS PROGRAM IS TO CITE BY NAME, and this instrument does not pretend
otherwise: it does not repair citations, it MEASURES how many moved and shows WHICH, so the
handoff can say which of them are load-bearing (a `.pin`, a guard, `patterns.md`) and which are
prose in a task record that no instrument reads. T459 reported that `tasks.json` alone carries
SIX moved citations where an earlier sweep had said one; T466 is forbidden to edit `tasks.json`
(it is the driver file), so the only honest thing to do is COUNT and DECLARE.

INPUTS, all on the command line so no repository path is spelled here (guard_dead_path_frontier):
  argv[1]  the BEFORE text of the cited file
  argv[2]  the AFTER text of the cited file
  argv[3]  the repo-relative name the citations use, e.g. <dir>/conformance.sh
Tracked file list arrives on stdin, one path per line.
"""
import re
import sys


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("usage: citation-sweep.py <before> <after> <cited-name>  "
                         "(tracked paths on stdin)\n")
        return 3
    before_path, after_path, cited = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(before_path, "r", encoding="utf-8", errors="surrogateescape") as fh:
        before = fh.read().split("\n")
    with open(after_path, "r", encoding="utf-8", errors="surrogateescape") as fh:
        after = fh.read().split("\n")
    if len(before) < 100 or len(after) < 100:
        sys.stderr.write("REFUSED: one of the two texts is under 100 lines; that is not the "
                         "file this sweep is about.\n")
        return 3
    tracked = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]
    if len(tracked) < 100:
        sys.stderr.write("REFUSED: tracked path list has %d rows. An empty corpus finds no "
                         "moved citation and would report the sweep clean.\n" % len(tracked))
        return 3

    base = cited.rsplit("/", 1)[-1]
    pat = re.compile(re.escape(base) + r":(\d+)")

    # CALIBRATION (P-72): the cited file must cite ITSELF somewhere, or the pattern is wrong.
    selfhits = 0
    for ln in after:
        selfhits += len(pat.findall(ln))
    if selfhits == 0:
        sys.stderr.write("REFUSED: CALIBRATION FAILED -- the pattern finds no citation even "
                         "inside the cited file. The reader is broken, not the tree.\n")
        return 3
    print("CALIBRATION: the citation pattern finds %d occurrence(s) inside the cited file "
          "itself." % selfhits)

    total = 0
    moved = 0
    dead = 0
    perfile = {}
    movers = []
    for p in tracked:
        try:
            with open(p, "r", encoding="utf-8", errors="surrogateescape") as fh:
                text = fh.read()
        except (OSError, UnicodeError):
            continue
        for m in pat.finditer(text):
            n = int(m.group(1))
            total += 1
            b = before[n - 1] if 0 < n <= len(before) else None
            a = after[n - 1] if 0 < n <= len(after) else None
            if a is None:
                dead += 1
                perfile[p] = perfile.get(p, 0) + 1
                movers.append((p, n, "OFF THE END", b))
            elif b != a:
                moved += 1
                perfile[p] = perfile.get(p, 0) + 1
                movers.append((p, n, "MOVED", b))
    print("INBOUND CITATIONS OF %s ACROSS %d TRACKED FILES: %d total, %d now point at "
          "DIFFERENT TEXT, %d point PAST THE END." % (base, len(tracked), total, moved, dead))
    print("BY FILE (only files with at least one moved or dead citation):")
    for p in sorted(perfile):
        print("  %4d  %s" % (perfile[p], p))
    print("EVERY MOVED CITATION, with the line it USED to name:")
    for p, n, kind, b in sorted(movers):
        print("  %-11s %s:%d  was: %s" % (kind, p, n, (b or "")[:88]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
