#!/usr/bin/env python3
"""T159 — derive CaptureT159.java MECHANICALLY from the committed CaptureT100.java.

Identical derivation to T117's build_harness.py / build_harness_pass2.py, from the
SAME source harness, so T159's rig is the same rig as T117's, T100's and pass 3g's.
The differences are (1) the class name, (2) the sweep case list between the two rig
calibrations and the end of the list, replaced by /tmp/t159-cases.java, (3) the
WHY-THIS-PASS-EXISTS paragraph, and (4) the seam-call handler (HUNK below).

T176 (raised by T169): this builder did NOT reproduce the committed CaptureT159.java
-- it emitted the seam handler with `catch (RuntimeException e)` and
`e.printStackTrace(System.err)` still in place, and T159 applied its own two hunks
(both inside that one handler) BY HAND afterwards, undocumented in this script. T176
verified those two hand hunks are correct and necessary, not a mistake to revert:
java.lang.StackOverflowError is an Error, not a RuntimeException, so the ORIGINAL
handler could not catch the very failure T159 exists to probe (see the
WHY-THIS-PASS-EXISTS paragraph below -- T159 asks the region above n = 1000, which
T169 later showed is exactly where the reference oracle can StackOverflow); and
run-t159.sh refuses any run whose stderr is non-empty, so
`e.printStackTrace(System.err)` would make a THREW cell abort the whole sweep
instead of being recorded as data. HUNK below applies both changes mechanically, so
the chain from recipe to committed evidence reproduces.

Nothing that produces a NUMBER is touched by any of the four differences above --
the handler change affects only whether a thrown exception is recorded as data (and
kept out of stderr) versus escaping as a rig failure; it does not alter the success
path. That is what keeps the two rig calibrations (P-CAL-ZPA / P-CAL-ZPB against pass
3g's T64-ZP-A / T64-ZP-B) a meaningful check on this harness -- and it is what makes
a byte-identity comparison between a T159 cell and the corresponding committed T117
cell meaningful.

CaptureT100.java is READ, never written (T114's standing ruling).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')
OUT = os.path.join(HERE, 'CaptureT159.java')

# ---- HUNK: the seam-call handler, applied BY HAND in the committed file (T176) ------------------
OLD_HANDLER = """        } catch (RuntimeException e) {
            // T21 P1-9: keep the frames. A discarded stack trace is a lost finding.
            b.append("      \\"observed\\": null,\\n");
            b.append("      \\"error\\": \\"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\\"", "'").replace("\\n", " ")).append("\\",\\n");
            b.append("      \\"errorStackTop\\": [");
            StackTraceElement[] st = e.getStackTrace();
            int n = Math.min(st.length, 25);
            for (int i = 0; i < n; i++) {
                b.append(i == 0 ? "" : ", ").append(q(st[i].toString()));
            }
            b.append("],\\n");
            Throwable cause = e.getCause();
            b.append("      \\"errorCause\\": ").append(q(cause == null ? null : cause.getClass().getName() + ": " + cause.getMessage())).append("\\n");
            b.append("    }");
            e.printStackTrace(System.err);
            return b.toString();
        }
"""

NEW_HANDLER = """        } catch (Throwable e) { // T159: Throwable, not RuntimeException - a StackOverflowError must be RECORDED, not fatal
            // T21 P1-9: keep the frames. A discarded stack trace is a lost finding.
            b.append("      \\"observed\\": null,\\n");
            b.append("      \\"error\\": \\"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\\"", "'").replace("\\n", " ")).append("\\",\\n");
            b.append("      \\"errorStackTop\\": [");
            StackTraceElement[] st = e.getStackTrace();
            int n = Math.min(st.length, 25);
            for (int i = 0; i < n; i++) {
                b.append(i == 0 ? "" : ", ").append(q(st[i].toString()));
            }
            b.append("],\\n");
            Throwable cause = e.getCause();
            b.append("      \\"errorCause\\": ").append(q(cause == null ? null : cause.getClass().getName() + ": " + cause.getMessage())).append("\\n");
            b.append("    }");
            // T159: the trace is kept in errorStackTop above; it is deliberately NOT printed to
            // stderr, because run-t159.sh refuses the run on non-empty stderr and an errored cell
            // is DATA for this probe, not a rig failure. postcheck_t159.py counts and names them.
            return b.toString();
        }
"""

text = open(SRC).read()
assert text.count(OLD_HANDLER) == 1, 'the pre-fix handler is not where this script expects it, or appears more than once'

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

text = text.replace(OLD_HANDLER, NEW_HANDLER)
assert 'catch (RuntimeException e) {\n            // T21 P1-9' not in text, 'old handler still present'
assert 'printStackTrace' not in text, 'still prints to stderr'
assert text.count(NEW_HANDLER) == 1, 'new handler not applied exactly once'

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
