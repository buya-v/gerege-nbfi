#!/usr/bin/env python3
"""T456 -- re-derive T451's C-T449-3 and C-T449-4 cardinals from tree listings.

Takes listings on stdin-free files so the git call and the arithmetic are separable and
a reader can re-run either half.  Prints the cardinal AND the commit it was taken at,
because the whole point of C-T449-3 is that a cardinal without its commit rots.

usage: 01-cardinals.py <tree-listing> <label>
"""
import collections
import re
import sys

LIST, LABEL = sys.argv[1], sys.argv[2]
paths = [l.rstrip("\n") for l in open(LIST, encoding="utf-8") if l.strip()]
if not paths:
    sys.exit("ABORT: %s is empty -- a census over nothing proves nothing" % LIST)
print("listing            : %s   (%s)" % (LIST, LABEL))
print("tracked paths      : %d" % len(paths))

# ---------------- C-T449-3: the handoff index's inert population -------------------
ho = [p for p in paths if p.startswith(".softhouse/handoff/")]
base = [p.rsplit("/", 1)[-1] for p in ho]
md = [b for b in base if b.endswith(".md")]
notmd = [b for b in base if not b.endswith(".md")]
bare = [b for b in md if re.match(r"^[Tt][0-9]+\.md$", b)]
a2 = [b for b in md if re.match(r"^A2-[0-9]+\.md$", b)]
inert = [b for b in md if b not in bare and b not in a2]
print()
print("C-T449-3  handoff paths tracked        : %d" % len(ho))
print("          ending .md                   : %d" % len(md))
print("          NOT .md (loop `continue`s)   : %d  %s"
      % (len(notmd), dict(collections.Counter(
          "." + b.rsplit(".", 1)[-1] if "." in b else "(none)"
          for b in notmd).most_common(6))))
print("          bare T###.md   (DO key)      : %d" % len(bare))
print("          A2-<n>.md      (DO key)      : %d" % len(a2))
print("          <id>-<slug>.md (key nothing) : %d   <-- the INERT population"
      % len(inert))
print("          shipped-before-T451 figure   : 313 == %d - %d == %s"
      % (len(ho), len(bare), len(ho) - len(bare)))

# ---------------- C-T449-4: where the 24 T268 paths actually are --------------------
ANY = re.compile(r"(?<![0-9A-Za-z])T268(?![0-9A-Za-z])", re.I)
LEAD = re.compile(r"T268(?![0-9A-Za-z])", re.I)
ment, own = [], []
for p in paths:
    parts = p.split("/")
    if any(ANY.search(c) for c in parts):
        (own if any(LEAD.match(c) for c in parts) else ment).append(p)
print()
print("C-T449-4  paths MENTIONING T268        : %d" % (len(ment) + len(own)))
print("          of those, OWNED by T268      : %d" % len(own))
print("          mentions, by owning dir      :")
for k, v in sorted(collections.Counter(
        "/".join(p.split("/")[:3]) for p in ment).items()):
    print("             %4d  %s" % (v, k))
for p in ment:
    if not p.startswith(".softhouse/capture/t286-t268-retry/"):
        print("          THE ODD ONE OUT              : %s" % p)
