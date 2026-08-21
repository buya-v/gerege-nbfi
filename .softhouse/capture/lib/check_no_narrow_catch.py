#!/usr/bin/env python3
"""check_no_narrow_catch — T169. A LINT that fails when a NEW capture rig wraps the measured seam in
`catch (RuntimeException ...)` or `catch (Exception ...)`.

WHY A LINT AND NOT A REWRITE. Thirty-four Java rigs in this repository carry the narrow handler, and
every one of them PRODUCED COMMITTED EVIDENCE. T114's standing ruling forbids editing a script that
produced committed evidence, because the artefact then no longer corresponds to the code that made
it. So the historical rigs are FROZEN AND NAMED below, not corrected — and this lint's job is to
stop the defect propagating into the next rig, which is the only place it can still do harm.

The fix a new rig should apply is in `ThrewOutcome.java`, and the mechanical patch that applies it
is `capture/src/t169-red/build_harness_t169.py` (OLD_HANDLER -> NEW_HANDLER).

Usage:
  check_no_narrow_catch.py <repo-root>     exit 0 clean, exit 1 and name every new site otherwise
  check_no_narrow_catch.py --selftest      drive the lint RED on a synthetic new rig (P-22)
"""
import os
import re
import sys
import tempfile

JAVA_CATCH = re.compile(r'\bcatch\s*\(\s*(RuntimeException|Exception)\b')
SEAM_MARKERS = ('generator.generate(', 'ProgressiveLoanScheduleGenerator', 'calculateRepaymentSchedule',
                'MoneyHelper.getMathContext', '.generate(mc,')

# ---------------------------------------------------------------------------------------------
# FROZEN — every file below carried the narrow handler on 2026-08-21, when T169 measured it, and
# every one produced committed evidence. They are recorded, NOT corrected (T114's standing ruling).
# Adding a file here is a deliberate act that a reviewer can see in the diff.
# ---------------------------------------------------------------------------------------------
FROZEN = {
    '.softhouse/capture/actualactual/src/CaptureActualActual.java',
    '.softhouse/capture/audit-t44/mathcontext/src/CaptureMathContext.java',
    '.softhouse/capture/audit-t44/mathcontext/src/CaptureMathContext2.java',
    '.softhouse/capture/audit-t44/rerun-periodratio/src/CapturePeriodRatio.java',
    '.softhouse/capture/dec1-binding/src/CaptureBinding.java',
    '.softhouse/capture/mathcontext/src/CaptureMathContext.java',
    '.softhouse/capture/mathcontext/src/CaptureMathContext2.java',
    '.softhouse/capture/mathcontext/src/CaptureMathContext3.java',
    '.softhouse/capture/mathcontext/src/CaptureT50Ambient.java',
    '.softhouse/capture/mathcontext/src/CaptureT50Tier2.java',
    '.softhouse/capture/periodratio/src/CapturePeriodRatio.java',
    '.softhouse/capture/periodratio/src/CapturePeriodRatio2.java',
    '.softhouse/capture/src/Capture.java',
    '.softhouse/capture/src/Capture2.java',
    '.softhouse/capture/src/Capture3.java',
    '.softhouse/capture/src/Capture3b.java',
    '.softhouse/capture/src/Capture3c.java',
    '.softhouse/capture/src/Capture3d.java',
    '.softhouse/capture/src/Capture3e.java',
    '.softhouse/capture/src/Capture3f.java',
    '.softhouse/capture/src/Capture3g.java',
    '.softhouse/capture/src/Capture3h.java',
    '.softhouse/capture/src/Capture3i.java',
    '.softhouse/capture/src/T21Probe.java',
    '.softhouse/capture/t100-g8-rescope/src/CaptureT100.java',
    '.softhouse/capture/t117-familyb/src/CaptureT117.java',
    '.softhouse/capture/t117-familyb/src/CaptureT117P2.java',
    '.softhouse/capture/t159-review-t117/src/CaptureT159.java',   # SEAM handler already Throwable;
                                                                  # the remaining site is the ambient
                                                                  # MathContext read, not the seam.
    '.softhouse/capture/t83-nonamortizing/src/CaptureT83.java',
    '.softhouse/reviews/T84-evidence/src/CaptureT84.java',
    '.softhouse/reviews/T84-evidence/src/CaptureT84B.java',
    '.softhouse/reviews/t21v2/T21v2Probe.java',
    # T169's own controlled pair. `Pre` IS the historical handler, deliberately and by definition —
    # it exists to be driven red. `Post` has the T169 seam handler; its ONE remaining narrow catch is
    # around the ambient MoneyHelper.getMathContext() read, kept narrow so that the Pre/Post pair
    # differs in the seam handler ALONE and stays a controlled experiment. Raised as a follow-up.
    '.softhouse/capture/src/t169-red/CaptureT169Pre.java',
    '.softhouse/capture/src/t169-red/CaptureT169Post.java',
}


def try_block_for(lines, catch_idx):
    depth = 0
    i = catch_idx
    while i >= 0:
        line = lines[i]
        depth += line.count('}') - line.count('{')
        if re.search(r'\btry\s*\{', line) and depth <= 0:
            return '\n'.join(lines[i:catch_idx + 1])
        i -= 1
    return ''


def scan(root):
    """Every LOAD-BEARING narrow catch, as (relpath, line, text), plus what was INSPECTED.

    Returns (hits, files_opened, dirs_holding_java). T173 added the second and third: this
    lint fires only when it FINDS something, so a walk that opened ZERO .java files printed
    `0 total, 0 NEW`, said `clean`, and exited 0 — a refusal certifying a tree it never read.
    The counts are what let `check` turn that into an ERROR (P-35), and the DIRECTORY count
    is there for the same reason T166 added a package count on the Go side: a file count
    alone cannot tell a whole-tree walk apart from a single-directory one.
    """
    hits = []
    seen = 0
    dirs = set()
    excluded = []
    for dirpath, dirnames, filenames in os.walk(root):
        # `.claude/worktrees` holds OTHER checkouts of this repo -- one per worker ever
        # dispatched. Walking them makes this lint grade 40-odd trees the report does not
        # name, which is the very defect T165 exists to close, and it re-reports every
        # historical rig forever: on the driver's machine the whole-repo walk found 1954
        # .java files and 2292 NEW sites, ALL 2292 of them under .claude/worktrees and
        # NONE in this commit's own content. The exclusions are RETURNED and PRINTED, so
        # the graded root stays explicit rather than merely narrower. [T173 merge defect A,
        # found by the driver on merged main, local fire 20260821-054355]
        keep = []
        for d in dirnames:
            if d in ('.git', 'node_modules', 'build', '.gradle'):
                continue
            full = os.path.join(dirpath, d)
            if os.path.relpath(full, root).replace(os.sep, '/') == '.claude/worktrees':
                excluded.append(os.path.relpath(full, root).replace(os.sep, '/'))
                continue
            keep.append(d)
        dirnames[:] = keep
        for fn in filenames:
            if not fn.endswith('.java'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            seen += 1
            dirs.add(dirpath)
            lines = open(path, errors='replace').read().split('\n')
            for n, line in enumerate(lines):
                s = line.strip()
                if s.startswith('*') or s.startswith('//') or s.startswith('/*'):
                    continue
                if JAVA_CATCH.search(line) and any(m in try_block_for(lines, n) for m in SEAM_MARKERS):
                    hits.append((rel, n + 1, s))
    return hits, seen, dirs, excluded


def check(root):
    hits, seen, dirs, excluded = scan(root)
    new = [h for h in hits if h[0] not in FROZEN]
    frozen_hit_files = {h[0] for h in hits if h[0] in FROZEN}
    print('CENSUS narrow-catch — inspected %d .java files across %d directories under %s '
          '(recursive, whole repository; EXCLUDED %d other checkout root(s): %s)'
          % (seen, len(dirs), os.path.abspath(root), len(excluded),
             ', '.join(excluded) if excluded else 'none'))
    print('narrow load-bearing catch sites: %d total, %d in FROZEN files (%d files), %d NEW'
          % (len(hits), len(hits) - len(new), len(frozen_hit_files), len(new)))
    if seen == 0 or not dirs:
        print('REFUSED — INSPECTED %d .java FILES across %d DIRECTORIES under %s.'
              % (seen, len(dirs), os.path.abspath(root)))
        print('A lint that opens no file refuses nothing and reports clean. '
              'This is an ERROR, not a pass (P-35).')
        return 1
    if new:
        print('REFUSED — a NEW capture rig narrows its seam handler. '
              'java.lang.Error is exactly what the reference oracle throws.')
        for rel, line, text in new:
            print('  %s:%d  %s' % (rel, line, text))
        print('Fix: use ThrewOutcome (capture/lib/ThrewOutcome.java). '
              'Mechanical patch: capture/src/t169-red/build_harness_t169.py.')
        return 1
    print('clean: no capture rig outside the frozen set narrows its seam handler.')
    return 0


def selftest():
    """P-22: the lint must be able to FAIL. Plant a synthetic new rig and require a refusal."""
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, '.softhouse', 'capture', 'newrig', 'src')
        os.makedirs(d)
        # (a) a NEW rig with the narrow handler around the seam -> must be REFUSED
        open(os.path.join(d, 'CaptureBrandNew.java'), 'w').write(
            'class CaptureBrandNew {\n'
            '  void run() {\n'
            '    try {\n'
            '      plan = generator.generate(mc, config);\n'
            '    } catch (RuntimeException e) {\n'
            '      record(e);\n'
            '    }\n'
            '  }\n'
            '}\n')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('a new rig with a narrow seam handler was NOT refused')

        # (b) the same rig, fixed -> must PASS
        open(os.path.join(d, 'CaptureBrandNew.java'), 'w').write(
            'class CaptureBrandNew {\n'
            '  void run() {\n'
            '    try {\n'
            '      plan = generator.generate(mc, config);\n'
            '    } catch (Throwable t) {\n'
            '      if (ThrewOutcome.isFatal(t)) { throw t; }\n'
            '      ThrewOutcome.appendThrew(b, t, 25);\n'
            '    }\n'
            '  }\n'
            '}\n')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 0:
            fails.append('the FIXED rig was refused anyway — the lint is over-broad')

        # (c) a narrow catch that does NOT guard the seam -> must PASS (not over-broad)
        open(os.path.join(d, 'CaptureBrandNew.java'), 'w').write(
            'class CaptureBrandNew {\n'
            '  void run() {\n'
            '    try {\n'
            '      readSomeProperties();\n'
            '    } catch (RuntimeException e) {\n'
            '      record(e);\n'
            '    }\n'
            '  }\n'
            '}\n')
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 0:
            fails.append('a narrow catch away from the seam was refused — the lint is over-broad')

    # (d) T173, P-35: a tree with NO .java file at all -> ERROR, never `clean`. Before this
    #     the lint returned 0 here, because it fires only on what it FINDS and it found
    #     nothing. Deliberately a SEPARATE temporary directory from (a)-(c): reusing theirs
    #     after deleting the file would test deletion, not an unreachable root.
    with tempfile.TemporaryDirectory() as tmp:
        rc = check(tmp)
        print('  -> exit %d' % rc)
        if rc != 1:
            fails.append('a tree containing no .java file at all reported clean — the lint is vacuous')

    print()
    print('check_no_narrow_catch selftest: %d failure(s)' % len(fails))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(check(os.path.abspath(sys.argv[1])))
