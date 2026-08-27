#!/usr/bin/env python3
"""T302 attempt 2 — read-only probe of the T309 lock-commit discriminator.

Reads the `in_progress` set at a fire's lock commit and compares it with the
`in_progress` set at a later commit, exactly as
ready-tasks.py:dispatches_predating_this_fire() does, and reports which tasks
the T309 discriminator would classify as CORPSES (demotable in_session).

Read-only: runs `git show` in THIS worktree only, writes nothing.

Usage: cmp-lockset.py <lock-sha> [<now-sha>]
"""
import json
import subprocess
import sys

REPO = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8"


def blob(sha):
    o = subprocess.run(["git", "-C", REPO, "show",
                        "%s:.softhouse/tasks.json" % sha],
                       capture_output=True, text=True)
    if o.returncode != 0:
        sys.exit("git show %s failed: %s" % (sha, o.stderr.strip()))
    return {t["id"]: t for t in json.loads(o.stdout)["tasks"]}


lock_sha = sys.argv[1]
now_sha = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
lock, now = blob(lock_sha), blob(now_sha)
lp = {i for i, t in lock.items() if t.get("status") == "in_progress"}
np_ = {i for i, t in now.items() if t.get("status") == "in_progress"}
print("in_progress AT LOCK COMMIT %s (%d): %s" % (lock_sha, len(lp), sorted(lp)))
print("in_progress AT %s (%d): %s" % (now_sha, len(np_), sorted(np_)))
print()
print("INTERSECTION -> discriminator says CORPSE, DEMOTABLE:", sorted(lp & np_))
print("NOW-only     -> discriminator says LIVE, refuse     :", sorted(np_ - lp))
for i in sorted(lp & np_):
    t = now[i]
    print("   %-6s branch=%r fire=%r dispatched_at=%r status_at_lock=%r"
          % (i, t.get("branch"), t.get("fire"), t.get("dispatched_at"),
             lock[i].get("status")))
