#!/usr/bin/env python3
"""T100 — derive CaptureT100.java mechanically from T84's committed CaptureT84B.java.

The ONLY edits are: (1) the class name, (2) the sweep case list between the two rig calibrations
and the end of the list, replaced by /tmp/t100-cases.java, (3) the WHY-THIS-PASS-EXISTS paragraph.
Everything that produces a number — the seam call, the emitted columns, the emission rules, the
attestation block, the (19, HALF_UP) setting — is copied byte-for-byte, which is what makes the two
rig calibrations a meaningful check on this harness too.
"""
import re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'reviews', 'T84-evidence', 'src',
                   'CaptureT84B.java')
OUT = os.path.join(HERE, 'CaptureT100.java')

text = open(SRC).read()
lines = text.split('\n')

# 1. locate the sweep cases: every cases.add line that is NOT a rig calibration
idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T84B-' in l]
first, last = idx[0], idx[-1]
assert last - first + 1 == len(idx), 'sweep case block is not contiguous'

cases = open('/tmp/t100-cases.java').read().rstrip('\n').split('\n')
lines = lines[:first] + cases + lines[last + 1:]
text = '\n'.join(lines)

# 2. class name
text = text.replace('CaptureT84B', 'CaptureT100')   # class decl, harness field, getResource, ATTEST_SOURCES
assert 'CaptureT84B' not in text, 'stale references remain'

# 3. honest header — say what THIS pass is, and do not inherit T84B's description of its sweep
old_head = text[text.index(' * WHY THIS PASS EXISTS'):text.index(' * TWO RIG CALIBRATIONS')]
new_head = """ * WHY THIS PASS EXISTS — task T100, gate G-8. G-8 is being rewritten as TWO phenomena rather than
 * one: family A (T83's 198 cells: the outstanding-balance column is stale while the principal column
 * still sums to the disbursed amount) and family B (T84's 22 cells: the principal column itself does
 * not repay the loan). T100 writes that split into .softhouse/gates.md, so T100 re-asks the oracle
 * for the cells that DISCRIMINATE between the two families rather than restating T83's or T84's
 * numbers as the ground of its own claim. Fifteen cases, different tenant ids from T83's and T84's,
 * deliberately scrambled order, and two cells (600.0 % / MNT 0.01 / n = 122 and n = 250) ABOVE the
 * top of n that T84 swept, whose outcome is genuinely open.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, and does not compare anything. It asks the oracle for a schedule
 * and prints what came back. The prediction lives in
 * .softhouse/capture/t100-g8-rescope/PREDICTION.md and prediction.json, committed in an ANCESTOR
 * COMMIT of the one carrying this file, and the classification is done afterwards by
 * classify_two_families.py reading only the emitted JSON.
 *
"""
text = text.replace(old_head, new_head)

open(OUT, 'w').write(text)
n = text.count('cases.add(prodDates(')
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, n))
