#!/usr/bin/env python3
"""push-before-spawn AUDIT -- T336.  A DETECTOR, NOT A GUARD.  Read the next paragraph.

WHAT THIS IS AND IS NOT
=======================
This program **cannot prevent** a push-before-spawn violation.  It reconstructs, after the
fact, what `origin/main` said AT THE INSTANT each worker worktree was created, and exits
non-zero if origin was then still lying about the fire.  Nothing invokes it automatically
today.  Until a caller in the exit protocol runs it, the obligation it audits is a
**CONVENTION** -- that word, not "enforced" (P-45: a guard that only works when someone
remembers to run it enforces nothing).  `.softhouse/hooks/README.md` records why no git
hook can do better here.

WHY NOT A GIT HOOK -- MEASURED, NOT ASSUMED [T336, ../capture/t336-.../out/real-route-*]
========================================================================================
The agent harness creates each worker worktree WITHOUT RUNNING GIT HOOKS.  Measured on
2026-08-28 in the live repo: five real spawns produced ZERO `post-checkout` invocations and
ZERO `reference-transaction` invocations, while the same two hook files, in the same
`.git/hooks`, fired within 18 seconds for a worker's own `git checkout -b`.  So a hook at
the spawn instant does not merely fail to refuse (T280's F-C) -- IT DOES NOT RUN AT ALL.

WHAT "VIOLATION" MEANS HERE, AND WHY IT IS A CONTENT TEST AND NOT A CLOCK TEST
=============================================================================
P-85's harm is not "a push happened late" in the abstract.  It is: *while this worker was
alive, `origin/main` told the next orchestrator that the task was unclaimed and the fire
was not running.*  So for each spawn S this audit reconstructs origin/main as of S and asks
three content questions of that tree:

  1. does `.softhouse/LOCK` exist?              (else origin says no fire is running)
  2. does `.softhouse/RESUME.md` exist?         (the in-flight manifest)
  3. does `.softhouse/tasks.json` already carry the worker's task branch, with the task
     `in_progress`?                             (else `ready-tasks.py` run against origin
                                                 would have offered the task as READY with
                                                 no branch -- the duplicate-dispatch input)

Attempt 1 of this program compared every spawn against the LATEST publication of each file
and reported 177 violations over 60 spawns spanning ten days -- i.e. it flagged every fire
that had ever run, because a later fire pushed later.  A detector that says VIOLATION for
everything is exactly as useless as one that says CLEAN for everything (P-22).  The bug is
recorded rather than quietly fixed: see out/audit-live-repo-ATTEMPT1.txt.

HOW IT MEASURES
===============
spawn time  = st_birthtime of `.git/worktrees/<id>/`, the instant the worktree was created.
              Not a log the driver wrote about itself.
task branch = the LAST `checkout: moving from ... to softhouse/...` in that worktree's own
              `logs/HEAD`.  At `git worktree add` time the branch named in the dispatch
              record DOES NOT YET EXIST -- the harness creates the worktree on
              `worktree-agent-<id>` and the worker switches afterwards -- so the mapping
              from worktree to task can only be read from the worktree's reflog, after the
              fact.  This is precisely why no hook at spawn time could have checked it.
origin@S    = the newest entry in the reflog of `refs/remotes/origin/main` whose OWN entry
              time is <= S.  `%gd --date=unix`, never `%ct`: `%ct` is the committer date of
              the commit, and a commit made before the spawn but pushed after it would be
              silently forgiven -- which is the exact shape of both misses on record.

BLIND SPOTS, STATED (P-66)
==========================
1. **Pruned worktrees are invisible.**  `.git/worktrees/<id>/` is deleted when a worktree is
   removed, taking its birth time and its reflog with it.  This audit sees only spawns whose
   worktrees still exist and therefore UNDER-REPORTS.  Run it at batch close, not only at
   fire exit.  `--min-spawns N` makes "I saw fewer subjects than you expected" an error
   rather than a pass.
2. **Reflog expiry** (`gc.reflogExpire`, 90 days by default) makes old spawns unjudgeable.
   They are reported `PRE-HISTORY` and counted separately -- never as clean.
3. **A worktree that never adopted a `softhouse/*` branch** (a probe agent, an abandoned
   worker) cannot be mapped to a task.  Reported `UNMAPPED`, counted separately, never
   silently passed.
4. st_birthtime is APFS/HFS+ specific.  Elsewhere Python falls back to st_ctime;
   `--require-birthtime` refuses to run rather than audit the wrong clock.
5. It cannot distinguish "the driver pushed late" from "the driver never dispatched this
   worker through tasks.json at all".  Both are reported as VIOLATION, which is right for
   an alarm and wrong for a diagnosis; read section C before acting.

USAGE
  push-before-spawn-audit.py [--repo D] [--since ISO8601|EPOCH] [--min-spawns N]
                             [--worktree-glob G] [--require-birthtime] [--quiet]
Exit: 0 clean over what it could see, 1 violation, 2 the audit could not run.
"""
import argparse
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys

CHECKOUT_RE = re.compile(r"checkout: moving from \S+ to (\S+)")


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args),
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def iso(ts):
    return "unknown" if ts is None else datetime.datetime.fromtimestamp(ts).isoformat(
        sep=" ", timespec="seconds")


def worktrees(repo, glob, require_birthtime):
    """[(spawn_epoch, admin_dir_name, task_branch|None)] for every LIVE worktree."""
    d = os.path.join(repo, ".git", "worktrees")
    if not os.path.isdir(d):
        return [], "no %s -- this repo has no linked worktrees" % d
    out, warn = [], None
    for name in sorted(os.listdir(d)):
        if not fnmatch.fnmatch(name, glob):
            continue
        p = os.path.join(d, name)
        st = os.stat(p)
        bt = getattr(st, "st_birthtime", None)
        if bt is None:
            if require_birthtime:
                return [], ("this filesystem reports no st_birthtime and "
                            "--require-birthtime was given; refusing to audit the wrong "
                            "clock")
            bt, warn = st.st_ctime, "st_birthtime unavailable; fell back to st_ctime"
        branch = None
        try:
            for line in open(os.path.join(p, "logs", "HEAD")):
                m = CHECKOUT_RE.search(line)
                if m and m.group(1).startswith("softhouse/"):
                    branch = m.group(1)
        except OSError:
            pass
        out.append((bt, name, branch))
    return sorted(out), warn


def push_reflog(repo):
    """[(push_epoch, commit)] for refs/remotes/origin/main, OLDEST FIRST."""
    rc, out, err = git(repo, "reflog", "show", "refs/remotes/origin/main",
                       "--date=unix", "--format=%H %gd")
    if rc != 0:
        return [], "cannot read the reflog of refs/remotes/origin/main: %s" % err.strip()
    rows = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        sel = parts[1]
        if "@{" not in sel or not sel.endswith("}"):
            return [], ("reflog selector %r is not the expected `<ref>@{<epoch>}` shape "
                        "-- refusing to guess a push time" % sel)
        try:
            rows.append((int(sel.split("@{", 1)[1][:-1].split()[0]), parts[0]))
        except (ValueError, IndexError):
            return [], "could not parse a push time out of reflog selector %r" % sel
    rows.reverse()
    return rows, None


def origin_at(reflog, when):
    """The commit origin/main pointed at, at instant `when`. None if before the reflog."""
    seen = None
    for epoch, commit in reflog:
        if epoch <= when:
            seen = commit
        else:
            break
    return seen


def blob(repo, commit, path):
    rc, out, _ = git(repo, "show", "%s:%s" % (commit, path))
    return out if rc == 0 else None


def judge(repo, commit, branch):
    """What did origin/main say, at `commit`, about this spawn? -> (ok, [reasons])"""
    bad = []
    if blob(repo, commit, ".softhouse/LOCK") is None:
        bad.append("no .softhouse/LOCK on origin -- origin said NO FIRE WAS RUNNING")
    if blob(repo, commit, ".softhouse/RESUME.md") is None:
        bad.append("no in-flight .softhouse/RESUME.md on origin")
    raw = blob(repo, commit, ".softhouse/tasks.json")
    if raw is None:
        bad.append("no .softhouse/tasks.json on origin")
        return False, bad
    try:
        d = json.loads(raw)
    except ValueError as exc:
        bad.append("origin's tasks.json does not parse (%s)" % exc)
        return False, bad
    tasks = d["tasks"] if isinstance(d, dict) and "tasks" in d else d
    hit = [t for t in tasks if isinstance(t, dict) and t.get("branch") == branch]
    if not hit:
        bad.append("origin's dispatch record names NO task with branch %r -- "
                   "`ready-tasks.py` against origin would have offered it as READY with "
                   "no branch (the duplicate-dispatch input P-85 exists to prevent)"
                   % branch)
        tid = branch.split("/")[-1].split("-")[0]
        same = [t for t in tasks if isinstance(t, dict) and t.get("id") == tid]
        if same:
            bad.append("  task %s IS on origin, status=%r, branch=%r -- so the record was "
                       "published but not yet carrying this branch"
                       % (tid, same[0].get("status"), same[0].get("branch")))
    else:
        st = hit[0].get("status")
        if st != "in_progress":
            bad.append("origin's dispatch record has %s status=%r, not in_progress"
                       % (hit[0].get("id"), st))
    return (not bad), bad


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", default="/Users/buv/gerege-nbfi")
    ap.add_argument("--since", default=None,
                    help="ignore spawns before this (ISO8601 or epoch)")
    ap.add_argument("--min-spawns", type=int, default=1)
    ap.add_argument("--worktree-glob", default="agent-*")
    ap.add_argument("--require-birthtime", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)

    since = None
    if a.since:
        try:
            since = float(a.since)
        except ValueError:
            since = datetime.datetime.fromisoformat(a.since).timestamp()

    print("push-before-spawn audit -- repo %s" % repo)
    print("  SELECTOR: LIVE worktree admin dirs matching %r under .git/worktrees/%s"
          % (a.worktree_glob,
             "" if since is None else ", spawned at or after %s" % iso(since)))
    print("  It asks, for each spawn: what did origin/main SAY at that instant?")
    print("  BLIND SPOT: pruned worktrees are gone and invisible; this UNDER-REPORTS.")

    wts, warn = worktrees(repo, a.worktree_glob, a.require_birthtime)
    if warn:
        print("  WARNING: %s" % warn)
    if since is not None:
        wts = [r for r in wts if r[0] >= since]
    if len(wts) < a.min_spawns:
        print("\nA. SPAWNS SEEN (%d)" % len(wts))
        print("\nAUDIT COULD NOT RUN: saw %d spawns, --min-spawns %d. A check that "
              "inspected too few subjects must not print PASS (P-22)."
              % (len(wts), a.min_spawns))
        return 2

    reflog, why = push_reflog(repo)
    if why:
        print("\nAUDIT COULD NOT RUN: %s" % why)
        return 2

    print("\nA. SPAWNS SEEN (%d), each judged against origin/main AS OF ITS OWN INSTANT"
          % len(wts))
    viol = pre = unmapped = clean = 0
    details = []
    for t, name, branch in wts:
        commit = origin_at(reflog, t)
        if commit is None:
            pre += 1
            state = "PRE-HISTORY (no surviving reflog entry at or before this spawn)"
        elif branch is None:
            unmapped += 1
            state = "UNMAPPED (this worktree never adopted a softhouse/* branch)"
        else:
            ok, bad = judge(repo, commit, branch)
            if ok:
                clean += 1
                state = "published in time (origin %s carried %s in_progress)" % (
                    commit[:8], branch)
            else:
                viol += 1
                state = "VIOLATION vs origin %s" % commit[:8]
                details.append((t, name, branch, commit, bad))
        print("   %s  %-28s %-46s %s" % (iso(t), name, branch or "-", state))

    if details:
        print("\nB. THE VIOLATIONS, IN FULL")
        for t, name, branch, commit, bad in details:
            print("   %s  %s  (%s)" % (iso(t), name, branch))
            print("      origin/main was %s at that instant" % commit)
            for b in bad:
                print("      - %s" % b)

    print("\nC. VERDICT")
    print("   clean=%d  VIOLATION=%d  pre-history=%d  unmapped=%d  (of %d live worktrees)"
          % (clean, viol, pre, unmapped, len(wts)))
    if viol:
        print("   For each violation window, origin's HEAD was an ACTIVE LIE to the next "
              "orchestrator (P-85).")
        return 1
    if clean == 0:
        print("   NOTHING WAS ACTUALLY JUDGED -- every subject was pre-history or "
              "unmapped. This is not a pass (P-22).")
        return 2
    print("   No violation among the %d spawns this audit could judge." % clean)
    print("   THIS IS NOT ENFORCEMENT. Nothing prevented a violation; this run only "
          "failed to find one, over subjects that still exist (P-45).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
