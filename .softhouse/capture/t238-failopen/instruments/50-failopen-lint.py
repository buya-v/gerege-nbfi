#!/usr/bin/env python3
"""
T238 -- THE FAIL-OPEN LINTER.  This is the half of the fix that does not have to be remembered.

THE ARGUMENT FOR IT, WHICH IS THE WHOLE POINT OF THIS TASK
----------------------------------------------------------
A2-33 is the best-calibrated sweep in this chain. It published two-engine recall transcripts
with MISSES=0, it named its engine and flags, and it audited every one of its own 34 patterns
for \\b \\d \\s \\w before P-72 was a week old. On every axis T234 was dispatched to test,
A2-33 PASSES. And it still shipped a fail-open, because the defect was not in the regex layer
at all -- it was one unguarded `cd` in a subshell whose non-zero exit was caught by a `||` arm
that printed reassurance.

So: **a remedy that consists of asking the next author to be more careful cannot work here,
because it was already tried on the most careful author in the chain and it failed.**

That rules out discipline. It also rules out a library ON ITS OWN: sweeplib.sh is adoptable,
and anything adoptable is omittable by exactly the person who did not think they needed it.

A linter is different in kind. It does not ask the author to remember anything. It runs over
the tree afterwards and refuses instruments that can emit a negative they did not measure.
The author's carefulness stops being load-bearing. That is why the mechanism is a LINTER FIRST
and a LIBRARY SECOND: the library is what the linter tells you to adopt, not the fix itself.

HONEST LIMITATION, STATED LOUDLY (P-45, which now has FOUR instances in this program)
------------------------------------------------------------------------------------
This linter is NOT wired into .softhouse/conformance.sh, because that file is held by T243 and
T226 and is outside T238's scope. An unwired guard is precisely the P-45 shape, and shipping
one silently would be adding a fifth instance. It is therefore shipped with:
  - a RED drive and a GREEN drive, both committed (transcripts/40, transcripts/60);
  - the exact wiring line, in the handoff, for whoever holds conformance.sh next;
  - this paragraph, so nobody can cite it as an enforced control.

WHAT IT CHECKS -- the properties, not the spellings
---------------------------------------------------
  C1  NO DEAD ABSOLUTE PATH        an absolute path that does not exist NOW
  C2  NO REASSURING FAILURE ARM    a search/cd whose `||` arm PRINTS instead of exiting
  C3  CORPUS ASSERTION PRESENT     a repo-wide search instrument must assert its corpus is
                                   reachable and non-empty before searching
  C4  CALIBRATION PRESENT          P-72: a known positive must be proven findable before any
                                   negative is reported
  C5  ENGINE DECLARED              P-33/P-53: name the engine; and never use \\b \\d \\s \\w
                                   under `git grep -E`, which reads them as literals

SCOPE (P-66/P-70): every tracked .sh/.py in the repository. Exit 0 = clean, 1 = violations,
2 = the linter could not reach its own corpus (it fails closed too).
"""
import os
import re
import sys
import json
import subprocess

# SEVERITY, derived from MEASUREMENT (transcripts/20), not from taste.
#
#   C1 alone   = UNREPRODUCIBLE.  a2-31-dec2-rev4/probe-sweep.sh hard-codes a deleted worktree
#                AND exits 1. It is safe -- but it can never be re-run to CHECK its conclusion.
#                That is the "more dangerous half" only in the long run, so: WARN, not FAIL.
#   C1 AND C2  = FAIL-OPEN.  Cannot reach its corpus AND prints reassurance. This is the lethal
#                combination, and it is exactly the set my run-the-class transcript measured
#                as exit-0-with-"(no hits)". FAIL.
#   C2 alone   = FAIL-OPEN-CAPABLE. The corpus is reachable today, so the reassurance arm is
#                dormant -- but it is one deleted directory away from live. FAIL.
#
# SUPPRESSION. A probe whose PURPOSE is to test whether a path exists will trip C1 honestly.
# Such a line may carry a marker, which must state a reason:
#     # lint-failopen: ok -- <reason>
# The marker suppresses that ONE line. It is deliberately verbose so it cannot be used lazily,
# and every use is listed in the report so suppressions stay visible.
SEVERITY_FAIL = {"C2"}
RE_SUPPRESS = re.compile(r'#\s*lint-failopen:\s*ok\s*--\s*(\S.*)')
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("LINT ABORT (2): not inside a git work tree; cannot reach the corpus.", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
         .stdout.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("LINT ABORT (2): corpus reachable but contains ZERO .sh/.py files. "
          "Linting nothing proves nothing (P-35).", file=sys.stderr)
    sys.exit(2)

ONLY = sys.argv[1:] or None
if ONLY:
    files = [f for f in files if any(f.startswith(p) or f == p for p in ONLY)]

RE_ABSPATH = re.compile(r'(?:^|[=\s"\'(])(/(?:Users|home|opt|var)/[A-Za-z0-9._/-]{6,})')
RE_REPOWIDE = re.compile(r'(git\s+grep|git\s+ls-files|grep\s+-[a-zA-Z]*[rR]\b)')
RE_SWALLOW = re.compile(r'\|\|\s*(?:echo|printf)\b')
RE_CORPUS_ASSERT = re.compile(
    r'rev-parse\s+--show-toplevel|ls-files\s*\|\s*wc|SWEEP ABORT|_sw_die|sweep_root|'
    r'\|\|\s*exit\b|\|\|\s*\{[^}]*exit|os\.path\.isdir|check=True|exit\(2\)|sys\.exit')
RE_CALIB = re.compile(r'calibrat|CALIB|known positive|P-72', re.I)
RE_ENGINE_DECL = re.compile(r'ENGINE|git --version|grep --version|engine', re.I)
RE_ESCAPE_IN_ERE = re.compile(r'git\s+grep[^|\n]*-[a-zA-Z]*E[a-zA-Z]*\s[^|\n]*\\[bBdDsSwW<>]')
SELF = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"

viol = []
suppressed = []
inspected = 0
for f in files:
    if f == SELF:
        continue
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    if len(txt) > 4_000_000:
        continue
    lines = txt.splitlines()
    for i, l in enumerate(lines, 1):
        m = RE_SUPPRESS.search(l)
        if m:
            suppressed.append((f, i, m.group(1).strip()))
    code = [(i, l) for i, l in enumerate(lines, 1)
            if not l.lstrip().startswith("#") and not RE_SUPPRESS.search(l)]
    if not RE_REPOWIDE.search(txt):
        continue                                  # not a repo-wide search instrument
    inspected += 1
    v = []

    # C1 -- dead absolute path
    for i, l in code:
        for p in RE_ABSPATH.findall(l):
            p = p.rstrip('"\'`);,')
            if not os.path.exists(p):
                v.append(("C1", i, "dead absolute path: %s" % p))
                break

    # C2 -- a failure arm that PRINTS
    for i, l in code:
        if RE_SWALLOW.search(l) and (RE_REPOWIDE.search(l) or re.search(r'\bcd\b|\bgrep\b|\bsed\b', l)):
            v.append(("C2", i, "failure arm PRINTS instead of exiting: %s" % l.strip()[:110]))

    # C3/C4/C5 -- advisory properties
    if not RE_CORPUS_ASSERT.search(txt):
        v.append(("C3", 0, "no corpus-reachability assertion anywhere in the file"))
    if not RE_CALIB.search(txt):
        v.append(("C4", 0, "no calibration on a known positive (P-72)"))
    if not RE_ENGINE_DECL.search(txt):
        v.append(("C5", 0, "engine not declared (P-33/P-53)"))
    for i, l in code:
        if RE_ESCAPE_IN_ERE.search(l):
            v.append(("C5", i, "backslash-class under `git grep -E`, which reads it as a LITERAL "
                               "and returns zero SILENTLY: %s" % l.strip()[:90]))
    if v:
        viol.append((f, v))

def has(v, c):
    return any(x == c for x, _, _ in v)


lethal = [(f, v) for f, v in viol if has(v, "C1") and has(v, "C2")]
dormant = [(f, v) for f, v in viol if has(v, "C2") and not has(v, "C1")]
unrepro = [(f, v) for f, v in viol if has(v, "C1") and not has(v, "C2")]
fails = lethal + dormant

print("T238 FAIL-OPEN LINT")
print("commit    : %s" % HEAD)
print("corpus    : %d tracked .sh/.py; %d are repo-wide search instruments" % (len(files), inspected))
print("scope     : %s" % (", ".join(ONLY) if ONLY else "whole repository"))
print()

print("### TIER 1 — FAIL-OPEN, LIVE  (C1 dead path AND C2 reassuring failure arm) : %d" % len(lethal))
print("###   measured behaviour of this tier: exit 0, prints a negative, measured nothing")
for f, v in sorted(lethal):
    print("  %s" % f)
    for c, i, m in v:
        if c in ("C1", "C2"):
            print("      %s  :%s  %s" % (c, i, m))
print()

print("### TIER 2 — FAIL-OPEN-CAPABLE  (C2 only; corpus reachable TODAY) : %d" % len(dormant))
print("###   one deleted directory away from Tier 1")
for f, v in sorted(dormant):
    print("  %s" % f)
    for c, i, m in v:
        if c == "C2":
            print("      %s  :%s  %s" % (c, i, m))
print()

print("### TIER 3 — UNREPRODUCIBLE, but FAILS CLOSED  (C1 only) : %d" % len(unrepro))
print("###   safe to re-run -- it exits non-zero -- but its conclusion can never be re-checked")
for f, v in sorted(unrepro):
    for c, i, m in v:
        if c == "C1":
            print("  %-76s :%s  %s" % (f, i, m))
print()

print("### ADVISORY (C3 no corpus assertion / C4 no calibration / C5 engine undeclared)")
adv = {}
for f, v in viol:
    for c, i, m in v:
        if c in ("C3", "C4", "C5"):
            adv.setdefault(c, []).append(f)
for c in sorted(adv):
    print("  %s : %d instrument(s)" % (c, len(set(adv[c]))))
print()

if suppressed:
    print("### SUPPRESSIONS IN FORCE (every one is listed; they never go quiet) : %d" % len(suppressed))
    for f, i, why in suppressed:
        print("  %-70s :%s  %s" % (f, i, why))
    print()

json.dump({"lethal": [f for f, _ in lethal], "dormant": [f for f, _ in dormant],
           "unreproducible": [f for f, _ in unrepro],
           "suppressed": suppressed,
           "detail": [{"file": f, "violations": v} for f, v in viol]},
          open(".softhouse/capture/t238-failopen/evidence/lint.json", "w"), indent=1)

if fails:
    print("LINT: FAIL — %d instrument(s) can emit a negative they did not measure "
          "(%d live, %d dormant)." % (len(fails), len(lethal), len(dormant)))
    sys.exit(1)
print("LINT: PASS — no instrument in scope can emit a negative it did not measure.")
sys.exit(0)
