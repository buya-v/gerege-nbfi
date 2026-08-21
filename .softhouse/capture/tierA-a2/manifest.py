#!/usr/bin/env python3
"""Build MANIFEST.sha256 over this capture — observations, recipes AND the rig — and verify it.

  python3 manifest.py write     -> (re)write MANIFEST.sha256
  python3 manifest.py verify    -> exit 0 only if the whole capture is accounted for

What is covered
---------------
  out/**   the observations (recursively)
  req/**   the exact request bodies that produced them (recursively) — a capture whose
           request body has drifted is not reproducible, which is why req/ is hashed too
  sql/**   the queries (recursively)
  ./*      every file in this directory except MANIFEST.sha256 itself: CAPTURE-PLAN.md
           (which carries all seven findings), DEFECTS-FOUND-BY-REVIEW.md, cap.sh,
           env.sh, the mkreq*/run-* recipes, the provers, and manifest.py ITSELF

A2-5 fixes for D-3 (P-22 class: three ways this guard was blind)
---------------------------------------------------------------
  (i)   VACUOUS ON EMPTY INPUT. It printed "OK: 0 files match" and exited 0 on an empty
        manifest. A guard that inspects zero files must be an ERROR, not a pass
        (P-22). Two zero-input refusals now fire before any comparison, and a
        REQUIRED-file floor means a stripped manifest cannot pass either.
  (ii)  NON-RECURSIVE. os.listdir() saw only the top level of out/, so a fabricated
        observation dropped in out/<subdir>/ was laundered as verified. The walk is now
        recursive, so such a file is UNTRACKED and the run goes red.
  (iii) COVERED NEITHER THE ANALYSIS DOC NOR THE RIG NOR ITSELF. The A2-4 reviewer
        appended "MNT rounds HALF_EVEN and money may be stored as float" to
        CAPTURE-PLAN.md and verify stayed GREEN. Every file in this directory is now
        hashed, this script included.

  Flag integrity. FLAGGED-NOT-REPRODUCIBLE.txt lists the 30 attempt1-* files whose
  recipes are provably false (D-1). They are covered like any other evidence — deleting
  evidence to make a rig look clean is worse than carrying it flagged — and verify
  cross-checks that every flagged path still exists AND is still in the manifest, then
  re-prints the flag so no reader of a green run can miss it.

Every one of these was driven RED against the real pre-fix bytes before being shipped:
see prove-manifest-blind-red.py and RED-GREEN-D3-manifest-blindness.txt.
prove-manifest-red.py separately proves the hash comparison itself is failable.
"""
import hashlib
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(DIR, "MANIFEST.sha256")
MANIFEST_NAME = "MANIFEST.sha256"
FLAGFILE = "FLAGGED-NOT-REPRODUCIBLE.txt"
DIRS = ("out", "req", "sql")

# A manifest that does not list these is not a manifest of THIS capture. Without this
# floor, `write`ing over a stripped tree and `verify`ing it would pass on a handful of
# files while the evidence went unchecked — the vacuous pass of D-3(i) by another route.
REQUIRED = (
    "CAPTURE-PLAN.md",
    "DEFECTS-FOUND-BY-REVIEW.md",
    FLAGFILE,
    "cap.sh",
    "env.sh",
    "manifest.py",
)


def digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def entries():
    """Yield (manifest-relative-path, absolute-path), deterministically ordered.

    out/, req/, sql/ first and RECURSIVELY (D-3 ii), then every file in this directory
    except the manifest itself (D-3 iii). The dir-first ordering is deliberate: it keeps
    the pre-A2-5 lines byte-identical and in place, so extending coverage is provably an
    addition and not a rewrite of the evidence's hashes.
    """
    for d in DIRS:
        base = os.path.join(DIR, d)
        if not os.path.isdir(base):
            continue
        for root, dirnames, filenames in os.walk(base, followlinks=True):
            dirnames.sort()
            for n in sorted(filenames):
                p = os.path.join(root, n)
                if os.path.isfile(p):
                    yield os.path.relpath(p, DIR), p
    for n in sorted(os.listdir(DIR)):
        p = os.path.join(DIR, n)
        if n == MANIFEST_NAME:
            continue
        if os.path.isfile(p):
            yield n, p


def flagged():
    """Paths flagged non-reproducible (D-1). Missing flag file is itself a failure."""
    p = os.path.join(DIR, FLAGFILE)
    if not os.path.exists(p):
        return None
    out = []
    for line in open(p):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def write():
    lines = [f"{digest(p)}  {rel}\n" for rel, p in entries()]
    with open(MAN, "w") as f:
        f.writelines(lines)
    print(f"wrote {MAN} with {len(lines)} entries")


def verify():
    if not os.path.exists(MAN):
        print("MANIFEST.sha256 missing", file=sys.stderr)
        return 1

    want = {}
    for lineno, line in enumerate(open(MAN), 1):
        line = line.rstrip("\n")
        if not line:
            continue
        try:
            h, rel = line.split("  ", 1)
        except ValueError:
            print(f"MALFORMED MANIFEST.sha256 line {lineno}: {line!r}", file=sys.stderr)
            return 1
        want[rel] = h

    # --- D-3(i): zero inspected files is an ERROR, not a pass. Checked BEFORE any
    # comparison, so the refusal is unambiguous rather than incidental.
    if not want:
        print("REFUSING: MANIFEST.sha256 lists 0 files — INSPECTED NOTHING. "
              "A guard that checks nothing is not a guard (P-22).", file=sys.stderr)
        return 1

    have = {rel: digest(p) for rel, p in entries()}
    if not have:
        print("REFUSING: found 0 files under out/, req/, sql/ or this directory — "
              "INSPECTED NOTHING.", file=sys.stderr)
        return 1

    missing_required = [r for r in REQUIRED if r not in want]
    if missing_required:
        print("REFUSING: MANIFEST.sha256 does not cover " + ", ".join(missing_required)
              + " — this is not a manifest of this capture.", file=sys.stderr)
        return 1

    bad = 0
    for rel, h in sorted(want.items()):
        if rel not in have:
            print(f"MISSING   {rel}"); bad += 1
        elif have[rel] != h:
            print(f"CHANGED   {rel}\n  manifest {h}\n  actual   {have[rel]}"); bad += 1
    for rel in sorted(have):
        if rel not in want:
            print(f"UNTRACKED {rel}"); bad += 1

    # --- flag integrity: the D-1 evidence must stay present AND stay covered.
    flags = flagged()
    if flags is None:
        print(f"REFUSING: {FLAGFILE} is missing — the D-1 flag on the attempt1-* "
              "evidence cannot be dropped.", file=sys.stderr)
        return 1
    for rel in flags:
        if not os.path.isfile(os.path.join(DIR, rel)):
            print(f"FLAGGED-BUT-ABSENT   {rel}  (flagged evidence must not be deleted)"); bad += 1
        elif rel not in want:
            print(f"FLAGGED-BUT-UNCOVERED {rel}  (flagged evidence must stay in the manifest)"); bad += 1

    if bad:
        print(f"\nFAIL: {bad} discrepancy/ies", file=sys.stderr)
        return 1

    ev = sum(1 for rel in want if rel.split("/")[0] in DIRS)
    print(f"OK: {len(want)} files match MANIFEST.sha256 "
          f"({ev} under out/ req/ sql/, {len(want) - ev} rig + docs, this script included)")
    print(f"FLAGGED, covered, NOT citable: {len(flags)} attempt1-* files — recipes provably "
          f"false (D-1), see {FLAGFILE}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "write":
        write()
    else:
        sys.exit(verify())
