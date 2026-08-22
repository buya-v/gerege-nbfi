#!/usr/bin/env python3
"""
T238 -- THE MULTI-LINE AXIS.

EVERY sweep in this program has been LINE-ORIENTED. T234 measured 743 matches spanning a
newline across 161 files, outside the reach of every one of them. PR-7 predicted that the
fail-open class has instances whose defect straddles a line break and is therefore invisible
to a line-oriented instrument. This tests that.

ENGINE AND FLAGS, declared per P-33/P-53:
    python3 re, DOTALL + IGNORECASE, over the whole file as ONE string.
    Python `re` implements \\b \\d \\s \\w properly -- unlike `git grep -E`, which reads them
    as literals and returns zero SILENTLY (re-measured at 477dc2d, transcripts/00-engines.txt).

P-72 CALIBRATION IS MANDATORY AND IS ENFORCED: this script REFUSES to report any negative
until it has found a known positive that is, by construction, split across a newline.
Exit 0 measured / 91 empty corpus / 92 calibration missed.
"""
import os
import re
import sys
import subprocess

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT:
    print("ABORT (91): not in a git work tree", file=sys.stderr)
    sys.exit(91)
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
         .stdout.split("\n") if f.endswith((".sh", ".py", ".md"))]
if not files:
    print("ABORT (91): corpus empty. A sweep over nothing proves nothing (P-35).", file=sys.stderr)
    sys.exit(91)

# ---------------------------------------------------------------- P-72 calibration
CAL_FILE = ".softhouse/capture/t238-failopen/evidence/engine-calibration-corpus.txt"
CAL_RE = re.compile(r'no\s+other\s+site\s+exists', re.I | re.S)
try:
    cal_txt = open(CAL_FILE, encoding="utf-8", errors="replace").read()
except OSError:
    print("ABORT (92): calibration corpus missing: %s" % CAL_FILE, file=sys.stderr)
    sys.exit(92)
if "\n" not in cal_txt[cal_txt.lower().find("no other"):][:40]:
    print("ABORT (92): calibration corpus no longer splits the known positive across a newline; "
          "the calibration would not prove multi-line reach.", file=sys.stderr)
    sys.exit(92)
if not CAL_RE.search(cal_txt):
    print("ABORT (92): CALIBRATION MISSED a known positive that IS present and IS split across "
          "a newline. No negative from this run is interpretable (P-72).", file=sys.stderr)
    sys.exit(92)
# and the control: a line-oriented engine must MISS it, or the calibration proves nothing
line_hit = any(CAL_RE.search(l) for l in cal_txt.splitlines())
print("T238 MULTI-LINE SWEEP")
print("commit      : %s" % HEAD)
print("corpus      : %d tracked .sh/.py/.md files" % len(files))
print("engine      : python3 re, DOTALL|IGNORECASE, whole-file")
print("CALIBRATION : PASS — the split known positive IS found multi-line; "
      "line-oriented control finds it: %s" % line_hit)
print("              (the control MUST be False, else the calibration proves nothing)")
if line_hit:
    print("ABORT (92): the control matched line-oriented too; calibration is not discriminating.",
          file=sys.stderr)
    sys.exit(92)
print()

# ---------------------------------------------------------------- the sweep
# Fail-open shapes whose two halves can sit on different lines. Line-oriented sweeps cannot
# see any of these; that is precisely why they have never been counted.
PATTERNS = [
    ("ML-1  cd ... <newline> ... || echo",  # lint-failopen: ok -- this is a PATTERN LITERAL describing the defect, not an instance of it
     r'\bcd\s+["\']?[^\n]{3,120}\n[^\n]{0,200}\|\|\s*(?:echo|printf)'),
    ("ML-2  search ... <newline> continuation ... || echo",
     r'(?:git\s+grep|grep)\s[^\n]{0,200}\\\n[^\n]{0,200}\|\|\s*(?:echo|printf)'),
    ("ML-3  a `||` arm on its OWN line following a search",
     r'(?:git\s+grep|grep)\s[^\n]{0,200}\n\s*\|\|\s*(?:echo|printf|true|:)'),
    ("ML-4  for-in-command-substitution spanning a newline",
     r'for\s+\w+\s+in\s+\$\([^\n)]{0,200}\n[^)]{0,200}\)'),
    ("ML-5  closure claim split across a newline",
     r'(?:population\s+is\s+closed|no\s+other\s+(?:site|instance|occurrence)\s+exists'
     r'|does\s+not\s+exist\s+anywhere)'),
]

total = 0
for label, rx in PATTERNS:
    cre = re.compile(rx, re.I | re.S)
    ml_only = []
    for f in files:
        if f.startswith(".softhouse/capture/t238-failopen/"):
            continue
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if len(txt) > 4_000_000:
            continue
        for m in cre.finditer(txt):
            frag = m.group(0)
            if "\n" not in frag:
                continue                       # a line-oriented sweep would already have it
            line = txt[:m.start()].count("\n") + 1
            ml_only.append((f, line, " / ".join(frag.split("\n"))[:150]))
    print("########## %s" % label)
    print("##########   regex: %s" % rx[:120])
    if ml_only:
        total += len(ml_only)
        for f, ln, frag in ml_only[:12]:
            print("   %s:%d  %s" % (f, ln, frag))
        if len(ml_only) > 12:
            print("   ... and %d more" % (len(ml_only) - 12))
    else:
        print("   MEASURED ZERO (engine ran over %d files and matched nothing spanning a newline)"
              % len(files))
    print("   multi-line-ONLY matches: %d" % len(ml_only))
    print()

print("==================================================================")
print("MULTILINE-RESULT: commit=%s corpus=%d patterns=%d multiline_only_matches=%d calibration=PASS"
      % (HEAD[:7], len(files), len(PATTERNS), total))
print()
print("READ THIS CAREFULLY. A multi-line-ONLY match is one whose matched text CONTAINS a newline.")
print("No line-oriented sweep in this program -- and that is all of them -- could have found one.")
sys.exit(0)
