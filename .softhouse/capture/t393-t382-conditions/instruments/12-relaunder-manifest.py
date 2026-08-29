#!/usr/bin/env python3
"""T393 — LAUNDER one MANIFEST.sha256 row to match the mutated bytes on disk.

Used only by 10-drive-conditions.sh, and only inside a scratch clone. Two of T393's cases
are about laundering, and they point in opposite directions:

  f3b   mutate a fork-sha NON-observation entry AND rewrite its manifest row.
        ARM E must STILL catch it, because ARM E compares against the IMMUTABLE fork blob
        and never reads a recorded digest. This case is what makes ARM E worth having
        rather than being a restatement of ARM C.

  f1-13b  mutate a POST-FORK observation AND rewrite its manifest row.
        [CORRECTED BY T433 / C-T423-1 — WHAT STOOD HERE WAS FALSE, IN A TRACKED EXECUTABLE.]
        This paragraph used to read, verbatim: "Nothing catches it, at either ref. That is
        the DISCLOSED RESIDUAL: there is no committed baseline older than HEAD for those 632
        observations. Driving it is how the boundary statement in
        verify-capture-integrity.py's docstring becomes a measurement instead of a hope."
        The last claim was not a measurement and not a hope — it was FALSE, and it was
        load-bearing: T393's handoff reasoned FROM the impossibility to send the next task
        to build a substitute artefact this repository already contained.
        THE BASELINE EXISTS AND ALWAYS DID: the blob at the commit that FIRST ADDED each
        observation, `git log --diff-filter=A -- <path>`. It is an object inside an
        ALREADY-COMMITTED commit, so laundering MANIFEST.sha256 inside the mutating commit
        cannot reach it. T433 swept the WHOLE 632 — two independent derivations of the birth
        commit agreeing 632/632; all 632 born STRICTLY OLDER than the tip; 0 born at the
        tip; 631 still byte-identical to their birth blob; exactly one legitimate re-capture,
        out/A2-370-db-ledger-state.txt, adjudicated by digest
        (.softhouse/capture/t433-t423-c1/out/00-whole-632-sweep.txt).
        f1-13b IS NOW CAUGHT, by ARM F — section 8 of verify-capture-integrity.py — which
        exits 1 naming the laundered file. This script still LAUNDERS the row, because
        laundering is exactly what ARM F must survive; what changed is the expected colour,
        from `0 0` to `0 1` in 10-drive-conditions.sh.

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
