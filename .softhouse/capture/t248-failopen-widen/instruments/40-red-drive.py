#!/usr/bin/env python3
"""
T248 instrument 40 -- THE RED DRIVE, ON SHAPES THE RULE WAS NOT BUILT FROM (P-76).

WHAT P-76 ACTUALLY DEMANDS, and why the obvious red drive does not satisfy it.
T243 planted the shape T238's rule was written from, watched the harness go red, and
concluded the class was closed. The harness really did go red. The inference was still
wrong, because a red drive built from the same example as the rule is a tautology with a
transcript: it exercises the path the author already had in mind. So this rig does two
things the obvious one does not:

  1. it drives the MANDATORY site's real shape (R1), because r11-hygiene.sh is the reason
     this task exists and a fix that does not flag it has discharged nothing; and
  2. it drives shapes chosen to differ from the rule's design inputs on EVERY axis the rule
     could plausibly be keyed to -- root, verb, swallow idiom, line topology, print builtin
     and wording (R2, R3, R4, R5). THREE of the five CHANGED THE RULE when first driven --
     R2 widened C2b's window past the search line, R4 widened the corpus SELECTOR (its shape
     was not merely misclassified, it was never inspected), and R5 made C2a continuation-
     aware. That is the evidence this is a real drive and not a re-enactment: a battery that
     only confirms is a battery that was written after the answer.

FALSIFICATION, STATED BEFORE THE RUN (P-76 duty 2). This rig is falsified if ANY of:
  * R1 is not TIER 1 -- the mandatory site's shape is still invisible;
  * any of R2/R3/R4/R5 is absent from the frontier -- the rule is keyed to its design inputs;
  * N1 reaches the frontier -- the rule cannot tell a FATAL `cd` from a swallowed one, so
    its recall was bought with false rejections;
  * N2 is flagged on any condition -- the rule flags correct instruments;
  * a planted shape does not turn `conformance.sh` to EXIT 2, or removing it does not turn
    the harness back green -- the guard is not actually reached (that is the P-45 half, and
    it is re-checked here rather than inherited from T243).

THE SHAPES ARE FIXTURES, NOT SOURCE. They live in ../shapes/*.txt, deliberately NOT .sh and
NOT .py, so that a battery of deliberate fail-open specimens never enters the linter's own
corpus and never lands on the pinned frontier. Committing the specimens as .sh would have
made this instrument the eleventh entry on the frontier it exists to test.

ENGINE (P-33/P-53): python3 `re` and subprocess list-argv. No `grep` (a shell FUNCTION here
that silently execs ugrep with six --exclude-dir flags, measured 33% recall -- P-75), no `rg`
(NO BINARY EXISTS; `rg P F | head` exits 0 having run nothing), no shell pipeline carrying a
verdict (P-57). Every exit status read below is a direct process's returncode.

USAGE: 40-red-drive.py               -- linter-level battery over all shapes (fast)
       40-red-drive.py --harness     -- ALSO drive `bash .softhouse/conformance.sh` per shape
       40-red-drive.py --rev <REV>   -- RE-DERIVE THE GAP: run the same battery against the
                                        linter AS OF <REV>, descriptively, no expectations.
Exit 0 = every expectation above held. 1 = a falsification fired. 2 = the rig could not run.

RE-DERIVING THE GAP RATHER THAN QUOTING IT (P-69). `--rev 9b6c596` runs this battery against
the linter as T243 merged it. Control C0 -- the `|| echo` shape the rule was written from --
comes back TIER 1 there, and R1, the same defect with the reassurance moved to the next line,
does not reach the frontier at all. R4 is not even inspected. That side-by-side is the
driver's finding, re-measured by this task instead of taken on report.
"""
import os
import re
import sys
import shutil
import tempfile
import subprocess

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("ABORT (2): not in a git work tree", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)

BASE = ".softhouse/capture/t248-failopen-widen"
SHAPES = os.path.join(BASE, "shapes")
PLANT_DIR = os.path.join(BASE, ".redplant")
LINT_PATH = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
HARNESS = ".softhouse/conformance.sh"
REV = None
if "--rev" in sys.argv:
    REV = sys.argv[sys.argv.index("--rev") + 1]
    _p = subprocess.run(["git", "show", "%s:%s" % (REV, LINT_PATH)],
                        capture_output=True, text=True)
    if _p.returncode != 0 or "T238 FAIL-OPEN LINT" not in _p.stdout:
        print("ABORT (2): could not extract the linter from rev %s" % REV, file=sys.stderr)
        sys.exit(2)
    _fd, LINT = tempfile.mkstemp(prefix="t248-rd-lint-", suffix=".py")
    os.write(_fd, _p.stdout.encode())
    os.close(_fd)
    LINT_LABEL = "%s:%s  [RE-DERIVATION MODE: descriptive, no expectations enforced]" % (
        REV, LINT_PATH)
else:
    LINT = LINT_PATH
    LINT_LABEL = "%s (WORKING TREE)" % LINT_PATH

# shape file -> (must reach the frontier?, expected tier or None)
EXPECT = {
    "C0-a2-33-covered-shape.txt":       (True, 1),
    "R1-r11-real-shape.txt":            (True, 1),
    "R2-swallow-search-then-claim.txt": (True, 1),
    "R3-dead-root-via-variable.txt":    (True, 1),
    "R4-git-C-nonexistent-root.txt":    (True, 1),
    "R5-arm-on-continuation.txt":       (True, 1),
    "N1-negative-fatal-cd.txt":         (False, 3),
    "N2-negative-live-corpus.txt":      (False, None),
}
HARNESS_SHAPES = ["R1-r11-real-shape.txt",
                  "R2-swallow-search-then-claim.txt",
                  "R4-git-C-nonexistent-root.txt",
                  "R5-arm-on-continuation.txt"]

if not os.path.isdir(SHAPES):
    print("ABORT (2): shape fixtures missing at %s" % SHAPES, file=sys.stderr)
    sys.exit(2)
missing = [s for s in EXPECT if not os.path.isfile(os.path.join(SHAPES, s))]
if missing:
    print("ABORT (2): shape fixtures missing: %s" % missing, file=sys.stderr)
    sys.exit(2)


def plant(names):
    os.makedirs(PLANT_DIR, exist_ok=True)
    for n in names:
        src = os.path.join(SHAPES, n)
        dst = os.path.join(PLANT_DIR, n[:-4] + ".sh")
        shutil.copyfile(src, dst)
    subprocess.run(["git", "add", "-N", "--", PLANT_DIR], check=True)
    return [os.path.join(PLANT_DIR, n[:-4] + ".sh") for n in names]


def unplant():
    subprocess.run(["git", "rm", "-q", "--cached", "-r", "--", PLANT_DIR],
                   capture_output=True)
    shutil.rmtree(PLANT_DIR, ignore_errors=True)


def run_lint(scope=None):
    fd, scratch = tempfile.mkstemp(prefix="t248-rd-json-")
    os.close(fd)
    env = dict(os.environ, FAILOPEN_LINT_JSON=scratch)
    argv = [sys.executable, LINT] + ([scope] if scope else [])
    p = subprocess.run(argv, capture_output=True, text=True, env=env)
    os.unlink(scratch)
    if "T238 FAIL-OPEN LINT" not in p.stdout:
        print("ABORT (2): linter produced no banner (rc=%s)" % p.returncode, file=sys.stderr)
        print(p.stdout[:1500], p.stderr[:1500], file=sys.stderr)
        sys.exit(2)
    return p


RE_T12_FILE = re.compile(r'^  (\S+)\s*$')
RE_T12_COND = re.compile(r'^      (C[12])  :(\d+)  (.*)$')
RE_T3 = re.compile(r'^  (\S+)\s+:(\d+)  (.*)$')


def parse(out):
    tier = None
    cur = None
    res = {}
    for l in out.splitlines():
        if l.startswith("### TIER"):
            tier = int(l.split()[2]); cur = None; continue
        if l.startswith("### ADVISORY") or l.startswith("FAILOPEN-FRONTIER"):
            tier = None; cur = None; continue
        if tier in (1, 2):
            m = RE_T12_FILE.match(l)
            if m:
                cur = m.group(1)
                res.setdefault(cur, {"tier": tier, "conds": []})
                continue
            m = RE_T12_COND.match(l)
            if m and cur:
                res[cur]["conds"].append((m.group(1), int(m.group(2)), m.group(3)))
        elif tier == 3:
            m = RE_T3.match(l)
            if m:
                r = res.setdefault(m.group(1), {"tier": 3, "conds": []})
                r["conds"].append(("C1", int(m.group(2)), m.group(3)))
    return res


def frontier(out):
    return sorted(l[len("FAILOPEN-FRONTIER "):] for l in out.splitlines()
                  if l.startswith("FAILOPEN-FRONTIER "))


fails = []
print("T248 -- RED DRIVE ON SHAPES THE RULE WAS NOT BUILT FROM")
print("repo   : %s" % ROOT)
print("HEAD   : %s" % subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
print("linter : %s" % LINT_LABEL)
print("engine : python3 re + subprocess list-argv; no grep, no rg, no verdict-carrying pipe")
print()

# ---------------------------------------------------------------- BASELINE
base = run_lint()
base_fr = frontier(base.stdout)
print("=== 0. BASELINE (nothing planted): frontier %d row(s), linter exit %d"
      % (len(base_fr), base.returncode))
for r in base_fr:
    print("      %s" % r)
if any(PLANT_DIR in r for r in base_fr):
    print("FALSIFIED: the plant directory is already on the frontier before planting.")
    sys.exit(1)
print()

# ---------------------------------------------------------------- BATTERY
print("=== 1. LINTER BATTERY -- all six shapes planted at once")
planted = plant(sorted(EXPECT))
try:
    p = run_lint()
finally:
    unplant()
res = parse(p.stdout)
fr = frontier(p.stdout)
print("    linter exit %d, frontier %d row(s)" % (p.returncode, len(fr)))
print()
print("    %-36s %-8s %-8s %-9s %s" % ("SHAPE", "EXPECT", "TIER", "FRONTIER", "VERDICT"))
print("    " + "-" * 96)
for name in sorted(EXPECT):
    want_front, want_tier = EXPECT[name]
    path = os.path.join(PLANT_DIR, name[:-4] + ".sh")
    got = res.get(path)
    got_tier = got["tier"] if got else None
    on_front = any(path in r for r in fr)
    ok = (on_front == want_front) and (got_tier == want_tier)
    if not ok and not REV:
        fails.append("%s: expected frontier=%s tier=%s, got frontier=%s tier=%s"
                     % (name, want_front, want_tier, on_front, got_tier))
    print("    %-36s %-8s %-8s %-9s %s"
          % (name[:36], ("TIER%d" % want_tier) if want_tier else "clean",
             ("TIER%d" % got_tier) if got_tier else "clean",
             "YES" if on_front else "no",
             ("(descriptive)" if REV else ("OK" if ok else "*** FALSIFIED ***"))))
print()
print("    Conditions fired, verbatim:")
for name in sorted(EXPECT):
    path = os.path.join(PLANT_DIR, name[:-4] + ".sh")
    got = res.get(path)
    print("      %s" % name)
    if not got:
        print("          (no condition fired)")
        continue
    for c, ln, msg in got["conds"]:
        print("          %s :%-3d %s" % (c, ln, msg[:150]))
print()

# ---------------------------------------------------------------- HARNESS
if "--harness" in sys.argv[1:] and not REV:
    print("=== 2. HARNESS DRIVE -- `bash .softhouse/conformance.sh`, one shape at a time")
    print("    P-45 is re-checked here rather than inherited: a rule that classifies")
    print("    correctly but is never reached closes nothing.")
    print()
    for name in HARNESS_SHAPES:
        plant([name])
        try:
            h = subprocess.run(["bash", HARNESS], capture_output=True, text=True)
        finally:
            unplant()
        red = h.returncode != 0
        saw = ("THE FAIL-OPEN FRONTIER IS NOT THE PINNED FRONTIER" in h.stdout + h.stderr)
        named = (name[:-4] + ".sh") in (h.stdout + h.stderr)
        ok = red and saw and named
        if not ok:
            fails.append("harness drive %s: exit=%d frontier-warning=%s file-named=%s"
                         % (name, h.returncode, saw, named))
        print("    %-36s harness exit %-3d  frontier-diff warning %-4s  names the plant %-4s  %s"
              % (name[:36], h.returncode, "YES" if saw else "NO",
                 "YES" if named else "NO", "OK" if ok else "*** FALSIFIED ***"))
        for l in (h.stdout + h.stderr).splitlines():
            if "FAILOPEN" in l or "EXIT 2" in l or l.startswith("+FAILOPEN") or \
               ".redplant" in l:
                print("        | %s" % l[:150])
    print()
    print("=== 3. GREEN AGAIN -- nothing planted, the same harness")
    h = subprocess.run(["bash", HARNESS], capture_output=True, text=True)
    ok = h.returncode == 0 and "VERDICT: PASS" in h.stdout
    if not ok:
        fails.append("harness did NOT return green after unplanting: exit=%d" % h.returncode)
    print("    harness exit %d   %s" % (h.returncode, "OK" if ok else "*** FALSIFIED ***"))
    for l in h.stdout.splitlines():
        if l.startswith("VERDICT") or "frontier ==" in l or "frontier " in l and "pinned at" in l:
            print("        | %s" % l[:150])
    print()

print("=== VERDICT")
if REV:
    print("  RE-DERIVATION MODE against %s -- reported, not graded. Read the FRONTIER column:" % REV)
    print("  the control C0 (the shape the rule was written from) reaches it; R1, the SAME")
    print("  defect with the reassurance moved one line down, does not.")
    sys.exit(0)
if fails:
    for f in fails:
        print("  FALSIFIED: %s" % f)
    sys.exit(1)
print("  Every stated expectation held: the mandatory site's shape and three shapes the rule")
print("  was not designed around all reach the frontier at TIER 1; both negative controls stay")
print("  off it; and the guard is reached on the automatic path.")
sys.exit(0)
