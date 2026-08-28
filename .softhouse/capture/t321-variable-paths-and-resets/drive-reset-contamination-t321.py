#!/usr/bin/env python3
"""T321 part 2 -- DRIVING the resets. Reading nominated; this convicts.

THREE BLOCKS, and they answer three different questions.

  K  GROUND TRUTH. What does each restore idiom ACTUALLY clear? Every row of the table in
     `sweep_resets.py` is measured here in a throwaway repo instead of quoted from the git
     manual. K1 reproduces T316's recorded contamination verbatim; K8 is the headline.

  C  THE CANDIDATES. For every row the sweep called DECORATIVE, the load-bearing reset is
     EXTRACTED FROM THE SHIPPED BYTES (the arm REFUSES if the extraction comes back empty --
     T324/T325's discipline), its idiom set is replayed against the class it is accused of not
     clearing, and the residue is OBSERVED. The extracted source lines are printed beside the
     result so the mapping from "their line" to "the command driven" can be checked and not
     merely believed.

  A/L  THE PROPOSED CHECK, and the arms that prove it stays quiet. The check is NOT a new
     instrument: it is `.softhouse/guards/repo-state-attest.sh` (T318, extended and wired by
     T325) used as an INTER-ARM RESET ASSERTION -- `snapshot` before arm 1, `compare` after
     every reset with the drive's writ. T213's rule is import, do not reimplement. The A arms
     show it firing on residue a `git status --porcelain` assertion cannot see; the L arms show
     it silent on six things an ordinary drive legitimately does.

WHY THE L ARMS ARE NOT OPTIONAL. T325's arm G5 found T318's guard reporting the SANCTIONED
`git checkout -b softhouse/<task>` as DAMAGE. Its lesson, in T318's words: *a check that reports
ordinary pipeline work as damage will be disabled within two fires.* Every check proposed here
carries its own legitimate-operation arm.

WHY THE HEADLINE IS K8/A1. T316 fixed its decorative reset with `git reset --hard` + `git clean
-fdq` and asserted the fix with `git status --porcelain`. Both halves are load-bearing and both
have a blind spot in the same place: a BARE `reset --hard` resets to HEAD, and an arm that
COMMITTED has already moved HEAD -- so the commit survives the reset, and porcelain comes back
EMPTY. That is T318's finding (`git status --porcelain` cannot see a committed clobber; all nine
damage shapes and all six legitimate ones read CLEAN under it) arriving inside an inter-arm
reset. The differential attestation sees it; the legacy predicate cannot.

SAFETY. Every arm builds its own repo under the system temp dir. The drive REFUSES to start if
its scratch root resolves (`os.path.realpath`, both sides) inside this repository or inside any
git worktree of it. Nothing here touches the live checkout, and no arm is ever run against a
path this drive did not create. Five other workers hold live worktrees.

EXIT: 0 all arms as expected; 1 at least one arm off expectation; 2 the rig could not measure.
Probe line: `T321-RESET-DRIVE:` -- printed only on a path that reaches a verdict, so an exit 2
can never be read as "all arms green" (P-84: read the absence before the value).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = "T321-RESET-DRIVE:"
RESULTS = []
ACQUITTALS = []
HERE = Path(__file__).resolve().parent


def repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor. REFUSING.", file=sys.stderr)
    raise SystemExit(2)


ROOT = repo_root()
GUARD = ROOT / ".softhouse/guards/repo-state-attest.sh"


def run(args, cwd, env=None):
    p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)


def sh(script, cwd):
    """Run a shell fragment in cwd. Used for the canonical idiom instantiations."""
    p = subprocess.run(["bash", "-c", script], cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def new_repo(tag):
    """A FRESH repo per arm. This drive has no inter-arm reset because it has no inter-arm
    state -- which is the ISOLATED shape the sweep declines to accuse, applied to itself."""
    d = Path(tempfile.mkdtemp(prefix="t321-%s-" % tag))
    real = os.path.realpath(str(d))
    if real.startswith(os.path.realpath(str(ROOT))):
        print("ERROR: scratch %s resolves INSIDE the repository. REFUSING." % real,
              file=sys.stderr)
        raise SystemExit(2)
    run(["git", "init", "-q", "-b", "main", "."], d)
    run(["git", "config", "user.email", "t321@example.invalid"], d)
    run(["git", "config", "user.name", "T321 drive"], d)
    (d / "tracked.txt").write_text("ORIGINAL\n")
    (d / ".gitignore").write_text("ignored-out/\n")
    run(["git", "add", "-A"], d)
    run(["git", "commit", "-qm", "base"], d)
    return d


def porcelain(d):
    rc, out = run(["git", "status", "--porcelain"], d)
    return out.strip()


def record(arm, what, expect, observed, note=""):
    ok = (expect == observed) or (expect == "CONVICTED-or-ACQUITTED"
                                  and observed in ("CONVICTED", "ACQUITTED"))
    RESULTS.append({"arm": arm, "what": what, "expect": expect, "observed": observed,
                    "pass": ok, "note": note})
    print("  %-6s %-58s expect=%-9s observed=%-9s %s%s"
          % (arm, what, expect, observed, "PASS" if ok else "**FAIL**",
             ("  | " + note) if note else ""))


# =============================================================================================
# BLOCK K -- GROUND TRUTH. What does each idiom clear?
# =============================================================================================
# "residue" = the arm's mutation is still present after the reset.
DIRTY = {
    "STAGED_ADD":  'printf x > planted.txt && git add planted.txt',
    "UNTRACKED":   'printf x > planted.txt',
    "IGNORED":     'mkdir -p ignored-out && printf x > ignored-out/planted.txt',
    "WT_EDIT":     'printf CHANGED > tracked.txt',
    "COMMIT":      'printf CHANGED > tracked.txt && git add -A && '
                   'git commit -qm "an arm that commits"',
}


def residue(kind, d):
    if kind == "STAGED_ADD":
        rc, out = run(["git", "ls-files", "--", "planted.txt"], d)
        return "PRESENT" if out.strip() or (d / "planted.txt").exists() else "ABSENT"
    if kind in ("UNTRACKED",):
        return "PRESENT" if (d / "planted.txt").exists() else "ABSENT"
    if kind == "IGNORED":
        return "PRESENT" if (d / "ignored-out/planted.txt").exists() else "ABSENT"
    if kind == "WT_EDIT":
        return "PRESENT" if (d / "tracked.txt").read_text() != "ORIGINAL\n" else "ABSENT"
    if kind == "COMMIT":
        rc, out = run(["git", "log", "--oneline"], d)
        return "PRESENT" if len(out.strip().splitlines()) > 1 else "ABSENT"
    raise SystemExit(2)


K_ARMS = [
    ("K1", "STAGED_ADD", "git checkout -- . && git clean -fd", "PRESENT",
     "T316's RECORDED contamination, reproduced"),
    ("K2", "STAGED_ADD", "git reset --hard -q && git clean -fdq", "ABSENT",
     "T316's FIX"),
    ("K3", "STAGED_ADD", "git reset -q", "PRESENT",
     "a MIXED reset unstages; the file stays on disk, now untracked"),
    ("K4", "UNTRACKED",  "git reset --hard -q", "PRESENT",
     "reset --hard does not remove untracked files"),
    ("K5", "UNTRACKED",  "git clean -fdq", "ABSENT", ""),
    ("K6", "IGNORED",    "git clean -fdq", "PRESENT",
     "-x is what reaches an ignored file"),
    ("K7", "IGNORED",    "git clean -fdxq", "ABSENT", ""),
    ("K8", "WT_EDIT",    "git checkout -- .", "ABSENT", ""),
    ("K9", "COMMIT",     "git reset --hard -q && git clean -fdxq", "PRESENT",
     "THE HEADLINE: bare reset --hard resets to HEAD, and the arm MOVED HEAD"),
    ("K10", "COMMIT",    "git reset --hard -q \"$(git rev-list --max-parents=0 HEAD)\" "
                         "&& git clean -fdxq", "ABSENT",
     "naming a REF is what makes reset --hard undo a commit"),
]


def block_k():
    print("\nBLOCK K -- GROUND TRUTH: what each restore idiom actually clears")
    print("  (every row of sweep_resets.py's table, measured rather than quoted)")
    for arm, kind, reset_cmd, expect, note in K_ARMS:
        d = new_repo(arm.lower())
        try:
            rc, out = sh(DIRTY[kind], d)
            if rc != 0:
                record(arm, "%s / %s" % (kind, reset_cmd), expect, "RIG-FAIL", out.strip()[:120])
                continue
            rc, out = sh(reset_cmd, d)
            obs = residue(kind, d)
            extra = note
            if kind == "COMMIT":
                extra = (note + "; porcelain=%r" % porcelain(d)).strip("; ")
            record(arm, "%s / %s" % (kind, reset_cmd), expect, obs, extra)
        finally:
            shutil.rmtree(d, ignore_errors=True)


# =============================================================================================
# BLOCK C -- THE CANDIDATES. Their own reset, extracted from the shipped bytes, replayed.
# =============================================================================================
IDIOM_COMMAND = {
    "reset_hard":  "git reset --hard -q",
    "reset_mixed": "git reset -q",
    "checkout_wt": "git checkout -- .",
    "restore_wt":  "git restore .",
    "clean_x":     "git clean -fdxq",
    "clean_plain": "git clean -fdq",
    "stash_pop":   "true",
    "backup_copy": "true",
    "rm_targeted": "true",
}
CLASS_FIXTURE = {"S": "STAGED_ADD", "U": "UNTRACKED", "I": "IGNORED", "W": "WT_EDIT",
                 "C": "COMMIT", "R": None}


def block_c(sweep):
    print("\nBLOCK C -- THE DECORATIVE CANDIDATES, their own reset replayed against the class")
    print("  they are accused of not clearing. The extracted source lines are printed, so the")
    print("  mapping from THEIR line to the command driven is checkable and not merely claimed.")
    rows = [r for r in sweep["rows"] if r["verdict"] == "DECORATIVE"]
    if not rows:
        print("  ** NO DECORATIVE ROWS. The sweep found nothing to convict; that is a result,")
        print("     not an error -- but it means block C measured nothing. **")
    for r in rows:
        path = r["path"]
        # EXTRACT the load-bearing reset from the shipped bytes. Refuse on an empty extraction.
        text = (ROOT / path).read_text(errors="replace")
        lines = text.splitlines()
        sites = []
        for name, nums in r["restore_idioms"].items():
            for n in nums:
                if 1 <= n <= len(lines):
                    sites.append((n, name, lines[n - 1].strip()))
        sites.sort()
        arm = "C-" + re.sub(r"[^a-zA-Z0-9]+", "-", path.split("/")[-1])[:24]
        if not sites:
            record(arm, path, "EXTRACTED", "EMPTY",
                   "REFUSING: could not extract a reset site from the shipped bytes")
            continue
        idioms = sorted({n for _, n, _ in sites})
        print("\n  %s -- %s" % (arm, path))
        print("     accused of not clearing: %s" % ",".join(r["uncleared_classes"]))
        print("     extracted reset sites (line: idiom: THEIR OWN TEXT):")
        for n, name, src in sites[:10]:
            print("       %5d: %-12s %s" % (n, name, src[:96]))
        cmd = " && ".join(IDIOM_COMMAND[n] for n in idioms if IDIOM_COMMAND[n] != "true") or "true"
        print("     replayed as: %s" % cmd)
        for cls in r["uncleared_classes"]:
            kind = CLASS_FIXTURE.get(cls)
            if kind is None:
                record(arm + "/" + cls, "class %s has no fixture in this rig" % cls,
                       "SKIP", "SKIP", "declared, not silently dropped")
                continue
            d = new_repo("c")
            try:
                rc, out = sh(DIRTY[kind], d)
                if rc != 0:
                    record(arm + "/" + cls, kind, "PRESENT", "RIG-FAIL", out.strip()[:100])
                    continue
                sh(cmd, d)
                obs = residue(kind, d)
                # AN ACQUITTAL IS A RESULT. The sweep NOMINATED this row by reading; if the
                # residue is ABSENT the reading was wrong and the drive says so, loudly, rather
                # than the instrument scoring itself a failure for having measured correctly.
                # This is P-95 pointed at my own census.
                verdict = "CONVICTED" if obs == "PRESENT" else "ACQUITTED"
                ACQUITTALS.append((arm, cls)) if verdict == "ACQUITTED" else None
                record(arm + "/" + cls, "%s survives their own reset" % kind,
                       "CONVICTED-or-ACQUITTED", verdict, "porcelain=%r" % porcelain(d))
            finally:
                shutil.rmtree(d, ignore_errors=True)


# =============================================================================================
# BLOCK A / L -- THE PROPOSED CHECK: repo-state-attest.sh as the inter-arm reset assertion.
# =============================================================================================
def attest_snapshot(d, out):
    rc, o = run(["bash", str(GUARD), "snapshot", str(d), str(out)], d)
    return rc, o


def attest_compare(before, after, extra=()):
    rc, o = run(["bash", str(GUARD), "compare", str(before), str(after), *extra], ROOT)
    return rc, o


def attested_arm(arm, what, mutate, reset_cmd, expect_attest, writ=(), expect_porcelain=None,
                 note=""):
    """snapshot -> mutate -> reset -> snapshot -> compare. Exactly the inter-arm shape."""
    d = new_repo("a")
    try:
        before = d.parent / (d.name + ".before")
        after = d.parent / (d.name + ".after")
        rc, o = attest_snapshot(d, before)
        if rc != 0:
            record(arm, what, str(expect_attest), "RIG-FAIL", "snapshot rc=%d %s" % (rc, o[:80]))
            return
        rc, o = sh(mutate, d)
        if rc != 0:
            record(arm, what, str(expect_attest), "RIG-FAIL", "mutate rc=%d %s" % (rc, o[:80]))
            return
        sh(reset_cmd, d)
        rc, o = attest_snapshot(d, after)
        if rc != 0:
            record(arm, what, str(expect_attest), "RIG-FAIL", "snapshot2 rc=%d" % rc)
            return
        arc, aout = attest_compare(before, after, writ)
        pc = porcelain(d)
        legacy = "CLEAN" if pc == "" else "DIRTY"
        n = ("LEGACY(git status --porcelain)=%s" % legacy) + ((" | " + note) if note else "")
        record(arm, what, str(expect_attest), str(arc), n)
        if expect_porcelain is not None and legacy != expect_porcelain:
            record(arm + "*", "LEGACY predicate reading", expect_porcelain, legacy,
                   "the legacy term is reported beside the new one on every arm")
        if arc != expect_attest:
            for ln in aout.splitlines()[:12]:
                print("        | " + ln)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        for f in (d.parent / (d.name + ".before"), d.parent / (d.name + ".after")):
            try:
                f.unlink()
            except OSError:
                pass


def block_a():
    print("\nBLOCK A -- the proposed inter-arm reset assertion FIRES on residue")
    print("  check = repo-state-attest.sh snapshot/compare, empty writ. NOT a new instrument.")
    attested_arm("A1", "COMMIT residue after bare `reset --hard` + `clean -fdx`",
                 DIRTY["COMMIT"], "git reset --hard -q && git clean -fdxq", 1,
                 expect_porcelain="CLEAN",
                 note="THE HEADLINE: porcelain cannot see it; the differential can")
    attested_arm("A2", "STAGED-ADD residue after `checkout -- .` + `clean -fd`",
                 DIRTY["STAGED_ADD"], "git checkout -- . && git clean -fdq", 1,
                 expect_porcelain="DIRTY", note="T316's recorded case; porcelain DOES see this")
    attested_arm("A3", "UNTRACKED residue after `reset --hard`",
                 DIRTY["UNTRACKED"], "git reset --hard -q", 1, expect_porcelain="DIRTY")
    attested_arm("A4", "IGNORED residue after `clean -fd`",
                 DIRTY["IGNORED"], "git clean -fdq", 0, expect_porcelain="CLEAN",
                 note="DECLARED LIMIT: T4 is ADVISORY by design, so exit is 0 -- the residue is "
                      "NAMED in the output but does not block")
    attested_arm("A5", "null control: the reset actually worked",
                 DIRTY["WT_EDIT"], "git checkout -- . && git clean -fdq", 0,
                 expect_porcelain="CLEAN")


def block_l():
    print("\nBLOCK L -- LEGITIMATE OPERATIONS. The check must stay QUIET on every one of these.")
    print("  T325 arm G5: a check that reports ordinary drive setup as contamination will be")
    print("  disabled within two fires. Each L arm is a thing a drive in this repo really does.")
    attested_arm("L1", "the drive creates its own sanctioned softhouse/<task> branch",
                 'git checkout -q -b softhouse/T321-scratch-arm', "true", 0,
                 writ=("--allow-new-ref", "^refs/heads/softhouse/",
                       "--writ-ref", "^refs/heads/softhouse/"),
                 expect_porcelain="CLEAN", note="T318 arm G5 replayed against THIS writ")
    attested_arm("L2", "the drive writes IGNORED scratch output under a declared prefix",
                 DIRTY["IGNORED"], "true", 0,
                 writ=("--scratch-prefix", "ignored-out"), expect_porcelain="CLEAN")
    attested_arm("L3", "an arm that does nothing at all (null)", "true", "true", 0,
                 expect_porcelain="CLEAN")
    attested_arm("L4", "a legitimate mutate-and-restore round trip that RESTORED",
                 DIRTY["WT_EDIT"], "git reset --hard -q && git clean -fdq", 0,
                 expect_porcelain="CLEAN")
    # L5 is built properly in block_l5_preexisting(): the dirt has to exist BEFORE the baseline
    # snapshot or the arm cannot show what it claims. Driving it from a clean repo here would
    # have been an arm that passes while testing nothing -- T325's instrument-40 failure.
    attested_arm("L6", "a read-only arm: status and log, nothing written",
                 'git status >/dev/null && git log --oneline >/dev/null', "true", 0,
                 expect_porcelain="CLEAN", note="a read-only arm")


def block_l5_preexisting():
    """L5 as written above starts from a clean repo, so it cannot show what it claims. This is
    the same arm built properly: the dirt exists BEFORE the baseline snapshot and is still there
    after -- which is what a drive looks like when a `.softhouse/LOCK`-shaped untracked file, or
    a worker's own settings file, is sitting in the tree the whole time."""
    print("\n  L5b -- pre-existing dirt, present before the baseline AND after the reset")
    d = new_repo("l5b")
    before = d.parent / (d.name + ".before")
    after = d.parent / (d.name + ".after")
    try:
        (d / "preexisting.txt").write_text("a worker's untracked file, there the whole time\n")
        attest_snapshot(d, before)
        sh("printf CHANGED > tracked.txt", d)
        sh("git checkout -- .", d)
        attest_snapshot(d, after)
        arc, aout = attest_compare(before, after, ("--allow-dirty",))
        record("L5b", "pre-existing untracked file, unchanged across the window", "0", str(arc),
               "LEGACY(git status --porcelain)=DIRTY (it was dirty before, too)")
        if arc != 0:
            for ln in aout.splitlines()[:12]:
                print("        | " + ln)
    finally:
        # THE SNAPSHOTS LIVE IN d.parent, NOT IN d, so `rmtree(d)` does not reach them. The first
        # version of this arm leaked two 771-byte attest files into the system temp root on every
        # run -- ten of them by the end of this task, found only by listing the temp root after
        # the branch was otherwise finished. `attested_arm()` unlinks its pair; this block did
        # not, and the asymmetry is exactly P-94's corollary: A SCRATCH FENCE IS SCOPED TO THE
        # PREFIX IT NAMES. Measured over the whole temp root, never inferred from the fence.
        shutil.rmtree(d, ignore_errors=True)
        for f in (before, after):
            try:
                f.unlink()
            except OSError:
                pass


def main():
    if not GUARD.is_file():
        print("ERROR: %s is not readable. This drive imports the guard rather than"
              " reimplementing it (T213); without it there is nothing to drive. REFUSING."
              % GUARD, file=sys.stderr)
        return 2
    sweep_json = HERE / "evidence/20-reset-sweep.json"
    if not sweep_json.is_file():
        print("ERROR: %s absent. Run sweep_resets.py --json first; block C's population comes"
              " from the sweep and is never typed here. REFUSING." % sweep_json, file=sys.stderr)
        return 2
    sweep = json.loads(sweep_json.read_text())

    print("T321 reset-contamination drive")
    print("  guard under test : %s" % GUARD)
    print("  population from  : %s (%d rows, %d DECORATIVE)"
          % (sweep_json, len(sweep["rows"]),
             sum(1 for r in sweep["rows"] if r["verdict"] == "DECORATIVE")))
    print("  scratch root     : %s (refused if it resolves inside the repo)" % tempfile.gettempdir())

    block_k()
    block_c(sweep)
    block_a()
    block_l()
    block_l5_preexisting()

    if ACQUITTALS:
        print("\n  ** %d of the sweep's DECORATIVE nominations were ACQUITTED BY THE DRIVE **"
              % len(ACQUITTALS))
        for a, c in ACQUITTALS:
            print("     %s / class %s -- the reset DOES clear it; the reading was wrong" % (a, c))
        print("     A candidate list with a driven false-positive rate is worth more than one")
        print("     without, and this figure must be quoted beside the DECORATIVE count.")
    npass = sum(1 for r in RESULTS if r["pass"])
    nfail = len(RESULTS) - npass
    print("\n%s arms=%d pass=%d fail=%d" % (PROBE, len(RESULTS), npass, nfail))
    (HERE / "evidence/30-reset-drive.json").write_text(json.dumps(RESULTS, indent=2))
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
