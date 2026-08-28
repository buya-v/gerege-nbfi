#!/usr/bin/env python3
r"""
T381 -- insert the backslash-class PROBE SELECTOR into a copy of `casualty-sweep.sh`.

    python3 t381-insert-probe-selector.py <src.sh> <dst.sh>

WHY THIS IS A SCRIPT AND NOT ONE LINE OF `awk`. The first version of D-R3b did this with

    awk -v ins="$PROBE_SEL" '/^echo$/ && !seen { print ins; seen=1 } { print }'

and it was WRONG, silently, in the one way that mattered: **`awk -v` expands escape sequences in
the assigned value**, so the `\b` in the probe pattern was turned into an actual BACKSPACE
character before it ever reached the file. The drive then measured a selector carrying a
backspace, not a selector carrying a backslash-class -- so the BEFORE arm printed MEASURED ZERO
for the wrong reason and the AFTER arm did not refuse at all, which is exactly how the defect
was caught. An instrument that mangles its own test input is the same class of error as an
instrument that emits a negative it did not measure; the drive caught it, and this file is the
repair. [T381, D-R3b, first run]

The insertion point is the bare `echo` line that precedes `END OF SWEEP`, i.e. after S16 and
before the summary. Both the marker and the insertion are COUNT-ANCHORED: exactly one marker
must be found and the written file must contain exactly one probe line, or this exits non-zero.
"""
import sys

PROBE = r"""sel "ZZ-DRIVE  a selector carrying a backslash-class" -n -E 'zz\bprobe'"""
MARKER = "echo\n"

if len(sys.argv) != 3:
    sys.exit(__doc__)
src, dst = sys.argv[1], sys.argv[2]
lines = open(src, encoding="utf-8").readlines()

n = sum(1 for l in lines if l == MARKER)
if n < 1:
    sys.exit("insert-probe: no bare `echo` marker line found in %s" % src)

out, done = [], False
for l in lines:
    if l == MARKER and not done:
        out.append(PROBE + "\n")
        done = True
    out.append(l)
if not done:
    sys.exit("insert-probe: marker never matched in %s" % src)

text = "".join(out)
if text.count(PROBE) != 1:
    sys.exit("insert-probe: probe selector present %d times, expected 1" % text.count(PROBE))
if r"\b" not in text[text.index(PROBE):text.index(PROBE) + len(PROBE)]:
    sys.exit("insert-probe: the probe lost its backslash-class on the way in -- refusing")
open(dst, "w", encoding="utf-8").write(text)
print("inserted the probe selector, backslash-class intact: %s" % PROBE)
