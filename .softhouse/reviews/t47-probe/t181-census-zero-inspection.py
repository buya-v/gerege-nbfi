#!/usr/bin/env python3
"""T181 -- the counterfactual that makes T178's census defect material.

T178's F-1 says, of the 25 unguarded t41-probe rewriters (two of them LIVE):

    "`t178-guard-census.py` and `t178-wider-family.py` are committed and ready
     to be pointed at them"

This script does exactly that -- against the UNHARDENED FORK-POINT bytes, i.e.
the state in which two of those files were live gate bypasses against the
ratified DEC-1 -- and records what the census actually reports.

MECHANISM (t178-guard-census.py):
    line 232  files = sorted(glob.glob(os.path.join(SCAN, "t47_edit_*.py")))
    line 304  sys.exit(1 if (reachable or unmeasured or skipped) else 0)

The glob is hard-wired to the `t47_edit_*.py` family.  The t41 family is named
`edit*.py`.  So `--scan=<t41-probe>` matches nothing, every counter is 0, and
the script exits 0 -- GREEN -- having inspected NOTHING.

This is P-35 exactly: a check inspecting ZERO items is an ERROR, not a pass.
It is committed as evidence for T181 finding F-2.

READ-ONLY with respect to the repository.  Copies fork-point bytes into a temp
directory and runs the census (which itself executes nothing) against it.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CENSUS = os.path.join(HERE, "t178-guard-census.py")
FORK = "dfa1bfa96084a2175f0d89d0a401a8c105d9a35f"
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"


def sha256_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a),
                          capture_output=True, text=True, errors="replace")


def main():
    adr0 = sha256_file(os.path.join(REPO, ADR_REL))
    go0 = sha256_file(os.path.join(REPO, GO_REL))

    # --- materialise the UNHARDENED fork-point t41-probe family ------------
    tmp = tempfile.mkdtemp(prefix="t181-t41fork-")
    r = git("ls-tree", "-r", "--name-only", FORK,
            ".softhouse/reviews/t41-probe/")
    names = [l for l in r.stdout.splitlines()
             if os.path.basename(l).startswith("edit")
             and l.endswith(".py")]
    for rel in names:
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (FORK, rel)],
                              capture_output=True).stdout
        io.open(os.path.join(tmp, os.path.basename(rel)), "wb").write(blob)

    print("=" * 74)
    print("T181 F-2 -- ZERO-INSPECTION GREEN in t178-guard-census.py")
    print("=" * 74)
    print()
    print("fork point                       : %s" % FORK)
    print("UNHARDENED t41 rewriters staged  : %d" % len(names))
    print("staged at                        : %s" % tmp)
    print("of these, LIVE at the fork point : 2  (edit2.py, edit10.py)")
    print("   -- both hard-wired the RELATIVE path %s" % ADR_REL)
    print("   -- so repo-root cwd reached the RATIFIED document")
    print()
    print("Now run T178's census against exactly that directory, as F-1 says:")
    print("-" * 74)

    p = subprocess.run([sys.executable, CENSUS, "--scan=%s" % tmp],
                       capture_output=True, text=True, errors="replace")
    tail = p.stdout.strip().splitlines()[-4:]
    for l in tail:
        print("   " + l)
    print("-" * 74)
    print("census exit code                 : %d   <-- %s"
          % (p.returncode, "GREEN / PASS" if p.returncode == 0 else "red"))
    print()

    ok = (p.returncode == 0)
    print("VERDICT ON THE TOOL:")
    if ok:
        print("  The census reports a clean PASS over a directory containing")
        print("  %d unguarded in-place rewriters of a ratified DEC-n," % len(names))
        print("  TWO OF WHICH WERE LIVE.  It measured 0 files and said so, but")
        print("  it EXITED 0 -- so any caller keying on the exit status, which")
        print("  is precisely what T178's own F-3 proposes ('make it a HARD")
        print("  check in the verifier'), reads this as 'no bypasses exist'.")
        print()
        print("  P-35: a check inspecting ZERO items is an ERROR, not a pass.")
    else:
        print("  census refused the empty scan; F-2 does not hold")

    adr1 = sha256_file(os.path.join(REPO, ADR_REL))
    go1 = sha256_file(os.path.join(REPO, GO_REL))
    print()
    print("REPO DEC-1       %s  %s"
          % (adr1, "UNCHANGED" if adr1 == adr0 else "*** MOVED ***"))
    print("REPO contract.go %s  %s"
          % (go1, "UNCHANGED" if go1 == go0 else "*** MOVED ***"))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
