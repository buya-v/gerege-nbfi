#!/usr/bin/env python3
"""T339 probe -- INDEPENDENT of T270's census.

Question this answers, and only this: for EVERY supersession register anywhere
under .softhouse/, does the basename of any superseded original occur in ANY
`run-all*.sh` in the tree, and if so is that occurrence an INTERPRETER
INVOCATION or only a mention?

Written from scratch for the review.  It does NOT import, read, or reuse
`census-superseded-invocations.py`; if the two disagree that disagreement is
the finding.

  python3 t339-runall-supersession-sweep.py <tree-root>

Exit 0 always -- this is a measuring instrument for a human, not a gate.
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SH = os.path.join(ROOT, ".softhouse")

# --- TERM 1: find registers by walking, not by being told where they are.
registers = []
for dirpath, dirnames, filenames in os.walk(SH):
    dirnames[:] = [d for d in dirnames if d not in (".git",)]
    for fn in filenames:
        low = fn.lower()
        if "supersed" in low and (low.endswith(".txt") or low.endswith(".md")):
            registers.append(os.path.join(dirpath, fn))
registers.sort()

# --- TERM 2: parse `A -> B` out of each register (same grammar the rig uses).
ARROW = re.compile(r"^\s*([A-Za-z0-9._/-]+)\s*->\s*([A-Za-z0-9._/-]+)\s*$")
entries = {}          # basename of original -> list of (register, replacement)
for reg in registers:
    n = 0
    with open(reg, errors="replace") as fh:
        for raw in fh:
            line = raw.split("#")[0]
            # markdown registers put the arrow inside backticks / list items
            line = line.replace("`", "").replace("*", "").strip().lstrip("- ")
            m = ARROW.match(line)
            if m:
                entries.setdefault(os.path.basename(m.group(1)), []).append(
                    (os.path.relpath(reg, ROOT), m.group(2)))
                n += 1
    print("REGISTER  %-70s %d entr(ies)" % (os.path.relpath(reg, ROOT), n))
print()
print("SUPERSEDED ORIGINALS DECLARED: %d" % len(entries))
for k in sorted(entries):
    print("   %-40s %s" % (k, entries[k]))
print()

# --- TERM 3: every run-all*.sh in the tree.
runalls = []
for dirpath, dirnames, filenames in os.walk(SH):
    dirnames[:] = [d for d in dirnames if d not in (".git",)]
    for fn in filenames:
        if fn.startswith("run-all") and fn.endswith(".sh"):
            runalls.append(os.path.join(dirpath, fn))
runalls.sort()
print("RUN-ALL SCRIPTS FOUND BY WALKING: %d" % len(runalls))
for r in runalls:
    print("   %s" % os.path.relpath(r, ROOT))
print()

# --- TERM 4: classify each occurrence.
# An INVOCATION is the basename appearing as the *thing being run*: after an
# interpreter word, or after `source`/`.`, or as the head of a command, and NOT
# inside an echo/comment/quoted prose.
INTERP = r"(?:python3?|python3\.\d+|bash|sh|zsh|source|\.)"
findings = []
for r in runalls:
    with open(r, errors="replace") as fh:
        for i, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            stripped = line.strip()
            for base in entries:
                if base not in line:
                    continue
                kind = "MENTIONED"
                # comment?
                if stripped.startswith("#"):
                    kind = "COMMENT"
                elif re.match(r"^\s*echo\b", stripped):
                    kind = "ECHO-PROSE"
                elif re.search(INTERP + r"\s+(?:-\S+\s+)*[\"']?[^\s\"';|&]*" +
                               re.escape(base) + r"[\"']?(?:\s|$|;|\||&|\))", line):
                    kind = "INVOCATION"
                elif re.search(r"(?:^|[;&|(]\s*)[\"']?[^\s\"';|&]*" + re.escape(base) +
                               r"[\"']?(?:\s|$|;|\||&|\))", line):
                    kind = "INVOCATION(head-of-command)"
                findings.append((os.path.relpath(r, ROOT), i, base, kind, stripped[:110]))

print("OCCURRENCES OF A SUPERSEDED BASENAME IN A run-all*.sh: %d" % len(findings))
for f in findings:
    print("  %-45s :%-4d %-30s %-26s %s" % f)
print()
inv = [f for f in findings if f[3].startswith("INVOCATION")]
print("VERDICT: %d INVOCATION(s) of a superseded artefact from a run-all*.sh" % len(inv))
for f in inv:
    print("  !! %s:%d  %s   %s" % (f[0], f[1], f[2], f[4]))
if not inv:
    print("  none.  (Statement about THIS search: %d register(s), %d declared original(s), "
          "%d run-all*.sh, whole-file scan of each.)" % (len(registers), len(entries), len(runalls)))

# --- TERM 5: self-test -- the sweep must be able to SEE an invocation.
print()
print("SELF-TEST (P-22: an instrument that cannot report a positive is not an instrument)")
import tempfile
with tempfile.TemporaryDirectory() as td:
    probe = os.path.join(td, "run-all-selftest.sh")
    victim = sorted(entries)[0] if entries else "nothing.py"
    with open(probe, "w") as fh:
        fh.write('#!/bin/bash\npython3 "$DIR/%s"\necho "%s is mentioned only"\n# %s\n'
                 % (victim, victim, victim))
    got = []
    with open(probe) as fh:
        for i, raw in enumerate(fh, 1):
            line = raw.rstrip("\n"); stripped = line.strip()
            if victim not in line:
                continue
            if stripped.startswith("#"):
                k = "COMMENT"
            elif re.match(r"^\s*echo\b", stripped):
                k = "ECHO-PROSE"
            elif re.search(INTERP + r"\s+(?:-\S+\s+)*[\"']?[^\s\"';|&]*" +
                           re.escape(victim) + r"[\"']?(?:\s|$|;|\||&|\))", line):
                k = "INVOCATION"
            else:
                k = "MENTIONED"
            got.append(k)
    want = ["INVOCATION", "ECHO-PROSE", "COMMENT"]
    print("  synthetic run-all with one invocation + one echo + one comment -> %s" % got)
    print("  %s" % ("ok  the sweep discriminates all three" if got == want
                    else "REFUSE  the sweep is BLIND: expected %s" % want))
    if got != want:
        sys.exit(2)
