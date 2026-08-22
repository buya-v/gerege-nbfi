#!/usr/bin/env python3
"""T116 — derive CaptureT116.java MECHANICALLY from the committed CaptureT100.java.

T114's standing ruling: do not edit a script that produced committed evidence. This script does not
edit CaptureT100.java — it reads it and writes a NEW file. The ONLY differences are (1) the class
name, (2) the sweep case list between the two rig calibrations and the end of the list, replaced by
/tmp/t116-cases.java, and (3) the WHY-THIS-PASS-EXISTS paragraph.

A FOURTH difference, added after the narrow-catch guard refused the first build: the seam-call
handler is replaced by the T169 `catch (Throwable)` / ThrewOutcome form, and the success path gains
its explicit `"outcome": "observed"` line. Both hunks are IMPORTED from the committed
`capture/src/t169-red/build_harness_t169.py` rather than retyped, so they cannot drift from the
version the guard was written against. T169 proved that pair changes no number, and T116's two rig
calibrations re-prove it here.

Everything that produces a number — the seam call, the emitted columns, the emission rules, the
attestation block, the (19, HALF_UP) setting — is copied byte-for-byte, which is what makes the two
rig calibrations (P-CAL-ZPA / P-CAL-ZPB, which must reproduce pass 3g's T64-ZP-A / T64-ZP-B cell for
cell) a meaningful check on THIS harness and not only on T100's.

The derivation is asserted, not assumed.
"""
import importlib.util
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

# 4. THE T169 HANDLER, applied MECHANICALLY, with the two hunks read verbatim out of the committed
#    build_harness_t169.py rather than retyped. CaptureT100.java's handler is `catch (RuntimeException
#    e)`, and java.lang.StackOverflowError is an Error, not a RuntimeException: T159 detonated that
#    hole against this very oracle. The conformance harness's narrow-catch guard REFUSES a NEW rig
#    that ships the old handler, and refusing is right -- so T116 does not ship it.
spec169 = importlib.util.spec_from_file_location(
    't169b', os.path.join(CAPTURE_ROOT, 'src', 't169-red', 'build_harness_t169.py'))
t169b = importlib.util.module_from_spec(spec169)
sys.argv = [sys.argv[0], CAPTURE_ROOT, '/tmp/t116-cases.java']   # its module body reads argv
spec169.loader.exec_module(t169b)
assert text.count(t169b.OLD_HANDLER) == 1, 'the pre-fix handler is not where this script expects it'
assert text.count(t169b.OLD_SUCCESS) == 1, 'the success-path marker appears more than once'
text = text.replace(t169b.OLD_HANDLER, t169b.NEW_HANDLER)
text = text.replace(t169b.OLD_SUCCESS, t169b.NEW_SUCCESS)
assert 'catch (RuntimeException e) {\n            // T21 P1-9' not in text, 'old handler survives'
assert 'printStackTrace' not in text, 'the rig still prints frames to stderr'
assert 'ThrewOutcome.appendThrew' in text, 'the T169 handler did not land'

# 5. THE AMBIENT-MATHCONTEXT HANDLER. T169's pair deliberately left this one narrow so that Pre and
#    Post differed in the SEAM handler alone; T169 raised widening it as a follow-up and the guard's
#    FROZEN list excuses CaptureT159/T169Pre/T169Post for exactly that reason. T116's harness is a
#    NEW file, so the guard flags it, and it is right to: the honest fix is to widen the handler, not
#    to add a file created today to a list of files that carried the defect when it was measured.
#    This catch is entered only if MoneyHelper.getMathContext() THROWS, which it does not on any
#    T116 case -- the postcheck asserts the ambient context is (19, HALF_UP, ordinal 4) on all five
#    -- so the change is behaviour-preserving here, and T116 verified that by re-running the capture
#    and diffing every `observed` and `inputs` block against the pre-change run: 5 of 5 identical.
OLD_AMBIENT = """            } catch (RuntimeException e) {
                ambientMathContext = e.getClass().getName() + ": " + e.getMessage();"""
NEW_AMBIENT = """            } catch (Throwable e) {
                // T116: Throwable, not RuntimeException. An Error raised while READING the ambient
                // MathContext would otherwise escape and kill the JVM before any JSON is printed,
                // which is the same class of hole T169 closed at the seam. See T169 follow-up 2.
                ambientMathContext = e.getClass().getName() + ": " + e.getMessage();"""
assert text.count(OLD_AMBIENT) == 1, 'the ambient handler is not where this script expects it'
text = text.replace(OLD_AMBIENT, NEW_AMBIENT)
assert 'catch (RuntimeException' not in text, 'a narrow catch survives in the rig'

open(OUT, 'w').write(text)
n = text.count('cases.add(prodDates(')
print('wrote %s  (%d cases incl. 2 rig calibrations)' % (OUT, n))
sys.exit(0)
