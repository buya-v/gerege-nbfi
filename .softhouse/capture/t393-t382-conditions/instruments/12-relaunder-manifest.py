#!/usr/bin/env python3
"""T393 — LAUNDER one MANIFEST.sha256 row to match the mutated bytes on disk.

Used only by 10-drive-conditions.sh, and only inside a scratch clone. Two of T393's cases
are about laundering, and they point in opposite directions:

  f3b   mutate a fork-sha NON-observation entry AND rewrite its manifest row.
        ARM E must STILL catch it, because ARM E compares against the IMMUTABLE fork blob
        and never reads a recorded digest. This case is what makes ARM E worth having
        rather than being a restatement of ARM C.

  f1-13b  mutate a POST-FORK observation AND rewrite its manifest row.
        Nothing catches it, at either ref. That is the DISCLOSED RESIDUAL: there is no
        committed baseline older than HEAD for those 632 observations. Driving it is how
        the boundary statement in verify-capture-integrity.py's docstring becomes a
        measurement instead of a hope.

argv: <clone root> <capture-relative name>.  REFUSES (exit 2) if the row is not there —
a laundering step that silently did nothing would turn a residual case into a caught one
and report the wrong colour.
"""
import hashlib
import os
import sys

if len(sys.argv) != 3:
    sys.stderr.write("usage: 12-relaunder-manifest.py <clone-root> <capture-relative-name>\n")
    sys.exit(2)

CLONE, NAME = sys.argv[1], sys.argv[2]
CAPREL = ".softhouse/capture/tierA-a2"
MANPATH = os.path.join(CLONE, CAPREL, "MANIFEST.sha256")
TARGET = os.path.join(CLONE, CAPREL, NAME)

with open(TARGET, "rb") as fh:
    digest = hashlib.sha256(fh.read()).hexdigest()

with open(MANPATH, "r", encoding="utf-8") as fh:
    lines = fh.read().split("\n")

hits = 0
for i, line in enumerate(lines):
    stripped = line.rstrip()
    if not stripped or stripped.startswith("#"):
        continue
    parts = stripped.split(None, 1)
    if len(parts) != 2:
        continue
    if parts[1].lstrip("*").strip() == NAME:
        lines[i] = line.replace(parts[0], digest, 1)
        hits += 1

if hits != 1:
    sys.stderr.write("REFUSED: %s matched %d manifest rows, expected exactly 1.\n"
                     % (NAME, hits))
    sys.exit(2)

with open(MANPATH, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("laundered manifest row for %s -> %s" % (NAME, digest))
sys.exit(0)
