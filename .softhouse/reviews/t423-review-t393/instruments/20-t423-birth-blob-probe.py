#!/usr/bin/env python3
"""T423 — IS T393's DISCLOSED RESIDUAL ACTUALLY UNCLOSABLE?

T393's boundary statement says, in the shipped docstring and in run-all.sh's banner:

    "Closing this needs a committed baseline OLDER than HEAD for the post-fork
     observations, which does not exist and cannot be manufactured here."

That is the claim this probe tests. There IS a committed baseline older than HEAD for every
one of the 632 post-fork observations: **the blob at the commit that FIRST ADDED it**. It is
immutable for exactly the reason ARM A's fork blob is immutable — reaching it requires
rewriting main's history, not editing the working tree, and no same-commit manifest rewrite
touches it.

This probe measures the two things that decide whether that is a usable arm:

  (1) FEASIBILITY — on a CLEAN tree, does every post-fork observation still equal its birth
      blob? If any legitimately changed after being added, a birth-blob arm would be RED on a
      clean corpus and the proposal is worthless. This is the measurement that decides it, and
      it is the one T393 did not take.
  (2) REACH — for the file T393's residual case mutates, does the birth blob differ from the
      laundered HEAD blob? If yes, the residual is detectable by material that already exists.

Exit 0 = the probe ran. The finding is in the printed numbers, not in the exit code; this is
a measurement instrument, not a guard.

P-25: no floating point. P-24: no merge-base anywhere; every baseline is a real commit sha.
"""
import collections
import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = os.environ.get("T423_ROOT") or str(pathlib.Path(__file__).resolve().parents[4])
REF = os.environ.get("T423_REF", "softhouse/T393-t382-conditions")
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
CAP = ".softhouse/capture/tierA-a2"
OBS = ("out", "req")


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def obs_at(ref):
    return sorted(x.strip() for x in
                  git("ls-tree", "-r", "--name-only", ref, "--",
                      CAP + "/out", CAP + "/req").decode().split("\n") if x.strip())


fork_obs = set(obs_at(FORK))
head_obs = obs_at(REF)
post = sorted(set(head_obs) - fork_obs)
print("post-fork observations (ARM A cannot see these): %d" % len(post))

# --- one history pass; earliest ADD per path.
print("walking history for `first added in` commits (one pass, --diff-filter=A) ...")
raw = git("log", REF, "--diff-filter=A", "--name-only", "--format=%H", "--", CAP).decode()
birth = {}
cur = None
for line in raw.split("\n"):
    line = line.rstrip()
    if not line:
        continue
    if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
        cur = line
        continue
    # git log walks newest-first, so the LAST assignment seen is the EARLIEST add
    birth[line] = cur
print("paths with a recorded ADD commit under %s: %d" % (CAP, len(birth)))

missing_birth = [p for p in post if p not in birth]
print("post-fork observations with NO recorded ADD commit (renames etc.): %d"
      % len(missing_birth))
for p in missing_birth[:5]:
    print("    %s" % p)

print()
print("=== (1) FEASIBILITY — on the CLEAN tree, does each post-fork observation still equal")
print("        the blob at the commit that FIRST ADDED it? ===")
same = 0
moved = []
unreadable = []
births = collections.Counter()
for rel in post:
    b = birth.get(rel)
    if b is None:
        unreadable.append((rel, "no ADD commit"))
        continue
    births[b] += 1
    try:
        blob = git("show", b + ":" + rel)
    except subprocess.CalledProcessError as exc:
        unreadable.append((rel, repr(exc)))
        continue
    with open(os.path.join(ROOT, rel), "rb") as fh:
        disk = fh.read()
    if sha(blob) == sha(disk):
        same += 1
    else:
        moved.append((rel, b))
print("    equal to their birth blob : %d" % same)
print("    CHANGED since birth       : %d" % len(moved))
print("    unresolvable              : %d" % len(unreadable))
for rel, b in moved[:10]:
    print("      CHANGED %s  (born %s)" % (rel, b[:12]))
for rel, why in unreadable[:10]:
    print("      UNRESOLVABLE %s  %s" % (rel, why))
print("    distinct birth commits covering the post-fork set: %d" % len(births))
for c, n in births.most_common(10):
    print("      %s  %4d observations" % (c[:12], n))

print()
print("=== (2) REACH — the residual's own target ===")
target = post[0] if post else None
print("    T393's drive mutates the sorted-first post-fork observation: %s" % target)
if target and target in birth:
    b = birth[target]
    print("    born at %s  (%s)" % (b, git("log", "-1", "--format=%s", b).decode().strip()))
    print("    birth blob sha256 : %s" % sha(git("show", b + ":" + target)))
    print("    HEAD  blob sha256 : %s" % sha(git("show", REF + ":" + target)))
    print("    A same-commit manifest rewrite CANNOT change the birth blob: it is an object in")
    print("    an ALREADY-COMMITTED commit, reachable only by rewriting history — the exact")
    print("    property that makes ARM A immune to laundering (T382 matrix case 17).")

print()
print("VERDICT OF THE PROBE — read the two numbers above, not this sentence:")
print("  a birth-blob arm is FEASIBLE iff 'CHANGED since birth' is 0 on the clean tree,")
print("  and it REACHES the residual iff the birth blob is a different object from the")
print("  laundered HEAD blob the attacker controls.")
sys.exit(0)
