#!/usr/bin/env python3
"""T423 — WHICH TRACKED FILES UNDER `.softhouse/capture/tierA-a2/` IS SECTION 10 STILL BLIND TO?

T393's DOES-NOT-COVER block names ONE residual: a committed change to a post-fork
*observation* whose MANIFEST row is rewritten in the same commit. This instrument asks the
complementary question the block does not answer — after ARMs A..E, WHICH tracked files in
that directory are graded by NO arm at all, even WITHOUT laundering?

The arms, by population:
  ARM A  fork-sha tree, out/ + req/                     (403)
  ARM B  HEAD tree,     out/ + req/                     (1035)
  ARM C  current MANIFEST rows under out/ or req/       (1035, set-equality + digest)
  ARM D  disk walk of out/ + req/                       (1035, lstat)
  ARM E  fork-sha MANIFEST rows NOT under out/ or req/  (27, vs the immutable fork blob)

So the graded set is  {out/,req/ at HEAD}  UNION  {the 27}. Everything else tracked under the
capture directory is graded by nothing here, and section 4 only reaches it if it is in the
FORK-SHA manifest — which by construction the 27 already are.

Exit 0 = the census ran. The finding is the printed set, not the exit code.
P-25: no floating point. Every number is a len(). P-24: literal immutable sha, no merge-base.
"""
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


def manifest_rows(blob):
    rows = {}
    for raw in blob.decode("utf-8").splitlines():
        s = raw.strip()
        if not s or s[0] == "#":
            continue
        bits = s.split(None, 1)
        if len(bits) != 2:
            continue
        rows[bits[1].lstrip("*").strip()] = bits[0]
    return rows


tracked = sorted(x.strip()[len(CAP) + 1:] for x in
                 git("ls-tree", "-r", "--name-only", REF, "--", CAP).decode().split("\n")
                 if x.strip())
obs_at_head = set(p for p in tracked if p.split("/")[0] in OBS)
man_now = manifest_rows(git("show", REF + ":" + CAP + "/MANIFEST.sha256"))
man_fork = manifest_rows(git("show", FORK + ":" + CAP + "/MANIFEST.sha256"))
arm_e = set(k for k in man_fork if k.split("/")[0] not in OBS)

print("=== T423 — the set section 10 does NOT grade ===")
print("REF  %s -> %s" % (REF, git("rev-parse", REF).decode().strip()))
print()
print("tracked files under %s                 : %d" % (CAP, len(tracked)))
print("  of those under out/ or req/ (ARMs A-D)                     : %d" % len(obs_at_head))
print("  of those NOT under out/ or req/                            : %d"
      % (len(tracked) - len(obs_at_head)))
print("ARM E's population (fork-sha manifest rows outside out/req)   : %d" % len(arm_e))

nonobs_tracked = sorted(p for p in tracked if p.split("/")[0] not in OBS)
ungraded = sorted(set(nonobs_tracked) - arm_e)
print("current MANIFEST rows outside out/ or req/                    : %d"
      % len([k for k in man_now if k.split("/")[0] not in OBS]))
print()
print("*** TRACKED UNDER THE CAPTURE DIR AND GRADED BY NO ARM OF SECTION 10 : %d ***"
      % len(ungraded))
for p in ungraded:
    has_row = "row" if p in man_now else "NO-ROW"
    in_fork_tree = subprocess.run(
        ["git", "-C", ROOT, "cat-file", "-e", "%s:%s/%s" % (FORK, CAP, p)],
        capture_output=True).returncode == 0
    print("    %-52s %-7s %s" % (p, has_row, "in-fork-tree" if in_fork_tree else "post-fork"))

print()
print("NOTE ON SECTION 4: it compares the FORK-SHA manifest's entries. A file that is not in")
print("that manifest is outside section 4's third arm too, so for the post-fork members of")
print("the set above NOTHING in run-all.sh compares them against anything.")
sys.exit(0)
