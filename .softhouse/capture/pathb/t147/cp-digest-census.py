#!/usr/bin/env python3
"""T147 — census of the `CP_DIGEST` backlog item, by BYTES, so the fixer is not misled.

T125's handoff §7 registered the classpath-digest backlog as *"`CP_DIGEST` — 11 rigs"*.  The
count of the PHENOMENON is right and the eleven paths are right.  The TOKEN is not: five of
the eleven rigs compute the same digest inline, inside the `ok "..."` line, with no variable
at all — so a fixer who greps the symbol `CP_DIGEST` finds SIX of eleven and silently leaves
the other five.  That is T125's own declared blind spot #1 ("a guard that computes an ordinary
local and never compares it is invisible to both nets") landing inside the backlog entry that
declares it.  T136 found it; this script is the measurement, re-run rather than quoted.

The scan reads bytes and counts with `bytes.count` / `re` — no `grep`, so no BSD-grep
multibyte blindness (P-33).  No floating point anywhere: this counts files (P-25).

Usage: python3 cp-digest-census.py     Exit 0 = the census ran and the two forms sum to the
                                       registered total; exit 1 = it does not; exit 2 = the
                                       census inspected nothing (P-35).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE = os.path.normpath(os.path.join(HERE, '..', '..'))   # .softhouse/capture

# The registered backlog total, from T125 handoff §7 as corrected by T136 F-6 and by this
# script.  Asserted, not printed (P-35).
REGISTERED_RIGS = 11
EXPECT_NAMED = 6
EXPECT_INLINE_ONLY = 5

NAMED = b'CP_DIGEST'
# The unnamed form: the digest is computed inside the `ok` line's own command substitution.
INLINE = re.compile(rb'digest \$\(shasum')


def main():
    rows = []
    for dirpath, _dirnames, filenames in os.walk(CAPTURE):
        for fn in sorted(filenames):
            if not fn.endswith('.sh'):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, 'rb') as fh:
                blob = fh.read()
            n_named = blob.count(NAMED)
            n_inline = len(INLINE.findall(blob))
            if n_named or n_inline:
                rows.append((os.path.relpath(path, CAPTURE), n_named, n_inline))
    rows.sort()

    if not rows:
        print('  *** CENSUS NOT PERFORMED *** no shell rig under %s mentions either form.'
              % CAPTURE)
        print('      Zero files inspected is an error, not a clean result (P-35).')
        return 2

    print('  %-58s %9s %8s' % ('shell rig (relative to .softhouse/capture)', 'CP_DIGEST', 'inline'))
    print('  ' + '-' * 78)
    named = inline_only = 0
    for rel, n_named, n_inline in rows:
        print('  %-58s %9d %8d' % (rel, n_named, n_inline))
        if n_named:
            named += 1
        elif n_inline:
            inline_only += 1
    total = named + inline_only
    print('  ' + '-' * 78)
    print('  rigs naming the variable CP_DIGEST : %d' % named)
    print('  rigs using the INLINE, UNNAMED form: %d' % inline_only)
    print('  total rigs exhibiting the phenomenon: %d' % total)

    bad = []
    if named != EXPECT_NAMED:
        bad.append('rigs naming CP_DIGEST is %d, expected %d' % (named, EXPECT_NAMED))
    if inline_only != EXPECT_INLINE_ONLY:
        bad.append('rigs using only the inline form is %d, expected %d'
                   % (inline_only, EXPECT_INLINE_ONLY))
    if total != REGISTERED_RIGS:
        bad.append('total rigs is %d, but the backlog is registered at %d'
                   % (total, REGISTERED_RIGS))
    if bad:
        print()
        print('  *** CENSUS DISAGREES WITH THE REGISTERED BACKLOG ***')
        for b in bad:
            print('    - %s' % b)
        print('  Correct the register, or the fixer will size the work from a wrong number.')
        return 1
    print()
    print('  ASSERTED: %d rigs inspected; %d name the variable and %d do not, summing to the'
          % (len(rows), named, inline_only))
    print('  registered total of %d. A fixer that greps `CP_DIGEST` reaches %d of %d.'
          % (REGISTERED_RIGS, named, REGISTERED_RIGS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
