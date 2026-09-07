#!/usr/bin/env python3
"""T536 -- THE THIRD REPAIR THE TOOL DID NOT NAME: REWORD THE NOTE.

T527 tells its reader the repair is one of two things: push the branch, or correct the
note to say UNRECOVERED. T528 F-1 found a third, and the driver reproduced it on the real
record in a throwaway worktree:

    T509's note on `main` reads
        "landed 857dd4d8 on softhouse/T509-ledgerguard-blindspot (merge base 10baca08)"
    Change EXACTLY  `(merge base 10baca08)` -> `(merge-base commit 10baca08)`.

Under T527, `merge[ -]base <sha>` was the REFERENCE anchor and `commit <sha>` was a
LANDING anchor, so one word moved `UNBACKED-BRANCH T509` out of the findings and into the
waivers -- 21 findings became 20. The `UNBACKED-COMMIT` for `857dd4d8` survived, so it was
a partial defence, not none; but the branch claim was silenced by a rewrite that changed
no fact.

This probe runs the REAL record twice -- once as written, once with that one substitution
-- WITHOUT touching `tasks.json` on disk (it patches `load_records` in memory; the driver
did it by editing a throwaway copy and restoring it). It asserts the reword changes
NOTHING, and, as an anti-vacuity control, that the substitution really did land in the
record it graded.

Usage: python3 t536-reword.py [repo]
"""
import copy
import importlib.util
import os
import sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
spec = importlib.util.spec_from_file_location(
    "cb", os.path.join(REPO, ".softhouse", "bin", "check-branch-published.py"))
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

BEFORE = "(merge base 10baca08)"
AFTER = "(merge-base commit 10baca08)"
SUBJECT = "softhouse/T509-ledgerguard-blindspot"
BASELINE = os.path.join(REPO, cb.DEFAULT_BASELINE)

_real = cb.load_records
substitutions = [0]


def reworded(repo):
    out = []
    for source, t in _real(repo):
        if str(t.get("id")) == "T509":
            t = copy.deepcopy(t)
            n = t.get("note")
            if isinstance(n, list):
                t["note"] = [x.replace(BEFORE, AFTER) if isinstance(x, str) else x
                             for x in n]
                substitutions[0] += sum(BEFORE in x for x in n if isinstance(x, str))
            elif isinstance(n, str):
                substitutions[0] += n.count(BEFORE)
                t["note"] = n.replace(BEFORE, AFTER)
        out.append((source, t))
    return out


def summarise(res):
    return sorted((f[1], f[2], f[4]) for f in res["findings"])


print("as written:")
plain = summarise(cb.check(REPO, BASELINE))
print("  %d finding(s); T509 branch claim present: %s"
      % (len(plain), ("UNBACKED-BRANCH", "T509", SUBJECT) in plain))

cb.load_records = reworded
print()
print("with %r -> %r (one word):" % (BEFORE, AFTER))
rw = summarise(cb.check(REPO, BASELINE))
print("  %d finding(s); T509 branch claim present: %s"
      % (len(rw), ("UNBACKED-BRANCH", "T509", SUBJECT) in rw))

fails = 0
print()
if substitutions[0] < 1:
    # ANTI-VACUITY. If the phrase is no longer in the record, this probe proves nothing
    # and must say so rather than printing a green it did not earn.
    print("*** VACUOUS: %r does not appear in T509's note any more. This probe graded a"
          % BEFORE)
    print("    record it did not change. Re-point it at the phrasing the record uses.")
    fails += 1
else:
    print("substitutions actually applied: %d" % substitutions[0])
if plain != rw:
    print("*** BREAK: the reword changed the verdict.")
    for x in sorted(set(plain) - set(rw)):
        print("    silenced by the reword: %s" % (x,))
    for x in sorted(set(rw) - set(plain)):
        print("    raised by the reword   : %s" % (x,))
    fails += 1
else:
    print("IDENTICAL: the reword silences nothing. `merge-base commit X` is a base "
          "citation")
    print("whether or not the word `commit` is in it, and T536 makes LANDING earned "
          "rather than")
    print("assumed, so a paraphrase has nothing to fall through to.")
sys.exit(1 if fails else 0)
