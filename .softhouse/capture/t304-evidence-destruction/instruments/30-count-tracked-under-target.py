#!/usr/bin/env python3
"""T304 instrument 30 — for every HARD-destructive site over a tracked path, count the
TRACKED FILES that would be destroyed.

"Hard-destructive" = rm / mv / shutil.rmtree / os.remove / os.unlink / git clean /
git checkout -- / git restore / git reset --hard / sed -i / perl -i.
Output redirection and `tee` are handled separately by instrument 40, because a redirect
over a tracked file destroys ONE file and the operand extraction for `>` is noisier.

The count is `len([p for p in git ls-files if p == target or p.startswith(target+'/')])`.
A target whose count is 0 destroys nothing committed -- it is a scratch path that merely
LOOKS tracked because its PARENT is tracked.  That distinction is the whole finding:
it is the difference between class (a) and class (b).

Input : TSV from 20-resolve-targets.py on stdin.  Output: TSV, one row per site.
"""
import os
import re
import subprocess
import sys

HARD = {'rm', 'mv', 'py-rmtree', 'git-clean', 'git-restore', 'inplace-edit'}

tracked = subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                         check=True).stdout.splitlines()


def count_under(target):
    t = os.path.normpath(target).rstrip('/')
    if t.startswith('./'):
        t = t[2:]
    n = 0
    for p in tracked:
        if p == t or p.startswith(t + '/'):
            n += 1
    return n


def main():
    sys.stdin.readline()
    print('\t'.join(['tracked_files_destroyed', 'op', 'file', 'lineno', 'target', 'text']))
    rows = []
    for line in sys.stdin:
        f = line.rstrip('\n').split('\t')
        if len(f) < 6:
            continue
        verdict, path, lineno, op, target, text = f[:6]
        if op not in HARD:
            continue
        # A target still holding a '$' is a family; count what its literal prefix holds.
        probe = target.split('$', 1)[0].rstrip('/') if '$' in target else target
        rows.append((count_under(probe), op, path, lineno, target, text))
    rows.sort(key=lambda r: (-r[0], r[2], int(r[3])))
    for r in rows:
        print('\t'.join(str(x) for x in r))
    nz = [r for r in rows if r[0] > 0]
    files = sorted({r[2] for r in nz})
    sys.stderr.write('HARD sites over a tracked path: %d\n' % len(rows))
    sys.stderr.write('  ... of which destroy >=1 TRACKED FILE: %d, in %d instruments\n'
                     % (len(nz), len(files)))
    for f in files:
        sys.stderr.write('    %s\n' % f)


if __name__ == '__main__':
    main()
