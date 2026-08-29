#!/usr/bin/env python3
"""T350 -- drive `branch_wip()` + `reconcile_action()` over the SIX real cases.

WHICH BYTES ARE UNDER TEST.  The module is imported from a path given on the
command line, so the SAME file the fire runs is the file driven -- RED against
the tree at `main`, GREEN against this worker's tree.  T213's rule: the fixture
and the fire must run the same bytes, not a copy that drifts.

    python3 20-drive.py <path-to-ready-tasks.py> <label>

Every case names a fixture `main` sha and the refs that must exist beside it.
The fixture is rebuilt per case, because the whole point is that the verdict
depends on WHERE MAIN IS, and today's main hides all four defects.
"""
import importlib.util
import os
import subprocess
import sys

FIX = "/tmp/t350-fixture"

# (label, fixture main sha, {refname: sha or None to delete}, recorded branch, tid, what should happen)
CASES = [
    ("A/T339  name-only rescue ref, work NOT on main",
     "ac72956b9a7503356eaca8ffb88fb5c5a911870e",
     {"softhouse/rescued-t339-base-20260828-080001":
      "7e8825b9f345d7f14399bc5fdb57c082b759ddcb",
      "softhouse/T339-review-t270": None},
     "softhouse/T339-review-t270", "T339",
     "MUST DEMOTE -- the only ref is named for a WORKTREE, its diff vs main is a "
     "deletion in .softhouse/reviews/A2-11/ plus .t347-postcheckout-marker, and "
     "nothing in it names t339."),

    ("B/T431  branch head IS the driver's dispatch commit",
     "280817a1ffed480321ebf6318d5a363457f7ba72",
     {"softhouse/T431-t407-conditions":
      "280817a1ffed480321ebf6318d5a363457f7ba72"},
     "softhouse/T431-t407-conditions", "T431",
     "MUST DEMOTE -- zero commits ahead of main, ancestor of main only because it "
     "IS main, and nothing bearing t431 is on main. C-T407-1 was UNSTARTED."),

    ("C/T421  branch pruned post-merge, 33 files ON MAIN",
     "HEAD",
     {"softhouse/T421-t406-conditions": None},
     "softhouse/T421-t406-conditions", "T421",
     "MUST REFUSE -- .softhouse/capture/t421-t406-conditions/ is tracked on main."),

    ("D/T428  branch DELETED, 35 files ON MAIN",
     "HEAD",
     {"softhouse/T428-review-t421": None},
     "softhouse/T428-review-t421", "T428",
     "MUST REFUSE -- .softhouse/reviews/t428-review-t421/ is tracked on main."),

    ("E/T351  CONTROL: live ref carries REAL t351 content",
     "HEAD",
     {"softhouse/T351-old-name": None},
     "softhouse/T351-old-name", "T351",
     "MUST REFUSE -- softhouse/T351-progress-accounting is 1 commit ahead of main "
     "and its diff names .softhouse/capture/t351-progress-accounting/. Demoting "
     "would fork a line that still exists."),

    ("F/T442  CONTROL: live ref carries REAL t442 content",
     "HEAD",
     {"softhouse/T442-old-name": None},
     "softhouse/T442-old-name", "T442",
     "MUST REFUSE -- softhouse/T442-t440-conditions is 1 commit ahead of main and "
     "its diff names .softhouse/capture/t424/instruments/t442-*."),
]


def git(*a):
    p = subprocess.run(["git", "-C", FIX] + list(a), capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def load(path):
    spec = importlib.util.spec_from_file_location("rt_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if len(sys.argv) < 3:
        print("usage: 20-drive.py <path-to-ready-tasks.py> <label>", file=sys.stderr)
        return 64
    path, label = os.path.abspath(sys.argv[1]), sys.argv[2]
    rc, head, _ = git("rev-parse", "HEAD")
    print("=" * 78)
    print("T350 DRIVE -- %s" % label)
    print("module under test: %s" % path)
    digest = subprocess.run(["shasum", "-a", "256", path], capture_output=True,
                            text=True).stdout.split()[0]
    print("module sha256:     %s" % digest)
    print("fixture:           %s (clone HEAD %s)" % (FIX, head[:9]))
    print("=" * 78)
    verdicts = []
    for label_c, main_sha, refs, branch, tid, expect in CASES:
        if main_sha == "HEAD":
            main_sha = head
        git("checkout", "--quiet", "--detach", main_sha)
        git("branch", "-f", "main", main_sha)
        for name, target in refs.items():
            if target is None:
                git("update-ref", "-d", "refs/heads/" + name)
            else:
                git("update-ref", "refs/heads/" + name, target)
        mod = load(path)
        mod.set_repo(FIX)
        mod._LANDED = ("uncached", None)
        mod._REF_INDEX = ("uncached", None)
        if hasattr(mod, "_MAINPATHS"):
            mod._MAINPATHS = ("uncached", None)
        kind, text = mod.branch_wip(branch, tid)
        action = mod.reconcile_action(kind)
        print()
        print("-" * 78)
        print("CASE %s" % label_c)
        print("  fixture main   : %s" % main_sha[:9])
        print("  recorded branch: %s" % branch)
        print("  task id        : %s" % tid)
        print("  EXPECTED       : %s" % expect)
        print("  ---")
        print("  WIP kind       : %s" % kind)
        print("  RECONCILE WOULD: %s" % action)
        print("  note           : %s" % text)
        verdicts.append((label_c, kind, action))
    print()
    print("=" * 78)
    print("SUMMARY -- %s" % label)
    for lc, kind, action in verdicts:
        print("  %-52s %-26s %s" % (lc[:52], kind, action.split(" --")[0]))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
