#!/usr/bin/env python3
"""T357 — split two run-all.sh transcripts into sections and diff them section by section.

The point of this file is a single question that must be MEASURED and not asserted:
after T357 replaced the retired hard-coded worktree root in five A2-11 scripts, do the
sections that used to abort now reproduce the COMMITTED transcript's text? If they do,
the substitution restored the evidence. If they do not, the difference is named here and
adjudicated in the handoff, rather than being hidden behind the word "output-neutral".
"""
import difflib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent


def sections(path):
    """dict {section-number: [lines]} keyed on the '############ N.' banners."""
    out, cur = {}, None
    for line in pathlib.Path(path).read_text().splitlines():
        m = re.match(r"^############ (\d+)\.", line)
        if m:
            cur = int(m.group(1))
            out.setdefault(cur, [])
            continue
        if cur is not None:
            out[cur].append(line)
    return out


a_path, b_path = sys.argv[1], sys.argv[2]
A, B = sections(a_path), sections(b_path)
print("A =", a_path)
print("B =", b_path)
print()
rc = 0
for n in sorted(set(A) | set(B)):
    la, lb = A.get(n), B.get(n)
    if la is None or lb is None:
        print("section %d: PRESENT-IN-ONLY-ONE  A=%s B=%s" % (n, la is not None, lb is not None))
        rc = 1
        continue
    if la == lb:
        print("section %d: IDENTICAL  (%d lines)" % (n, len(la)))
        continue
    rc = 1
    d = list(difflib.unified_diff(la, lb, "A/sec%d" % n, "B/sec%d" % n, lineterm="", n=1))
    adds = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
    dels = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
    print("section %d: DIFFERS  (+%d / -%d)" % (n, adds, dels))
    for x in d:
        print("    " + x)
    print()
print()
print("sections differing:", rc)
sys.exit(0)
