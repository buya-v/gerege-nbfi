#!/usr/bin/env python3
"""T528 -- adversarial probe of T527's LANDING/REFERENCE classifier.

Each case: a task whose branch is NOT on origin, with a note that names a sha which IS
on origin/main (the fixture's own main tip -- a legitimate "reference" commit, exactly
like a merge base). If the classifier reads that sha as LANDING, the missing branch is
CLEARED -- the T508 defect, reproduced through a different phrasing.

want=2 means "the guard must still refuse". want=0 means the phrasing legitimately
proves landing.
"""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import importlib.util

CB = sys.argv[1]
spec = importlib.util.spec_from_file_location("cb", CB)
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

CASES = [
    # (name, note-template, expected_rc, comment)
    ("A-merge-base-plain",
     "done and scope-checked (merge base {main})", 2, "R5, the shipped control"),
    ("B-merge-base-COMMIT-worded",
     "done; merge-base commit {main}, scope clean", 2,
     "'merge-base commit X' -- the LANDING 'commit X' anchor fires, REFERENCE does not"),
    ("C-branched-from-at",
     "branched from main @ {main}; work is on the branch", 2,
     "'@ X' LANDING anchor over an ordinary base citation"),
    ("D-forked-at",
     "forked at {main}, 3 commits on top", 2, "'@' not present -- control for C"),
    ("E-base-branch-paren",
     "based on softhouse/TP-pushed ({main}) -- stacked on top", 2,
     "branch-then-paren LANDING anchor over a BASE branch and its tip"),
    ("F-rebased-onto",
     "rebased onto {main} after the merge of T400", 2,
     "'onto X' -- no anchor at all, should be UNCLASSIFIED, branch still refused"),
    ("G-review-cites-another-task",
     "reviewed T400 which landed {main}; my own work is on the branch", 2,
     "a REVIEW task citing ANOTHER task's landing commit"),
    ("H-diverges-at",
     "diverges from origin/main at commit {main}", 2,
     "'at commit X' -- LANDING anchor on a divergence point"),
    ("I-genuine-landing",
     "landed {main} on softhouse/TN-never-pushed", 0,
     "the legitimate exemption -- must still PASS"),
    ("J-cherry-picked-from",
     "cherry-picked from {main}", 2, "no anchor"),
    ("K-stack-region-base",
     "stack {main} (T400 base) -> my work", 2,
     "the stack REGION anchor is LANDING; a base named inside it clears the branch"),
    ("L-supersedes",
     "supersedes the work merged as {main} by T400", 2,
     "'merged as X' naming ANOTHER task's merge"),
]


def run():
    base = tempfile.mkdtemp(prefix="t528-attack-")
    fails = 0
    print("%-28s %-4s %-4s %s" % ("case", "got", "want", "verdict"))
    print("-" * 90)
    for name, tmpl, want, comment in CASES:
        d = os.path.join(base, name)
        os.makedirs(d)
        repo, f = cb._fixture(d)
        note = tmpl.format(**f)
        cb._write_tasks(repo, [{"id": "TN", "status": "done",
                                "branch": "softhouse/TN-never-pushed", "note": note}])
        rc, text = cb._run_check(repo, None)
        ok = rc == want
        if not ok:
            fails += 1
        print("%-28s %-4s %-4s %s" % (name, rc, want, "ok" if ok else "*** BREAK ***"))
        print("      note: %s" % note)
        print("      %s" % comment)
        if not ok:
            for ln in text.splitlines():
                if "WAIVED (merged" in ln or "ancestor of" in ln or "UNBACKED" in ln \
                        or "REFUSE" in ln or "CLEAN" in ln:
                    print("      | " + ln.strip())
        print()
    print("%d break(s)" % fails)
    shutil.rmtree(base, ignore_errors=True)
    return fails


sys.exit(1 if run() else 0)
