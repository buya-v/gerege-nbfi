#!/usr/bin/env python3
"""T304 instrument 60 — wire the fail-closed guard into the instruments PROVEN defective.

NOT a mass patch.  The eight files below are named one at a time, each with the exact
`EV=` line it must follow and the measured count of TRACKED files its `rm -rf` destroys.
A file whose anchor line is not found EXACTLY once REFUSES rather than guessing, and a
file already wired is skipped.  Nothing is patched by pattern.

The count column is not decoration: it is the proof that the file belongs in class (a).
It is re-measured at wire time from `git ls-files` and the wiring REFUSES if the measured
count is 0 -- because a 0 would mean the target is scratch and the file is class (b),
and mass-patching a class-(b) instrument is the specific error this task was told to
avoid (T284 found five of thirteen sites correct by design, one of whose 'repair' would
have destroyed a RED arm).
"""
import os
import subprocess
import sys

GUARD_REL = '.softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh'

# (path, anchor line to insert AFTER, target path used for the count, variable name)
SITES = [
    ('.softhouse/capture/t250-tenant-attestation/instruments/20-redA-sidecar-tracks-the-send.sh',
     'EV="$HERE/../evidence/redA"',
     '.softhouse/capture/t250-tenant-attestation/evidence/redA', 'EV'),
    ('.softhouse/capture/t250-tenant-attestation/instruments/30-redB-mismatch-detected.sh',
     'EV="$HERE/../evidence/redB"',
     '.softhouse/capture/t250-tenant-attestation/evidence/redB', 'EV'),
    ('.softhouse/capture/t250-tenant-attestation/instruments/40-redC-shapes-not-designed-around.sh',
     'EV="$HERE/../evidence/redC"',
     '.softhouse/capture/t250-tenant-attestation/evidence/redC', 'EV'),
    ('.softhouse/capture/t274-attestation-failopen/instruments/10-four-routes-red-green.sh',
     'EV="$TASK/evidence"',
     '.softhouse/capture/t274-attestation-failopen/evidence', 'EV'),
    ('.softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh',
     'EV="$TASK/evidence/wrap"',
     '.softhouse/capture/t274-attestation-failopen/evidence/wrap', 'EV'),
    ('.softhouse/capture/t274-attestation-failopen/instruments/30-t250-arms-still-hold.sh',
     'EV="$TASK/evidence/t250arms"',
     '.softhouse/capture/t274-attestation-failopen/evidence/t250arms', 'EV'),
    ('.softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh',
     'EV="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence/redB"',
     '.softhouse/reviews/t261-tenant-attestation/evidence/redB', 'EV'),
    ('.softhouse/reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh',
     'EV="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence/redC"',
     '.softhouse/reviews/t261-tenant-attestation/evidence/redC', 'EV'),
]

BLOCK = '''# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds {n} TRACKED files. T114 binds: committed evidence is named and
# SUPERSEDED by a scratch copy, never rewritten in place. Documenting the hazard in a
# handoff enforces nothing (P-45: "A test-only guard is not a guard ... verify the path
# that actually executes ... calls it, not merely that a test does") -- so the refusal
# is here, on the executing path, ahead of the destruction.
#   run for a NEW answer:  T304_EVIDENCE_SCRATCH="$(mktemp -d)" bash "$0"
#   read the OLD answer :  do not run it; the corpus is at the path above.
. "$(git rev-parse --show-toplevel)/{guard}"
{var}="$(t304_evidence_root "${var}")" || exit 2
# --- end T304 guard -----------------------------------------------------------------
'''


def main():
    apply = '--apply' in sys.argv
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True,
                          text=True, check=True).stdout.strip()
    os.chdir(root)
    rc = 0
    for path, anchor, target, var in SITES:
        n = len(subprocess.run(['git', 'ls-files', '--', target], capture_output=True,
                               text=True, check=True).stdout.split())
        if n == 0:
            print('REFUSED  %s: target %s holds 0 tracked files -- that is class (b), '
                  'not (a). Not patching.' % (path, target))
            rc = 2
            continue
        src = open(path, encoding='utf-8').read()
        if 'T304 FAIL-CLOSED GUARD' in src:
            print('SKIP     %s (already wired)' % path)
            continue
        if src.count(anchor + '\n') != 1:
            print('REFUSED  %s: anchor %r occurs %d times, expected exactly 1.'
                  % (path, anchor, src.count(anchor + '\n')))
            rc = 2
            continue
        block = BLOCK.format(n=n, guard=GUARD_REL, var=var)
        new = src.replace(anchor + '\n', anchor + '\n' + block, 1)
        print('WIRE     %-96s  protects %4d tracked files' % (path, n))
        if apply:
            open(path, 'w', encoding='utf-8').write(new)
    if not apply:
        print('\n(dry run -- pass --apply to write)')
    return rc


if __name__ == '__main__':
    sys.exit(main())
