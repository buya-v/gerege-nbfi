#!/usr/bin/env python3
"""T169 — build the PRE-FIX and POST-FIX harnesses as a CONTROLLED PAIR.

Both are derived MECHANICALLY from the committed `t100-g8-rescope/src/CaptureT100.java`, which is
READ and never written (T114's standing ruling: do not edit a script that produced committed
evidence). The two outputs differ from each other in exactly TWO hunks, both inside the seam-call
handler, and this script ASSERTS that — see `verify_pair()` at the bottom, which is the whole point
of building them from one source instead of writing them by hand.

    CaptureT169Pre.java    the handler EXACTLY as T83 / T84 / T100 / T117 shipped it:
                             catch (RuntimeException e) { ...; e.printStackTrace(System.err); }
    CaptureT169Post.java   the T169 handler:
                             catch (Throwable t) { fatal? announce+rethrow : ThrewOutcome.appendThrew }
                           plus `"outcome": "observed"` on the success path, so that a cell's
                           outcome is a FIELD and not an inference.

A note on the same script one task earlier: `t159-review-t117/src/build_harness_t159.py` does NOT
reproduce the committed `CaptureT159.java` — running it emits the file with `catch (RuntimeException
e)` and `e.printStackTrace(System.err)` still in place, because T159 applied its own two hunks by
hand afterwards. The diff is exactly and only the change T159 documents, so nothing T159 reported is
affected, but the builder is not a reproduction of the harness. T169's builder applies its hunks
mechanically so that it is.

Usage:  build_harness_t169.py <capture-root> <cases-file>
"""
import os
import subprocess
import sys

CAPTURE_ROOT = os.path.abspath(sys.argv[1])
CASES_FILE = os.path.abspath(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'src', 'CaptureT100.java')

WHY = """ * WHY THIS PASS EXISTS -- task T169. NOT to measure the oracle: to measure THE RIG. Every capture
 * harness in this program wrapped the seam call in `catch (RuntimeException e)`, and
 * java.lang.StackOverflowError is an Error, not a RuntimeException. T159 detonated that hole with
 * (B = 10001 minor, n = 2000) at 600.0 percent, which the reference oracle cannot evaluate: it
 * recurses into itself at ProgressiveEMICalculator.java:1214 until the stack is gone. The failure
 * is NOT monotone -- (B = 10001, n = 3000) succeeds -- so the region cannot be bounded by probing
 * its edges, and a rig that cannot RECORD the throw cannot even report that it happened.
 *
 * This pass asks the same five cells twice: once with the PRE-FIX handler and once with the T169
 * handler. The pre-fix run is expected to DIE, emitting no capture at all, so that its sweep can
 * report neither the throw nor anything else. The post-fix run is expected to complete and report
 * the throwing cell as a first-class THREW outcome, with its class and message, alongside the two
 * rig calibrations reproducing pass 3g cell for cell -- which is what proves the handler change
 * moved no number.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It asks the oracle for a schedule and prints
 * what came back, or records what was thrown instead. It classifies nothing; postcheck_t169.py does
 * that afterwards, reading only the emitted JSON, through .softhouse/capture/lib/sweep_integrity.py.
 *
"""

# ---- HUNK 1: the handler -----------------------------------------------------------------------
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

NEW_HANDLER = """        } catch (Throwable t) {
            // T169. Throwable, NOT RuntimeException. java.lang.StackOverflowError is an Error, so
            // the handler this replaces could not see it at all: it escaped run(), escaped main(),
            // and killed the JVM before a byte of JSON was printed. A throw is now a FIRST-CLASS
            // OUTCOME -- neither an observation nor an absence. The fatal rule, and the reason the
            // frames go to the JSON instead of to stderr, are documented in ThrewOutcome.java.
            if (ThrewOutcome.isFatal(t)) {
                ThrewOutcome.announceFatal(c.id(), t);
                throw t;
            }
            ThrewOutcome.appendThrew(b, t, 25);
            return b.toString();
        }
"""

# ---- HUNK 2: the success path declares its outcome ----------------------------------------------
OLD_SUCCESS = """        b.append("      \\"observed\\": {\\n");"""
NEW_SUCCESS = """        b.append("      \\"outcome\\": \\"observed\\",\\n");
        b.append("      \\"observed\\": {\\n");"""


def derive(text, cls, cases):
    lines = text.split('\n')
    idx = [i for i, l in enumerate(lines) if 'cases.add(prodDates("T100-' in l]
    assert idx, 'no T100 sweep cases found in the source harness'
    first, last = idx[0], idx[-1]
    assert last - first + 1 == len(idx), 'sweep case block is not contiguous'
    lines = lines[:first] + cases + lines[last + 1:]
    text = '\n'.join(lines)

    text = text.replace('CaptureT100', cls)
    assert 'CaptureT100' not in text, 'stale references remain'

    head_a = text.index(' * WHY THIS PASS EXISTS')
    head_b = text.index(' * TWO RIG CALIBRATIONS')
    text = text[:head_a] + WHY + text[head_b:]
    return text


def main():
    src = open(SRC).read()
    assert OLD_HANDLER in src, 'the pre-fix handler is not where this script expects it'
    assert src.count(OLD_HANDLER) == 1, 'the pre-fix handler appears more than once'
    assert src.count(OLD_SUCCESS) == 1, 'the success-path marker appears %d times' % src.count(OLD_SUCCESS)

    cases = open(CASES_FILE).read().rstrip('\n').split('\n')

    pre = derive(src, 'CaptureT169Pre', cases)
    post = derive(src, 'CaptureT169Post', cases)
    post = post.replace(OLD_HANDLER, NEW_HANDLER)
    post = post.replace(OLD_SUCCESS, NEW_SUCCESS)
    assert 'catch (RuntimeException e) {\n            // T21 P1-9' not in post, 'post still has the old handler'
    assert 'printStackTrace' not in post, 'post still prints to stderr'

    open(os.path.join(HERE, 'CaptureT169Pre.java'), 'w').write(pre)
    open(os.path.join(HERE, 'CaptureT169Post.java'), 'w').write(post)

    verify_pair(pre, post)
    print('wrote CaptureT169Pre.java and CaptureT169Post.java (%d cases incl. 2 rig calibrations)'
          % pre.count('cases.add(prodDates('))


def verify_pair(pre, post):
    """The pair must differ ONLY in the handler and the one success-path line. Proved by diff."""
    a = os.path.join(HERE, '.pair-pre.tmp')
    b = os.path.join(HERE, '.pair-post.tmp')
    open(a, 'w').write(pre.replace('CaptureT169Pre', 'X'))
    open(b, 'w').write(post.replace('CaptureT169Post', 'X'))
    diff = subprocess.run(['diff', '-u', a, b], capture_output=True, text=True).stdout
    os.remove(a)
    os.remove(b)
    changed = [l for l in diff.split('\n') if (l.startswith('-') or l.startswith('+'))
               and not l.startswith('---') and not l.startswith('+++')]
    removed = [l for l in changed if l.startswith('-')]
    added = [l for l in changed if l.startswith('+')]
    # Everything removed must come from the old handler; everything added from the new one.
    for l in removed:
        assert l[1:] in OLD_HANDLER or l[1:] == OLD_SUCCESS, 'unexpected removal: %r' % l
    for l in added:
        assert l[1:] in NEW_HANDLER or l[1:] in NEW_SUCCESS, 'unexpected addition: %r' % l
    print('PAIR VERIFIED: the two harnesses differ in %d removed / %d added lines, all of them '
          'inside the seam-call handler or the one success-path outcome line. Nothing that '
          'produces a NUMBER differs.' % (len(removed), len(added)))


if __name__ == '__main__':
    main()
