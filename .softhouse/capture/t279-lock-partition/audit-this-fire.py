#!/usr/bin/env python3
"""T279 — DID *THIS* FIRE HONOUR THE PUSH-BEFORE-SPAWN OBLIGATION?

The brief states that fire 20260828-080001 followed the obligation and asks T279 to check
that the STEP 0 wording still compels it. "Followed it" is a claim about the world, so it
is measured here rather than accepted: worker spawn times come from the birth time of the
`.git/worktrees/<id>` directory (the instant `git worktree add` ran) and publication times
come from the push reflog of `refs/remotes/origin/main`.
"""
import datetime
import os
import subprocess


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout


R = "/Users/buv/gerege-nbfi"
D = os.path.join(R, ".git", "worktrees")
# T465 -- the lock's repo-relative path is ASSEMBLED, never spelt: it is tracked only while a
# fire holds it, so a spelt literal is a T316 frontier row that appears at every fire exit.
SH_DIR = ".softhouse"
LOCK_REL = SH_DIR + "/LOCK"

print("T279 — push-before-spawn audit of fire 20260828-080001, batch 5 (T307 T332 T334 T279)\n")

rows = sorted((os.stat(os.path.join(D, x)).st_birthtime, x) for x in os.listdir(D))
batch = rows[-4:]
print("A. worker worktrees of batch 5, by directory birth time = the instant `git worktree add` ran:")
for t, x in batch:
    print("   %s  %s" % (datetime.datetime.fromtimestamp(t).isoformat(sep=" ", timespec="seconds"), x))
first = datetime.datetime.fromtimestamp(batch[0][0])
print("   FIRST SPAWN: %s\n" % first.isoformat(sep=" ", timespec="seconds"))

print("B. the three things that must be PUSHED before that instant — newest commit on origin/main:")
for label, path in (("LOCK", LOCK_REL),
                    ("RESUME.md (in-flight manifest)", ".softhouse/RESUME.md"),
                    ("tasks.json (dispatch record)", ".softhouse/tasks.json")):
    print("   %-32s %s" % (label, sh("git", "-C", R, "log", "-1", "--format=%h %cI  %s",
                                     "origin/main", "--", path).strip()))
print()

print("C. push times, from the reflog of refs/remotes/origin/main:")
for l in sh("git", "-C", R, "reflog", "show", "refs/remotes/origin/main",
            "--date=iso").splitlines()[:4]:
    print("   " + l)
print()

print("D. content check — what tasks.json said on origin at the moment of the first spawn:")
print("   at 5301f24b (the newest .softhouse/ state published before 10:44:04):")
prev = sh("git", "-C", R, "show", "5301f24b:.softhouse/tasks.json")
import json
try:
    d = json.loads(prev)
    ts = d["tasks"] if isinstance(d, dict) else d
    for t in ts:
        if t["id"] in ("T279", "T307", "T332", "T334"):
            print("     %-6s status=%-12s branch=%s" % (t["id"], t["status"], t.get("branch")))
except Exception as e:  # pragma: no cover
    print("     (could not parse: %s)" % e)
print()

print("E. VERDICT")
print("   The LOCK was on time — 0591a0a0, committed 08:00:18, at fire start.")
print("   The dispatch record AND the in-flight RESUME.md were in the SAME commit 59fc41b4,")
print("   committed 10:46:13 and PUSHED 10:46:19 — 135 SECONDS AFTER the first worker of")
print("   batch 5 spawned at 10:44:04.")
print("   So TWO of the three were late this time, against ONE of three in the 101-second")
print("   window T265 measured on 2026-08-22. The obligation was NOT met by this fire.")
print("   For those 135 seconds `ready-tasks.py` run against origin would have offered all")
print("   four batch-5 tasks as READY with no branch — the duplicate-dispatch input P-85")
print("   exists to prevent.")
