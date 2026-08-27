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
import contextlib
import io
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

    # -----------------------------------------------------------------------------------
    # (e)-(h) THE EXCLUSION, DRIVEN BOTH DIRECTIONS. [T191, T188's finding F-1]
    #
    # `scan` decides what this lint may IGNORE, and until now that branch was the one
    # branch its own P-22 machinery could not demonstrate: cases (a)-(d) all plant inside
    # the tree's own content, so every one of them passes whether the exclusion is present,
    # absent, inverted, or misspelt. An exclusion is a licence to say nothing about a
    # subtree; a licence that nothing tests is P-22 pointed at the lint's blind spot rather
    # than at its trigger. Both directions, because fixing one alone converts a false alarm
    # into a silent pass (P-50, P-57 rule 3):
    #     IGNORED — the rig under `.claude/worktrees/` must NOT be refused, and the census
    #               must NAME the exclusion rather than merely be quieter;
    #     REFUSED — the byte-identical rig in the tree's own content MUST be refused.
    # Then (g) plants BOTH AT ONCE, because that is the only arm that can tell a working
    # exclusion apart from a lint that has stopped refusing anything at all.
    # -----------------------------------------------------------------------------------
    NARROW_RIG = (
        'class CaptureBrandNew {\n'
        '  void run() {\n'
        '    try {\n'
        '      plan = generator.generate(mc, config);\n'
        '    } catch (RuntimeException e) {\n'
        '      record(e);\n'
        '    }\n'
        '  }\n'
        '}\n')
    CLEAN_RIG = (
        'class CaptureAlreadyFixed {\n'
        '  void run() {\n'
        '    try {\n'
        '      plan = generator.generate(mc, config);\n'
        '    } catch (Throwable t) {\n'
        '      if (ThrewOutcome.isFatal(t)) { throw t; }\n'
        '      ThrewOutcome.appendThrew(b, t, 25);\n'
        '    }\n'
        '  }\n'
        '}\n')

    def _plant(root, rel, body):
        path = os.path.join(root, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').write(body)
        return path

    def _run(root):
        """check(root) with its stdout captured AND echoed, so assertions can read it."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(root)
        out = buf.getvalue()
        sys.stdout.write(out)
        print('  -> exit %d' % rc)
        return rc, out

    OWN = '.softhouse/capture/newrig/src/CaptureBrandNew.java'
    WT = '.claude/worktrees/agent-deadbeef/.softhouse/capture/newrig/src/CaptureBrandNew.java'

    # (e) IGNORED direction. A clean own-tree rig keeps `seen > 0`, so a rc of 0 means
    #     "inspected and found nothing to refuse" and not the vacuous-walk ERROR of (d).
    with tempfile.TemporaryDirectory() as tmp:
        _plant(tmp, '.softhouse/capture/existing/src/CaptureAlreadyFixed.java', CLEAN_RIG)
        _plant(tmp, WT, NARROW_RIG)
        rc, out = _run(tmp)
        if rc != 0:
            fails.append('(e) a narrow-catch rig under .claude/worktrees was REFUSED — the '
                         'exclusion is not in force, and this lint would grade every historical checkout')
        if 'CaptureBrandNew.java' in out:
            fails.append('(e) the report NAMED a file under .claude/worktrees — it is grading a '
                         'subtree it claims to exclude')
        if 'EXCLUDED 1 other checkout root(s): .claude/worktrees' not in out:
            fails.append('(e) the census did not NAME the exclusion. A walk that is merely quieter '
                         'is indistinguishable from one that found nothing (P-35/T165): '
                         'got %r' % out.splitlines()[0:1])
        if 'inspected 1 .java files' not in out:
            fails.append('(e) expected exactly the 1 own-tree .java file to be inspected; census says %r'
                         % out.splitlines()[0:1])

    # (f) REFUSED direction. THE BYTE-IDENTICAL RIG in the tree's own content. If (e) passed
    #     and this fails, the exclusion is over-broad; if both pass, the predicate discriminates.
    with tempfile.TemporaryDirectory() as tmp:
        _plant(tmp, '.softhouse/capture/existing/src/CaptureAlreadyFixed.java', CLEAN_RIG)
        _plant(tmp, OWN, NARROW_RIG)
        rc, out = _run(tmp)
        if rc != 1:
            fails.append('(f) the SAME rig in the tree\'s own content was NOT refused — the '
                         'exclusion is over-broad, or the lint has stopped refusing anything')
        if OWN not in out:
            fails.append('(f) the refusal did not NAME %s' % OWN)

    # (g) BOTH AT ONCE — the arm that actually separates the two hypotheses. The refusal must
    #     name the own-tree file and ONLY it: exactly one NEW site, from the tree's own content.
    with tempfile.TemporaryDirectory() as tmp:
        _plant(tmp, OWN, NARROW_RIG)
        _plant(tmp, WT, NARROW_RIG)
        rc, out = _run(tmp)
        if rc != 1:
            fails.append('(g) with a narrow rig in BOTH trees the lint did not refuse at all')
        if '%d NEW' % 1 not in out and ', 1 NEW' not in out:
            fails.append('(g) expected exactly 1 NEW site (the own-tree one); census line was %r'
                         % [l for l in out.splitlines() if 'NEW' in l])
        if OWN not in out:
            fails.append('(g) the refusal did not name the own-tree file')
        if 'worktrees' in out.replace('EXCLUDED 1 other checkout root(s): .claude/worktrees', ''):
            fails.append('(g) the refusal named a path under .claude/worktrees as well as the '
                         'own-tree file — the exclusion leaks')

    # (h) THE EXCLUSION IS ANCHORED AT THE GRADED ROOT, and that is deliberate, not an
    #     oversight: the predicate is `relpath(dir, root) == '.claude/worktrees'`, so it names
    #     EXACTLY ONE directory that the census can print, rather than a glob whose reach a
    #     reader cannot see. A `.claude/worktrees` nested deeper in real repository content is
    #     NOT a checkout root and IS graded. Frozen here so that a later widening to a
    #     substring/`in path` test — which would silently un-grade any path containing those
    #     bytes — has to change a failing selftest to land. Note the direction: this arm fails
    #     CLOSED (a spurious refusal), which is the safe side for a money-adjacent lint.
    with tempfile.TemporaryDirectory() as tmp:
        _plant(tmp, 'src/vendor/.claude/worktrees/CaptureBrandNew.java', NARROW_RIG)
        rc, out = _run(tmp)
        if rc != 1:
            fails.append('(h) a .claude/worktrees nested below the graded root was IGNORED — the '
                         'exclusion has been widened from one named directory to a path substring')
        if 'EXCLUDED 0 other checkout root(s): none' not in out:
            fails.append('(h) the census claimed a checkout-root exclusion for a directory that is '
                         'not at the graded root')

    print()
    print('check_no_narrow_catch selftest: %d failure(s)' % len(fails))
    for f in fails:
        print('  FAIL ' + f)
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(check(os.path.abspath(sys.argv[1])))
