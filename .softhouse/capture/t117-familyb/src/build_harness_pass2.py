#!/usr/bin/env python3
"""T117 PASS 2 — derive CaptureT117P2.java MECHANICALLY from the committed CaptureT100.java.

Same derivation as build_harness.py, from the same source, so pass 2's rig is the same rig as
pass 1's and as T100's: the ONLY differences are (1) the class name, (2) the sweep case list
between the two rig calibrations and the end of the list, replaced by /tmp/t117p2-cases.java, and
(3) the WHY-THIS-PASS-EXISTS paragraph. Nothing that produces a number is touched, which is what
keeps the two rig calibrations (P-CAL-ZPA / P-CAL-ZPB against pass 3g's T64-ZP-A / T64-ZP-B) a
meaningful check on this harness.

CaptureT100.java is READ, never written (T114's standing ruling).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')
OUT = os.path.join(HERE, 'CaptureT117P2.java')

text = open(SRC).read()
lines = text.split('\n')

idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T100-' in l]
assert idx, 'no T100 sweep cases found in the source harness'
first, last = idx[0], idx[-1]
assert last - first + 1 == len(idx), 'sweep case block is not contiguous'

cases = open('/tmp/t117p2-cases.java').read().rstrip('\n').split('\n')
lines = lines[:first] + cases + lines[last + 1:]
text = '\n'.join(lines)

text = text.replace('CaptureT100', 'CaptureT117P2')
assert 'CaptureT100' not in text, 'stale references remain'

old_head = text[text.index(' * WHY THIS PASS EXISTS'):text.index(' * TWO RIG CALIBRATIONS')]
new_head = """ * WHY THIS PASS EXISTS — task T117 PASS 2, gate G-8. T117 pass 1 refuted its own registered
 * prediction that family B's failing principal cannot exceed one minor unit: family B was
 * observed at B = 3 and B = 5 minor units (MNT 0.03, MNT 0.05). Pass 1 therefore killed the
 * "sub-minor-unit dust" description and established NO upper bound at all — B = 5 is simply the
 * largest principal it was asked to try. Pass 2 asks how far up it goes: an odd-principal ladder
 * to 120,000,001 minor units (MNT 1,200,000.01), an even-principal control ladder, a contiguous
 * B = 6..20 run at n = 150, and two re-asks of pass-1 cells under new tenant ids.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t117-familyb/PREDICTION-PASS2.md and prediction-pass2.json, committed in an
 * ANCESTOR COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_t117.py reading only the emitted JSON.
 *
"""
text = text.replace(old_head, new_head)

open(OUT, 'w').write(text)
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, text.count('cases.add(prodDates(')))
sys.exit(0)
