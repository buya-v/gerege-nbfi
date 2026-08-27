#!/usr/bin/env python3
"""T164 -- drive guard-parse-float-ast.py RED, then GREEN. Transcript:
RED-GREEN-T164-parse-float-ast.txt

  python3 prove-parse-float-guard-red.py   -> exit 0 only if every arm behaves as asserted

P-22: a guard you have not personally driven red is worse than no guard, because it is
believed. The defect this file exists to close is EXACTLY that -- `prove-mkreq7-guard-
red.py:143` asserted the no-float property with a WHOLE-FILE SOURCE GREP:

    check("it parses JSON numbers as Decimal", "parse_float=decimal.Decimal" in src)

and `parse_float=decimal.Decimal` occurs TWICE in `analyze7.py`, once at line 39 in the
code and once at line 6 in the file's OWN DOCSTRING. ARM 0 below deletes the keyword from
the CODE and shows the old guard STILL PASSES. Every later arm shows the AST guard does
not.

T114: nothing here touches a committed byte. Every arm runs against a scratch copy of the
rig in a throwaway temp directory; `prove-mkreq7-guard-red.py`, `analyze7.py`,
`resolve7.py` and `verify-provenance-a2-15.py` are left byte-identical on disk. Nothing
here contacts the oracle.

THE ARMS
  0   REPRODUCTION -- old grep guard stays GREEN with parse_float deleted from the CODE
  1   the same sabotage makes the AST guard FAIL, naming analyze7.py:39
  2   the LEGITIMATE rig, untouched, still PASSES
  3   ZERO CALL SITES INSPECTED is an ERROR, not a pass       (the fail-open half)
  4   ZERO PYTHON FILES is an ERROR, not a pass
  5   a file the guard cannot parse is an ERROR, not a skip
  6   an ALIASED loader (`import json as J`) cannot hide a site
  7   a `from json import loads as L` loader cannot hide a site either
  8   `parse_float=float` -- a keyword that satisfies a grep and changes nothing -- FAILS
  9   a register record whose site does not exist            -> REFUSE (stale)
  10  a register record whose site now carries parse_float   -> REFUSE (stale)
  11  a register record whose pinned source has drifted      -> REFUSE
  12  an unknown register category                           -> REFUSE, never a skip
  13  FROZEN-T114 dies the moment the file is edited (sha256 no longer matches)
  14  REPRODUCTION-T207 is GREEN while the target still lacks parse_float
  15  REPRODUCTION-T207 dies the moment the target is FIXED
  16  the selector self-test is itself failable
"""
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
GUARD = "guard-parse-float-ast.py"
REGISTER = "PARSE-FLOAT-EXEMPT.txt"
FAILURES = []
CASES = 0

# Files the register's FROZEN preconditions name; the scratch root needs them present.
EVIDENCE = ("RED-GREEN-A2-7-guards.txt", "PROVENANCE-A2-15.txt", "MANIFEST.sha256")
EVIDENCE_SUB = ("req/a2-7-loan-220-resolved.json",)


def check(label, cond, detail=""):
    global CASES
    CASES += 1
    detail = detail if isinstance(detail, str) else repr(detail)
    print(("  ok   " if cond else "  FAIL ") + label + (("\n         " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


def scratch():
    """A throwaway copy of the rig: every .py, the register, and the named evidence."""
    d = tempfile.mkdtemp(prefix="t164-guard.")
    for n in sorted(os.listdir(DIR)):
        p = os.path.join(DIR, n)
        if os.path.isfile(p) and (n.endswith(".py") or n == REGISTER or n in EVIDENCE):
            shutil.copy(p, os.path.join(d, n))
    for rel in EVIDENCE_SUB:
        src = os.path.join(DIR, rel)
        if os.path.exists(src):
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            shutil.copy(src, os.path.join(d, rel))
    return d


def run_guard(root):
    p = subprocess.run([sys.executable, os.path.join(DIR, GUARD), "--root", root],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def edit(root, name, old, new, expect=1):
    p = os.path.join(root, name)
    src = open(p).read()
    if src.count(old) != expect:
        raise SystemExit("PROVER BUG: %r occurs %d time(s) in %s, expected %d"
                         % (old, src.count(old), name, expect))
    open(p, "w").write(src.replace(old, new))


def append_register(root, line):
    with open(os.path.join(root, REGISTER), "a") as f:
        f.write(line + "\n")


# --------------------------------------------------------------------------- ARM 0 + 1
def arm_reproduction_and_fix():
    print("ARM 0 -- REPRODUCE: the OLD grep guard stays GREEN with parse_float deleted "
          "from analyze7.py's CODE")
    d = scratch()
    edit(d, "analyze7.py",
         "        return json.load(f, parse_float=decimal.Decimal)\n",
         "        return json.load(f)\n")
    lines = open(os.path.join(d, "analyze7.py")).read().split("\n")
    occ = [i + 1 for i, l in enumerate(lines) if "parse_float" in l]
    print("         analyze7.py:39 is now: %r" % lines[38].strip())
    print("         `parse_float` now occurs on line(s) %s -- the DOCSTRING only:" % occ)
    for i in occ:
        print("           %d: %s" % (i, lines[i - 1].strip()))

    # the old guard, verbatim from prove-mkreq7-guard-red.py:142-144
    src = open(os.path.join(d, "analyze7.py")).read()
    old_a = "parse_float=decimal.Decimal" in src
    old_b = "float(" not in src.replace("parse_float=", "")
    check("OLD guard assertion 1 `\"parse_float=decimal.Decimal\" in src` still TRUE "
          "-> it still reports ok", old_a is True, "value=%r" % old_a)
    check("OLD guard assertion 2 `\"float(\" not in src...` still TRUE", old_b is True,
          "value=%r" % old_b)
    check("OLD guard verdict on the SABOTAGED rig: PASS (this is the defect)",
          old_a and old_b, "0 failures -> exit 0")

    # and what the sabotage actually does
    r = subprocess.run(
        [sys.executable, "-c",
         "import json;print(type(json.load(open(%r))['pageItems'][0]['amount']).__name__)"
         % os.path.join(DIR, "out", "A2-235-je-after-recovery.json")],
        capture_output=True, text=True)
    check("meanwhile the sabotaged loader really does build a binary double",
          r.stdout.strip() == "float", "an oracle amount now loads as type %r" % r.stdout.strip())
    print()

    print("ARM 1 -- the SAME sabotage makes the AST guard FAIL, and it names the line")
    rc, out, err = run_guard(d)
    check("AST guard exits 1 (FAIL) where the old guard exited 0", rc == 1, "rc=%d" % rc)
    check("it names analyze7.py:39 as the violation", "analyze7.py:39" in err,
          [l for l in err.split("\n") if "analyze7" in l][:2])
    check("it reports exactly 1 violation",
          "VIOLATIONS .......................... 1" in out,
          [l for l in out.split("\n") if "VIOLATION" in l][:2])
    check("the docstring occurrence did NOT rescue it",
          "analyze7.py:6" not in out and "analyze7.py:6" not in err)
    shutil.rmtree(d)
    print()


# ----------------------------------------------------------------------------- ARM 2
def arm_legitimate_green():
    print("ARM 2 -- the LEGITIMATE rig, untouched, still PASSES")
    d = scratch()
    rc, out, err = run_guard(d)
    check("AST guard exits 0 on the real rig", rc == 0, "rc=%d stderr=%r" % (rc, err[:200]))
    check("and it says how much it inspected, positively (P-35)",
          "CALL SITES inspected" in out and "PASS --" in out,
          [l.strip() for l in out.split("\n") if "inspected" in l][:3])
    n = [l for l in out.split("\n") if "CALL SITES inspected" in l]
    check("the population it inspected is non-zero and stated", bool(n) and "0" != n[0].split()[-1],
          n[0].strip() if n else "")
    shutil.rmtree(d)
    print()


# ------------------------------------------------------------------- ARM 3, 4, 5
def arm_nil_coverage():
    print("ARM 3 -- ZERO CALL SITES INSPECTED is an ERROR, not a pass (the fail-open half)")
    d = tempfile.mkdtemp(prefix="t164-nosites.")
    open(os.path.join(d, "inert.py"), "w").write(
        '"""parse_float=decimal.Decimal -- a docstring decoy and nothing else."""\n'
        "X = 1\n")
    rc, out, err = run_guard(d)
    check("a root with Python files but NO json.load call sites exits 2, not 0", rc == 2,
          "rc=%d" % rc)
    check("and it says so in the NIL COVERAGE / INSPECTED NOTHING shape",
          "NIL COVERAGE" in err and "INSPECTED NOTHING" in err,
          err.strip().split("\n")[-1][:160])
    check("it did NOT report a pass", "PASS --" not in out)
    shutil.rmtree(d)
    print()

    print("ARM 4 -- ZERO PYTHON FILES is an ERROR, not a pass")
    d = tempfile.mkdtemp(prefix="t164-empty.")
    rc, out, err = run_guard(d)
    check("an empty root exits 2, not 0", rc == 2, "rc=%d" % rc)
    check("and it says 0 Python files, INSPECTED NOTHING",
          "0 Python files" in err and "INSPECTED NOTHING" in err,
          err.strip().split("\n")[-1][:160])
    shutil.rmtree(d)
    print()

    print("ARM 5 -- a file the guard cannot PARSE is an ERROR, not a silent skip")
    d = scratch()
    open(os.path.join(d, "broken.py"), "w").write("def (:\n")
    rc, out, err = run_guard(d)
    check("an unparseable file exits 2", rc == 2, "rc=%d" % rc)
    check("and it names the file rather than dropping it", "broken.py" in err,
          err.strip().split("\n")[-1][:160])
    shutil.rmtree(d)
    print()


# ------------------------------------------------------------------------ ARM 6, 7, 8
def arm_selector():
    print("ARM 6 -- an ALIASED loader cannot hide a site (`import json as J`)")
    d = scratch()
    open(os.path.join(d, "aliased.py"), "w").write(
        '"""parse_float=decimal.Decimal appears here, in the docstring, and nowhere else."""\n'
        "import json as J\n"
        'v = J.load(open("x"))\n')
    rc, out, err = run_guard(d)
    check("the aliased call site is FOUND and fails the guard", rc == 1, "rc=%d" % rc)
    check("it names aliased.py:3", "aliased.py:3" in err,
          [l.strip() for l in err.split("\n") if "aliased" in l][:2])
    shutil.rmtree(d)
    print()

    print("ARM 7 -- `from json import loads as L` cannot hide a site either")
    d = scratch()
    open(os.path.join(d, "fromimp.py"), "w").write(
        "from json import loads as L\n"
        'v = L("{}")\n')
    rc, out, err = run_guard(d)
    check("the bare-name call site is FOUND and fails the guard", rc == 1, "rc=%d" % rc)
    check("it names fromimp.py:2", "fromimp.py:2" in err,
          [l.strip() for l in err.split("\n") if "fromimp" in l][:2])
    shutil.rmtree(d)
    print()

    print("ARM 8 -- `parse_float=float` satisfies a grep and changes NOTHING; it FAILS")
    d = scratch()
    open(os.path.join(d, "dodge.py"), "w").write(
        "import json\n"
        'v = json.load(open("x"), parse_float=float)\n')
    rc, out, err = run_guard(d)
    check("parse_float=float is a violation, not a pass", rc == 1, "rc=%d" % rc)
    check("and it is named as a no-op", "no-op" in err,
          [l.strip() for l in err.split("\n") if "dodge" in l][:2])
    check("the dodge is counted separately in the population",
          "parse_float=float (a dodge)  1" in out,
          [l.strip() for l in out.split("\n") if "dodge" in l][:1])
    shutil.rmtree(d)
    print()


# --------------------------------------------------------------- ARM 9..13: the register
def arm_register():
    print("ARM 9 -- a register record naming a site that DOES NOT EXIST is a REFUSAL")
    d = scratch()
    append_register(d, "analyze7.py | 9999 | FROZEN-T114 | nothing here | "
                       "produced:MANIFEST.sha256 | invented")
    rc, out, err = run_guard(d)
    check("a stale record exits 2 (REFUSE), not 0 and not 1", rc == 2, "rc=%d" % rc)
    check("and it is named STALE", "STALE" in out and "stale" in err,
          [l.strip() for l in err.split("\n") if "9999" in l][:1])
    shutil.rmtree(d)
    print()

    print("ARM 10 -- a register record for a site that NOW CARRIES parse_float is a REFUSAL")
    d = scratch()
    append_register(d, "analyze7.py | 39 | FROZEN-T114 | "
                       "return json.load(f, parse_float=decimal.Decimal) | "
                       "produced:MANIFEST.sha256 | an exemption nobody needs")
    rc, out, err = run_guard(d)
    check("an unnecessary exemption exits 2, so the register cannot silently rot", rc == 2,
          "rc=%d" % rc)
    check("and it says the site is already compliant",
          "already carries parse_float" in err or "already compliant" in out,
          [l.strip() for l in err.split("\n") if "analyze7" in l][:1])
    shutil.rmtree(d)
    print()

    print("ARM 11 -- a record whose PINNED SOURCE has drifted is a REFUSAL")
    d = scratch()
    edit(d, "resolve7.py", "    body = json.load(open(tmpl))",
         "    body = json.load(open(tmpl))  # a comment that moves nothing else")
    rc, out, err = run_guard(d)
    check("changing the exempted line's text exits 2", rc == 2, "rc=%d" % rc)
    check("and the drift is named", "drifted" in err or "DRIFT" in out,
          [l.strip() for l in out.split("\n") if "DRIFT" in l][:1])
    shutil.rmtree(d)
    print()

    print("ARM 12 -- an UNKNOWN register category is a REFUSAL, never a silent skip")
    d = scratch()
    append_register(d, "analyze7.py | 39 | LOOKS-FINE-TO-ME | x | y | z")
    rc, out, err = run_guard(d)
    check("an unrecognised category exits 2", rc == 2, "rc=%d" % rc)
    check("and it says a category it does not recognise is a refusal",
          "not one of" in err, err.strip().split("\n")[-1][:160])
    shutil.rmtree(d)
    print()

    print("ARM 13 -- FROZEN-T114 dies the moment the file is EDITED (T114 is the whole "
          "point: a file being edited is not frozen)")
    d = scratch()
    with open(os.path.join(d, "verify-provenance-a2-15.py"), "a") as f:
        f.write("# one byte appended AT EOF, so line 24 does not move: this is a sha256\n"
                "# change and nothing else, which is exactly what T114 forbids silently.\n")
    rc, out, err = run_guard(d)
    check("editing an exempted frozen file exits 2", rc == 2, "rc=%d" % rc)
    check("and the refusal says the file has been edited",
          "HAS BEEN EDITED" in err or "HAS BEEN EDITED" in out,
          [l.strip() for l in err.split("\n") if "EDITED" in l][:1])
    shutil.rmtree(d)
    print()


# ------------------------------------------------------------------- ARM 14, 15: T207
def arm_reproduction_category():
    print("ARM 14 -- REPRODUCTION-T207 is GREEN while the target still lacks parse_float "
          "(T207: 'add parse_float' is sometimes the WRONG repair)")
    d = scratch()
    os.makedirs(os.path.join(d, "under-measurement"), exist_ok=True)
    open(os.path.join(d, "under-measurement", "target.py"), "w").write(
        "import json\n"
        "import decimal\n"
        'CFG = json.load(open("cfg"), parse_float=decimal.Decimal)\n'
        'DOC = json.load(open("doc"))\n')          # line 4: the unfixed target
    open(os.path.join(d, "measurer.py"), "w").write(
        "import json\n"
        'A = json.load(open("f"))\n')              # line 2: reproduces line 4 above
    append_register(d, 'measurer.py | 2 | REPRODUCTION-T207 | A = json.load(open("f")) | '
                       "reproduces:under-measurement/target.py:4 | "
                       "byte-for-byte the target's own loading; fixing it would make the "
                       "measurer report what a tool that does not exist would see")
    rc, out, err = run_guard(d)
    check("a declared faithful reproduction does NOT fail the guard", rc == 0,
          "rc=%d stderr=%r" % (rc, err[:200]))
    check("and it is printed with its precondition outcome, not hidden",
          "REPRODUCTION-T207" in out and "faithful" in out,
          [l.strip() for l in out.split("\n") if "REPRODUCTION-T207" in l][:1])

    print("ARM 15 -- ... and it DIES the moment the target is FIXED")
    edit(d, os.path.join("under-measurement", "target.py"),
         'DOC = json.load(open("doc"))\n',
         'DOC = json.load(open("doc"), parse_float=decimal.Decimal)\n')
    rc, out, err = run_guard(d)
    check("fixing the target makes the exemption stale -> exit 2", rc == 2, "rc=%d" % rc)
    check("and the refusal says the target was fixed so this is no longer faithful",
          "NOW CARRIES parse_float" in err,
          [l.strip() for l in err.split("\n") if "NOW CARRIES" in l][:1])
    shutil.rmtree(d)
    print()


# ------------------------------------------------------------------------------ ARM 16
def arm_selftest_is_failable():
    print("ARM 16 -- the SELECTOR SELF-TEST is itself failable (a self-test that cannot "
          "fail is the same defect one level up)")
    d = tempfile.mkdtemp(prefix="t164-selftest.")
    g = os.path.join(d, GUARD)
    src = open(os.path.join(DIR, GUARD)).read()
    # blind the selector exactly the way an alias-unaware implementation would be blind
    src = src.replace('LOADERS = ("load", "loads")', 'LOADERS = ("load",)')
    open(g, "w").write(src)
    p = subprocess.run([sys.executable, g, "--root", DIR], capture_output=True, text=True)
    check("a selector that has stopped selecting REFUSES rather than reporting an absence",
          p.returncode == 2, "rc=%d" % p.returncode)
    check("and it says the self-test failed",
          "SELECTOR SELF-TEST FAILED" in p.stderr, p.stderr.strip().split("\n")[-1][:160])
    shutil.rmtree(d)
    print()


if __name__ == "__main__":
    print("=" * 78)
    print("T164 -- RED/GREEN drive of guard-parse-float-ast.py")
    print("=" * 78)
    print()
    arm_reproduction_and_fix()
    arm_legitimate_green()
    arm_nil_coverage()
    arm_selector()
    arm_register()
    arm_reproduction_category()
    arm_selftest_is_failable()
    print("%d assertions, %d failed" % (CASES, len(FAILURES)))
    for f in FAILURES:
        print("  FAILED: " + f)
    sys.exit(1 if FAILURES else 0)
