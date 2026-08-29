#!/usr/bin/env python3
"""
T454 -- CENSUS OF WORKING-TREE READS IN conformance.sh.

THE GENERAL FORM T446 NAMED AND DID NOT MEASURE:
  THE TEXT THAT EXECUTES IS NOT NECESSARILY THE TEXT THAT IS COMMITTED.
Every argument in this repository that rests on "the harness grades itself", or on "the
guard runs the checker", inherits it.  T446 closed one function; this asks how many other
sites in the same file read or EXECUTE a tracked path off this host's filesystem instead of
out of git.

WHAT IT REPORTS, per site: the line, whether it is executable text or a comment, and
whether the path it names contains a character that this host's filesystem FOLDS (the four
measured by fold-census.py).  A site whose path contains a foldable character is
attackable by exactly the LONGS construction; a site whose path is pure unfoldable ASCII is
attackable only through an uppercase spelling, which loses the sort.

IT MUST NOT PRINT A NEGATIVE IT DID NOT MEASURE.
  * the corpus is asserted reachable and non-empty before any search (exit 3 otherwise);
  * the matcher is calibrated on a line KNOWN to be present -- the `bash "$REPO_ROOT/...
    check-ledger-invariants.sh"` invocation -- and refuses to report any count if that
    known positive is missed (exit 2);
  * "no sites" and "could not search" are different exit codes.
"""

import os
import re
import sys

# The four characters this host's APFS volume folds onto printable ASCII, MEASURED by
# instruments/fold-census.py --all-ascii (evidence/02-fold-census-all-ascii.txt).  They are
# listed by the ASCII character they fold ONTO, because that is what a path is searched for.
FOLDABLE = {
    "s": "U+017F LATIN SMALL LETTER LONG S",
    "k": "U+212A KELVIN SIGN",
    ";": "U+037E GREEK QUESTION MARK",
    "`": "U+1FEF GREEK VARIA",
}

SITE = re.compile(r'\$REPO_ROOT/')
CALIB = 'check-ledger-invariants.sh'


def main():
    if len(sys.argv) < 2:
        print("usage: worktree-read-census.py <path to conformance.sh>")
        return 3
    conf = sys.argv[1]
    if not os.path.isfile(conf):
        print("CORPUS UNREACHABLE: %s is not a file" % conf)
        return 3
    with open(conf, "r", encoding="utf-8", errors="surrogateescape") as fh:
        lines = fh.read().split("\n")
    if len(lines) < 100:
        print("CORPUS TOO SMALL: %s has %d lines; this file is thousands." % (conf, len(lines)))
        return 3
    print("T454 WORKING-TREE READ CENSUS")
    print("file            : %s" % conf)
    print("lines           : %d" % len(lines))

    hits = []
    for i, ln in enumerate(lines, 1):
        if SITE.search(ln):
            hits.append((i, ln))
    if not any(CALIB in ln for _, ln in hits):
        print("CALIBRATION MISSED: the known-present site naming %s was not" % CALIB)
        print("found by this matcher. No count below is interpretable. REFUSED.")
        return 2
    print("calibrate+      : PASS -- the known %s site was found" % CALIB)
    print("total $REPO_ROOT/ occurrences (comments included): %d" % len(hits))

    exec_hits = [(i, ln) for i, ln in hits if not ln.lstrip().startswith("#")]
    print("of which EXECUTABLE text                         : %d" % len(exec_hits))

    # ------------------------------------------------------------------ TWO PASSES.
    # THE WHOLE POINT OF T446's MAJOR-2 IS THAT WATCHING WHERE A VALUE IS READ IS NOT
    # WATCHING WHERE IT IS USED, and a census that only matched the line carrying
    # `$REPO_ROOT/` would commit exactly that error: almost every site in this file assigns
    # the path to a local and touches the filesystem SOMEWHERE ELSE.  So: pass 1 binds
    # variable -> path, pass 2 finds where each bound variable is USED in a position that
    # touches this host's filesystem.
    ASSIGN = re.compile(r'(?:local\s+)?([A-Za-z_][A-Za-z0-9_]*)="\$REPO_ROOT/([^"]*)"')
    bound = {}
    for i, ln in exec_hits:
        for m in ASSIGN.finditer(ln):
            bound.setdefault(m.group(1), []).append((i, m.group(2)))
    print("variables bound to a $REPO_ROOT path             : %d (%s)"
          % (len(bound), " ".join(sorted(bound))))

    # A USE that touches the filesystem: an interpreter or a file test or a redirect or a
    # command substitution reading it.  `cd "$REPO_ROOT" && git ...` is NOT one -- git
    # answers from the index there, which is the whole shape T445 moved this file to.
    USE = re.compile(
        r'(?:^|[;&|(]|\s)(?:bash|sh|python3|/usr/bin/python3|go|cat|source|\.)\s+[^\n]*"\$(%s)"'
        r'|\[\s*!?\s*-[a-zA-Z]\s+"\$(%s)"'
        r'|(?:cat|LC_ALL=C grep|grep|wc|sed|awk|head|tail)\s+[^\n]*"\$(%s)"')

    print("")
    print("%-7s %-9s %-12s %s" % ("line", "kind", "folds", "text"))
    reads = 0
    fold_sites = 0
    seen = []
    names = "|".join(re.escape(n) for n in sorted(bound)) or "\x00nomatch"
    use_re = re.compile(USE.pattern % (names, names, names))
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("#"):
            continue
        m = use_re.search(ln)
        direct = re.search(
            r'(?:^|[;&|(]|\s)(?:bash|sh|python3|/usr/bin/python3|go|cat|source|\.)\s+[^\n]*"\$REPO_ROOT/'
            r'|\[\s*!?\s*-[a-zA-Z]\s+"\$REPO_ROOT/'
            r'|(?:cat|LC_ALL=C grep|grep)\s+[^\n]*"\$REPO_ROOT/', ln)
        if not m and not direct:
            continue
        if m:
            var = next(g for g in m.groups() if g)
            paths = [p for _, p in bound.get(var, [])]
            kind = "USE"
        else:
            dm = re.search(r'\$REPO_ROOT/([^"\'\s)]*)', ln)
            paths = [dm.group(1)] if dm else [""]
            kind = "DIRECT"
        folds = sorted({c for p in paths for c in p if c in FOLDABLE})
        reads += 1
        if folds:
            fold_sites += 1
        seen.append((i, kind, folds, ln.strip()))
        print("%-7d %-9s %-12s %s" % (i, kind, ",".join(folds) or "-", ln.strip()[:92]))

    print("")
    print("EXECUTABLE sites that TOUCH the filesystem at a $REPO_ROOT path : %d" % reads)
    print("of those, whose path contains a character this host FOLDS       : %d" % fold_sites)
    print("")
    print("FOLD TABLE USED (measured, evidence/02-fold-census-all-ascii.txt):")
    for k, v in sorted(FOLDABLE.items()):
        print("  '%s'  <-  %s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
