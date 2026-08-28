#!/usr/bin/env python3
"""T330 -- the four-arm drive for branch-absence.

`git rev-parse --verify <branch>` returns the SAME "not found" for four different
worlds.  Three of them are worlds in which work exists and re-dispatching destroys or
duplicates it; one is the world the reconciler assumed unconditionally.

    (a) merged-and-pruned  -- the T324 defect.  Work is on main, branch deleted.
    (b) never-started      -- the only world the old code was right about.
    (c) renamed            -- T302 measured one (T299).  Live line under another name.
    (d) case-shadowed      -- T308's 2026-08-27 defect, T312's hook.  Live line under a
                              case-variant that is PACKED, so neither the filesystem's
                              case-folding nor git's case-SENSITIVE packed-refs match
                              can reach it from the recorded spelling.

EVERY ARM IS BUILT IN A SCRATCH REPO under tempfile.mkdtemp().  Nothing here touches the
live repo, its refs, or its worktrees -- arms (c) and (d) manipulate refs directly and
seven worktrees with live content exist; destroying one is the damage class T318/T324/
T325 are about.

Usage:  drive.py <path-to-ready-tasks.py>       # arm results for THAT copy of the code

RED  = run it against `git show main:.softhouse/bin/ready-tasks.py`.
GREEN= run it against the working tree.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GIT = shutil.which("git")


def sh(cwd, *argv, **kw):
    env = dict(os.environ)
    env.update({"GIT_AUTHOR_NAME": "t330", "GIT_AUTHOR_EMAIL": "t330@example.invalid",
                "GIT_COMMITTER_NAME": "t330", "GIT_COMMITTER_EMAIL": "t330@example.invalid"})
    p = subprocess.run([GIT] + list(argv), cwd=cwd, capture_output=True, text=True, env=env)
    if p.returncode != 0 and not kw.get("allow_fail"):
        raise SystemExit("git %s failed in %s: %s" % (" ".join(argv), cwd, p.stderr))
    return p.stdout.strip()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def new_repo():
    d = tempfile.mkdtemp(prefix="t330-arm-")
    sh(d, "init", "-q", "-b", "main")
    write(os.path.join(d, "seed.txt"), "seed\n")
    sh(d, "add", "-A")
    sh(d, "commit", "-q", "-m", "seed")
    return d


def load_module(path, repo):
    """Fresh module object each call -- ready-tasks.py caches its ref index and (after
    T330) its landed-evidence index for the life of the process, and each arm is a
    DIFFERENT repo.  A shared cache would make arm N answer with arm N-1's refs."""
    binname = "rt_%d" % load_module.n
    load_module.n += 1
    spec = importlib.util.spec_from_file_location(binname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.set_repo(repo)
    return mod


load_module.n = 0


# ---------------------------------------------------------------------- the arms ---
def arm_a_merged_and_pruned():
    """T324, exactly: commit `T900: ...`, merge commit `Merge T900: ...`, handoff on
    main, feature branch deleted afterwards."""
    d = new_repo()
    branch = "softhouse/T900-merged-and-pruned"
    sh(d, "checkout", "-q", "-b", branch)
    write(os.path.join(d, ".softhouse/handoff/run1/T900.md"), "# T900 handoff\n")
    write(os.path.join(d, "work.txt"), "real work\n")
    sh(d, "add", "-A")
    sh(d, "commit", "-q", "-m", "T900: handoff -- the work that actually landed")
    sh(d, "checkout", "-q", "main")
    sh(d, "merge", "-q", "--no-ff", branch, "-m",
       "Merge T900: the work landed and this branch is about to be pruned")
    sh(d, "branch", "-q", "-D", branch)          # THE PRUNE
    return d, branch, "MUST NOT DEMOTE -- the work is on main"


def arm_b_never_started():
    d = new_repo()
    return d, "softhouse/T901-never-started", "MUST DEMOTE -- nothing exists anywhere"


def arm_c_renamed():
    """T302 measured this on T299: the recorded name went stale after a rename and the
    live line was elsewhere.  No merge evidence -- the work has NOT landed."""
    d = new_repo()
    recorded = "softhouse/T902-old-name"
    live = "softhouse/T902-new-name"
    sh(d, "checkout", "-q", "-b", live)
    write(os.path.join(d, "wip.txt"), "uncommitted-elsewhere\n")
    sh(d, "add", "-A")
    sh(d, "commit", "-q", "-m", "T902: work in progress on the renamed branch")
    sh(d, "checkout", "-q", "main")
    return d, recorded, "MUST NOT DEMOTE -- a live line exists at %s" % live


def arm_d_case_shadowed():
    """T308's defect.  The ONLY spelling that exists is a case-variant, and it lives in
    packed-refs, which git matches CASE-SENSITIVELY (branch_sweep.RefIndex._read_packed
    says so in as many words).  So the recorded spelling misses on the loose lookup
    (no such file) AND on the packed lookup (case mismatch) -- byte-identical `absent`
    -- while 1 commit sits on the variant."""
    d = new_repo()
    recorded = "softhouse/T903-Case-Shadow"
    variant = "softhouse/t903-case-shadow"
    sh(d, "checkout", "-q", "-b", variant)
    write(os.path.join(d, "shadow.txt"), "the hidden line\n")
    sh(d, "add", "-A")
    sh(d, "commit", "-q", "-m", "T903: the commit no name reaches")
    sha = sh(d, "rev-parse", "HEAD")
    sh(d, "checkout", "-q", "main")
    # Force it PACKED-ONLY: pack, then delete the loose file by hand so no filesystem
    # case-folding can resolve the recorded spelling.
    sh(d, "pack-refs", "--all")
    loose = os.path.join(d, ".git", "refs", "heads", *variant.split("/"))
    if os.path.exists(loose):
        os.unlink(loose)
    return d, recorded, ("MUST NOT DEMOTE -- packed-only case-variant %s holds %s"
                         % (variant, sha[:9]))


ARMS = [("a", "merged-and-pruned", arm_a_merged_and_pruned),
        ("b", "never-started", arm_b_never_started),
        ("c", "renamed", arm_c_renamed),
        ("d", "case-shadowed", arm_d_case_shadowed)]


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    modpath = os.path.abspath(argv[1])
    print("MODULE UNDER DRIVE: %s" % modpath)
    print("git:               %s" % GIT)
    print("")
    dirs = []
    fails = 0
    for letter, name, build in ARMS:
        d, branch, expectation = build()
        dirs.append(d)
        # sanity: the arm must actually be byte-identical to the others at rev-parse
        p = subprocess.run([GIT, "rev-parse", "--verify", "--quiet", branch + "^{commit}"],
                           cwd=d, capture_output=True, text=True)
        mod = load_module(modpath, d)
        tid = "T90" + {"a": "0", "b": "1", "c": "2", "d": "3"}[letter]
        try:
            kind, text = mod.branch_wip(branch, tid)      # T330 signature
            sigshape = "branch_wip(branch, tid)"
        except TypeError:
            kind, text = mod.branch_wip(branch)           # pre-T330 signature
            sigshape = "branch_wip(branch)  [PRE-T330 -- takes no task id at all]"
        # What reconcile() would DO with that kind, read from the module itself.
        # What reconcile() would DO with that kind -- asked of the module, never assumed.
        # Pre-T330 there is nothing to ask: reconcile()'s `for t in demote:` loop writes
        # `needs_retry` for EVERY task it is handed, whatever branch_wip returned. The
        # kind is printed and never compared. That is the whole defect.
        action = getattr(mod, "reconcile_action", None)
        act = (action(kind) if action else
               "demote to needs_retry  (pre-T330: reconcile() demotes EVERY kind; the "
               "verdict is printed, never compared)")
        print("ARM (%s) %s" % (letter, name.upper()))
        print("  scratch repo   : %s" % d)
        print("  recorded branch: %s" % branch)
        print("  git rev-parse  : rc=%d out=%r   <-- IDENTICAL ACROSS ALL FOUR ARMS"
              % (p.returncode, p.stdout.strip()))
        print("  signature      : %s" % sigshape)
        print("  VERDICT        : %s" % kind)
        print("  ACTION         : %s" % act)
        print("  EXPECTED       : %s" % expectation)
        wrong = ("MUST NOT DEMOTE" in expectation) == act.startswith("demote")
        print("  RESULT         : %s" % ("WRONG  <<<<" if wrong else "correct"))
        if wrong:
            fails += 1
        print("  note           : %s" % text.replace("\n", " ")[:400])
        print("")
    print("ARMS WRONG: %d of %d" % (fails, len(ARMS)))
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
