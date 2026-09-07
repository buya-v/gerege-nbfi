#!/usr/bin/env python3
"""T537 item 1 -- A THIRD SET OF PHRASINGS, invented against T536's classifier.

The recurring argument T527 -> T528 -> T536 is F-1: `LANDING` was the DEFAULT anchor
classification, so ONE reworded word laundered a genuinely missing branch into the
waivers. T527 closed one phrasing (`merge base X`). T528 broke it with a second
(`merge-base commit X`). T536 answers by INVERTING the default: extraction no longer
carries a role, and only `LANDING_PROMOTIONS` / `LANDING_BINDINGS` can promote, subject
to dominant vetoes.

THE QUESTION THIS SCRIPT ASKS: is that a CLASS or a LONGER LIST? Every note below is a
BASE / REFERENCE / REFUTATION citation -- none of them asserts, truthfully, that this
task's work is on main -- and every one is written in an idiom sampled from REAL notes in
this repo's own `.softhouse/tasks.json`. Each is placed on the SAME fixture, with the SAME
genuinely-absent branch `softhouse/TN-never-pushed`, and the SAME sha, which is
`origin/main` itself and therefore trivially an ancestor of `origin/main`.

    exit 2 = the guard REFUSED -> the phrasing did NOT launder the branch (good)
    exit 0 = the guard called it CLEAN -> the missing branch was WAIVED (a BREAK)

Run:  python3 t537-attack.py <path-to-worktree-at-18c64389>
"""
import importlib.util
import os
import sys
import tempfile

WT = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "cbp", os.path.join(WT, ".softhouse", "bin", "check-branch-published.py"))
cbp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cbp)

# Each entry: (name, note-template, why-this-is-NOT-a-landing-claim, real-note-idiom-source)
CASES = [
    ("N1-merges-clean-into-main-at",
     "COMPLETE, merges clean into main@%s",
     "'merges clean into main@X' says the branch WILL merge, i.e. it has NOT merged. X "
     "is main's tip, not the work.",
     "T374 note, verbatim shape: 'COMPLETE, 4 commits, merges clean into main@faf5746e'"),

    ("N2-origin-main-tip-at-dispatch",
     "origin/main tip %s at dispatch; my work is still on the branch",
     "'main tip X' is a citation of MAIN's tip. It is the one sha guaranteed to be an "
     "ancestor of main whether or not a line of the work landed -- exactly R5's argument "
     "in a phrasing R5 does not cover.",
     "T335 'main, head d09585f58' / T375 'main, head 2422adc96' idiom, with `tip` for "
     "`head` -- and `head` IS vetoed while `tip` is a promotion."),

    ("N3-rebased-on-main-at",
     "DONE, rebased on main @ %s",
     "a rebase target is a base. BASE_WORDS carries `rebased?\\s+onto` and `based?\\s+on`; "
     "'rebased on' matches NEITHER (no word boundary before 'based' inside 'rebased').",
     "T375 '17 commits over main' / rebase vocabulary used throughout the run notes"),

    ("N4-refutation-read-as-assertion",
     "CORRECTION: the earlier note claiming this landed %s is WITHDRAWN and FALSE -- "
     "nothing from this task ever reached origin",
     "this note DENIES that the work landed. The classifier has no notion of polarity, "
     "so the denial reads as the assertion.",
     "T503's own note: 'THE DRIVER'S EARLIER NOTE ON THIS TASK WAS WRONG AND IS "
     "WITHDRAWN.' -- this repo writes corrections in exactly this voice"),

    ("N5-other-task-named-AFTER-without-a-preposition",
     "the merge commit %s that T400 landed is already on main; mine is not",
     "the sha belongs to T400. V2's TRAILING arm only fires on an attribution "
     "preposition (by/for/from/belonging to/owned by); 'that T400 landed' is none of "
     "them, and the LEADING arm looks only to the left of the sha.",
     "T528's own case L shape ('supersedes the work merged as X by T400') with the "
     "preposition dropped -- the narrowing T536 chose on purpose"),

    ("N6-verified-against-main-at",
     "COMPLETE, verified against main @ %s",
     "a verification TARGET is a base citation.",
     "T509 'DRIVER-VERIFIED BY EXECUTION' + T374 'main@faf5746e'"),

    ("N7-tip-of-the-base-branch",
     "stacked work; base branch tip %s, my commits sit above it",
     "'base branch tip X' names the BASE. `stacked?\\s+on` is a veto word but 'stacked "
     "work;' is not, and `tip X` promotes.",
     "T515 'stack 78a17873/2e1a09df (T501) -> 5c4233fc (T510)' vocabulary"),

    ("N8-merged-at-negated",
     "NOT merged at %s -- this branch is UNRECOVERED and must be re-run",
     "an explicit negation of a merge claim. Polarity again, from the other side of the "
     "same sentence.",
     "T536's own note on itself: 'branch ... NEVER REACHED origin ... Nothing to rescue.'"),
]


# ANTI-VACUITY. If the fixture went CLEAN for a reason unrelated to the note -- a branch
# that was never really absent, a checker that waives everything -- the block above would
# be worthless. These two run on the SAME fixture and MUST both go RED.
CONTROLS = [
    ("CTL-no-sha-at-all", "done and scope-checked; the branch was deleted, trust me"),
    ("CTL-T527s-own-R5-phrasing", "done and scope-checked (merge base %s)"),
    ("CTL-T528s-own-F1-phrasing", "done; merge-base commit %s, scope clean"),
]


def main():
    base = tempfile.mkdtemp(prefix="t537-attack-")
    T = lambda **kw: dict({"id": "TN", "status": "done"}, **kw)
    breaks, held = [], []
    print("=" * 78)
    print("T537 item 1 -- THIRD-PHRASING ATTACK on T536's LANDING classifier")
    print("=" * 78)
    print("fixture: `softhouse/TN-never-pushed` is a branch NO origin has ever heard of.")
    print("the sha in every note is origin/main's own tip -- an ancestor of origin/main")
    print("by construction, and therefore able to satisfy the merged-and-pruned waiver")
    print("the moment the classifier reads it as this task's LANDING.")
    print()
    for name, tpl, why, src in CASES:
        d = os.path.join(base, name)
        os.makedirs(d)
        repo, f = cbp._fixture(d)
        note = tpl % f["main"]
        cbp._write_tasks(repo, [T(id="TN", branch="softhouse/TN-never-pushed",
                                  note=note)])
        rc, text = cbp._run_check(repo, None)
        waived = "merged-and-pruned, PROVED): 1" in text
        verdict = "BREAK -- LAUNDERED" if rc == 0 else "held (REFUSED)"
        (breaks if rc == 0 else held).append((name, note, verdict, why, src))
        print("%-46s rc=%d  waived=%-5s  %s" % (name, rc, waived, verdict))
        print("    note: %s" % note)
        if rc == 0:
            for ln in text.splitlines():
                if "WAIVED (merged" in ln or "TN " in ln or "ancestor of origin/main" in ln:
                    print("    | %s" % ln.strip())
        print()

    print("=" * 78)
    print("RESULT: %d of %d third phrasings LAUNDERED a genuinely missing branch."
          % (len(breaks), len(CASES)))
    print("=" * 78)
    for name, note, _v, why, src in breaks:
        print()
        print("BREAK %s" % name)
        print("  note text : %s" % note)
        print("  why this is not a landing claim: %s" % why)
        print("  idiom source: %s" % src)
    print()
    print("HELD (%d):" % len(held))
    for name, note, _v, _w, _s in held:
        print("  %-46s %s" % (name, note))

    print()
    print("=" * 78)
    print("ANTI-VACUITY CONTROLS -- same fixture, same absent branch. All must be rc=2,")
    print("or the block above proves nothing about the notes.")
    print("=" * 78)
    bad = 0
    for name, tpl in CONTROLS:
        d = os.path.join(base, name)
        os.makedirs(d)
        repo, f = cbp._fixture(d)
        note = tpl % f["main"] if "%s" in tpl else tpl
        cbp._write_tasks(repo, [T(id="TN", branch="softhouse/TN-never-pushed",
                                  note=note)])
        rc, text = cbp._run_check(repo, None)
        ok = rc == 2 and "UNBACKED-BRANCH" in text
        bad += 0 if ok else 1
        print("%-46s rc=%d  %s" % (name, rc, "RED as required" if ok else "*** VACUOUS"))
        print("    note: %s" % note)
    print()
    print("controls failing: %d (must be 0)" % bad)


if __name__ == "__main__":
    main()
