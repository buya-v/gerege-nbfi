#!/usr/bin/env python3
"""T273 — do the NEW guard's population selector and the FAIL-OPEN LINTER's agree?

The new guard `guard_no_host_state_in_lint_corpus` in .softhouse/conformance.sh must
inspect AT LEAST the files the fail-open linter classifies, or it can be walked around
by putting the offending assignment in a file the guard does not read. The guard uses
`git grep -E` (POSIX ERE, no `\\b`); the linter uses Python `re` over the whole file
text. Those are two engines and two spellings, so the agreement is MEASURED here rather
than assumed (P-33/P-53: name the engine; P-67: state both terms).

ENGINE DECLARATION: this file uses `git ls-files` + Python `re` for the linter arm and
`git grep -E` for the guard arm. No bare `grep`, no `rg`.

Prints both populations, both differences, and a verdict line. Exit 0 if the guard's
population is a SUPERSET of the linter's (that is the property the guard needs), 1 if
the linter sees a file the guard would not.
"""
import re
import subprocess
import sys

LINTER_RE = re.compile(
    r'(git\s+(?:-[A-Za-z]\s+\S+\s+|--[A-Za-z-]+=\S+\s+|-[A-Za-z]+\s+)*(?:grep|ls-files)\b'
    r'|grep\s+-[a-zA-Z]*[rR]\b)')
SELF = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"

GUARD_ERE = (r'(git[[:space:]]+(-[A-Za-z][[:space:]]+[^[:space:]]+[[:space:]]+'
             r'|--[A-Za-z-]+=[^[:space:]]+[[:space:]]+|-[A-Za-z]+[[:space:]]+)*'
             r'(grep|ls-files)|grep[[:space:]]+-[a-zA-Z]*[rR])')


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout


rc, out = run(["git", "ls-files"])
if rc != 0:
    print("T273: git ls-files failed (exit %d) — not inside a work tree." % rc)
    sys.exit(2)
files = [f for f in out.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("T273: zero tracked .sh/.py files. A comparison over nothing proves nothing (P-35).")
    sys.exit(2)

linter = set()
for f in files:
    if f == SELF:
        continue
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    if len(txt) > 4_000_000:
        continue
    if LINTER_RE.search(txt):
        linter.add(f)

rc, out = run(["git", "grep", "-l", "-E", GUARD_ERE, "--", "*.sh", "*.py"])
# git grep: 0 = matches, 1 = NO MATCH, >1 = ERROR. Nonzero is not "clean".
if rc > 1:
    print("T273: git grep -E errored (exit %d). That is an ERROR, never an empty result." % rc)
    sys.exit(2)
guard = set(f for f in out.split("\n") if f)
guard.discard(SELF)     # the guard excludes the linter itself, exactly as the linter does

print("### T273 selector agreement")
print("  linter population (Python re, whole file text) : %d" % len(linter))
print("  guard  population (git grep -E, line-based)    : %d" % len(guard))
print("  --- files the GUARD sees and the LINTER does not (%d) — harmless, the guard is wider:"
      % len(guard - linter))
for f in sorted(guard - linter):
    print("        %s" % f)
print("  --- files the LINTER sees and the GUARD does not (%d) — EACH ONE IS A HOLE:"
      % len(linter - guard))
for f in sorted(linter - guard):
    print("        %s" % f)

if linter - guard:
    print("VERDICT: NOT A SUPERSET — the guard would not read %d file(s) the linter classifies."
          % len(linter - guard))
    sys.exit(1)
print("VERDICT: SUPERSET — every file the fail-open linter classifies is read by the guard.")
sys.exit(0)
