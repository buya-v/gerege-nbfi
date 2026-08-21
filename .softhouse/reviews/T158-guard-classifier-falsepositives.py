#!/usr/bin/env python3
# T158 — which LINE made each "guarded" classification true?  T156's GUARD regex is
#   ^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register|__exit__|contextmanager)
# which excludes `#` comments but NOT Python docstrings, shell here-docs or echoed text.
import re, sys
GUARD = re.compile(r"(?m)^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register|__exit__|contextmanager)")
for p in sys.argv[1:]:
    src = open(p, encoding="utf-8").read()
    m = [(i + 1, l.strip()) for i, l in enumerate(src.splitlines()) if GUARD.search(l)]
    real = len(re.findall(r"(?m)^\s*trap\s", src)) + len(re.findall(r"(?m)^\s*finally\s*:", src)) \
        + len(re.findall(r"atexit\.register", src))
    print("%s   real guards=%d   GUARD-matching lines=%d" % (p, real, len(m)))
    for ln, t in m[:4]:
        print("    %5d | %s" % (ln, t[:120]))
    print()
