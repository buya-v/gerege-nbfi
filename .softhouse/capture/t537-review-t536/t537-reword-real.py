#!/usr/bin/env python3
"""T537 item 1, on the REAL RECORD -- the same move T528 made against T527, in a
phrasing T536 has never seen.

T528's F-1 demonstration was: reword T509's real note on `main` from `merge base
10baca08` to `merge-base commit 10baca08` -- ONE WORD -- and `UNBACKED-BRANCH T509`
moves out of the findings and into the waivers. T536 closed that phrasing.

This does the same thing with `origin/main tip <sha> at dispatch`, and it uses the sha
that fire cloud-20260906-2000 measured this evening as T509's REPUBLISHED landing
(`23966a65`, an ancestor of origin/main -- see
.softhouse/observations/2026-09-06-republished-under-new-hash.md). The note below is a
BASE citation: it says main's tip at dispatch, and says in plain words that the work is
still on the branch.

It edits a COPY of tasks.json inside a scratch worktree, runs the checker, and restores.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

WT = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "cbp", os.path.join(WT, ".softhouse", "bin", "check-branch-published.py"))
cbp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cbp)

TASKS = os.path.join(WT, ".softhouse", "tasks.json")
BL = os.path.join(WT, ".softhouse", "capture", "t527-branch-published", "baseline.json")
BACKUP = TASKS + ".t537-backup"

REPUBLISHED = "23966a65"     # measured tonight as T509's landing on origin/main


def report(tag):
    res = cbp.check(WT, BL, timeout=180)
    findings = {(f[1], f[2], f[4]) for f in res["findings"]}
    waived = {(w[1], w[2]) for w in res["waived"] if w[0] == "PRUNED-PROVED"}
    print("%-10s findings=%-3d pruned-proved-waivers=%-3d   T509 branch is: %s"
          % (tag, len(findings), len(waived),
             "A FINDING" if ("UNBACKED-BRANCH", "T509",
                             "softhouse/T509-ledgerguard-blindspot") in findings
             else ("WAIVED" if ("T509", "softhouse/T509-ledgerguard-blindspot") in waived
                   else "absent from both")))
    return findings, waived


def main():
    rc = subprocess.run(["git", "cat-file", "-t", REPUBLISHED], cwd=WT,
                        capture_output=True, text=True)
    print("git cat-file -t %s -> %s" % (REPUBLISHED, rc.stdout.strip() or rc.stderr.strip()))
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", REPUBLISHED, "origin/main"],
                        cwd=WT, capture_output=True, text=True)
    print("git merge-base --is-ancestor %s origin/main -> exit %d (0 = it IS on main)"
          % (REPUBLISHED, rc.returncode))
    print()

    shutil.copy(TASKS, BACKUP)
    try:
        before_f, before_w = report("BEFORE")
        d = json.load(open(TASKS))
        hit = None
        for t in d["tasks"]:
            if t["id"] == "T509":
                hit = t
                break
        assert hit is not None, "T509 not in the record"
        old = hit["note"]
        print()
        print("T509's note, first line, as recorded:")
        print("  %s" % old.splitlines()[0][:140])
        new = ("origin/main tip %s at dispatch; my work is still on the branch and has "
               "NOT been merged." % REPUBLISHED)
        hit["note"] = new
        print()
        print("T509's note, REWORDED by T537 into a base citation that denies landing:")
        print("  %s" % new)
        print()
        with open(TASKS, "w") as fh:
            json.dump(d, fh, indent=1)
        after_f, after_w = report("AFTER")
        print()
        gone = before_f - after_f
        gained = after_w - before_w
        print("findings REMOVED by the rewording: %d" % len(gone))
        for g in sorted(gone):
            print("   -%s" % (g,))
        print("waivers GAINED by the rewording: %d" % len(gained))
        for g in sorted(gained):
            print("   +%s" % (g,))
    finally:
        shutil.move(BACKUP, TASKS)
        print()
        print("tasks.json restored: %s" % (not os.path.exists(BACKUP)))


if __name__ == "__main__":
    main()
