#!/usr/bin/env python3
"""T255 — DRIVE THE ROT MECHANISM RED (P-22). A checker nobody has seen FAIL is
not a checker; it is a decoration.

Seven perturbations, run against a SCRATCH COPY of the tree. Nothing in the
repository is modified: every mutation happens under a temporary directory that
is deleted at the end, and this script asserts that the real DEC-2 and the real
`.softhouse/conformance.sh` are byte-identical before and after it runs.

R0  CALIBRATION      unperturbed scratch                -> both checkers agree
R1  THE T253 COLLISION: 30 lines inserted ABOVE every guard citation, which is
    exactly what `T253` did to `.softhouse/conformance.sh` in this same fire
                                                        -> LINE NUMBERS ROT
                                                        -> ANCHORS DO NOT
R2  the ANCHORED THING is renamed                        -> ANCHOR ROT (bites)
R3  an anchor's text is DUPLICATED                       -> AMBIGUOUS (bites)
R4  a guard is REMOVED from run_guards                   -> DERIVED count fails
R5  two guards are REORDERED in run_guards               -> DERIVED order fails
R6  the document's own [DERIVED: ...] token is edited    -> DERIVED value fails

R1 is the whole argument. It is the ONLY perturbation of the seven that a
documentation change should be indifferent to, and it is the one that has
rejected three consecutive revisions of DEC-2.

No `cd`. No `|| true`. No bare `grep`, no `rg`. Every subprocess result is
classified: 0, 1 and 2 mean different things and none of them is discarded.
Exit 0 = every arm behaved as required; 1 = an arm did not; 2 = could not run.
"""
import hashlib
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

# The three conformance.sh line numbers revision 7 was DRAFTED with, and the
# three its reviewer RE-MEASURED. Both sets are used below to show what a dead
# line number resolves to.
DRAFTED = {"run_guards": 1474, "guard_ledger_invariants || failed=1": 1494,
           "guard_no_fail_open_instruments || failed=1": 1495}
REMEASURED = {"run_guards": 1504, "guard_ledger_invariants || failed=1": 1524,
              "guard_no_fail_open_instruments || failed=1": 1525}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build_scratch(base):
    """Copy just what the two checkers read."""
    for rel in [ADR_REL, SH_REL,
                "nexus/internal/apps/ledger/conformance/vector.go",
                "nexus/internal/apps/ledger/conformance/admit.go",
                "nexus/internal/apps/loanschedule/conformance/vector.go",
                "nexus/internal/apps/loanschedule/conformance/admit.go"]:
        dst = os.path.join(base, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), dst)
    for rel in [INSTR_REL + "/20-verify-anchors.py", OLD_REL]:
        dst = os.path.join(base, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), dst)
    return base


def run(base, rel):
    """Run a checker inside the scratch tree. Returns (rc, stdout+stderr).
    rc is CLASSIFIED by the caller; it is never coerced with `|| true`."""
    proc = subprocess.run([sys.executable, os.path.join(base, rel)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def arm(label, expect_anchor_rc, base, note=""):
    rc, out = run(base, INSTR_REL + "/20-verify-anchors.py")
    ok = (rc == expect_anchor_rc)
    print("  %-58s anchors exit %d (want %d)  %s" % (label, rc, expect_anchor_rc, "OK" if ok else "*** ARM FAILED ***"))
    if note:
        print("      %s" % note)
    if not ok:
        print("      --- checker output ---")
        for l in out.split("\n")[-25:]:
            print("      %s" % l)
    return ok, out


def main():
    adr_before, sh_before = sha(os.path.join(ROOT, ADR_REL)), sha(os.path.join(ROOT, SH_REL))
    print("real tree, before: DEC-2 %s" % adr_before)
    print("                   conformance.sh %s" % sh_before)
    print("")

    all_ok = True
    tmp = tempfile.mkdtemp(prefix="t255-red-drive-")
    try:
        # ---------------------------------------------------------- R0
        print("=== R0  CALIBRATION — unperturbed scratch copy ===")
        b = build_scratch(os.path.join(tmp, "r0"))
        ok, _ = arm("R0 unperturbed", 0, b,
                    "a checker that fails on a clean tree proves nothing when it fails on a dirty one")
        all_ok &= ok
        # ONE VARIABLE AT A TIME. `verify-line-numbers.py`'s ADR_ROWS were written
        # against the PRE-revision-8 document, so running it against the new one
        # conflates two causes. The pre-rev-8 blob is restored from git for this
        # arm so the figure below is about `.softhouse/conformance.sh` and nothing else.
        pre = os.path.join(tmp, "pre")
        build_scratch(pre)
        blob = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + ADR_REL],
                              capture_output=True, text=True)
        if blob.returncode != 0:
            print("REFUSE (exit 2): could not read HEAD's DEC-2 blob: %s" % blob.stderr.strip())
            return 2
        write(os.path.join(pre, ADR_REL), blob.stdout)
        rc_old, out_old = run(pre, OLD_REL)
        print("      rev-7's hand-listed line-number checker, run against the PRE-revision-8")
        print("      DEC-2 (restored from HEAD) so only conformance.sh varies: exit %d" % rc_old)
        moved = re.search(r"(\d+) row\(s\) MOVED out of (\d+)", out_old)
        if moved:
            print("      -> %s of %s rows already MOVED at a71c140, BEFORE any perturbation," % moved.groups())
            print("         and ALL of them are its four conformance.sh rows.")
            print("         That is G-14 re-enacting itself: revision 7's replacements, and the")
            print("         review's re-measurement of them, are BOTH stale at this commit.")
        print("      SCOPE, both terms counted (P-67): that checker's SH_ROWS holds 4 rows;")
        print("      DEC-2 carried 115 `path:NNNN` citations at a71c140, 90 of them into this")
        print("      repository. A hand-written row list answers a question about its author's")
        print("      memory, not about the document (P-66).")
        print("")

        # ---------------------------------------------------------- R1
        print("=== R1  THE T253 COLLISION — 30 lines inserted ABOVE every guard citation ===")
        print("    T253 rewrote ten `mktemp -t` sites in .softhouse/conformance.sh in this fire,")
        print("    the first four of them ABOVE every citation DEC-2 carries. This arm reproduces")
        print("    that shape: a change that alters NOTHING any citation refers to.")
        b = build_scratch(os.path.join(tmp, "r1"))
        p = os.path.join(b, SH_REL)
        lines = read(p).split("\n")
        pad = ["# T255 RED DRIVE: a line T253's mktemp rewrite could have added, "
               "changing nothing DEC-2 cites." for _ in range(30)]
        lines[1399:1399] = pad          # insert above line 1400, i.e. above every guard citation
        write(p, "\n".join(lines))
        ok, _ = arm("R1 30 lines inserted above the citations", 0, b,
                    "ANCHORS ARE INDIFFERENT TO IT — which is the entire point of revision 8")
        all_ok &= ok
        # same isolation: pre-revision-8 ADR, perturbed conformance.sh
        pre1 = os.path.join(tmp, "pre1")
        build_scratch(pre1)
        write(os.path.join(pre1, ADR_REL), blob.stdout)
        shutil.copy2(p, os.path.join(pre1, SH_REL))
        rc_old, out_old = run(pre1, OLD_REL)
        moved2 = re.search(r"(\d+) row\(s\) MOVED out of (\d+)", out_old)
        print("      rev-7's line-number checker, same isolation: exit %d, %s"
              % (rc_old, ("%s of %s rows MOVED" % moved2.groups()) if moved2 else "no summary line"))
        body = read(p).split("\n")
        print("      AND THIS IS WHY IT IS NOT CLERICAL — a dead line number does not resolve to")
        print("      nothing. It resolves to a plausible neighbour, so a reader is MISLED, not STOPPED:")
        for label, n in sorted(REMEASURED.items(), key=lambda kv: kv[1]):
            got = body[n - 1] if n <= len(body) else "<beyond EOF>"
            print("        the review re-measured %-42s to :%d, which now reads" % ("`%s`" % label, n))
            print("            %s" % got.strip()[:104])
        if rc_old == 0:
            print("      *** ARM FAILED: the line-number checker did NOT notice. ***")
            all_ok = False
        print("")

        # ---------------------------------------------------------- R2
        print("=== R2  the ANCHORED THING is renamed — the anchor MUST bite ===")
        b = build_scratch(os.path.join(tmp, "r2"))
        p = os.path.join(b, SH_REL)
        t = read(p)
        assert t.count("guard_ledger_invariants() {") == 1
        write(p, t.replace("guard_ledger_invariants() {", "guard_ledger_invariants_RENAMED() {", 1))
        ok, out = arm("R2 anchored function renamed", 1, b,
                      "expected: ROT on three anchor rows AND a DERIVED mismatch")
        all_ok &= ok
        if "ROT" not in out:
            print("      *** ARM FAILED: no ROT row printed. ***")
            all_ok = False
        print("")

        # ---------------------------------------------------------- R3
        print("=== R3  an anchor's text is DUPLICATED — uniqueness MUST bite ===")
        b = build_scratch(os.path.join(tmp, "r3"))
        p = os.path.join(b, SH_REL)
        t = read(p)
        write(p, t.replace("NEXUS_DIR=\"$REPO_ROOT/nexus\"",
                           "NEXUS_DIR=\"$REPO_ROOT/nexus\"\n# NEXUS_DIR=\"$REPO_ROOT/nexus\"", 1))
        ok, out = arm("R3 anchor duplicated", 1, b,
                      "an anchor that matches twice names nothing; AMBIG, not a silent pass")
        all_ok &= ok
        if "AMBIG" not in out:
            print("      *** ARM FAILED: no AMBIG row printed. ***")
            all_ok = False
        print("")

        # ---------------------------------------------------------- R4
        print("=== R4  a guard is REMOVED from run_guards — the DERIVED count MUST bite ===")
        b = build_scratch(os.path.join(tmp, "r4"))
        p = os.path.join(b, SH_REL)
        t = read(p)
        victim = [l for l in t.split("\n") if re.match(r"^\s*guard_gofmt\s*\|\|\s*failed=1\s*$", l)]
        if len(victim) != 1:
            print("REFUSE (exit 2): could not find exactly one guard_gofmt tally line to remove.")
            return 2
        write(p, t.replace(victim[0] + "\n", "", 1))
        ok, out = arm("R4 guard_gofmt removed from run_guards", 1, b,
                      "expected: fence != source, invoked 8->7, tallied 7->6, ordinal shifts")
        all_ok &= ok
        if "MISMATCH" not in out:
            print("      *** ARM FAILED: no MISMATCH row printed. ***")
            all_ok = False
        print("")

        # ---------------------------------------------------------- R5
        print("=== R5  two guards are REORDERED — the DERIVED ORDER MUST bite ===")
        print("    (a count-only check would pass this. It is here because it would.)")
        b = build_scratch(os.path.join(tmp, "r5"))
        p = os.path.join(b, SH_REL)
        t = read(p)
        a_line = [l for l in t.split("\n") if re.match(r"^\s*guard_gofmt\s*\|\|\s*failed=1\s*$", l)][0]
        b_line = [l for l in t.split("\n")
                  if re.match(r"^\s*guard_no_float_in_harness\s*\|\|\s*failed=1\s*$", l)][0]
        t2 = t.replace(a_line, "\x00SWAP\x00", 1).replace(b_line, a_line, 1).replace("\x00SWAP\x00", b_line, 1)
        write(p, t2)
        ok, out = arm("R5 two tallied guards swapped", 1, b,
                      "counts are unchanged at 8/7 — only the ORDER moved, and it is caught")
        all_ok &= ok
        if "the fence is not the source's invocation list, in order." not in out:
            print("      *** ARM FAILED: the order check did not fire. ***")
            all_ok = False
        print("")

        # ---------------------------------------------------------- R6
        print("=== R6  the DOCUMENT's own [DERIVED: ...] token is edited — MUST bite ===")
        b = build_scratch(os.path.join(tmp, "r6"))
        p = os.path.join(b, ADR_REL)
        t = read(p)
        old = "[DERIVED: run_guards invokes 8 | tallies 7 | `guard_ledger_invariants` is invocation #7 and tallied #6]"
        if t.count(old) != 1:
            print("REFUSE (exit 2): the [DERIVED: ...] token is not present exactly once in DEC-2.")
            return 2
        write(p, t.replace(old, old.replace("tallies 7", "tallies 9"), 1))
        ok, out = arm("R6 document claims 9 tallied guards", 1, b,
                      "the document lying about the source is caught as readily as the reverse")
        all_ok &= ok
        print("")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    adr_after, sh_after = sha(os.path.join(ROOT, ADR_REL)), sha(os.path.join(ROOT, SH_REL))
    print("real tree, after:  DEC-2 %s" % adr_after)
    print("                   conformance.sh %s" % sh_after)
    if adr_after != adr_before or sh_after != sh_before:
        print("*** THE RED DRIVE MODIFIED THE REAL TREE. That is a defect in this instrument. ***")
        return 1
    print("UNCHANGED — every mutation happened in a scratch tree, which is now deleted.")
    print("")
    print("RED DRIVE: %s" % ("ALL ARMS BEHAVED AS REQUIRED" if all_ok else "AT LEAST ONE ARM FAILED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
