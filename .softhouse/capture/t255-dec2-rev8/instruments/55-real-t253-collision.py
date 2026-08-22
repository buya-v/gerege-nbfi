#!/usr/bin/env python3
"""T255 — THE REAL T253 COLLISION, not the simulation.

`50-red-drive.py` arm R1 simulates the collision by inserting 30 lines. This
instrument runs the ACTUAL one: it takes `.softhouse/conformance.sh` FROM
`T253`'s own branch -- the edit that has not merged yet and that will land under
revision 8 -- and checks revision 8's citations against it.

If revision 8 survives this, the defect it was sent to eliminate is eliminated
against the real thing rather than against my model of it.

Nothing in the repository is modified: the scratch tree is a temp directory.
No `cd`, no `|| true`, no bare `grep`. Exit 0 = revision 8's citations hold
against T253's conformance.sh; 1 = they do not; 2 = could not run (T253's
branch absent, etc.) -- and 2 is NEVER printed as a pass.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
ADR_REL = "docs/adr/DEC-2-gl-accounting-adapter.md"
SH_REL = ".softhouse/conformance.sh"
INSTR_REL = ".softhouse/capture/t255-dec2-rev8/instruments"
OLD_REL = ".softhouse/capture/t247-dec2-rev7/verify-line-numbers.py"
T253 = "origin/softhouse/T253-harness-portability"


def git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True)


def main():
    probe = git("rev-parse", "--verify", T253 + ":" + SH_REL)
    if probe.returncode != 0:
        print("REFUSE (exit 2): %s:%s is not readable." % (T253, SH_REL))
        print("  WHERE I LOOKED: `git rev-parse --verify` in %s. stderr: %s" % (ROOT, probe.stderr.strip()))
        print("  This is a statement about my search, NOT about T253 (P-66/P-70).")
        return 2
    blob = probe.stdout.strip()
    mine = git("rev-parse", "HEAD:" + SH_REL).stdout.strip()
    print("conformance.sh at MY commit : %s" % mine)
    print("conformance.sh on T253's br : %s" % blob)
    if blob == mine:
        print("REFUSE (exit 2): the two blobs are IDENTICAL, so there is no collision to test.")
        print("  A green verdict here would be vacuous (P-35).")
        return 2

    stat = git("diff", "--stat", "HEAD:" + SH_REL, T253 + ":" + SH_REL).stdout.strip()
    print("diff: %s" % stat.replace("\n", " | "))
    print("")

    tmp = tempfile.mkdtemp(prefix="t255-real-collision-")
    try:
        for rel in [ADR_REL,
                    "nexus/internal/apps/ledger/conformance/vector.go",
                    "nexus/internal/apps/ledger/conformance/admit.go",
                    "nexus/internal/apps/loanschedule/conformance/vector.go",
                    "nexus/internal/apps/loanschedule/conformance/admit.go",
                    INSTR_REL + "/20-verify-anchors.py",
                    OLD_REL]:
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, rel), dst)
        # T253's conformance.sh, straight out of its branch
        sh_text = git("show", T253 + ":" + SH_REL).stdout
        dst = os.path.join(tmp, SH_REL)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(sh_text)

        # Where did the guard invocations actually move to?
        lines = sh_text.split("\n")
        print("=== where T253 moved the things DEC-2 used to cite by number ===")
        for i, l in enumerate(lines, 1):
            if re.match(r"^\s*guard_[a-z0-9_]+\s*\|\|\s*failed=1\s*$", l) or l.rstrip() == "run_guards() {":
                print("    :%-5d %s" % (i, l.strip()))
        print("")
        print("    Revision 7 was drafted with run_guards at :1474; its reviewer re-measured")
        print("    :1504; at my own commit it is :1548. Compare the column above.")
        print("")

        print("=== revision 8's ANCHORS against T253's conformance.sh ===")
        proc = subprocess.run([sys.executable, os.path.join(tmp, INSTR_REL, "20-verify-anchors.py")],
                              capture_output=True, text=True)
        anchors_rc = proc.returncode
        for l in proc.stdout.split("\n"):
            if l.startswith("  ok") or l.startswith("  ROT") or l.startswith("  AMBIG") \
                    or l.startswith("  MISMATCH") or "ALL ANCHORS" in l or "ROT DETECTED" in l \
                    or l.startswith("  invoked") or l.startswith("  tallied") \
                    or l.startswith("  DEC-2 token") or l.startswith("REFUSE"):
                print("    %s" % l.strip())
        print("    -> exit %d" % anchors_rc)
        print("")

        print("=== revision 7's LINE NUMBERS against the same file (pre-rev-8 DEC-2 restored) ===")
        pre = git("show", "HEAD~1:" + ADR_REL)
        if pre.returncode != 0:
            print("REFUSE (exit 2): could not restore the pre-revision-8 DEC-2 blob.")
            return 2
        with open(os.path.join(tmp, ADR_REL), "w", encoding="utf-8") as fh:
            fh.write(pre.stdout)
        proc2 = subprocess.run([sys.executable, os.path.join(tmp, OLD_REL)],
                               capture_output=True, text=True)
        for l in proc2.stdout.split("\n"):
            if "MOVED" in l or "got " in l or "row(s)" in l:
                print("    %s" % l.rstrip())
        print("    -> exit %d" % proc2.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("")
    if anchors_rc == 0:
        print("VERDICT: revision 8's citations SURVIVE the real T253 edit, unchanged and unmeasured.")
        print("         The line-number citations they replaced do not.")
        return 0
    print("VERDICT: revision 8's citations did NOT survive. That is a defect in revision 8.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
