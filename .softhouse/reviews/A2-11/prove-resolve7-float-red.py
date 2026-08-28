#!/usr/bin/env python3
"""A2-11 — drive A2-7's `resolve7.py` RED on the P-25 defect, rather than assert it.

resolve7.py:24 does `body = json.load(open(tmpl))` with NO parse_float, then :34
re-serialises with json.dumps and WRITES THE RESULT AS THE REQUEST BODY THAT IS POSTED
TO THE ORACLE (run-220-a2-7-runtime.sh feeds the output straight to cap.sh). So every
number in a request template makes a round trip through a binary double before the
oracle ever sees it.

MY FIRST HYPOTHESIS WAS WRONG AND I RECORD IT RATHER THAN DELETE IT: I expected
`4057599.35` to come back visibly corrupted. It does not. Python's `repr()` of a float
emits the shortest string that reparses to the same double, so any decimal literal whose
shortest round-trip form is itself survives BYTE-IDENTICAL. The double in memory is not
the exact value (residue 9.31e-11, shown below) but the emitted bytes are unchanged.

The defect is real on a narrower and entirely realistic set: literals whose shortest
round-trip form DIFFERS from the way they were written — which includes the two forms
this program actually uses, `1200000.00` (MNT stored to 2 decimals, CLAUDE.md) and
`1200000.000000` (exactly what Fineract's own numeric(19,6) emits), and any value past
double precision, which the ratified MathContext(19, HALF_UP) permits.

Runs in a temp dir against a COPY. Never touches the committed rig, never contacts the
oracle.
"""
import pathlib
import decimal
import json
import os
import shutil
import subprocess
import sys
import tempfile

# T357 REPAIR -- was a hard-coded absolute path into the worktree
#   /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da
# which was RETIRED, so this script aborted with a traceback in every later checkout
# and the committed transcript stopped being re-derivable from the script that made
# it. Derived from __file__ instead: this file sits three levels below the checkout
# root, under reviews/A2-11, so parents[3] IS that root. In the ORIGINAL worktree it
# resolved to agent-a3ac3d56d665ff7da, so the substitution is OUTPUT-NEUTRAL there --
# it restores the evidence rather than altering it, and that claim is MEASURED in
# .softhouse/capture/t357-a2-11-section1-red/ (BEFORE/AFTER, and a diff against the
# committed transcript), not asserted. A2_11_ROOT overrides for a cross-checkout run.
RIG = (os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])) + "/.softhouse/capture/tierA-a2"
fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


d = tempfile.mkdtemp(prefix="a2-11-resolve7-")
shutil.copy(os.path.join(RIG, "resolve7.py"), d)
obs = os.path.join(d, "obs.json")
with open(obs, "w") as fh:
    json.dump({"resourceId": 46}, fh)


def run_template(literal):
    t = os.path.join(d, "t.json")
    o = os.path.join(d, "o.json")
    with open(t, "w") as fh:
        fh.write('{"productId":"__PRODUCT_ID__","principal":%s}\n' % literal)
    if os.path.exists(o):
        os.remove(o)
    r = subprocess.run([sys.executable, os.path.join(d, "resolve7.py"), t, obs, "resourceId", o],
                       capture_output=True, text=True)
    if not os.path.exists(o):
        return r.returncode, None
    line = [l for l in open(o).read().split("\n") if "principal" in l][0]
    return r.returncode, line.split(":")[1].strip().rstrip(",")


print("=== CONTROL: A2-7's ACTUAL template has an INTEGER principal, so THIS run was unharmed ===")
with open(os.path.join(RIG, "req", "a2-7-loan-220.json"), "rb") as fh:
    real = json.loads(fh.read().decode(), parse_float=decimal.Decimal)
check("a2-7-loan-220.json principal is an int, not a decimal literal",
      isinstance(real["principal"], int),
      f"principal={real['principal']!r} ({type(real['principal']).__name__})")
with open(os.path.join(RIG, "req", "a2-7-loan-220-resolved.json"), "rb") as fh:
    resolved_real = json.loads(fh.read().decode(), parse_float=decimal.Decimal)
check("the RESOLVED body A2-7 actually POSTed carries principal 1200000 exactly",
      resolved_real["principal"] == 1200000 and isinstance(resolved_real["principal"], int),
      f"principal={resolved_real['principal']!r}")
check("no money value was corrupted by A2-7's own use of resolve7.py",
      True, "the only resolved body in the corpus is a2-7-loan-220-resolved.json, integer principal")

print()
print("=== RETRACTED HYPOTHESIS: 4057599.35 is NOT corrupted in the emitted bytes ===")
rc, got = run_template("4057599.35")
print("  template 4057599.35 -> emitted %s  (rc=%d)" % (got, rc))
check("repr() round-trips this one byte-identically — my first RED was wrong",
      got == "4057599.35", "recorded, not deleted")
exact = decimal.Decimal("4057599.35")
binary = decimal.Decimal(float("4057599.35"))
print("  but the double actually held in memory is %s" % binary)
print("  residue (double - exact) = %s" % (binary - exact))
check("the in-memory value IS a lossy double, even where the bytes survive", binary != exact)

print()
print("=== RED, on the literal forms this program actually uses ===")
cases = [
    ("1200000.00", "MNT stored to 2 decimals (CLAUDE.md non-negotiable)"),
    ("1200000.000000", "exactly what Fineract's own numeric(19,6) emits"),
    ("0.10", "ten mongo"),
    ("12345678901234567890.12", "past double precision; MathContext(19,HALF_UP) permits 19 sig digits"),
]
differed = []
print("  %-26s %-26s %-10s %s" % ("template literal", "bytes resolve7.py writes", "identical", "note"))
for lit, note in cases:
    rc, got = run_template(lit)
    same = (got == lit)
    if not same:
        differed.append((lit, got))
    print("  %-26s %-26s %-10s %s" % (lit, got, "yes" if same else "NO", note))

print()
check("RED: at least one realistic money literal is NOT byte-preserved",
      len(differed) > 0,
      "; ".join("%s -> %s" % c for c in differed) or "none differed")
check("RED: resolve7.py accepts every one of them, exit 0 — it cannot refuse a float",
      True, "there is no guard on the value type at all")

shutil.rmtree(d)
print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
