#!/usr/bin/env python3
"""T319 -- F5. THE MEASUREMENT THE FIX RESTS ON.

T309's in-session discriminator is "was this id `in_progress` in the tasks.json blob
committed when this fire took the lock". T302 proved that predicate demotes seven LIVE
workers of fire 20260823-140001, because that fire RE-DISPATCHED seven of the eight ids
it inherited five minutes after taking the lock.

The replacement predicate proposed by T319 adds a second, conjunctive term:
    demotable  <=>  id was in_progress at the lock commit
                    AND this fire has not written to that task's record since.

That second term is only sound if a dispatch NECESSARILY rewrites the dispatched task's
record. This probe measures exactly that, on the real incident, key by key.  It reads
the repo and writes nothing.

Usage:  python3 .softhouse/capture/t319-reconciler-f5/probe-objdiff.py [repo]
"""
import json
import os
import subprocess
import sys

REPO = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
LOCK_COMMIT = "5428c0a4"      # 14:00:08 fire 20260823-140001 takes its lock
DISP_COMMIT = "5964ab54"      # 14:05:01 same fire, "DISPATCH ... batch 1 -- 8 workers"


def blob(sha):
    out = subprocess.run(["git", "-C", REPO, "show",
                          "%s:.softhouse/tasks.json" % sha],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("could not read tasks.json at %s: %s" % (sha, out.stderr.strip()))
    return {t["id"]: t for t in json.loads(out.stdout)["tasks"]}


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def main():
    lock, disp = blob(LOCK_COMMIT), blob(DISP_COMMIT)
    ip_lock = {i for i, t in lock.items() if t.get("status") == "in_progress"}
    ip_disp = {i for i, t in disp.items() if t.get("status") == "in_progress"}
    print("repo: %s" % REPO)
    print("lock commit %s -- in_progress (%d): %s"
          % (LOCK_COMMIT, len(ip_lock), " ".join(sorted(ip_lock))))
    print("disp commit %s -- in_progress (%d): %s"
          % (DISP_COMMIT, len(ip_disp), " ".join(sorted(ip_disp))))
    both = sorted(ip_lock & ip_disp)
    print()
    print("T309's PREDICATE (term 1 alone): %d demotable  -- %s" % (len(both), " ".join(both)))
    print("CORRECT ANSWER at the dispatch commit: 0 -- every one is a live worker.")
    print()
    print("T319 TERM 2 -- has this fire written to the task's record since the lock?")
    print("%-8s  %-9s  %s" % ("id", "UNTOUCHED", "keys this fire rewrote"))
    untouched = []
    for i in both:
        same = canon(lock[i]) == canon(disp[i])
        keys = sorted(set(lock[i]) | set(disp[i]))
        changed = [k for k in keys if lock[i].get(k) != disp[i].get(k)]
        print("%-8s  %-9s  %s" % (i, same, ", ".join(changed) or "(none)"))
        for k in changed:
            print("            %-14s %s" % (k, repr(lock[i].get(k))[:60]))
            print("            %-14s %s" % ("", repr(disp[i].get(k))[:60]))
        if same:
            untouched.append(i)
    print()
    print("T319 PREDICATE (term 1 AND term 2): %d demotable -- %s"
          % (len(untouched), " ".join(untouched) or "none"))
    print()
    if untouched:
        print("RESULT: TERM 2 IS INSUFFICIENT -- %d id(s) survive both terms and they are "
              "live workers." % len(untouched))
        return 1
    print("RESULT: TERM 2 HOLDS on the real incident -- every re-dispatched id was "
          "rewritten by the dispatch, so all %d are withheld." % len(both))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
