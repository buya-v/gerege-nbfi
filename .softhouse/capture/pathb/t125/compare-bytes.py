#!/usr/bin/env python3
"""T125 — "no previously-passing capture changes its bytes", checked rather than asserted.

For every response body a GREEN re-run produced, find the committed body of the same name
and compare sha256 digests.  A capture with no committed counterpart is reported as such and
is NOT counted as a match — an absence is not agreement.

`attestation.json`, `preconditions.txt`, `stdout.txt`, `stderr.txt` and `CAPTURED-FROM-TENANT`
are excluded: they carry the run's own timestamps and paths, so they are EXPECTED to differ,
and comparing them would make the check fail for a reason that means nothing.  The claim
being tested is about the ORACLE'S ANSWERS.

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


def main(dirs):
    same = diff = nocounterpart = 0
    for d in dirs:
        if not os.path.isdir(d):
            continue
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
    return 1 if diff else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
