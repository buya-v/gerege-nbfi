#!/usr/bin/env python3
"""T252 instrument 20 -- IS A NUMERIC-CLAIM DETECTOR THE FIX? MEASURE, DO NOT ASSUME.

T252's brief proposes one: "a count is a claim too". The proposal is CORRECT as an
observation and the question is whether the OBVIOUS implementation of it -- add numeric
claim shapes to RE_REASSURE, the vocabulary C2b already consults -- actually closes the
gap. This probe answers that black-box, against the real linter and the real tree.

It measures THREE things, in this order, because the order is the argument:

  V0  BASELINE. What the shipped linter (T248, at HEAD) reports for the confirmed site.

  V1  THE NUMERIC VOCABULARY, ALONE. RE_REASSURE is widened with count shapes -- `: 0`,
      `= 0`, `0 <noun>`, `{var}`, `%d`, `$n` -- and the linter re-run. Does the confirmed
      site become visible? And what does the widening cost on the rest of the tree?

  V2  WHY, structurally. Two INDEPENDENT reasons are checked directly against the subject
      file, so the answer does not rest on V1 coming out one way:
        (a) C2b's print predicate is RE_UNCOND_PRINT = ^\\s*(echo|printf) -- SHELL ONLY.
            The subject's false count is emitted by `print(...)` inside a `python3 - <<PY`
            heredoc. No vocabulary reaches a line the print predicate never admits.
        (b) C2b associates a claim with a `cd` only inside C2B_WINDOW = 3 code lines.
            The subject's `cd` is at :24 and its false count at :142.
      Both are measured as DISTANCES and COUNTS here, not asserted.

ENGINE (P-33/P-53): pure `python3 re` over file bytes. No shell search engine is used, so
none of ugrep's --exclude-dir shadowing (P-75) and none of `git grep -E`'s literal-\\b
fabrication can reach these numbers.
"""
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
assert ROOT and os.path.isdir(ROOT), "T252-20 ABORT: not in a git work tree"
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

LINT = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
SUBJ = ".softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh"

print("T252 -- IS A NUMERIC-CLAIM DETECTOR THE FIX?")
print("commit  : %s" % HEAD)
print("linter  : %s (the version in the WORKING TREE)" % LINT)
print("subject : %s" % SUBJ)
print()

shipped = open(LINT, encoding="utf-8").read()
subj_lines = open(SUBJ, encoding="utf-8").read().splitlines()


# Scratch lives in a mkdtemp directory, not at a hard-coded `/tmp/...` literal. The literal
# form is what C1 flags as a dead absolute path -- correctly, since a linter cannot tell a
# scratch path from a corpus path by looking -- and the honest answer is not to suppress the
# rule but to stop writing the literal. Cleaned up at exit.
SCRATCH = tempfile.mkdtemp(prefix="t252-numeric-vocab-")
atexit.register(shutil.rmtree, SCRATCH, True)


def run_variant(src, tag):
    """Write `src` to a scratch linter and run it; return (stdout, frontier rows)."""
    p = os.path.join(SCRATCH, "lint-%s.py" % tag)
    open(p, "w", encoding="utf-8").write(src)
    r = subprocess.run([sys.executable, p],
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                FAILOPEN_LINT_JSON=os.path.join(SCRATCH, "lint-%s.json" % tag)))
    rows = sorted(l.split(" ", 1)[1] for l in r.stdout.splitlines()
                  if l.startswith("FAILOPEN-FRONTIER "))
    return r.stdout, rows


# ---------------------------------------------------------------- V0
print("### V0 -- BASELINE: what the shipped (T248) linter says about the confirmed site")
out0, rows0 = run_variant(shipped, "v0")
hits0 = [l for l in out0.splitlines() if SUBJ in l]
print("  frontier rows            : %d" % len(rows0))
print("  lines mentioning subject : %d" % len(hits0))
for l in hits0:
    print("    %s" % l.strip())
tier = None
cur = None
for l in out0.splitlines():
    if l.startswith("### TIER"):
        cur = l.split("—")[0].strip().replace("### ", "")
    if SUBJ in l and cur:
        tier = cur
print("  classified as            : %s" % (tier or "<UNCLASSIFIED>"))
print("  on the frontier?         : %s" % ("YES" if any(SUBJ in r for r in rows0) else "NO"))
print()

# ---------------------------------------------------------------- V1
print("### V1 -- ADD THE NUMERIC VOCABULARY TO RE_REASSURE, CHANGE NOTHING ELSE")
NUMERIC = (r"|:\s*[0-9]+\s*$|=\s*[0-9]+\b|\b[0-9]+\s+(?:files?|lines?|instruments?|cells?|"
           r"vectors?|entries|occurrences?|instances?|sites?)\b|\{[A-Za-z_][A-Za-z0-9_]*\}|"
           r"%d\b|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?\s*$")
OLD_TAIL = r"\bexpected above\b|\bno other\b|\bno further\b|\bno remaining\b', re.I)"
assert shipped.count(OLD_TAIL) == 1, "T252-20 ABORT: RE_REASSURE tail not found verbatim"
v1 = shipped.replace(OLD_TAIL, OLD_TAIL[:-len("', re.I)")] + NUMERIC + r"', re.I)")
assert v1 != shipped
out1, rows1 = run_variant(v1, "v1")
hits1 = [l for l in out1.splitlines() if SUBJ in l]
print("  numeric alternatives added: %d" % len([x for x in NUMERIC.split("|") if x]))
print("  frontier rows  V0 -> V1   : %d -> %d" % (len(rows0), len(rows1)))
gained = [r for r in rows1 if r not in rows0]
lost = [r for r in rows0 if r not in rows1]
print("  frontier GAINED           : %d" % len(gained))
for r in gained:
    print("      + %s" % r)
print("  frontier LOST             : %d" % len(lost))
for r in lost:
    print("      - %s" % r)
print("  does V1 see the subject?  : %s"
      % ("YES" if any(SUBJ in r for r in rows1) else "NO -- STILL INVISIBLE"))
print("  lines mentioning subject  : %d" % len(hits1))
for l in hits1:
    print("    %s" % l.strip())
print()

# ---------------------------------------------------------------- V2
print("### V2 -- WHY. Two INDEPENDENT structural blocks, measured against the subject file.")
RE_UNCOND_PRINT = re.compile(r'^\s*(?:echo|printf)\b')
RE_CD = re.compile(r'(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)cd\s+\S')

claim_ln = [i for i, l in enumerate(subj_lines, 1) if "PROMOTED CELLS SWEPT" in l]
cd_ln = [i for i, l in enumerate(subj_lines, 1)
         if RE_CD.search(l) and not l.lstrip().startswith("#")]
print("  (a) THE PRINT PREDICATE IS SHELL-ONLY")
print("      RE_UNCOND_PRINT = ^\\s*(?:echo|printf)\\b")
for i in claim_ln:
    l = subj_lines[i - 1]
    print("      subject :%d  %s" % (i, l.strip()[:96]))
    print("      matches RE_UNCOND_PRINT? : %s"
          % ("YES" if RE_UNCOND_PRINT.match(l) else "NO  <-- the line is never even offered "
                                                        "to the vocabulary"))
n_py_print = sum(1 for l in subj_lines if re.match(r'^\s*print\(', l))
n_sh_print = sum(1 for l in subj_lines if RE_UNCOND_PRINT.match(l))
print("      subject's print statements: %d shell echo/printf, %d python print( "
      "-- BOTH TERMS (P-67)" % (n_sh_print, n_py_print))
print("      of the %d python print( lines, how many carry a COUNT the reader will believe:"
      % n_py_print)
for i, l in enumerate(subj_lines, 1):
    if re.match(r'^\s*print\(', l) and re.search(r'\{(?:total|bad|c_resp|cs|c)\b', l):
        print("          :%d %s" % (i, l.strip()[:92]))
print()
print("  (b) THE ASSOCIATION WINDOW IS THREE CODE LINES")
print("      C2B_WINDOW = 3")
print("      subject `cd` lines            : %s" % (cd_ln or "<none>"))
print("      subject false-count line(s)   : %s" % (claim_ln or "<none>"))
if cd_ln and claim_ln:
    d_phys = claim_ln[0] - cd_ln[0]
    body = subj_lines[cd_ln[0]:claim_ln[0] - 1]
    d_code = sum(1 for l in body if l.strip() and not l.lstrip().startswith("#"))
    print("      distance                      : %d physical lines, %d CODE lines"
          % (d_phys, d_code))
    print("      inside a window of 3?         : %s" % ("YES" if d_code <= 3 else
                                                        "NO -- %dx too far" % (d_code // 3)))
    brk = next((k + cd_ln[0] + 1 for k, l in enumerate(body)
                if l.strip() and not l.lstrip().startswith("#")
                and not RE_UNCOND_PRINT.match(l)
                and not re.search(r'git\s+(?:grep|ls-files)\b', l)), None)
    print("      first line that BREAKS the association (neither a print nor a search): :%s  %s"
          % (brk, subj_lines[brk - 1].strip()[:70] if brk else ""))
print()

print("### CONCLUSION OF THIS PROBE -- read V1 and V2 together")
print("  V1 is the direct test of the brief's own proposal and V2 explains its result")
print("  structurally, so neither rests on the other.")
