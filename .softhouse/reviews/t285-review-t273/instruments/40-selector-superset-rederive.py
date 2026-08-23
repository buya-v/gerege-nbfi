#!/usr/bin/env python3
"""T285 — RE-DERIVE T273's load-bearing superset claim, without running T273's instrument.

guard_no_host_state_in_lint_corpus selects its population with `git grep -l -E "$rw"`
(POSIX ERE, LINE-BASED). The fail-open linter selects its population with a Python
`re.search(RE_REPOWIDE, txt)` over the WHOLE FILE TEXT, where `\\s` matches a NEWLINE.
So a file whose `git` and `grep` are split across two lines is IN the linter's corpus and
could be OUT of the guard's. Every such file is a hole: a host-state assignment could
enter the linter's corpus without ever entering the census.

T273 asserts the hole is empty (`linter \\ guard = 0`). This re-derives it from the two
source spellings directly, reading RE_REPOWIDE out of the shipped linter rather than
retyping it, and reading the ERE out of the shipped conformance.sh rather than retyping it.

Exit 0 = the guard's population is a superset of the linter's. Exit 1 = there are holes.
Exit 2 = this probe could not establish either (a refusal, never a pass).

ENGINE DECLARATION (P-33): Python `re` for the linter side; `git grep -E` (the real
selector, invoked as the guard invokes it) for the guard side.
"""
import os
import re
import subprocess
import sys

LINTER = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
CONF = ".softhouse/conformance.sh"

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
if not ROOT:
    print("T285 SELECTOR PROBE ABORT (2): not in a git work tree.")
    sys.exit(2)
os.chdir(ROOT)

# --- the linter's own regex, lifted from its source, not retyped -------------------
src = open(LINTER, encoding="utf-8", errors="replace").read()
m = re.search(r"RE_REPOWIDE = re\.compile\((.*?)\)\s*\n\n", src, re.S)
if not m:
    print("T285 SELECTOR PROBE REFUSED (2): could not lift RE_REPOWIDE out of %s." % LINTER)
    sys.exit(2)
parts = re.findall(r"r'((?:[^'\\]|\\.)*)'", m.group(1))
if not parts:
    print("T285 SELECTOR PROBE REFUSED (2): RE_REPOWIDE lifted but empty.")
    sys.exit(2)
RE_REPOWIDE = re.compile("".join(parts))
print("### T285 — SELECTOR SUPERSET RE-DERIVATION")
print("  tree   : %s" % ROOT)
print("  HEAD   : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
print("  RE_REPOWIDE lifted from %s:" % LINTER)
print("      %s" % RE_REPOWIDE.pattern)

# --- the guard's own ERE, lifted from conformance.sh, not retyped -------------------
conf = open(CONF, encoding="utf-8", errors="replace").read()
m = re.search(r"^\s*rw='([^']*)'", conf, re.M)
if not m:
    print("T285 SELECTOR PROBE REFUSED (2): could not lift the guard's `rw` ERE out of %s." % CONF)
    sys.exit(2)
RW = m.group(1)
print("  guard ERE lifted from %s:" % CONF)
print("      %s" % RW)
print()

# --- population A: the linter's ------------------------------------------------------
files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True)
         .stdout.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("T285 SELECTOR PROBE REFUSED (2): zero tracked .sh/.py files (P-35).")
    sys.exit(2)
linter_pop = set()
for f in files:
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    if RE_REPOWIDE.search(txt):
        linter_pop.add(f)

# --- population B: the guard's -------------------------------------------------------
p = subprocess.run(["git", "grep", "-l", "-E", RW, "--", "*.sh", "*.py"],
                   capture_output=True, text=True, env=dict(os.environ, LC_ALL="C"))
# git grep: 0 = matches, 1 = NO MATCH, >1 = ERROR (P-81). >1 is never "clean".
if p.returncode > 1:
    print("T285 SELECTOR PROBE REFUSED (2): `git grep` exited %d — an ERROR, not an empty "
          "result (P-81)." % p.returncode)
    print(p.stderr[:2000])
    sys.exit(2)
guard_pop = set(x for x in p.stdout.split("\n") if x)

SELF = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
linter_pop.discard(SELF)
guard_pop.discard(SELF)

holes = sorted(linter_pop - guard_pop)
extra = sorted(guard_pop - linter_pop)
print("  tracked .sh/.py files          : %d" % len(files))
print("  linter population (Python re)  : %d" % len(linter_pop))
print("  guard  population (git grep -E): %d" % len(guard_pop))
print("  IN LINTER, NOT IN GUARD (holes): %d" % len(holes))
for f in holes:
    print("      HOLE %s" % f)
print("  in guard, not in linter (slack): %d" % len(extra))
for f in extra:
    print("      slack %s" % f)
print()
if holes:
    print("### VERDICT: THE GUARD'S POPULATION IS NOT A SUPERSET. Each HOLE above is a file the")
    print("### fail-open linter classifies and the host-state census never looks at.")
    sys.exit(1)
print("### VERDICT: SUPERSET HOLDS — every file the linter classifies is also censused.")
sys.exit(0)
