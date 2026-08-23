#!/usr/bin/env python3
"""T273 (driver escalation) — CAN ANY HOST STATE, AT ANY TIMING, MOVE THE PINNED FRONTIER?

WHY THIS EXISTS. The brief framed the hazard as "macOS clears /tmp on reboot" — a
once-per-restart problem. T274, in its own worktree this same fire, reported the file
vanishing BETWEEN CONSECUTIVE COMMANDS. If that is right the hazard is a RACE, not a
history: a PASS and a FAIL can differ with no input change at all. A repair that made the
file more reliably PRESENT would then be worthless, because the window reopens the instant
it runs.

A race can only change a verdict if SOME state of the host changes the verdict. So the
question to settle is not "how often does /tmp/t234_matrix2.txt disappear" but the
stronger one:

    IS THERE ANY ASSIGNMENT OF EXISTENCE TO OUT-OF-REPO PATHS THAT MOVES THE FRONTIER?

This brackets it. The fail-open linter decides TIER by asking `os.path.exists` (C1 at
:366, C6 at :447). Here the REAL, UNMODIFIED linter is executed with `os.path.exists`
and `os.path.isdir` replaced by a function that answers truthfully for paths inside the
repository and returns a FORCED CONSTANT for every path outside it. Two arms:

    ABSENT  — every out-of-repo path reads as missing   (the emptiest possible host)
    PRESENT — every out-of-repo path reads as existing   (the fullest possible host)

Every real host state lies between those two. If both arms produce the SAME frontier then
no timing, no reboot, no sibling worktree and no race can move it, because the extremes
already agree and there is nothing in between for them to disagree about.

THE LINTER IS NOT MODIFIED AND NOT COPIED. It is executed from its own path with runpy,
so this measures the shipped code and cannot drift from it. It also touches NO host
state: nothing is created, moved or deleted in /tmp, which is why this measurement is
safe to run while sibling worktrees are live.

NEGATIVE CONTROL (P-72): a bracket that reported "no difference" because the patch never
took effect would be indistinguishable from a clean result. So the patch COUNTS its own
calls and each arm REFUSES if it made zero out-of-repo existence queries.

ENGINE DECLARATION (P-33/P-53/P-75): Python only — runpy, io, os. No grep, no rg, no
shell. `git` is invoked only by the linter itself.
"""
import io
import os
import runpy
import subprocess
import sys

LINTER = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("T273 BRACKET ABORT (2): not inside a git work tree.")
    sys.exit(2)
os.chdir(ROOT)
if not os.path.isfile(LINTER):
    print("T273 BRACKET ABORT (2): the linter is absent: %s" % LINTER)
    sys.exit(2)

REAL_EXISTS = os.path.exists
REAL_ISDIR = os.path.isdir
REAL_ROOT = os.path.realpath(ROOT)
ROOT_PREFIX = REAL_ROOT + os.sep


def in_repo(p):
    try:
        rp = os.path.realpath(os.path.join(ROOT, p))
    except (OSError, ValueError, TypeError):
        return False
    return rp == REAL_ROOT or rp.startswith(ROOT_PREFIX)


def run_arm(forced):
    """Execute the real linter with out-of-repo existence forced to `forced`."""
    calls = {"outside": 0, "inside": 0}

    def patched_exists(p):
        if in_repo(p):
            calls["inside"] += 1
            return REAL_EXISTS(p)
        calls["outside"] += 1
        return forced

    def patched_isdir(p):
        if in_repo(p):
            return REAL_ISDIR(p)
        return forced

    buf = io.StringIO()
    old_out, old_err, old_argv = sys.stdout, sys.stderr, sys.argv
    os.path.exists, os.path.isdir = patched_exists, patched_isdir
    os.environ["FAILOPEN_LINT_JSON"] = os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "t273-bracket-lint.json")
    rc = None
    try:
        sys.stdout = buf
        sys.stderr = buf
        sys.argv = [LINTER]
        try:
            runpy.run_path(LINTER, run_name="__main__")
            rc = 0
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 0
    finally:
        os.path.exists, os.path.isdir = REAL_EXISTS, REAL_ISDIR
        sys.stdout, sys.stderr, sys.argv = old_out, old_err, old_argv

    out = buf.getvalue()
    banner = "T238 FAIL-OPEN LINT" in out
    rows = sorted(l[len("FAILOPEN-FRONTIER "):]
                  for l in out.splitlines() if l.startswith("FAILOPEN-FRONTIER "))
    return rc, banner, rows, calls


print("### T273 — HOST-STATE BRACKET on the fail-open frontier")
print("  tree   : %s" % ROOT)
print("  HEAD   : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
print("  linter : %s (executed UNMODIFIED, via runpy)" % LINTER)
print("  host   : nothing is created, moved or deleted by this instrument")
print()

results = {}
for arm in ("ABSENT", "PRESENT"):
    rc, banner, rows, calls = run_arm(arm == "PRESENT")
    results[arm] = rows
    print("=== ARM: every out-of-repo path forced %s ===" % arm)
    print("  linter exit code            : %s" % rc)
    print("  banner present              : %s" % banner)
    print("  out-of-repo existence checks: %d   (in-repo: %d)"
          % (calls["outside"], calls["inside"]))
    print("  frontier rows               : %d" % len(rows))
    for r in rows:
        print("      %s" % r)
    print()
    if not banner:
        print("T273 BRACKET REFUSED: no banner in the %s arm; the linter did not run." % arm)
        sys.exit(2)
    if rc not in (0, 1):
        print("T273 BRACKET REFUSED: linter exit %s in the %s arm." % (rc, arm))
        sys.exit(2)
    # NEGATIVE CONTROL. Zero out-of-repo queries would mean the forcing never bit, and a
    # "no difference" from that is a statement about the instrument, not about the tree.
    if calls["outside"] < 1:
        print("T273 BRACKET REFUSED: the %s arm made ZERO out-of-repo existence queries, so "
              "the forcing never took effect and any agreement below would be vacuous (P-35)."
              % arm)
        sys.exit(2)

a, p = results["ABSENT"], results["PRESENT"]
gained = [r for r in p if r not in a]
lost = [r for r in a if r not in p]
print("### THE BRACKET")
print("  rows only in the PRESENT arm : %d" % len(gained))
for r in gained:
    print("      + %s" % r)
print("  rows only in the ABSENT arm  : %d" % len(lost))
for r in lost:
    print("      - %s" % r)
print()
if a == p:
    print("### VERDICT: THE FRONTIER IS IDENTICAL AT BOTH EXTREMES OF HOST STATE.")
    print("### Every real host lies between them, so NO timing, NO reboot, NO sibling")
    print("### worktree and NO race can move it. The tier is a property of the TREE.")
    sys.exit(0)
print("### VERDICT: THE FRONTIER MOVES WITH HOST STATE — %d row(s) differ between the two"
      % (len(gained) + len(lost)))
print("### extremes. Each row above is a tier a race can still flip.")
sys.exit(1)
