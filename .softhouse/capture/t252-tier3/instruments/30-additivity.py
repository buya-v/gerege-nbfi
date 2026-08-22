#!/usr/bin/env python3
"""T252 instrument 30 -- IS THE C6 WIDENING STRICTLY ADDITIVE?

The claim under test is not "the new linter finds more". It is the much stronger one T248
established and this task inherits: **nothing the shipped linter detected stops being
detected.** A widening that silently drops a prior detection is a regression wearing the
clothes of an improvement, and the only way to know is to run BOTH over the SAME tree and
diff every detection, not every summary line.

METHOD, and why it is diffed at this granularity:
  * SHIPPED  = the linter as committed at HEAD (`git show HEAD:<path>`), run from a scratch
               copy so the working tree is untouched.
  * WIDENED  = the linter in the working tree.
  * Both are run over the SAME checkout, in the same process environment, with their JSON
    diverted to scratch so neither dirties a tracked file.
  * A DETECTION is the triple (file, code, line) read out of each run's JSON `detail`, NOT
    out of stdout. Tier headings and wording changed in this task on purpose; keying the
    diff on rendered text would report every relabelled line as a loss and hide a real one.
  * The FRONTIER is diffed separately, as the sorted `FAILOPEN-FRONTIER` rows of stdout --
    the same BYTES conformance.sh consumes, so this measures the thing the gate reads.

ENGINE (P-33/P-53): pure `python3` -- subprocess + json. No shell search engine participates,
so ugrep's silently-prepended --exclude-dir flags (P-75, 33% recall measured) cannot reach
these numbers, and `git grep -E`'s literal-\\b fabrication cannot either.
"""
import json
import os
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
assert ROOT and os.path.isdir(ROOT), "T252-30 ABORT: not in a git work tree"
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
LINT = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"

shipped_src = subprocess.run(["git", "show", "HEAD:" + LINT],
                             capture_output=True, text=True)
assert shipped_src.returncode == 0 and shipped_src.stdout, \
    "T252-30 ABORT: cannot read the SHIPPED linter out of HEAD; there is nothing to diff against."
widened_src = open(LINT, encoding="utf-8").read()


def run(src, tag):
    p = "/tmp/t252-add-%s.py" % tag
    j = "/tmp/t252-add-%s.json" % tag
    open(p, "w", encoding="utf-8").write(src)
    r = subprocess.run([sys.executable, p], capture_output=True, text=True,
                       env=dict(os.environ, FAILOPEN_LINT_JSON=j))
    det = set()
    d = json.load(open(j))
    for e in d["detail"]:
        for code, line, _msg in e["violations"]:
            det.add((e["file"], code, line))
    front = sorted(l.split(" ", 1)[1] for l in r.stdout.splitlines()
                   if l.startswith("FAILOPEN-FRONTIER "))
    return r.returncode, det, front, d


print("T252 -- STRICT-ADDITIVITY PROOF FOR C6")
print("commit         : %s" % HEAD)
print("fork point     : %s" % subprocess.run(["git", "merge-base", "main", "HEAD"],
                                             capture_output=True, text=True).stdout.strip())
print("shipped linter : HEAD:%s  (%d bytes)" % (LINT, len(shipped_src.stdout)))
print("widened linter : working tree (%d bytes)" % len(widened_src))
print()

if shipped_src.stdout == widened_src:
    print("!!! THE TWO SOURCES ARE IDENTICAL. This proof would be vacuous -- a comparison of a")
    print("!!! file with itself always says ADDITIVE. Refusing to report a pass. (P-35)")
    sys.exit(2)

rc_a, det_a, front_a, _ja = run(shipped_src.stdout, "shipped")
rc_b, det_b, front_b, jb = run(widened_src, "widened")

print("### DETECTIONS  (file, code, line) triples out of each run's JSON `detail`")
print("  SHIPPED : %d detections, exit %d" % (len(det_a), rc_a))
print("  WIDENED : %d detections, exit %d" % (len(det_b), rc_b))
lost = sorted(det_a - det_b)
gained = sorted(det_b - det_a)
print()
print("  LOST    : %d   <-- MUST BE ZERO. A widening that drops a prior detection is a"
      % len(lost))
print("                     regression disguised as an improvement.")
for f, c, i in lost:
    print("      -  %-4s :%-5s %s" % (c, i, f))
if not lost:
    print("      (none -- every triple the shipped linter reported, the widened one reports)")
print()
print("  GAINED  : %d" % len(gained))
for f, c, i in gained:
    print("      +  %-4s :%-5s %s" % (c, i, f))
print()

print("### FRONTIER  (the FAILOPEN-FRONTIER rows -- the exact bytes conformance.sh consumes)")
print("  SHIPPED : %d rows" % len(front_a))
print("  WIDENED : %d rows" % len(front_b))
flost = [r for r in front_a if r not in front_b]
fgain = [r for r in front_b if r not in front_a]
print("  LOST    : %d" % len(flost))
for r in flost:
    print("      - %s" % r)
print("  GAINED  : %d" % len(fgain))
for r in fgain:
    print("      + %s" % r)
print()

print("### THE PINNED INSTRUMENTS -- did any of them MOVE? (the pin is a FRONTIER, not an AMNESTY)")
PINNED = [
    ".softhouse/capture/t238-failopen/evidence/red-drive/sweep-ORIGINAL.sh",
    ".softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-32-evidence/sweep.sh",
    ".softhouse/reviews/T138-evidence/r11-hygiene.sh",
    ".softhouse/capture/t234-sweep-instrument-audit/instruments/00-engine-baseline.sh",
    ".softhouse/capture/t234-sweep-instrument-audit/instruments/02-escape-matrix-fix.sh",
    ".softhouse/capture/t239-r11-rerun/instruments/00-engines.sh",
    ".softhouse/capture/t239-r11-rerun/instruments/10-population.sh",
    ".softhouse/capture/t239-r11-rerun/instruments/31-coverage.sh",
    ".softhouse/capture/t239-r11-rerun/instruments/50-red-drive.sh",
    ".softhouse/capture/t239-r11-rerun/instruments/51-run-r11-verbatim.sh",
]
moved = 0
for f in PINNED:
    a = next((r for r in front_a if r.endswith(" " + f) or r.split(" ", 1)[1] == f), None)
    b = next((r for r in front_b if r.endswith(" " + f) or r.split(" ", 1)[1] == f), None)
    ta = a.split(" ", 1)[0] if a else "<absent>"
    tb = b.split(" ", 1)[0] if b else "<absent>"
    same = "SAME" if ta == tb else "*** MOVED ***"
    if ta != tb:
        moved += 1
    print("  %-6s -> %-6s  %s  %s" % (ta, tb, same, f))
print("  pinned rows that MOVED: %d  (must be 0 -- T252 may not repair or reclassify a pinned"
      % moved)
print("                           instrument, and sweep-ORIGINAL.sh is a SPECIMEN, not an")
print("                           instrument, so it stays on the frontier permanently)")
print()

print("### TIER 3, BOTH TERMS (P-67)")
for tag, j in (("WIDENED", jb),):
    u = j["unreproducible"]
    n_find = sum(1 for e in j["detail"] if e["file"] in u
                 for c, _i, _m in e["violations"] if c == "C1")
    print("  %s : %d file(s) / %d dead-path finding(s)" % (tag, len(u), n_find))
    for f in sorted(u):
        print("      %-72s [%s]" % (f, j["unreproducible_ground"][f][:60]))
print()

ok = (not lost) and (not flost) and (moved == 0)
print("VERDICT: %s" % ("STRICTLY ADDITIVE (LOST = none, no pinned row moved)" if ok
                       else "*** NOT ADDITIVE -- see LOST / MOVED above ***"))
sys.exit(0 if ok else 1)
