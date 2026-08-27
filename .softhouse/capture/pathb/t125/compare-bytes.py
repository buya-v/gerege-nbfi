#!/usr/bin/env python3
"""T125 — "no previously-passing capture changes its bytes", checked rather than asserted.

For every response body a GREEN re-run produced, find the committed body of the same name
and compare sha256 digests.  A capture with no committed counterpart is reported as such and
is NOT counted as a match — an absence is not agreement.

`attestation.json`, `preconditions.txt`, `stdout.txt`, `stderr.txt` and `CAPTURED-FROM-TENANT`
are excluded: they carry the run's own timestamps and paths, so they are EXPECTED to differ,
and comparing them would make the check fail for a reason that means nothing.  The claim
being tested is about the ORACLE'S ANSWERS.

T147 (P-35).  Until now this script was phrased as a NEGATIVE assertion — `return 1 if diff
else 0` — so an empty argv, a typo'd path or a directory that was never created printed
"byte-identical: 0   CHANGED: 0" and exited 0, having hashed nothing.  Measured on the
pre-fix bytes: `python3 compare-bytes.py` with no arguments, and with a non-existent
directory, both exit 0 (`capture/pathb/t147/red-pre-fix/f2-compare-bytes-prefix.txt`).  That
is `patterns.md`'s own rule verbatim — *a guard that inspects zero files must be an error,
not a pass* — inside the task whose subject is that class.  The check is now POSITIVE: at
least one directory must be named, every named directory must exist, at least one body must
be compared, and every compared body must be byte-identical.  Exit 2 = the check could not
be performed; exit 1 = it was performed and a body changed.

No floating point: digests and byte counts only (P-25).
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATHB = os.path.normpath(os.path.join(HERE, '..'))
CH = os.path.normpath(os.path.join(PATHB, '..', 'charges'))

# Where the committed counterpart of each re-captured body lives, in search order.
COMMITTED_DIRS = [
    os.path.join(PATHB, 'out'),                          # B-01..B-04 committed corpus
    os.path.join(PATHB, 't36', 'out', 'recapture-gerege'),
    os.path.join(PATHB, 't76', 'out', 'recapture-gerege'),
    os.path.join(PATHB, 't80', 'out', 'attest-gerege'),
    os.path.join(CH, 'out', 'attested'),                 # T40's committed charges set
    os.path.join(CH, 'out', 'fc'),                       # T40's first issue
]
SKIP = {'attestation.json', 'preconditions.txt', 'stdout.txt', 'stderr.txt',
        'scratch.diff', 'CAPTURED-FROM-TENANT'}


def sha256(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


EXIT_CHANGED = 1          # the comparison ran and a previously-committed body changed
EXIT_NOT_PERFORMED = 2    # the comparison could not be performed at all — NOT a pass


def cannot_check(why):
    print('  --')
    print('  *** BYTE-IDENTITY CHECK NOT PERFORMED *** %s' % why)
    print('      Zero files inspected is an ERROR, not agreement (P-35). This script asserts')
    print('      that N bodies were compared and each equalled its committed counterpart; it')
    print('      cannot make that assertion about N = 0.')
    sys.exit(EXIT_NOT_PERFORMED)


def main(dirs):
    # POSITIVE precondition 1: somebody must have named a directory.
    if not dirs:
        cannot_check('no capture directory was named on the command line.')
    # POSITIVE precondition 2: every directory named must actually exist. A silent `continue`
    # over a typo'd or never-created path is how "0 CHANGED" gets printed about nothing.
    missing = [d for d in dirs if not os.path.isdir(d)]
    if missing:
        cannot_check('these named directories do not exist: %s' % ', '.join(missing))
    same = diff = nocounterpart = 0
    for d in dirs:
        for name in sorted(os.listdir(d)):
            if name in SKIP or not name.endswith('.json'):
                continue
            fresh = os.path.join(d, name)
            found = None
            for cd in COMMITTED_DIRS:
                cand = os.path.join(cd, name)
                if os.path.exists(cand):
                    found = cand
                    break
            if found is None:
                print('  NO COMMITTED COUNTERPART  %s' % os.path.relpath(fresh, PATHB))
                nocounterpart += 1
                continue
            a, b = sha256(fresh), sha256(found)
            if a == b:
                print('  BYTE-IDENTICAL            %-34s == %s' % (name, os.path.relpath(found, PATHB)))
                same += 1
            else:
                print('  *** BYTES CHANGED ***     %-34s %s != %s' % (name, a[:16], b[:16]))
                print('                            fresh=%s committed=%s'
                      % (os.path.relpath(fresh, PATHB), os.path.relpath(found, PATHB)))
                diff += 1
    print('  --')
    print('  byte-identical: %d   CHANGED: %d   no committed counterpart: %d'
          % (same, diff, nocounterpart))
    # POSITIVE precondition 3: the directories existed but held nothing gradeable. An empty
    # capture directory is a failed capture, not a clean one.
    if same + diff == 0:
        cannot_check('%d directories were read and NOT ONE body had a committed counterpart '
                     'to compare against (%d had none).' % (len(dirs), nocounterpart))
    # The assertion, stated positively: N were compared, and each equalled its counterpart.
    if diff:
        return EXIT_CHANGED
    print('  ASSERTED: %d bodies were compared against their committed counterparts and '
          'each was byte-identical.' % same)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
