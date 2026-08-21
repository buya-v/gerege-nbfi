#!/usr/bin/env python3
"""A2-11 — P-22: are A2-7's 16 assertions genuinely FALSIFIABLE, or vacuous?

Running A2-7's prover and seeing "16 assertions, 0 failed" proves nothing about the
prover — a check that cannot fail also prints 0 failed. So this SABOTAGES the guarded
scripts, one mutation at a time, in a throwaway copy of the whole rig directory, and
asserts that A2-7's prover NOTICES. A mutation the prover sleeps through is a vacuous
assertion.

Never touches the committed rig; never contacts the oracle.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

RIG = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da/.softhouse/capture/tierA-a2"
PROVER = "prove-mkreq7-guard-red.py"
fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def run_prover_with(mutations):
    """Copy the rig scripts into a temp dir, apply mutations, run A2-7's prover there."""
    d = tempfile.mkdtemp(prefix="a2-11-falsify-")
    for f in (PROVER, "mkreq7.py", "resolve7.py", "analyze7.py"):
        shutil.copy(os.path.join(RIG, f), d)
    os.makedirs(os.path.join(d, "out"), exist_ok=True)
    shutil.copy(os.path.join(RIG, "out", "A2-235-je-after-recovery.json"), os.path.join(d, "out"))
    for fname, old, new in mutations:
        p = os.path.join(d, fname)
        src = open(p).read()
        if old not in src:
            shutil.rmtree(d)
            return None, "MUTATION TARGET NOT FOUND in %s: %r" % (fname, old[:70])
        open(p, "w").write(src.replace(old, new, 1))
    r = subprocess.run([sys.executable, os.path.join(d, PROVER)], capture_output=True, text=True)
    shutil.rmtree(d)
    return r, None


print("=== BASELINE: the unmutated prover on an unmutated copy ===")
r, err = run_prover_with([])
assert err is None, err
n_ok = len(re.findall(r"^  ok ", r.stdout, re.M))
n_fail = len(re.findall(r"^  FAIL ", r.stdout, re.M))
print("  exit=%d  ok=%d  FAIL=%d   last line: %s" % (r.returncode, n_ok, n_fail, r.stdout.strip().split("\n")[-1]))
check("baseline: exit 0 and exactly 16 assertions, none failed",
      r.returncode == 0 and n_ok == 16 and n_fail == 0)

print()
print("=== SABOTAGE 1 — remove mkreq7.py's D-1 abort (the guard the prover exists for) ===")
mk = open(os.path.join(RIG, "mkreq7.py")).read()
m = re.search(r"^.*(sys\.exit|raise SystemExit|return 1).*$", mk, re.M)
print("  mkreq7.py's abort line:", (m.group(0).strip() if m else "<not found>"))
r, err = run_prover_with([("mkreq7.py", m.group(0), "        pass  # sabotaged by A2-11")])
if err:
    print("  " + err)
    check("sabotage 1 could be applied", False, err)
else:
    n_fail = len(re.findall(r"^  FAIL ", r.stdout, re.M))
    print("  exit=%d  FAIL=%d" % (r.returncode, n_fail))
    for line in r.stdout.split("\n"):
        if line.startswith("  FAIL"):
            print("     " + line.strip())
    check("RED: removing the abort makes A2-7's prover FAIL (assertion is falsifiable)",
          r.returncode != 0 and n_fail > 0, "exit=%d fails=%d" % (r.returncode, n_fail))

print()
print("=== SABOTAGE 2 — make resolve7.py INVENT a value instead of refusing ===")
r, err = run_prover_with([("resolve7.py",
                           "    if key not in resp:",
                           "    if key not in resp:\n        resp[key] = 999999\n    if False:")])
if err:
    print("  " + err)
    check("sabotage 2 could be applied", False, err)
else:
    n_fail = len(re.findall(r"^  FAIL ", r.stdout, re.M))
    print("  exit=%d  FAIL=%d" % (r.returncode, n_fail))
    for line in r.stdout.split("\n"):
        if line.startswith("  FAIL"):
            print("     " + line.strip())
    check("RED: an inventing resolve7.py makes the prover FAIL",
          r.returncode != 0 and n_fail > 0, "exit=%d fails=%d" % (r.returncode, n_fail))

print()
print("=== SABOTAGE 3 — drop parse_float from analyze7.py's CODE, leaving its docstring ===")
print("  NOTE: `parse_float=decimal.Decimal` appears TWICE in analyze7.py — once in the")
print("  module docstring (line 6) and once in the code (line 39). A2-7's assertion is a")
print("  substring search over the WHOLE FILE, so mutating only the code leaves it green.")
r, err = run_prover_with([("analyze7.py",
                           "return json.load(f, parse_float=decimal.Decimal)",
                           "return json.load(f)")])
if err:
    print("  " + err)
    check("sabotage 3 could be applied", False, err)
else:
    n_fail = len(re.findall(r"^  FAIL ", r.stdout, re.M))
    print("  exit=%d  FAIL=%d" % (r.returncode, n_fail))
    for line in r.stdout.split("\n"):
        if line.startswith("  FAIL"):
            print("     " + line.strip())
    check("KNOWN LIMIT: removing parse_float from the CODE leaves A2-7's assertion GREEN, "
          "because it greps the whole file including the docstring",
          r.returncode == 0 and n_fail == 0,
          "exit=%d fails=%d — the assertion is real but is a source grep, not a behaviour test"
          % (r.returncode, n_fail))

print()
print("=== SABOTAGE 4 — the KNOWN-WEAK arm: analyze7.py's float guard is a SOURCE GREP ===")
print("  A2-7 asserts \"it never calls bare float()\" by string search on its own source:")
print('      check("it never calls bare float()", "float(" not in src.replace("parse_float=", ""))')
print("  So a float introduced by any OTHER spelling is invisible to it. Demonstrating:")
r, err = run_prover_with([("analyze7.py", "debits = decimal.Decimal(0)",
                           "debits = decimal.Decimal(0)\n    _sabotage = __builtins__.__dict__['float']('0.1') + 0.2")])
if err:
    print("  " + err)
else:
    n_fail = len(re.findall(r"^  FAIL ", r.stdout, re.M))
    print("  exit=%d  FAIL=%d  <- a binary-float expression was inserted into the money script" % (r.returncode, n_fail))
    check("KNOWN LIMIT (not a defect A2-7 hid — it is stated as a source check): "
          "a float reached by an alias is NOT caught",
          r.returncode == 0 and n_fail == 0,
          "the prover still reports 0 failures; recorded as a stated blind spot")

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
