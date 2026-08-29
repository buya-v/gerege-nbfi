#!/usr/bin/env python3
"""T469 -- INDEPENDENT census of set A (pairs that CARRY under the shipped anchors).

Reimplemented from the two regexes in `id_pattern()` and the two halves of
`ref_content_evidence` (subject = `anywhere`, path component = `leading`), read
through `git for-each-ref` + `git log` + `git diff` rather than through the module,
so this is a second derivation and not the same program twice (T448's rule).

argv: <repo> <ready-tasks.py to read ids from tasks.json>
"""
import json
import os
import re
import subprocess
import sys

REPO = os.path.abspath(sys.argv[1])
S = "." + "softhouse"                      # assembled, never a literal


def g(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True,
                          text=True).stdout


refs = sorted(x for x in g("for-each-ref", "--format=%(refname:short)",
                           "refs/heads").split("\n") if x)
head = g("rev-parse", "HEAD").strip()
tree = g("rev-parse", "HEAD^{tree}").strip()

ID = re.compile(r"(?<![0-9A-Za-z])(T[0-9]+)(?![0-9A-Za-z])", re.IGNORECASE)

# ids nameable from a head, T451's keying: the FIRST id in the short name
ids = {}
for r in refs:
    m = ID.search(r)
    if m:
        ids.setdefault(m.group(1).upper(), set()).add(r)

pairs = []
for tid, own in sorted(ids.items()):
    pat = re.compile(r"(?<![0-9A-Za-z])" + tid + r"(?![0-9A-Za-z])", re.IGNORECASE)
    for r in refs:
        if r in own:
            continue
        if pat.search(r):
            pairs.append((tid, r))

anywhere_c = {}
leading_c = {}
A, C = [], []
for tid, ref in pairs:
    aw = anywhere_c.setdefault(tid, re.compile(
        r"(?<![0-9A-Za-z])" + tid + r"(?![0-9A-Za-z])", re.IGNORECASE))
    ld = leading_c.setdefault(tid, re.compile(tid + r"(?![0-9A-Za-z])", re.IGNORECASE))
    subs = [l.split("\t", 1)[-1] for l in g("log", "--format=%H%x09%s",
                                            "main..%s" % ref).split("\n") if l]
    paths = [p for p in g("diff", "--name-only", "main...%s" % ref).split("\n") if p]
    by_subject = any(aw.search(s) for s in subs)
    by_path = any(ld.match(part) for p in paths for part in p.split("/"))
    if by_subject or by_path:
        owner = ID.search(ref)
        owner = owner.group(1).upper() if owner else "?"
        A.append((tid, ref, owner, "FOREIGN" if owner != tid else "own",
                  "subject" if by_subject else "", "path" if by_path else ""))
    else:
        C.append((tid, ref))

print("TREE %s  (HEAD %s)" % (tree, head[:12]))
print("live refs %d ; ids nameable from a head %d ; (id, other-ref) pairs %d"
      % (len(refs), len(ids), len(pairs)))
print()
print("SET A -- pairs that CARRY under the SHIPPED anchors: %d" % len(A))
for row in A:
    print("   %-6s %-46s owner=%-6s %-8s %s%s"
          % (row[0], row[1], row[2], row[3], row[4], (" " + row[5]) if row[5] else ""))
print()
print("   of which FOREIGN-owned: %d" % sum(1 for r in A if r[3] == "FOREIGN"))
print("SET C -- name-only under BOTH anchors: %d" % len(C))
