#!/usr/bin/env python3
"""T440 point 4 sweep: find the DEFECTIVE PIPESTATUS shape anywhere in the harness.

The shape: a statement that reads ${PIPESTATUS[n]} (which itself REPLACES PIPESTATUS with the
one-element array holding that statement's own status), followed by ANOTHER read of PIPESTATUS
before the next pipeline. The second read is stale-or-unbound, and under `set -u` the script
dies with status 1 -- indistinguishable from a guard that caught a failing arm.

SAFE shape: `p=( "${PIPESTATUS[@]}" )` -- one statement, whole array.
Also safe: exactly ONE read per pipeline.

The denominator is printed. A census that says "0 found" without saying how many it looked at
is the fail-open it is hunting.
"""
import re, subprocess, sys, os

root = sys.argv[1]
files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split()
PS = re.compile(r'\$\{PIPESTATUS\[')
PSIDX = re.compile(r'\$\{PIPESTATUS\[([0-9@*]+)\]')
# a pipeline: a `|` that is not `||`, not inside an obvious comment
PIPE = re.compile(r'(?<!\|)\|(?!\|)')

scanned = 0
withps = []
findings = []
safe_whole_array = []

for f in files:
    p = os.path.join(root, f)
    if not (f.endswith(".sh") or f.endswith(".bash") or f.endswith(".patch") or f.endswith(".py")):
        continue
    try:
        lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    except Exception:
        continue
    scanned += 1
    hits = [(i, l) for i, l in enumerate(lines) if PS.search(l)]
    if not hits:
        continue
    withps.append((f, len(hits)))
    # walk the file; track whether a pipeline has run since the last PIPESTATUS-reading statement
    last_read = None   # (lineno, text)
    for i, l in enumerate(lines):
        stripped = l.strip()
        is_comment = stripped.startswith("#") or stripped.startswith("+#") or stripped.startswith("-#")
        if PS.search(l) and not is_comment:
            idx = PSIDX.search(l)
            whole = idx and idx.group(1) in ("@", "*")
            nreads = len(PS.findall(l))
            if whole and nreads == 1:
                safe_whole_array.append((f, i + 1, stripped))
                last_read = None
                continue
            # if this same line contains a pipeline BEFORE the read, PIPESTATUS is fresh
            first_read = PS.search(l).start()
            pm = PIPE.search(l)
            if pm is not None and pm.start() < first_read:
                last_read = None
            if last_read is not None:
                findings.append((f, last_read[0], last_read[1], i + 1, stripped))
            last_read = (i + 1, stripped)
        elif PIPE.search(l) and not is_comment:
            # a new pipeline resets PIPESTATUS
            last_read = None

print("T440 PIPESTATUS SHAPE CENSUS")
print("  root:", root)
print("  tracked .sh/.bash/.py/.patch files scanned (DENOMINATOR):", scanned)
print("  of those, files mentioning PIPESTATUS:", len(withps))
for f, n in sorted(withps):
    print("      %-88s %d mention(s)" % (f, n))
print()
print("  SAFE whole-array copies `( \"${PIPESTATUS[@]}\" )`:", len(safe_whole_array))
for f, ln, t in safe_whole_array:
    print("      %s:%d  %s" % (f, ln, t[:100]))
print()
print("  DEFECTIVE SHAPE (a second PIPESTATUS read with no intervening pipeline):", len(findings))
for f, l1, t1, l2, t2 in findings:
    print("      %s:%d -> :%d" % (f, l1, l2))
    print("          %s" % t1[:110])
    print("          %s" % t2[:110])
print()
print("T440-PS-CENSUS-RESULT: scanned=%d withps=%d defective=%d safe_whole=%d"
      % (scanned, len(withps), len(findings), len(safe_whole_array)))
