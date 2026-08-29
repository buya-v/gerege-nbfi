#!/usr/bin/env python3
"""T456 -- T451's DECIDING claim, checked against the actual ref, not against its note.

CLAIM (T451 C-T449-2, Measurement 3): the only real instance of T449's "case K" shape in
this repo -- work owned by one id filed under ANOTHER id's directory -- is ALREADY caught
by the shipped OWNING (`leading`) anchor, because a path COMPONENT includes the FILENAME
and this program names the file for its owner.  T449's fixture missed it only because its
fixture filename was `work.txt`.

This instrument reads the ref's real diff and its real subjects, applies both anchors
re-implemented from the regexes in `id_pattern()`, and prints the per-component verdict so
nothing has to be taken on trust.  It also runs the counterfactual: the same paths with the
owner-naming filename replaced by a filename that names nobody.
"""
import re
import subprocess
import sys

REF = "softhouse/rescued-t428-t421tree-20260828-140005"
TID = "T428"
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()


def g(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True)


ANYWHERE = re.compile(r"(?<![0-9A-Za-z])" + re.escape(TID) + r"(?![0-9A-Za-z])", re.I)
LEADING = re.compile(re.escape(TID) + r"(?![0-9A-Za-z])", re.I)

p = g("rev-parse", "--verify", REF)
if p.returncode != 0:
    print("ABORT: ref %s does not resolve. This is a statement about the SEARCH, not the"
          " world: rc=%s %s" % (REF, p.returncode, p.stderr.strip()))
    sys.exit(90)
print("ref resolves at %s" % p.stdout.strip()[:9])

log = g("log", "--format=%h%x09%s", "main..%s" % REF)
print("\nSUBJECT HALF (generous, `anywhere`) -- commits this ref has that main does not:")
subj_hits = 0
for line in log.stdout.splitlines():
    sha, _, s = line.partition("\t")
    hit = bool(ANYWHERE.search(s))
    subj_hits += hit
    print("   %s  names %s? %-3s  %r" % (sha, TID, "YES" if hit else "no", s))
print("   subject hits: %d  <-- the sweep's boilerplate names NO id, so this half is mute"
      % subj_hits)

d = g("diff", "--name-only", "main...%s" % REF)
paths = d.stdout.splitlines()
print("\nPATH HALF -- %d path(s), per COMPONENT:" % len(paths))
own_l = own_a = 0
for path in paths:
    parts = path.split("/")
    l = [x for x in parts if LEADING.match(x)]
    a = [x for x in parts if ANYWHERE.search(x)]
    own_l += bool(l)
    own_a += bool(a)
    print("   %s" % path)
    print("      leading(OWNS)  -> %s" % (l or "[]"))
    print("      anywhere(ment) -> %s" % (a or "[]"))
print("\n  CARRIES under SHIPPED  (leading ) : %s   (%d/%d paths own)"
      % (bool(subj_hits or own_l), own_l, len(paths)))
print("  CARRIES under RELAXED  (anywhere) : %s   (%d/%d paths match)"
      % (bool(subj_hits or own_a), own_a, len(paths)))

print("\nCOUNTERFACTUAL -- T449's fixture filename, on the SAME directory:")
for path in paths:
    fake = "/".join(path.split("/")[:-1] + ["work.txt"])
    parts = fake.split("/")
    l = [x for x in parts if LEADING.match(x)]
    a = [x for x in parts if ANYWHERE.search(x)]
    print("   %-70s leading=%s anywhere=%s" % (fake, l or "[]", a or "[]"))
print("  -> with a filename that names nobody the OWNING anchor goes silent, which is")
print("     exactly and only why T449's case K looked uncaught.")
