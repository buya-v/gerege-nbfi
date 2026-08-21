#!/usr/bin/env python3
"""T159 — derive CaptureT159.java MECHANICALLY from the committed CaptureT100.java.

Identical derivation to T117's build_harness.py / build_harness_pass2.py, from the
SAME source harness, so T159's rig is the same rig as T117's, T100's and pass 3g's.
The only differences are (1) the class name, (2) the sweep case list between the two
rig calibrations and the end of the list, replaced by /tmp/t159-cases.java, and
(3) the WHY-THIS-PASS-EXISTS paragraph.

Nothing that produces a number is touched. That is what keeps the two rig
calibrations (P-CAL-ZPA / P-CAL-ZPB against pass 3g's T64-ZP-A / T64-ZP-B) a
meaningful check on this harness -- and it is what makes a byte-identity comparison
between a T159 cell and the corresponding committed T117 cell meaningful.

CaptureT100.java is READ, never written (T114's standing ruling).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')
OUT = os.path.join(HERE, 'CaptureT159.java')

text = open(SRC).read()
lines = text.split('\n')

idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T100-' in l]
assert idx, 'no T100 sweep cases found in the source harness'
first, last = idx[0], idx[-1]
assert last - first + 1 == len(idx), 'sweep case block is not contiguous'

cases = open('/tmp/t159-cases.java').read().rstrip('\n').split('\n')
lines = lines[:first] + cases + lines[last + 1:]
text = '\n'.join(lines)

text = text.replace('CaptureT100', 'CaptureT159')
assert 'CaptureT100' not in text, 'stale references remain'

old_head = text[text.index(' * WHY THIS PASS EXISTS'):text.index(' * TWO RIG CALIBRATIONS')]
new_head = """ * WHY THIS PASS EXISTS -- task T159, the INDEPENDENT REVIEW of T117, gate G-8. T117 reported a
 * largest unamortized residual of 501 minor units (MNT 5.01) and -- the consequential part --
 * that NO UPPER BOUND is established, because "the largest failing principal tracks the largest
 * term asked" and nothing above n = 1000 has ever been asked. That is a claim about the SHAPE OF
 * T117'S PROBE SET, and a reviewer must not take it on trust. This pass asks the region directly:
 * n > 1000 (never asked by anybody), odd principals in the 501..1001 gap T117's ladder jumped
 * over, T117's reported band boundaries at B = 1, and straight re-asks of T117's headline cell
 * and its three PARTIAL-amortization cells under fresh tenant ids.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t159-review-t117/PREDICTION-T159.md and prediction-t159.json, committed in an
 * ANCESTOR COMMIT of the one carrying this file, and the classification is done afterwards by
 * census_t159.py reading only the emitted JSON.
 *
"""
text = text.replace(old_head, new_head)

open(OUT, 'w').write(text)
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, text.count('cases.add(prodDates(')))
sys.exit(0)
