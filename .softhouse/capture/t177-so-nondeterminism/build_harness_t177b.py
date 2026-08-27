#!/usr/bin/env python3
"""Derive CaptureT177b.java MECHANICALLY from CaptureT177.java.

WHY A SECOND HARNESS AND NOT AN EDIT. `CaptureT177.java` produced the pilot and matrix-A evidence
that this task commits. T114's standing ruling forbids editing a script that produced committed
evidence, because the artefact then no longer corresponds to the code that made it — and T169
recorded that `build_harness_t159.py` failed to reproduce its own harness, which is exactly the gap
this script exists to close. So CaptureT177 is FROZEN and the one extra plan is added by derivation.

WHAT IS ADDED, and nothing else:
  a plan `cell:<principalMinorUnits>:<n>:<K>` that asks an ARBITRARY (principal, n) cell K times,
  so the cells G-8's HEADLINE actually rests on can be probed the same way the disputed cell was.
  It is purely additive: no existing plan's branch is touched, and the seam call, the Case record,
  every input field and the money handling are byte-identical.

verify_pair() ASSERTS that every differing line lies inside the new branch, the class name, or the
file's own header comment. If it does not, this script fails and writes nothing.

Usage: build_harness_t177b.py <rig-dir>
"""
import difflib
import os
import sys

NEW_BRANCH = '''        } else if (plan.startsWith("cell:")) {
            // T177b ONLY. An arbitrary (principal in MINOR UNITS, n) cell, asked K times, so the
            // cells G-8's headline rests on can be probed exactly as the disputed cell was. Money
            // stays integer minor units: cell(...) routes through minor(), which is
            // new BigDecimal(<int>).movePointLeft(2). No float, no decimal literal.
            String[] p = plan.split(":");
            int principalMinor = Integer.parseInt(p[1]);
            int n = Integer.parseInt(p[2]);
            int k = Integer.parseInt(p[3]);
            String id = "T177-CELL-R600p0-N" + n + "-B" + principalMinor;
            String tenant = "t177_cell_n" + n + "_b" + principalMinor;
            for (int i = 0; i < k; i++) {
                emit(series, runIdx, plan, seq, "probe", "main", -1L,
                        cell(id, principalMinor, n, "600.0", tenant), false);
            }
'''

ANCHOR = '        } else if (plan.startsWith("thread:")) {\n'

HEADER_NOTE = ''' *
 * ---------------------------------------------------------------------------------------------
 * CaptureT177b — DERIVED MECHANICALLY from CaptureT177.java by build_harness_t177b.py. The ONLY
 * addition is the `cell:<principalMinorUnits>:<n>:<K>` plan; every other line, including the seam
 * call and every input field, is byte-identical to the frozen CaptureT177.java.
 * ---------------------------------------------------------------------------------------------
'''


def verify_pair(src, out):
    """Every differing line must be inside the new branch, the class rename, or the header note."""
    allowed_added = set(x.rstrip() for x in NEW_BRANCH.splitlines() if x.strip())
    allowed_added |= set(x.rstrip() for x in HEADER_NOTE.splitlines() if x.strip())
    added, removed = [], []
    for line in difflib.unified_diff(src.splitlines(), out.splitlines(), lineterm='', n=0):
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        if line.startswith('+'):
            added.append(line[1:])
        elif line.startswith('-'):
            removed.append(line[1:])
    bad = []
    for a in added:
        s = a.strip()
        if not s:
            continue
        if a.rstrip() in allowed_added:
            continue
        if 'CaptureT177b' in a:
            continue
        bad.append('ADDED OUTSIDE THE ALLOWED HUNKS: ' + a)
    for r in removed:
        if 'CaptureT177' in r:
            continue
        if r.strip() == '':
            continue
        bad.append('REMOVED: ' + r)
    return added, removed, bad


def main():
    rig = sys.argv[1]
    src_path = os.path.join(rig, 'src', 'CaptureT177.java')
    out_path = os.path.join(rig, 'src', 'CaptureT177b.java')
    src = open(src_path).read()

    if ANCHOR not in src:
        sys.exit('BUILD FAILED: anchor branch not found in CaptureT177.java')
    out = src.replace(ANCHOR, NEW_BRANCH + ANCHOR, 1)
    out = out.replace('public class CaptureT177 {', 'public class CaptureT177b {', 1)
    out = out.replace(' */\nimport org.apache.fineract', HEADER_NOTE + ' */\nimport org.apache.fineract', 1)

    added, removed, bad = verify_pair(src, out)
    print('PAIR: %d added line(s), %d removed line(s)' % (len(added), len(removed)))
    for b in bad:
        print('  ' + b)
    if bad:
        sys.exit('BUILD FAILED: the derivation touches code outside the allowed hunks. Nothing written.')
    if len(added) < 10:
        sys.exit('BUILD FAILED: the derivation added almost nothing — it cannot have worked (P-35).')
    open(out_path, 'w').write(out)
    print('PAIR VERIFIED: every differing line is inside the new `cell:` branch, the class name, or')
    print('the header note. The seam call and every input field are byte-identical.')
    print('wrote ' + out_path)


if __name__ == '__main__':
    main()
