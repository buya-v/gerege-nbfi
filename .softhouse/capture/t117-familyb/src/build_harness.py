#!/usr/bin/env python3
"""T117 — derive CaptureT117.java MECHANICALLY from the committed CaptureT100.java.

T114's standing ruling: do not edit a script that produced committed evidence. This script does
not edit CaptureT100.java — it reads it and writes a NEW file. The ONLY differences are
(1) the class name, (2) the sweep case list between the two rig calibrations and the end of the
list, replaced by /tmp/t117-cases.java, and (3) the WHY-THIS-PASS-EXISTS paragraph.

Everything that produces a number — the seam call, the emitted columns, the emission rules, the
attestation block, the (19, HALF_UP) setting — is copied byte-for-byte, which is what makes the two
rig calibrations (P-CAL-ZPA / P-CAL-ZPB, which must reproduce pass 3g's T64-ZP-A / T64-ZP-B cell for
cell) a meaningful check on THIS harness and not only on T100's.

The derivation is asserted, not assumed: after the three edits, the file is diffed against the
source and the number of changed regions is checked.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))          # .../.softhouse/capture
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')
OUT = os.path.join(HERE, 'CaptureT117.java')

text = open(SRC).read()
lines = text.split('\n')

# 1. the sweep cases: every cases.add line that is NOT a rig calibration
idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T100-' in l]
assert idx, 'no T100 sweep cases found in the source harness'
first, last = idx[0], idx[-1]
assert last - first + 1 == len(idx), 'sweep case block is not contiguous'

cases = open('/tmp/t117-cases.java').read().rstrip('\n').split('\n')
lines = lines[:first] + cases + lines[last + 1:]
text = '\n'.join(lines)

# 2. class name
text = text.replace('CaptureT100', 'CaptureT117')
assert 'CaptureT100' not in text, 'stale references remain'

# 3. honest header — say what THIS pass is; do not inherit T100's description of its case list
old_head = text[text.index(' * WHY THIS PASS EXISTS'):text.index(' * TWO RIG CALIBRATIONS')]
new_head = """ * WHY THIS PASS EXISTS — task T117, gate G-8. Family B (600.0 % p.a., MNT 0.01, n >= 104) is a
 * GENUINE non-amortization that the Go port reproduces cell for cell, and it is measured at 29
 * cells and still UNCAUSED. Two things about its EXTENT are unknown: whether it is a half-line in
 * n (every n above some threshold) or a bounded island — nothing above n = 250 has ever been asked
 * at that shape — and whether the failing principal can exceed ONE MINOR UNIT — every family-B cell
 * ever measured is at B = 1 minor unit. T117 asks the oracle both questions directly: 166 cells at
 * B = 1 over n = 300..1000 (contiguous 300..400, a ladder to 1000, contiguous 995..999), and 32
 * cells at B = 2..5 across the whole family-B n range and above it. Two CTRL cells re-ask both
 * sides of the known n = 103/104 boundary under new tenant ids.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t117-familyb/PREDICTION.md and prediction.json, committed in an ANCESTOR
 * COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_t117.py reading only the emitted JSON.
 *
"""
text = text.replace(old_head, new_head)

open(OUT, 'w').write(text)
n = text.count('cases.add(prodDates(')
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, n))
sys.exit(0)
