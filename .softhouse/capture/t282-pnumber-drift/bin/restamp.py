#!/usr/bin/env python3
"""T282 -- re-derive the line numbers this task's own banner edit just SHIFTED.

This script exists because the repair for P-80 committed P-80. The banner edit
inserted ~30 lines at the top of patterns.md, which moved every definition line
below it, including the four line numbers the new banner cites. Citing :284 /
:1354 / :289 / :1381 after that insertion would have shipped a stale cardinal
inside the paragraph that names stale cardinals.

So the numbers are DERIVED FROM THE FILE, at the moment of writing, by the same
build_register() the checker grades with -- never typed. P-63: re-derive every
figure from the live artefact at the moment of use.
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATTERNS = os.path.join(ROOT, ".softhouse", "patterns.md")
GATES = os.path.join(ROOT, ".softhouse", "gates-proposed-answers.md")

spec = importlib.util.spec_from_file_location(
    "chk", os.path.join(HERE, "check-pnumber-citations.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

sha = sys.argv[1] if len(sys.argv) > 1 else "UNSTAMPED"

reg, coll, _ = m.build_register(m.read_lines(PATTERNS), (m.DEFN_HEAD, m.DEFN_BOLD))
d = dict((c["id"], (c["first_line"], c["again_line"])) for c in coll)
print("in-file collisions measured now: %s" % d)
if 12 not in d or 13 not in d:
    print("REFUSING: expected P-12 and P-13 collisions, got %s" % sorted(d))
    raise SystemExit(3)

g6 = [i + 1 for i, l in enumerate(m.read_lines(GATES))
      if l.strip().startswith("## P-6 ")]
if len(g6) != 1:
    print("REFUSING: gates-proposed-answers.md defines P-6 %d times" % len(g6))
    raise SystemExit(3)
g6 = g6[0]

s = io.open(PATTERNS, encoding="utf-8").read()
subs = [
    ("SHA_PLACEHOLDER", sha),
    ("`gates-proposed-answers.md:195` defines `P-6`",
     "`gates-proposed-answers.md:%d` defines `P-6`" % g6),
    ("| P-12 | `:284` —", "| P-12 | `:%d` —" % d[12][0]),
    ("| `:1354` —", "| `:%d` —" % d[12][1]),
    ("| P-13 | `:289` —", "| P-13 | `:%d` —" % d[13][0]),
    ("| `:1381` —", "| `:%d` —" % d[13][1]),
    ('"P-12 (`patterns.md:1354`)"', '"P-12 (`patterns.md:%d`)"' % d[12][1]),
]
for old, new in subs:
    n = s.count(old)
    print("  %-52s x%d -> %s" % (old[:52], n, new[:60]))
    s = s.replace(old, new)
io.open(PATTERNS, "w", encoding="utf-8").write(s)
print("restamped at sha %s; gates P-6 at :%d" % (sha, g6))
