#!/usr/bin/env python3
"""T270 — drive both T270 controls RED, then GREEN. Transcript: RED-GREEN-T270.txt

  python3 prove-t270-red.py      -> exit 0 only if every arm behaves as asserted

P-22: a guard you have not personally driven red is worse than no guard, because it is
believed. This task exists BECAUSE a guard that could not fail was believed for a fire.

TWO CONTROLS ARE DRIVEN HERE:

  A. `census-superseded-invocations.py` — does it actually FAIL when a superseded artefact
     is invoked, and does it stay GREEN on the shapes that are NOT violations (a mention, a
     name passed as an argument, a sandbox copy)? Both halves, because a census that flags
     everything buries the sites that matter exactly as badly as one that flags nothing.

  B. `.softhouse/reviews/A2-11/run-all.sh` section 8 — is it FAIL-CLOSED? Deleting the
     `SUPERSEDED.txt` redirect must make it REFUSE, not silently fall back to running the
     superseded guard. A fix that reverts itself under a plausible edit is not a fix.

Every arm runs in a throwaway temp tree. Nothing here writes to the committed tree and
nothing contacts the reference oracle.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOFTHOUSE = os.path.abspath(os.path.join(HERE, ".."))
REPO_SOFTHOUSE = os.path.abspath(os.path.join(HERE, "..", ".."))
CENSUS = os.path.join(HERE, "census-superseded-invocations.py")
A2_11 = os.path.join(REPO_SOFTHOUSE, "reviews", "A2-11")
RIG = os.path.join(REPO_SOFTHOUSE, "capture", "tierA-a2")

FAILURES = []
ARMS = 0


def check(label, cond, detail=""):
    global ARMS
    ARMS += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("\n         " + detail)
                                                        if detail else ""))
    if not cond:
        FAILURES.append(label)


def run_census(root):
    p = subprocess.run([sys.executable, CENSUS, "--root", root],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def synth(caller_body, register="old-guard.py -> new-guard.py\n", extra=None):
    """A minimal tree with one register, one superseded artefact and one caller."""
    d = tempfile.mkdtemp(prefix="t270-red.")
    os.makedirs(os.path.join(d, "capture", "rig"))
    os.makedirs(os.path.join(d, "reviews", "R"))
    with open(os.path.join(d, "capture", "rig", "SUPERSEDED.txt"), "w") as f:
        f.write(register)
    for n in ("old-guard.py", "new-guard.py"):
        with open(os.path.join(d, "capture", "rig", n), "w") as f:
            f.write("print('%s')\n" % n)
    with open(os.path.join(d, "reviews", "R", "run-all.sh"), "w") as f:
        f.write('#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\n' + caller_body)
    for rel, body in (extra or {}).items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(body)
    return d


# ===================================================================== CONTROL A
def arm_reproduce():
    print("\nARM 0 -- REPRODUCE: the exact shape T263 found. A run-all.sh that invokes a")
    print("         superseded guard by the exact line that was live at A2-11/run-all.sh:36")
    d = synth('python3 "$DIR/../../capture/rig/old-guard.py"; echo "exit=$?"\n')
    rc, out = run_census(d)
    check("the census FAILS (exit 1) on a live invocation of a superseded artefact",
          rc == 1, "rc=%d" % rc)
    check("it NAMES the caller, the line and the artefact",
          "reviews/R/run-all.sh:3" in out and "old-guard.py" in out)
    check("it grades the artefact STILL EXECUTED IN PLACE, not PRESERVED",
          "STILL EXECUTED IN PLACE" in out)
    # NOTE the first cut of this assertion was `"PASS --" not in out`, which matched the
    # census's own PROSE ("...still prints PASS -- is not preserved evidence..."). That is
    # this task's defect committed inside this task's own red-drive: a text match on a
    # whole output, satisfied by a sentence rather than by a verdict. Anchored to the
    # start of a line instead, which is where the verdict is actually printed.
    check("it does NOT print the PASS verdict line",
          not any(l.startswith("PASS --") for l in out.split("\n")))
    shutil.rmtree(d)


def arm_fixed():
    print("\nARM 1 -- GREEN: the same tree with the invocation redirected to the successor")
    d = synth('python3 "$DIR/../../capture/rig/new-guard.py"; echo "exit=$?"\n')
    rc, out = run_census(d)
    check("the census PASSES (exit 0) once nothing executes the superseded file",
          rc == 0, "rc=%d" % rc)
    check("the artefact is graded PRESERVED, not executed",
          "PRESERVED, not executed" in out)
    shutil.rmtree(d)


def arm_mention_is_not_execution():
    print("\nARM 2 -- GREEN: a MENTION is not an execution. Preserving the bytes REQUIRES")
    print("         naming the file, so a census that flags mentions is unusable.")
    d = synth('# old-guard.py is superseded; see SUPERSEDED.txt\n'
              'echo "the replacement for old-guard.py is new-guard.py"\n')
    rc, out = run_census(d)
    check("a comment naming the artefact does not fail the census", rc == 0, "rc=%d" % rc)
    check("an echo naming the artefact does not fail the census either",
          "STILL EXECUTED" not in out)
    shutil.rmtree(d)


def arm_argument_is_not_execution():
    print("\nARM 3 -- GREEN: the artefact name passed as an ARGUMENT to another program is")
    print("         not an invocation of it. This is the exact shape T270's own fix uses")
    print("         (`python3 resolve-supersession.py SUPERSEDED.txt <frozen-name>`), and")
    print("         the first cut of this census graded it EXECUTED -- a false finding.")
    d = synth('python3 "$DIR/lookup.py" "$DIR/../../capture/rig/SUPERSEDED.txt" '
              'old-guard.py\n',
              extra={"reviews/R/lookup.py": "import sys\nprint(sys.argv[2])\n"})
    rc, out = run_census(d)
    check("a name in argument position does not fail the census", rc == 0, "rc=%d" % rc)
    check("and it is graded PRESERVED", "PRESERVED, not executed" in out)
    shutil.rmtree(d)


def arm_sandbox_copy():
    print("\nARM 4 -- GREEN: running a SANDBOX COPY is what the registers prescribe")
    print("         ('RETAINED, BYTE-IDENTICAL, DO NOT RUN FOR A NEW ANSWER'), so a")
    print("         red-drive that copies the frozen file into a tempdir is not a finding.")
    d = synth('echo nothing\n', extra={"reviews/R/prove-red.py": (
        "import os, shutil, subprocess, sys, tempfile\n"
        "d = tempfile.mkdtemp()\n"
        "shutil.copy('old-guard.py', d)\n"
        "subprocess.run([sys.executable, os.path.join(d, 'old-guard.py')])\n")})
    rc, out = run_census(d)
    check("a sandbox copy does not fail the census", rc == 0, "rc=%d" % rc)
    check("but it IS counted and printed separately, not silently dropped",
          "EXEC-COPY" in out and "executed-as-copy" in out)
    shutil.rmtree(d)


def arm_nil_coverage():
    print("\nARM 5 -- RED: NIL COVERAGE. A tree with no register at all must REFUSE, never")
    print("         report a clean sweep. 'I found no violations' and 'I read nothing' are")
    print("         the same output unless the guard distinguishes them (P-45/P-80).")
    d = tempfile.mkdtemp(prefix="t270-red-nil.")
    os.makedirs(os.path.join(d, "capture"))
    with open(os.path.join(d, "capture", "x.sh"), "w") as f:
        f.write("echo hi\n")
    rc, out = run_census(d)
    check("0 registers found -> REFUSE, exit 2", rc == 2, "rc=%d" % rc)
    check("it says so, and does not print the PASS verdict line",
          "0 supersession registers" in out
          and not any(l.startswith("PASS --") for l in out.split("\n")))
    shutil.rmtree(d)


def arm_unreadable_register():
    print("\nARM 6 -- RED: a file that LOOKS like a register but parses to 0 entries and is")
    print("         not hand-declared must REFUSE. An unparsed register is a hole, and a")
    print("         hole reported as a clean result is the defect this task is about.")
    d = synth('echo nothing\n',
              extra={"capture/rig/OTHER-SUPERSEDES.md": "# prose, no parseable entries\n"})
    rc, out = run_census(d)
    check("an unparseable, undeclared register -> REFUSE, exit 2", rc == 2, "rc=%d" % rc)
    check("it names the file it could not read", "OTHER-SUPERSEDES.md" in out)
    shutil.rmtree(d)


def arm_findings_survive_a_refusal():
    print("\nARM 7 -- RED+RED: a refusal must NOT suppress a real finding. One unreadable")
    print("         register silencing every violation would be fail-open at the top level.")
    d = synth('python3 "$DIR/../../capture/rig/old-guard.py"\n',
              extra={"capture/rig/OTHER-SUPERSEDES.md": "# prose, no parseable entries\n"})
    rc, out = run_census(d)
    check("exit is 2 (refusal outranks), as the guard's own contract says", rc == 2,
          "rc=%d" % rc)
    check("but the FINDING is still printed in full, not swallowed",
          "EXECUTES the superseded old-guard.py IN PLACE" in out)
    shutil.rmtree(d)


def arm_selector_is_failable():
    print("\nARM 8 -- RED: is the SELECTOR SELF-TEST itself failable? Blind the selector and")
    print("         the census must abort, not report a clean tree it never inspected.")
    d = tempfile.mkdtemp(prefix="t270-red-sel.")
    blinded = os.path.join(d, "census-blinded.py")
    src = open(CENSUS).read()
    assert 'PY_RUNNERS = {"run", "call"' in src, "PY_RUNNERS literal moved; update this arm"
    with open(blinded, "w") as f:
        f.write(src.replace('PY_RUNNERS = {"run", "call"', 'PY_RUNNERS = {"NOTHING", "call"'))
    p = subprocess.run([sys.executable, blinded, "--root", SOFTHOUSE],
                       capture_output=True, text=True)
    out = p.stdout + p.stderr
    check("a blinded selector ABORTS rather than reporting a clean census",
          p.returncode != 0 and "SELECTOR SELF-TEST FAILED" in out,
          "rc=%d" % p.returncode)
    check("and it never prints the PASS verdict line",
          not any(l.startswith("PASS --") for l in out.split("\n")))
    shutil.rmtree(d)


# ===================================================================== CONTROL B
def arm_runall_is_fail_closed():
    print("\nARM 9 -- RED: is run-all.sh section 8 FAIL-CLOSED? Delete the SUPERSEDED.txt")
    print("         redirect and it must REFUSE. If it fell back to the frozen guard, the")
    print("         fix would undo itself the moment somebody tidied the register.")
    d = tempfile.mkdtemp(prefix="t270-red-runall.")
    rig = os.path.join(d, "capture", "tierA-a2")
    rev = os.path.join(d, "reviews", "A2-11")
    os.makedirs(rig)
    os.makedirs(rev)
    for n in ("SUPERSEDED.txt", "guard-parse-float-ast.py", "prove-mkreq7-guard-red.py",
              "PARSE-FLOAT-EXEMPT.txt", "MANIFEST.sha256", "analyze7.py"):
        shutil.copy(os.path.join(RIG, n), rig)
    shutil.copy(os.path.join(A2_11, "resolve-supersession.py"), rev)

    def section8(register_text):
        with open(os.path.join(rig, "SUPERSEDED.txt"), "w") as f:
            f.write(register_text)
        script = os.path.join(rev, "s8.sh")
        with open(script, "w") as f:
            f.write('#!/bin/bash\nDIR="%s"\nRIG="%s"\n' % (rev, rig))
            f.write('if REPL="$(python3 "$DIR/resolve-supersession.py" '
                    '"$RIG/SUPERSEDED.txt" prove-mkreq7-guard-red.py)"; then\n'
                    '  echo "RESOLVED: $REPL"\n'
                    '  python3 "$RIG/$REPL"; echo "exit=$?"\n'
                    'else\n  echo "exit=2  (REFUSED)"\nfi\n')
        p = subprocess.run(["bash", script], capture_output=True, text=True)
        return p.stdout + p.stderr

    good = open(os.path.join(RIG, "SUPERSEDED.txt")).read()
    out = section8(good)
    # NB the scratch rig holds only the handful of files this arm copies, so the
    # replacement's own verdict is not meaningful here; what IS asserted is that the
    # redirect resolves and the REPLACEMENT is the thing that runs.
    check("GREEN with the register intact: it resolves and RUNS THE REPLACEMENT",
          "RESOLVED: guard-parse-float-ast.py" in out
          and "json.load/loads call-site guard" in out)
    check("GREEN and the superseded guard's own banner is ABSENT from the output",
          "16 assertions" not in out)

    out = section8("# every redirect removed\n")
    check("RED  with the redirect deleted: it REFUSES", "REFUSED" in out)
    check("RED  and it does NOT fall back to running the superseded guard — the string "
          "`16 assertions, 0 failed` never appears", "16 assertions" not in out)
    check("RED  the refusal says why",
          "resolves nothing" in out or "does not name a replacement" in out)

    out = section8("prove-mkreq7-guard-red.py -> does-not-exist.py\n")
    check("RED  a redirect to a MISSING replacement also REFUSES, rather than running "
          "either file", "REFUSED" in out and "16 assertions" not in out)
    shutil.rmtree(d)


def arm_real_tree():
    print("\nARM 10 -- THE DELIVERED TREE, MEASURED (P-22: see the changed state, do not")
    print("          infer it). The census is run against the REAL .softhouse/ root.")
    rc, out = run_census(SOFTHOUSE)
    block = ""
    for chunk in out.split("\n  prove-mkreq7-guard-red.py\n")[1:]:
        block = chunk.split("\n  ")[0]
    check("on the delivered tree, prove-mkreq7-guard-red.py is graded PRESERVED",
          "PRESERVED, not executed" in block, block.strip().split("\n")[0].strip())
    check("and it is not reported as executed in place anywhere",
          "EXECUTES the superseded prove-mkreq7-guard-red.py" not in out)
    check("the bytes of the frozen file are still what MANIFEST.sha256 pins — preserving "
          "the bytes is the OTHER half of the obligation and is not assumed here",
          frozen_bytes_unmoved(), frozen_bytes_detail())


def frozen_digest():
    import hashlib
    h = hashlib.sha256()
    with open(os.path.join(RIG, "prove-mkreq7-guard-red.py"), "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def manifest_pin():
    for line in open(os.path.join(RIG, "MANIFEST.sha256")):
        h, _, rel = line.rstrip("\n").partition("  ")
        if rel == "prove-mkreq7-guard-red.py":
            return h
    return None


def frozen_bytes_unmoved():
    return frozen_digest() == manifest_pin()


def frozen_bytes_detail():
    return "sha256 %s ; MANIFEST pins %s" % (frozen_digest()[:16], (manifest_pin() or "")[:16])


if __name__ == "__main__":
    print("=" * 78)
    print("T270 — RED/GREEN for the superseded-artefact controls")
    print("=" * 78)
    arm_reproduce()
    arm_fixed()
    arm_mention_is_not_execution()
    arm_argument_is_not_execution()
    arm_sandbox_copy()
    arm_nil_coverage()
    arm_unreadable_register()
    arm_findings_survive_a_refusal()
    arm_selector_is_failable()
    arm_runall_is_fail_closed()
    arm_real_tree()
    print("\n%d assertions, %d failed" % (ARMS, len(FAILURES)))
    for f in FAILURES:
        print("  FAILED: " + f)
    sys.exit(1 if FAILURES else 0)
