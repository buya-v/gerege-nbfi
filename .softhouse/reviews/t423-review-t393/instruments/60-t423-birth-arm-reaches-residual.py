#!/usr/bin/env python3
"""T423 — DRIVE the condition, do not merely argue it: a BIRTH-BLOB arm CATCHES T393's
"unclosable" residual.

T393's shipped boundary block says of the laundered post-fork case:

    "Closing this needs a committed baseline OLDER than HEAD for the post-fork
     observations, which does not exist and cannot be manufactured here."

`20-t423-birth-blob-probe.py` measured that such a baseline DOES exist — the blob at the
commit that FIRST ADDED each observation — and that on a clean tree 631 of the 632 post-fork
observations still equal it (the one exception, `out/A2-370-db-ledger-state.txt`, is
adjudicable by digest exactly as ARM E adjudicates its two).

Measuring feasibility is not the same as showing the arm fires. THIS instrument implements
the arm read-only, in ~25 lines, and runs it against a repository in which T393's own residual
attack has already been committed — the post-fork observation mutated AND its MANIFEST row
rewritten in the SAME commit. Section 10 reports PASS on that repository at both refs
(`out/T423-MATRIX.tsv`, rows `t423-residual-postfork-laundered`). The question is whether this
arm does.

USAGE — no host path is written in this file (T256/T298); the target repository is required:
    T423_TARGET=<a repository/worktree to grade>  python3 60-t423-birth-arm-reaches-residual.py

EXIT 0  the arm found no unadjudicated difference (a CLEAN corpus).
EXIT 1  the arm found at least one, NAMED. On the laundered repository this is the expected
        result, and it is the whole point of the instrument.
EXIT 2  REFUSED — the arm could not measure (empty population, a path with no ADD commit).
        A refusal is never a pass.

P-25: no floating point; every number is a len() or a sha256 hex digest.
P-24: the fork baseline is the LITERAL immutable sha, never `git merge-base`.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.environ.get("T423_TARGET")
if not ROOT:
    print("REFUSED: T423_TARGET must name the repository to grade. No default: a guard that")
    print("silently grades the wrong tree is worse than one that will not run.")
    sys.exit(2)
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
CAP = ".softhouse/capture/tierA-a2"
OBS = ("out", "req")

# The single post-fork observation that legitimately changed after it was added, adjudicated
# BY DIGEST in both directions, in ARM E's own spelling: a further mutation moves it, and so
# does a revert to the birth bytes.  [birth digest, disk digest]  -- both measured on the
# clean T393 tree by 20-t423-birth-blob-probe.py.
ADJUDICATED = {
    "out/A2-370-db-ledger-state.txt": (
        "1ea4927a59068d0a5ec45773dbc50a4c80d9eaa0457f0cecdc820e4b8ed5f857",
        "1c23375b0f010cf5bb65b6fead9c9ec063fcafe9e4f16d713b34f367f41716e2"),
}


def git(*a, check=True):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=check).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def obs_at(ref):
    return set(x.strip() for x in
               git("ls-tree", "-r", "--name-only", ref, "--", CAP + "/out", CAP + "/req")
               .decode().split("\n") if x.strip())


print("=== T423 ARM F (proposed) — every POST-FORK observation vs the blob at the commit")
print("    that FIRST ADDED it. The baseline T393 says does not exist. ===")
print("    target %s" % ROOT)

post = sorted(obs_at("HEAD") - obs_at(FORK))
print("    post-fork observations: %d" % len(post))
if not post:
    print("  REFUSED  the post-fork population is EMPTY. A zero-difference table over an")
    print("           empty population is a vacuous pass, which is the defect this whole")
    print("           review chain exists to remove. REFUSED.")
    sys.exit(2)

raw = git("log", "HEAD", "--diff-filter=A", "--name-only", "--format=%H", "--", CAP).decode()
birth, cur = {}, None
for line in raw.split("\n"):
    line = line.rstrip()
    if not line:
        continue
    if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
        cur = line
        continue
    birth[line] = cur          # newest-first walk, so the LAST assignment is the EARLIEST add

no_birth = [p for p in post if p not in birth]
if no_birth:
    print("  REFUSED  %d post-fork observations have no recorded ADD commit: %s"
          % (len(no_birth), no_birth[:5]))
    print("           The arm's baseline is not derivable for them. REFUSED, never a pass.")
    sys.exit(2)

same, diff, adjudicated, moved = 0, [], 0, []
for rel in post:
    b = birth[rel]
    at_birth = git("show", b + ":" + rel)
    with open(os.path.join(ROOT, rel), "rb") as fh:
        today = fh.read()
    hb, ht = sha(at_birth), sha(today)
    name = rel[len(CAP) + 1:]
    if name in ADJUDICATED:
        if (hb, ht) == ADJUDICATED[name]:
            adjudicated += 1
        else:
            moved.append((name, ADJUDICATED[name], (hb, ht)))
    elif hb == ht:
        same += 1
    else:
        diff.append((name, b, hb, ht))

print("    equal to their birth blob         : %d" % same)
print("    adjudicated-different, UNMOVED    : %d" % adjudicated)
print("    DIFFER and are NOT adjudicated    : %d" % len(diff))
print("    adjudicated but MOVED             : %d" % len(moved))
for name, b, hb, ht in diff:
    print("      LAUNDERED-OR-MUTATED %s" % name)
    print("        born at %s" % b)
    print("        birth blob %s" % hb)
    print("        disk       %s" % ht)
for name, want, got in moved:
    print("      ADJUDICATION MOVED %s  adjudicated %s got %s" % (name, want, got))

print()
if diff or moved:
    print("VERDICT: FAIL (exit 1). A post-fork captured oracle observation differs from the")
    print("blob at the commit that first added it. Rewriting MANIFEST.sha256 in the same")
    print("commit does NOT reach this baseline: it is an object in an already-committed")
    print("commit. This is the case section 10 reports PASS on.")
    sys.exit(1)
print("VERDICT: PASS (exit 0). Every post-fork observation still equals its birth blob.")
sys.exit(0)
