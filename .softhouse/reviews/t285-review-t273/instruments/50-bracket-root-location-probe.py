#!/usr/bin/env python3
"""T285 — IS `guard_frontier_host_sensitivity` A PROPERTY OF THE TREE, OR OF WHERE THE
HARNESS WAS INVOKED FROM?

T273's 80-host-state-bracket.py decides "out of repo" with

    ROOT = git rev-parse --show-toplevel
    in_repo(p) = realpath(join(ROOT, p)).startswith(ROOT + os.sep)

Every agent worktree in this program lives UNDER the main checkout, at
`<main>/.claude/worktrees/agent-<hex>`, so `ROOT` is the WORKTREE when the BAR runs in a
worker and the MAIN CHECKOUT when the BAR runs where the driver merges. Three of the four
files in HOSTSENSITIVE_PIN_FRONTIER_DELTA name a dead SIBLING worktree by absolute path.
Those paths are OUT of repo under a worktree ROOT and IN repo under the main-checkout
ROOT — so the bracket FORCES them at one invocation site and answers TRUTHFULLY at the
other, and the delta is not the same number.

This probe runs the REAL bracket logic against THIS tree twice, changing ONLY the prefix
the in_repo predicate uses:

    arm W  — prefix = this worktree      (what a worker measures)
    arm M  — prefix = the main checkout  (what the driver's checkout measures)

Nothing else differs: same tree, same linter, same corpus, same process. It writes only
into a mktemp scratch directory it owns and removes, so unlike the instrument it is
probing it really does leave no shared temp file behind.

ENGINE DECLARATION (P-33): Python only — runpy, io, os, tempfile. `git` only via the
linter and two `rev-parse` reads.
"""
import io
import os
import runpy
import shutil
import subprocess
import sys
import tempfile

LINTER = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("T285 PROBE ABORT (2): not inside a git work tree.")
    sys.exit(2)
os.chdir(ROOT)
if not os.path.isfile(LINTER):
    print("T285 PROBE ABORT (2): the linter is absent: %s" % LINTER)
    sys.exit(2)

REAL_EXISTS = os.path.exists
REAL_ISDIR = os.path.isdir

# The main checkout is the ancestor of `<main>/.claude/worktrees/<name>`.
HERE = os.path.realpath(ROOT)
MARKER = os.sep + ".claude" + os.sep + "worktrees" + os.sep
MAIN = HERE.split(MARKER)[0] if MARKER in HERE else HERE

SCRATCH = tempfile.mkdtemp(prefix="t285-bracket-probe.")


def make_in_repo(prefix):
    real_prefix = os.path.realpath(prefix)
    pfx = real_prefix + os.sep

    def in_repo(p):
        try:
            rp = os.path.realpath(os.path.join(ROOT, p))
        except (OSError, ValueError, TypeError):
            return False
        return rp == real_prefix or rp.startswith(pfx)
    return in_repo


def run_arm(forced, in_repo, tag):
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
    os.environ["FAILOPEN_LINT_JSON"] = os.path.join(SCRATCH, "lint-%s.json" % tag)
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


print("### T285 — BRACKET ROOT-LOCATION PROBE")
print("  tree           : %s" % ROOT)
print("  HEAD           : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                               capture_output=True, text=True).stdout.strip())
print("  worktree prefix: %s" % HERE)
print("  main prefix    : %s" % MAIN)
print("  scratch        : %s (removed at exit)" % SCRATCH)
print()

if HERE == MAIN:
    print("T285 PROBE REFUSED: this checkout is not under a `.claude/worktrees/` path, so the")
    print("two invocation sites cannot be distinguished from here. Run it from a worker worktree.")
    shutil.rmtree(SCRATCH, ignore_errors=True)
    sys.exit(2)

deltas = {}
try:
    for label, prefix in (("W", HERE), ("M", MAIN)):
        in_repo = make_in_repo(prefix)
        arms = {}
        for name in ("ABSENT", "PRESENT"):
            rc, banner, rows, calls = run_arm(name == "PRESENT", in_repo, "%s-%s" % (label, name))
            arms[name] = rows
            if not banner or rc not in (0, 1):
                print("T285 PROBE REFUSED: arm %s/%s banner=%s rc=%s" % (label, name, banner, rc))
                sys.exit(2)
            if calls["outside"] < 1:
                print("T285 PROBE REFUSED: arm %s/%s made ZERO out-of-repo queries." % (label, name))
                sys.exit(2)
        a, p = arms["ABSENT"], arms["PRESENT"]
        d = sorted(["+" + r for r in p if r not in a] + ["-" + r for r in a if r not in p])
        deltas[label] = d
        site = "worker worktree ROOT" if label == "W" else "main checkout ROOT"
        print("=== in_repo prefix = %s (%s) ===" % (label, site))
        print("  host-sensitive frontier delta rows: %d" % len(d))
        for r in d:
            print("      %s" % r)
        print()
finally:
    shutil.rmtree(SCRATCH, ignore_errors=True)

W, M = deltas["W"], deltas["M"]
print("### ADJUDICATION")
if W == M:
    print("### The delta is IDENTICAL at both invocation sites (%d rows). The pin is a" % len(W))
    print("### property of the tree, not of where the harness was started.")
    sys.exit(0)
print("### THE DELTA DEPENDS ON WHERE THE HARNESS WAS INVOKED FROM: %d row(s) under a" % len(W))
print("### worker-worktree ROOT, %d under the main-checkout ROOT. Same tree, same linter," % len(M))
print("### same corpus, same process — only the in_repo prefix differs.")
print("  rows only under the WORKTREE prefix:")
for r in W:
    if r not in M:
        print("      %s" % r)
print("  rows only under the MAIN prefix:")
for r in M:
    if r not in W:
        print("      %s" % r)
sys.exit(1)
