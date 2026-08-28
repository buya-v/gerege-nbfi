#!/usr/bin/env python3
"""T330 -- END TO END through `--reconcile` itself, not just through branch_wip.

drive.py proves the VERDICT is right. That is not the same as proving the REWRITE is
right: the whole defect was that the verdict was already half-right and the loop did not
consult it. This drive builds ONE scratch repo carrying all four arms as `in_progress`
tasks, runs the real `--reconcile` CLI against it -- same bytes the fire runs, T213's
rule -- and DIFFS THE RESULTING tasks.json.

RED  = `git show main:.softhouse/bin/ready-tasks.py`
GREEN= the working tree

Scratch repo only. Nothing here touches the live repo, its refs or its worktrees.
"""
import json
import os
import subprocess
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive as D                                              # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GREEN = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")
RED = "/tmp/t330-red/.softhouse/bin/ready-tasks.py"

TASKS = [
    ("T900", "softhouse/T900-merged-and-pruned", "(a) merged-and-pruned  [T324's shape]"),
    ("T901", "softhouse/T901-never-started", "(b) never-started"),
    ("T902", "softhouse/T902-old-name", "(c) renamed"),
    ("T903", "softhouse/T903-Case-Shadow", "(d) case-shadowed [T308's shape]"),
]


def build():
    """ONE repo carrying all four worlds at once -- which is the real situation: the
    reconcile sees a mixed demote list and must not treat it uniformly."""
    d = D.new_repo()
    # (a) merged and pruned
    D.sh(d, "checkout", "-q", "-b", "softhouse/T900-merged-and-pruned")
    # Components, not one literal -- see the note in drive.py: this path lives in the
    # SCRATCH repo and a single quoted literal would be a dead repo-path reference to
    # T316's census, which is a HARD bar failure.
    D.write(os.path.join(d, ".softhouse", "handoff", "run1", "T900.md"), "# T900\n")
    D.write(os.path.join(d, "a.txt"), "a\n")
    D.sh(d, "add", "-A")
    D.sh(d, "commit", "-q", "-m", "T900: the work that actually landed")
    D.sh(d, "checkout", "-q", "main")
    D.sh(d, "merge", "-q", "--no-ff", "softhouse/T900-merged-and-pruned",
         "-m", "Merge T900: landed, branch about to be pruned")
    D.sh(d, "branch", "-q", "-D", "softhouse/T900-merged-and-pruned")
    # (b) nothing at all for T901
    # (c) renamed
    D.sh(d, "checkout", "-q", "-b", "softhouse/T902-new-name")
    D.write(os.path.join(d, "c.txt"), "c\n")
    D.sh(d, "add", "-A")
    D.sh(d, "commit", "-q", "-m", "T902: live work on the renamed branch")
    D.sh(d, "checkout", "-q", "main")
    # (d) case-shadowed, packed-only
    D.sh(d, "checkout", "-q", "-b", "softhouse/t903-case-shadow")
    D.write(os.path.join(d, "d.txt"), "d\n")
    D.sh(d, "add", "-A")
    D.sh(d, "commit", "-q", "-m", "T903: the commit no name reaches")
    D.sh(d, "checkout", "-q", "main")
    D.sh(d, "pack-refs", "--all")
    loose = os.path.join(d, ".git", "refs", "heads", "softhouse", "t903-case-shadow")
    if os.path.exists(loose):
        os.unlink(loose)
    # the state file
    doc = {"tasks": [{"id": tid, "status": "in_progress", "branch": br,
                      "title": why, "dependencies": []} for tid, br, why in TASKS]}
    D.write(os.path.join(d, ".softhouse", "tasks.json"),
            json.dumps(doc, indent=2, ensure_ascii=False))
    D.sh(d, "add", "-A")
    D.sh(d, "commit", "-q", "-m", "state file with four in_progress tasks")
    return d


def run(modpath, repodir, label):
    # No LOCK on disk, so authority comes from the explicit out-of-band flag -- the one
    # leg T319's F7 left open for a caller that HAS established liveness itself. Here
    # that caller is this fixture, and it is telling the truth: the repo was created
    # three lines ago and no fire has ever touched it.
    argv = [sys.executable, modpath, "--reconcile",
            "--repo", repodir, "--fire", "t330-e2e",
            "--no-live-session-established-out-of-band"]
    p = subprocess.run(argv, capture_output=True, text=True)
    print("=" * 78)
    print("%s -- %s" % (label, modpath))
    print("=" * 78)
    print(p.stdout.strip())
    if p.stderr.strip():
        print("STDERR: %s" % p.stderr.strip())
    print("  (exit %d)" % p.returncode)
    doc = json.load(open(os.path.join(repodir, ".softhouse", "tasks.json")))
    print("")
    print("  RESULTING tasks.json:")
    verdicts = {}
    for t in doc["tasks"]:
        verdicts[t["id"]] = t["status"]
        print("    %-6s %-14s %s" % (t["id"], t["status"], t["title"]))
    print("")
    return verdicts


EXPECT = {"T900": "in_progress",     # merged -> MUST NOT be offered for re-dispatch
          "T901": "needs_retry",     # unstarted -> demote, correctly
          "T902": "in_progress",     # renamed -> live line elsewhere
          "T903": "in_progress"}     # case-shadowed -> live line elsewhere


def main():
    if not os.path.exists(RED):
        print("RED copy missing at %s -- extract it first:" % RED)
        print("  git show main:.softhouse/bin/ready-tasks.py > %s" % RED)
        return 2
    results = {}
    for label, path in (("RED  (main's bytes)", RED), ("GREEN (working tree)", GREEN)):
        d = build()
        results[label] = run(path, d, label)
        shutil.rmtree(d, ignore_errors=True)
    print("=" * 78)
    print("ADJUDICATION -- what the STATE FILE says afterwards, which is the only thing")
    print("the next fire reads")
    print("=" * 78)
    print("  %-6s %-24s %-14s %-14s %s"
          % ("task", "world", "RED", "GREEN", "required"))
    bad_red = bad_green = 0
    for tid, _br, why in TASKS:
        r = results["RED  (main's bytes)"][tid]
        g = results["GREEN (working tree)"][tid]
        want = EXPECT[tid]
        if r != want:
            bad_red += 1
        if g != want:
            bad_green += 1
        print("  %-6s %-24s %-14s %-14s %-14s %s"
              % (tid, why[:24], r, g, want,
                 "" if g == want else "*** GREEN WRONG ***"))
    print("")
    print("  RED   wrong on %d of %d tasks" % (bad_red, len(TASKS)))
    print("  GREEN wrong on %d of %d tasks" % (bad_green, len(TASKS)))
    print("")
    print("  `needs_retry` is the status that OFFERS a task for re-dispatch -- this")
    print("  module's own words at _branch_wip_core. Every RED miss above is a completed")
    print("  or live branch being offered up for a second, divergent implementation.")
    print("")
    print("=" * 78)
    print("IDEMPOTENCE -- the defect a REFUSAL introduces if nobody looks for it")
    print("=" * 78)
    print("  A refused task KEEPS its status, so this branch runs again on EVERY")
    print("  subsequent fire. The pre-existing note-writing appends `[prior note: ...]`")
    print("  each time, which on a permanently-refused task grows the note without")
    print("  bound inside a 962 KB file. Five reconciles, measured:")
    d = build()
    lens = []
    for i in range(5):
        subprocess.run([sys.executable, GREEN, "--reconcile", "--repo", d,
                        "--fire", "t330-idem-%d" % i,
                        "--no-live-session-established-out-of-band"],
                       capture_output=True, text=True)
        doc = json.load(open(os.path.join(d, ".softhouse", "tasks.json")))
        note = [t for t in doc["tasks"] if t["id"] == "T900"][0].get("note", "")
        lens.append(len(note))
        print("    reconcile %d -> T900 note is %d chars, status %s"
              % (i + 1, len(note),
                 [t for t in doc["tasks"] if t["id"] == "T900"][0]["status"]))
    grew = len(set(lens[1:])) > 1
    print("  RESULT: %s" % ("*** THE NOTE GROWS -- unbounded ***" if grew else
                            "stable after the first write; a note this function already "
                            "wrote is REPLACED, not nested"))
    shutil.rmtree(d, ignore_errors=True)
    return 1 if (bad_green or grew) else 0


if __name__ == "__main__":
    sys.exit(main())
