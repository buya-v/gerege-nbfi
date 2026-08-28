#!/usr/bin/env python3
"""T349 -- replay the CANDIDATE PreToolUse push-gate against the four REAL dispatch
events this program has measured, using the real recorded inputs rather than hypotheticals.

For each event the inputs are:
  * the instant of the batch's first `git worktree add`   (measured, recorded)
  * the commit `origin/main` pointed at at that instant   (reflog of refs/remotes/origin/main)
  * the task ids the batch dispatched                     (diff of the dispatch commit)

Two candidate decision functions are replayed, because they do NOT agree:

  ANCESTOR-GATE  "is local HEAD an ancestor of origin/main?"
                 -- the obvious design, and it is WRONG here.

  CONTENT-GATE   "for the task id named in the Agent prompt, does origin/main's
                 .softhouse/tasks.json already carry it non-`pending` WITH a branch,
                 and does origin/main carry a LOCK and an in-flight RESUME.md?"
                 -- what the obligation actually says.

Ground truth per event is the recorded verdict (COMPLIANT / VIOLATION); the script
prints whether each gate agrees with it.
"""
import json
import subprocess
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/Users/buv/gerege-nbfi"


def git(*a):
    p = subprocess.run(["git", "--git-dir", REPO + "/.git", "--work-tree", REPO] + list(a),
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def show(rev, path):
    rc, out, err = git("show", "%s:%s" % (rev, path))
    return out if rc == 0 else None


def tasks_of(rev):
    raw = show(rev, ".softhouse/tasks.json")
    if raw is None:
        return None
    try:
        d = json.loads(raw)
    except Exception:
        return None
    ts = d["tasks"] if isinstance(d, dict) and "tasks" in d else d
    return {t["id"]: t for t in ts if isinstance(t, dict) and "id" in t}


# ---------------------------------------------------------------- the four events
# All times +0800 (Asia/Ulaanbaatar). Sources are named per field; nothing invented.
EVENTS = [
    dict(name="E1  2026-08-22 fire",
         verdict="VIOLATION",
         lateness_s=101,
         first_spawn="21:58:42", date="2026-08-22",
         origin_at_spawn="fe244198",     # reflog: pushed 21:58:08, next push 22:00:23
         dispatch_commit="fb371fdf",     # reflog: pushed 22:00:23
         src="reflog refs/remotes/origin/main + T265 finding quoted in tasks.json:3367"),
    dict(name="E2  2026-08-28 08:00 fire, batch 5",
         verdict="VIOLATION",
         lateness_s=135,
         first_spawn="10:44:04", date="2026-08-28",
         origin_at_spawn="5301f24b",     # reflog: pushed 09:20:30, next push 10:46:19
         dispatch_commit="59fc41b4",     # reflog: pushed 10:46:19
         src="reflog + .softhouse/capture/t279-lock-partition/audit-this-fire.py"),
    dict(name="E3  2026-08-28 14:00 fire, batch 1",
         verdict="COMPLIANT",
         lateness_s=-66,
         first_spawn="14:06:52", date="2026-08-28",
         origin_at_spawn="9ae2b01c",     # reflog: pushed 14:05:46
         dispatch_commit="9ae2b01c",
         src="observations/20260828-140005-push-before-spawn-measured.md + reflog"),
    dict(name="E4  2026-08-28 16:46 fire, wave 1a (the fire running T349)",
         verdict="COMPLIANT",
         lateness_s=-54,
         first_spawn="16:47:13", date="2026-08-28",
         origin_at_spawn="f6c83157",     # reflog: pushed 16:46:20
         dispatch_commit="f6c83157",
         src="T349 brief + reflog refs/remotes/origin/main"),
]


def batch_task_ids(ev):
    """The tasks the batch dispatched = those the dispatch commit flipped off `pending`."""
    after = tasks_of(ev["dispatch_commit"])
    rc, parents, _ = git("rev-parse", ev["dispatch_commit"] + "^")
    before = tasks_of(parents.strip()) if rc == 0 else None
    if after is None:
        return []
    ids = []
    for tid, t in after.items():
        st = t.get("status")
        br = t.get("branch")
        was = (before or {}).get(tid, {})
        if st not in ("pending", None) and br and (was.get("status") != st or was.get("branch") != br):
            ids.append(tid)
    return sorted(ids)


def ancestor_gate_hindsight(ev):
    """Was the dispatch commit already on origin/main at the spawn instant?
    This is the HINDSIGHT form -- it names a commit the hook cannot know about."""
    rc, _, _ = git("merge-base", "--is-ancestor", ev["dispatch_commit"], ev["origin_at_spawn"])
    if rc == 0:
        return "ALLOW", "dispatch commit %s is an ancestor of origin@spawn %s" % (
            ev["dispatch_commit"], ev["origin_at_spawn"])
    return "DENY", "dispatch commit %s NOT on origin@spawn %s" % (
        ev["dispatch_commit"], ev["origin_at_spawn"])


def ancestor_gate_computable(ev):
    """What the hook could ACTUALLY compute at spawn time: `is local HEAD on origin/main?`.
    The hook cannot name the dispatch commit; it can only look at whatever HEAD is.
    If the driver has not yet COMMITTED the dispatch record, local HEAD is whatever the
    last commit was -- and if that was already pushed, the gate allows the spawn while the
    dispatch record does not exist at all. Reconstructed here from commit timestamps."""
    dc_time = git("log", "-1", "--format=%cI", ev["dispatch_commit"])[1].strip()
    spawn = "%sT%s+08:00" % (ev["date"], ev["first_spawn"])
    existed = dc_time <= spawn
    # what was local HEAD at the spawn instant? the newest commit on the dispatch commit's
    # first-parent chain whose commit time <= spawn
    rc, out, _ = git("log", "--first-parent", "--format=%H %cI", ev["dispatch_commit"])
    head = None
    for line in out.splitlines():
        h, t = line.split()
        if t <= spawn:
            head = h
            break
    if head is None:
        return "UNKNOWN", "could not reconstruct local HEAD at spawn"
    onorigin = git("merge-base", "--is-ancestor", head, ev["origin_at_spawn"])[0] == 0
    note = "dispatch commit %s committed %s (%s at spawn); local HEAD@spawn=%s, on origin=%s" % (
        ev["dispatch_commit"], dc_time, "EXISTED" if existed else "DID NOT EXIST", head[:8], onorigin)
    if not existed:
        note += "  <-- the gate is judging a tree that does not contain the dispatch record"
    return ("ALLOW" if onorigin else "DENY"), note


def content_gate(ev, ids):
    """What the hook could ACTUALLY compute at spawn time, given the task id it can read
    out of the Agent tool_input prompt and the content of origin/main."""
    o = ev["origin_at_spawn"]
    at = tasks_of(o)
    lock = show(o, ".softhouse/LOCK")
    resume = show(o, ".softhouse/RESUME.md")
    reasons = []
    if at is None:
        return "DENY", ["origin/main at spawn carries no parseable .softhouse/tasks.json"]
    if lock is None:
        reasons.append("no .softhouse/LOCK on origin/main -> origin says NO FIRE IS RUNNING")
    if resume is None:
        reasons.append("no .softhouse/RESUME.md on origin/main")
    for tid in ids:
        t = at.get(tid)
        if t is None:
            reasons.append("%s absent from origin's tasks.json" % tid)
        elif t.get("status") in (None, "pending"):
            reasons.append("%s reads status=%r on origin (not dispatched)" % (tid, t.get("status")))
        elif not t.get("branch"):
            reasons.append("%s carries branch=%r on origin" % (tid, t.get("branch")))
    return ("DENY", reasons) if reasons else ("ALLOW", ["all %d dispatched tasks already published non-pending with a branch, LOCK and RESUME.md present" % len(ids)])


print("T349 -- candidate PreToolUse push-gate replayed against %d REAL dispatch events\n" % len(EVENTS))
score = {"ANCESTOR-hindsight": 0, "ANCESTOR-computable": 0, "CONTENT": 0}
for ev in EVENTS:
    ids = batch_task_ids(ev)
    want = "DENY" if ev["verdict"] == "VIOLATION" else "ALLOW"
    ah, ahr = ancestor_gate_hindsight(ev)
    ac, acr = ancestor_gate_computable(ev)
    cg, cr = content_gate(ev, ids)
    score["ANCESTOR-hindsight"] += (ah == want)
    score["ANCESTOR-computable"] += (ac == want)
    score["CONTENT"] += (cg == want)
    print("%s" % ev["name"])
    print("   recorded verdict : %-9s (%+d s vs first spawn)   first spawn %s +0800" % (
        ev["verdict"], ev["lateness_s"], ev["first_spawn"]))
    print("   origin/main@spawn: %s      dispatch commit: %s" % (ev["origin_at_spawn"], ev["dispatch_commit"]))
    print("   batch task ids   : %s" % (", ".join(ids) if ids else "(none recovered)"))
    print("   REQUIRED         : %s" % want)
    print("   ANCESTOR hindsight  : %-5s %s  %s" % (ah, "OK   " if ah == want else "WRONG", ahr))
    print("   ANCESTOR computable : %-5s %s  %s" % (ac, "OK   " if ac == want else "WRONG", acr))
    print("   CONTENT-GATE        : %-5s %s" % (cg, "OK   " if cg == want else "WRONG"))
    for r in cr:
        print("        - %s" % r)
    print("   source: %s" % ev["src"])
    print()

print("SCORE over the 4 recorded events (2 VIOLATION, 2 COMPLIANT):")
for k, v in sorted(score.items()):
    print("   %-20s %d/4 correct" % (k, v))
print()
print("NOTE on ANCESTOR-computable: on E2 it says DENY for the WRONG REASON -- an unrelated")
print("unpushed merge commit happened to be on local main at 10:42:53, 71 s before the spawn.")
print("The dispatch record itself did not exist until 10:46:13. That is luck, not a guard.")
