#!/usr/bin/env python3
"""T46 -- close the "corrections leak" hazard.

`patterns.md`: *"An author fixes the section the review named and leaves the sections that restate
the same claim.  Remedy: after any correction, grep the whole document for restatements of the
corrected claim."*

T46's corrections are appended at the end of the T39 and T40 handoffs.  A reader following either
document top-down would still meet the original wrong instruction.  This inserts an inline
**[SUPERSEDED …]** marker at every restatement site, WITHOUT deleting or rewording the original
sentence -- the record of what was claimed stays intact; only a pointer is added.

Idempotent: a line that already carries a marker is left alone.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4] / ".softhouse" / "handoff"

# (file, 1-based line number, anchor substring that must be on that line, marker)
SITES = [
    ("T39-periodratio-observation.md", 14, "1426-1436",
     "[SUPERSEDED by T46 C-1/C-4: the special case is `:1432`-`:1433`, and it is graded only "
     "JOINTLY with the packed whole-months rule -- see the CORRECTIONS section at the end.]"),
    ("T39-periodratio-observation.md", 15, "116 of 116",
     "[SUPERSEDED by T46 C-1: the null hypothesis is the wrong one -- a port with naive "
     "whole-months AND no special case also matches 116 of 116. See CORRECTIONS.]"),
    ("T39-periodratio-observation.md", 52, "1429-1434",
     "[SUPERSEDED by T46 C-4: the special case is `:1432` (predicate) and `:1433` (call); "
     "`:1429-1434` does not compile if deleted. And R3 is not the most plausible mis-port -- R4 is, "
     "and R4 is INDISTINGUISHABLE. See CORRECTIONS.]"),
    ("T39-periodratio-observation.md", 103, "1429-1434",
     "[SUPERSEDED by T46 C-1/C-4: this row grades the PAIR (special case AND packed "
     "whole-months), not `:1429-1434`. See CORRECTIONS.]"),
    ("T39-periodratio-observation.md", 178, ":1509",
     "[SUPERSEDED by T46 C-4: `daysInMonth` is computed at `:1508`.]"),
    ("T39-periodratio-observation.md", 356, "1426-1436",
     "[SUPERSEDED by T46 C-1: DEC-1 must pin the PACKED whole-months rule normatively alongside "
     "the special case -- neither clause is safe stated alone. The lines are `:1432`-`:1433`. "
     "See CORRECTIONS.]"),

    ("T40-charges-capture.md", 31, "invariant C5",
     "[SUPERSEDED by T46 C-3: C5 is a discrimination PROBE, not an invariant -- DEC-1 rev 8's "
     "ratified C-1 forbids asserting it. See CORRECTIONS.]"),
    ("T40-charges-capture.md", 366, "C5",
     "[SUPERSEDED by T46 C-3: relabelled probe P5, reported as a signed delta. See CORRECTIONS.]"),
    ("T40-charges-capture.md", 397, ":504",
     "[SUPERSEDED by T46 C-4: `:504` is the site of AGREEMENT. The disagreement is the cumulative "
     "MAIN LOOP at `:392` with `ScheduleCurrentPeriodParams.java:144-145`. See CORRECTIONS.]"),
    ("T40-charges-capture.md", 445, "C5",
     "[SUPERSEDED by T46 C-3: probe, not invariant.]"),
    ("T40-charges-capture.md", 553, "216 × p",
     "[SUPERSEDED by T46 C-2: the proof is FALSE and two ties have been OBSERVED -- "
     "`0.021875 %` of 21,600.00 = 4.725 -> 4.73, and `0.009375 %` = 2.025 -> 2.03. See CORRECTIONS.]"),
]


def main():
    edited = 0
    for fname, lineno, anchor, marker in SITES:
        p = ROOT / fname
        lines = p.read_text().split("\n")
        idx = lineno - 1
        if idx >= len(lines):
            print(f"  !! {fname}:{lineno} beyond end of file", file=sys.stderr)
            return 1
        line = lines[idx]
        if anchor not in line:
            print(f"  !! {fname}:{lineno} does not contain {anchor!r}: {line[:90]!r}",
                  file=sys.stderr)
            return 1
        if "[SUPERSEDED" in line:
            print(f"  -- {fname}:{lineno} already marked")
            continue
        lines[idx] = line + "  **" + marker + "**"
        p.write_text("\n".join(lines))
        edited += 1
        print(f"  ok {fname}:{lineno} marked")

    print(f"\n{edited} restatement site(s) marked SUPERSEDED. "
          "No original sentence was deleted or reworded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
