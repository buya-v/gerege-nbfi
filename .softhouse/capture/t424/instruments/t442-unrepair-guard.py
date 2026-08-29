#!/usr/bin/env python3
"""T442 -- reconstruct the PRE-REPAIR shape of T424's re-exec guard, for the RED arm.

`t442-t440-lows-drive.sh` grades the guard as the patch now ships it (GREEN). A green arm alone
proves nothing (P-22), so the red arm must be the SAME guard with the C-T440-5 repair taken back
out: the parent-pid refusal block deleted and the marker restored to the bare flag `1`. This
script performs that reversal and REFUSES if it changed nothing -- a red arm that is secretly
identical to the green one is not a red arm.

usage: t442-unrepair-guard.py <repaired-guard> <out-pre-repair-guard>
"""
import sys

if len(sys.argv) != 3:
    sys.stderr.write(__doc__)
    sys.exit(2)

src = open(sys.argv[1]).read().split('\n')
out, drop = [], False
for ln in src:
    if ln.startswith('if [ -n "${T381_DRIVE_INNER:-}" ]'):
        drop = True
    if drop:
        if ln == 'fi':
            drop = False
        continue
    out.append(ln.replace('T381_DRIVE_INNER="t424-inner:$$"', 'T381_DRIVE_INNER=1'))

txt = '\n'.join(out)
if 't424-inner' in txt:
    sys.stderr.write('REFUSED: the reversal left the repair behind\n')
    sys.exit(2)
if 'T381_DRIVE_INNER=1 bash' not in txt:
    sys.stderr.write('REFUSED: the reversal did not restore the flag marker\n')
    sys.exit(2)
if len(out) >= len(src):
    sys.stderr.write('REFUSED: the reversal removed no lines\n')
    sys.exit(2)
open(sys.argv[2], 'w').write(txt)
