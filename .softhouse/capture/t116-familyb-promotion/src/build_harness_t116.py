#!/usr/bin/env python3
"""T116 — derive CaptureT116.java MECHANICALLY from the committed CaptureT100.java.

T114's standing ruling: do not edit a script that produced committed evidence. This script does not
edit CaptureT100.java — it reads it and writes a NEW file. The ONLY differences are (1) the class
name, (2) the sweep case list between the two rig calibrations and the end of the list, replaced by
/tmp/t116-cases.java, and (3) the WHY-THIS-PASS-EXISTS paragraph.

Everything that produces a number — the seam call, the emitted columns, the emission rules, the
attestation block, the (19, HALF_UP) setting — is copied byte-for-byte, which is what makes the two
rig calibrations (P-CAL-ZPA / P-CAL-ZPB, which must reproduce pass 3g's T64-ZP-A / T64-ZP-B cell for
cell) a meaningful check on THIS harness and not only on T100's.

The derivation is asserted, not assumed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))          # .../.softhouse/capture
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')
OUT = os.path.join(HERE, 'CaptureT116.java')

text = open(SRC).read()
lines = text.split('\n')

# 1. the sweep cases: every cases.add line that is NOT a rig calibration
idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T100-' in l]
assert idx, 'no T100 sweep cases found in the source harness'
first, last = idx[0], idx[-1]
assert last - first + 1 == len(idx), 'sweep case block is not contiguous'

cases = open('/tmp/t116-cases.java').read().rstrip('\n').split('\n')
lines = lines[:first] + cases + lines[last + 1:]
text = '\n'.join(lines)

# 2. class name
text = text.replace('CaptureT100', 'CaptureT116')
assert 'CaptureT100' not in text, 'stale references remain'

# 3. honest header — say what THIS pass is; do not inherit T100's description of its case list
old_head = text[text.index(' * WHY THIS PASS EXISTS'):text.index(' * TWO RIG CALIBRATIONS')]
new_head = """ * WHY THIS PASS EXISTS - task T116, gate G-8, option (a). T116 carries an explicit PROMOTION
 * mandate: promote a parity vector over the family-B region with a narrow, declared
 * invariant_exemptions entry. Family B (600.0 % p.a., MNT 0.01, n >= 104) is a GENUINE
 * non-amortization that the Go port reproduces cell for cell, so the FAIL it produces without an
 * exemption is purely an invariant FAIL and the exemption is decisive; family A is a CELL DIFF,
 * over which an exemption has no power, and T116 does not attempt it.
 *
 * T116 re-captures the three cells it intends to promote from the live oracle rather than
 * transcribing another task's committed bytes: n = 103 (the amortizing cell below the boundary,
 * promotable with NO exemption), n = 104 (the lowest family-B cell ever observed) and n = 108 (the
 * cell T100's exemption demo graded at 761 cells / 0 diffs).
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t116-familyb-promotion/PREDICTION.md and prediction.json, committed in an
 * ANCESTOR COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_t116.py reading only the emitted JSON.
 *
"""
text = text.replace(old_head, new_head)

open(OUT, 'w').write(text)
n = text.count('cases.add(prodDates(')
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, n))
sys.exit(0)
