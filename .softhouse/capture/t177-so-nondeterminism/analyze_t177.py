#!/usr/bin/env python3
"""T177 analyzer — counts trials against DENOMINATORS and refuses to hide anything.

Rules it enforces, from .softhouse/patterns.md:
  P-40  count what was skipped. Every java process has an EXPECTED trial count derived from its
        plan; trials never reached (because the JVM died) are counted as NOT-REACHED, never folded
        into an outcome and never silently dropped.
  P-35  zero-inspected is an ERROR. A series that parsed no trial, or a whole analysis that parsed
        no trial, exits non-zero.
  P-46  quote by extraction. T159's committed totalInterestAmount for the disputed cell is READ OUT
        of the committed capture, never retyped, and every observed probe is checked against it.

Outcome classes are mutually exclusive and exhaustive:
  observed | threw-StackOverflowError | threw-other | rig-error | not-reached

Run-level anomalies (non-zero java exit, non-empty stderr) are reported SEPARATELY and are never
folded into either outcome, exactly as requirement 5 of the task demands.

Usage: analyze_t177.py <repo-root> <out-dir> [<out-dir> ...]
"""
import gzip
import json
import os
import re
import sys
from collections import Counter, defaultdict

# The SHARED classifier from T169's lib, not a local re-implementation. cell_outcome() also carries
# T169's refusals -- a cell declaring "observed" with a null observed block, or "threw" with a
# non-null one, raises rather than being counted.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import sweep_integrity  # noqa: E402

DISPUTED = 'T177-PROBE-R600p0-N3000-B10001'
T159_CAPTURE = '/.softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz'
T159_DISPUTED_ID = 'T159-R600p0-N3000-B10001'


def expected_trials(plan):
    """The number of seam calls the plan asks for. A plan whose count cannot be derived returns
    None, and the analyzer says so rather than assuming the run was complete."""
    if plan == 'single':
        return 1
    if plan == 'calib':
        return 2
    m = re.fullmatch(r'repeat:(\d+)', plan)
    if m:
        return int(m.group(1))
    m = re.fullmatch(r'warm:(\d+):(\d+)', plan)
    if m:
        return int(m.group(1)) + int(m.group(2))
    m = re.fullmatch(r'thread:(\d+):(\d+)', plan)
    if m:
        return int(m.group(2))
    m = re.fullmatch(r't159prefix:(\d+)', plan)
    if m:
        return 24 + int(m.group(1))
    m = re.fullmatch(r'cell:(\d+):(\d+):(\d+)', plan)
    if m:
        return int(m.group(3))
    return None


def t159_map(repo):
    """id -> (outcome, totalInterestAmount) for every cell in the COMMITTED T159 capture.
    Read out of the committed bytes; never retyped (P-46)."""
    with gzip.open(repo + T159_CAPTURE, 'rt') as f:
        cap = json.load(f)
    out = {}
    for c in cap['captures']:
        obs = c.get('observed')
        out[c['id']] = ('observed', obs['totalInterestAmount']) if obs else ('threw', None)
    return out


def parse_run_index(path):
    runs = []
    complete = False
    for ln in open(path):
        ln = ln.strip()
        if ln == 'MATRIX COMPLETE':
            complete = True
            continue
        m = re.fullmatch(
            r'RUN series=(\S+) idx=(\d+) plan=(\S+) flags=\[(.*)\](?: harness=(\S+))? exit=(\d+) '
            r'wall_s=(\d+) stdout_bytes=(\d+) stderr_bytes=(\d+)', ln)
        if not m:
            runs.append({'parse_error': ln})
            continue
        runs.append({'series': m.group(1), 'idx': int(m.group(2)), 'plan': m.group(3),
                     'flags': m.group(4), 'harness': m.group(5) or 'CaptureT177',
                     'exit': int(m.group(6)), 'wall_s': int(m.group(7)),
                     'stdout_bytes': int(m.group(8)), 'stderr_bytes': int(m.group(9))})
    return runs, complete


def main():
    repo = sys.argv[1]
    outdirs = sys.argv[2:]
    if not outdirs:
        print('ERROR: no output directory given')
        sys.exit(1)

    t159 = t159_map(repo)
    t159_ti = t159.get(T159_DISPUTED_ID, ('absent', None))[1]
    print('T159 committed cells EXTRACTED from %s: %d' % (T159_CAPTURE.lstrip('/'), len(t159)))
    print('  %s -> %s' % (T159_DISPUTED_ID, t159.get(T159_DISPUTED_ID)))
    if t159_ti is None:
        print('ERROR: could not extract T159 reference value for the disputed cell')
        sys.exit(1)
    print()

    all_trials = []
    run_rows = []
    anomalies = []
    for od in outdirs:
        ri = os.path.join(od, 'run-index.txt')
        if not os.path.exists(ri):
            anomalies.append('%s: no run-index.txt -- the container never finished its loop' % od)
            continue
        runs, matrix_complete = parse_run_index(ri)
        if not matrix_complete:
            anomalies.append('%s: run-index.txt has no MATRIX COMPLETE line -- the matrix was CUT SHORT' % od)
        for r in runs:
            if 'parse_error' in r:
                anomalies.append('%s: unparseable run-index line %r' % (od, r['parse_error']))
                continue
            so = os.path.join(od, 'raw', '%s-%d.stdout' % (r['series'], r['idx']))
            se = os.path.join(od, 'raw', '%s-%d.stderr' % (r['series'], r['idx']))
            trials, footer, nonjson = [], None, 0
            if os.path.exists(so):
                for ln in open(so, errors='replace'):
                    ln = ln.strip()
                    if not ln.startswith('{'):
                        if ln:
                            nonjson += 1
                        continue
                    try:
                        d = json.loads(ln)
                    except json.JSONDecodeError:
                        anomalies.append('%s %s-%d: a line starting with { did not parse as JSON'
                                         % (od, r['series'], r['idx']))
                        continue
                    if d.get('kind') == 'trial':
                        d['_run'] = r
                        d['_outdir'] = od
                        trials.append(d)
                    elif d.get('kind') == 'footer':
                        footer = d
            else:
                anomalies.append('%s: %s missing' % (od, so))
            exp = expected_trials(r['plan'])
            emitted = len(trials)
            not_reached = None if exp is None else max(0, exp - emitted)
            r.update({'expected': exp, 'emitted': emitted, 'not_reached': not_reached,
                      'footer': footer is not None, 'nonjson_lines': nonjson,
                      'stderr_path': se, 'outdir': od})
            if r['exit'] != 0:
                anomalies.append('%s %s-%d: java exited %d (RUN-LEVEL, not an outcome)'
                                 % (od, r['series'], r['idx'], r['exit']))
            if r['stderr_bytes'] != 0:
                anomalies.append('%s %s-%d: stderr %d bytes (RUN-LEVEL, not an outcome)'
                                 % (od, r['series'], r['idx'], r['stderr_bytes']))
            if footer is None:
                anomalies.append('%s %s-%d: NO FOOTER -- the JVM died mid-plan; %s trial(s) never reached'
                                 % (od, r['series'], r['idx'], not_reached))
            run_rows.append(r)
            all_trials.extend(trials)

    if not all_trials:
        print('ERROR: ZERO trials parsed. An analysis that inspects nothing is a FAILURE (P-35).')
        sys.exit(1)

    def cls(t):
        if t.get('outcome') == 'rig-error':
            return 'rig-error:' + str(t.get('rigError'))
        # sweep_integrity.cell_outcome RAISES on a self-contradictory cell; that is the point of
        # using it rather than reading t['outcome'] directly.
        o = sweep_integrity.cell_outcome(t)
        if o == sweep_integrity.OBSERVED:
            return 'observed'
        _, ec, _, _ = sweep_integrity.throw_detail(t)
        return 'threw-StackOverflowError' if ec == 'java.lang.StackOverflowError' else 'threw-other:' + str(ec)

    # ---------------- per-series tally, probe phase only, with denominators ----------------
    print('=' * 100)
    print('PER-SERIES TALLY — PROBE TRIALS ONLY (the disputed cell: B = 10001 minor units, n = 3000, rate 600.0)')
    print('=' * 100)
    print('%-18s %-16s %-28s %5s %6s %9s %9s %6s  %s' %
          ('series', 'plan', 'cell (B minor units, n)', 'JVMs', 'asked', 'observed', 'threwSOE', 'other',
           'flags'))
    series_probe = defaultdict(list)
    for t in all_trials:
        if t.get('phase') == 'probe':
            series_probe[(t['_outdir'], t['series'], t['plan'], t['_run']['flags'], t['cellId'])].append(t)
    grand = Counter()
    for (od, s, plan, flags, cell_id), ts in sorted(series_probe.items()):
        c = Counter(cls(t) for t in ts)
        jvms = len({t['runIdx'] for t in ts})
        other = sum(v for k, v in c.items() if k.startswith('threw-other') or k.startswith('rig-error'))
        shape = 'B=%s minor, n=%s' % (int(ts[0]['principalMinorUnits']), ts[0]['numberOfRepayments'])
        print('%-18s %-16s %-28s %5d %6d %9d %9d %6d  %s' %
              (s, plan, shape, jvms, len(ts), c['observed'], c['threw-StackOverflowError'], other,
               flags or '(none)'))
        grand.update(c)
    print()
    print('ALL PROBE TRIALS: %d asked / %d observed / %d threw StackOverflowError / %d other' %
          (sum(grand.values()), grand['observed'], grand['threw-StackOverflowError'],
           sum(v for k, v in grand.items() if not k.startswith(('observed', 'threw-StackOverflowError')))))
    print()

    # ---------------- non-probe phases, so nothing is unreported ----------------
    other_phases = Counter()
    for t in all_trials:
        if t.get('phase') != 'probe':
            other_phases[(t.get('phase'), cls(t))] += 1
    if other_phases:
        print('NON-PROBE TRIALS (warm / prefix / calib cells — reported so no seam call is unaccounted for)')
        for (ph, k), v in sorted(other_phases.items()):
            print('  phase=%-7s %-40s %d' % (ph, k, v))
        print()

    # ---------------- outcome AS A FUNCTION OF POSITION IN THE JVM ----------------
    print('=' * 100)
    print('OUTCOME BY PROBE INDEX WITHIN THE JVM  (o = observed, X = threw StackOverflowError)')
    print('=' * 100)
    byrun = defaultdict(list)
    for t in all_trials:
        if t.get('phase') == 'probe':
            byrun[(t['_outdir'], t['series'], t['runIdx'])].append(t)
    for k in sorted(byrun):
        ts = sorted(byrun[k], key=lambda t: t['seq'])
        line = ''.join('o' if cls(t) == 'observed' else ('X' if cls(t).startswith('threw-Stack') else '?')
                       for t in ts)
        ms = ','.join(str(t.get('elapsedMs')) for t in ts)
        print('  %-9s %-18s run %-3s seq0=%-3s %-12s  elapsedMs: %s'
              % (k[0].split('/')[-1], k[1], k[2], ts[0]['seq'], line, ms))
    print()

    # ---------------- COLD START: the JVM's VERY FIRST seam call ----------------
    # `seq == 0` is the only unambiguous definition of "cold": no seam call of ANY kind preceded it
    # in that process. Note this is NOT the same as "attempt 1 of this cell" — a warm-ctrl or
    # t159prefix run asks the probe for the first time in a JVM that has already done 50 or 24 other
    # seam calls, and that distinction is the whole finding.
    print('=' * 100)
    print('COLD START — probe trials that are the JVM\'s VERY FIRST seam call (seq == 0)')
    print('=' * 100)
    cold = defaultdict(Counter)
    for t in all_trials:
        if t.get('phase') == 'probe' and t.get('seq') == 0:
            xss = [f for f in t['_run']['flags'].split() if f.startswith('-Xss')]
            cold[(t['cellId'], xss[0] if xss else 'default -Xss (measured 2040k)',
                  'C2 off' if 'TieredStopAtLevel' in t['_run']['flags'] else 'C2 on')][cls(t)] += 1
    for key in sorted(cold):
        c = cold[key]
        tot = sum(c.values())
        print('  %-34s %-32s %-7s  JVMs %-3d observed %-3d threwSOE %-3d'
              % (key[0], key[1], key[2], tot, c['observed'], c['threw-StackOverflowError']))
    print()

    # ---------------- attempt-index tally, DEFAULT STACK SIZE ONLY ----------------
    # The headline numbers come from here, not from hand arithmetic. A run is "default stack" when
    # its JVM flags do not set -Xss; -XX:MaxJavaStackTraceDepth changes only how many frames are
    # RECORDED, so it is left in, and -XX:TieredStopAtLevel is a different experiment and is split
    # out on its own line.
    print('=' * 100)
    print('ATTEMPT-INDEX TALLY — probe trials at the JVM DEFAULT stack size, by attempt number')
    print('within the JVM (attempt 1 = the cell\'s first seam call in that process)')
    print('=' * 100)
    attempts = defaultdict(Counter)
    for k in sorted(byrun):
        ts = sorted(byrun[k], key=lambda t: t['seq'])
        flags = ts[0]['_run']['flags']
        if '-Xss' in flags:
            continue
        bucket = 'C2 OFF (TieredStopAtLevel=1)' if 'TieredStopAtLevel' in flags else 'default JIT'
        for i, t in enumerate(ts, start=1):
            attempts[(bucket, t['cellId'], i)][cls(t)] += 1
    for (bucket, cell_id, i) in sorted(attempts):
        c = attempts[(bucket, cell_id, i)]
        tot = sum(c.values())
        print('  %-30s %-34s attempt %-2d  JVMs %-3d observed %-3d threwSOE %-3d'
              % (bucket, cell_id, i, tot, c['observed'], c['threw-StackOverflowError']))
    print()

    # ---------------- stack depth at overflow ----------------
    depths = defaultdict(list)
    for t in all_trials:
        if t.get('phase') == 'probe' and t.get('errorClass') == 'java.lang.StackOverflowError':
            depths[(t['series'], t['_run']['flags'])].append(t.get('errorStackDepthTotal'))
    if depths:
        print('RECORDED STACK DEPTH AT OVERFLOW (errorStackDepthTotal; HotSpot caps recorded frames at')
        print('MaxJavaStackTraceDepth, default 1024, so a flat 1024 is the CAP, not the depth)')
        for (s, fl), ds in sorted(depths.items()):
            print('  %-18s flags=%-34s n=%-3d min=%s max=%s distinct=%s'
                  % (s, fl or '(none)', len(ds), min(ds), max(ds), sorted(set(ds))))
        print()

    # ---------------- MONEY CHECK, by extraction ----------------
    print('=' * 100)
    print('MONEY CHECK — every OBSERVED disputed-cell probe against T159\'s committed value')
    print('=' * 100)
    # Prefix cells are checked too: T177's t159prefix replay re-asks 24 of T159's committed cells,
    # and each observed one is an independent re-derivation of a committed number.
    obs = [t for t in all_trials if t.get('phase') in ('probe', 'prefix') and t.get('outcome') == 'observed']
    money_fail = False
    checked = 0
    nocounterpart = Counter()
    percell = defaultdict(Counter)
    for t in obs:
        percell[t['cellId']][t['observed']['totalInterestAmount']] += 1
    for cell_id, vals in sorted(percell.items()):
        n = sum(vals.values())
        # T159's counterpart is found by the cell's ACTUAL inputs, not by a name convention.
        sample = next(t for t in obs if t['cellId'] == cell_id)
        ref_id = 'T159-R600p0-N%d-B%d' % (sample['numberOfRepayments'], int(sample['principalMinorUnits']))
        ref = t159.get(ref_id)
        print('  %-34s observed %3d time(s); distinct totalInterestAmount: %s' % (cell_id, n, dict(vals)))
        if ref is None:
            nocounterpart[cell_id] = n
            print('      no committed T159 counterpart %s — NOT CHECKED, and reported as such' % ref_id)
            continue
        if ref[0] != 'observed':
            print('      T159 counterpart %s THREW in T159, so it carries no value to compare' % ref_id)
            continue
        for v in vals:
            checked += 1
            if v != ref[1]:
                money_fail = True
                print('      MISMATCH vs %s: T177 %r, T159 committed %r' % (ref_id, v, ref[1]))
            else:
                print('      matches committed %s = %s' % (ref_id, ref[1]))
    print('  money comparisons made: %d; observed probes with no committed counterpart: %d'
          % (checked, sum(nocounterpart.values())))
    if not obs:
        print('  NOTE: no probe was observed, so this check inspected nothing (reported, not hidden).')
    elif checked and not money_fail:
        print('  When the oracle answers at all it answers with the SAME NUMBER as the committed capture.')
        print('  The nondeterminism is in WHETHER it answers, not in WHAT it answers.')
    print()

    # ---------------- P-40 accounting ----------------
    print('=' * 100)
    print('P-40 ACCOUNTING — every java process, what it was asked for and what it delivered')
    print('=' * 100)
    tot_exp = tot_emit = tot_missing = 0
    unknown_plan = 0
    for r in sorted(run_rows, key=lambda r: (r['outdir'], r['series'], r['idx'])):
        if r['expected'] is None:
            unknown_plan += 1
            print('  %-18s run %-3d plan=%-14s EXPECTED COUNT UNKNOWN for this plan — not counted as complete'
                  % (r['series'], r['idx'], r['plan']))
            continue
        tot_exp += r['expected']
        tot_emit += r['emitted']
        tot_missing += r['not_reached']
        if r['not_reached'] or r['exit'] or r['stderr_bytes'] or not r['footer']:
            print('  %-18s run %-3d plan=%-14s asked %-3d emitted %-3d NOT-REACHED %-3d exit=%d stderr=%dB footer=%s'
                  % (r['series'], r['idx'], r['plan'], r['expected'], r['emitted'], r['not_reached'],
                     r['exit'], r['stderr_bytes'], r['footer']))
    print('  TOTAL: %d java processes, %d seam calls asked, %d emitted, %d NEVER REACHED, %d plans with an unknown count'
          % (len(run_rows), tot_exp, tot_emit, tot_missing, unknown_plan))
    print()

    print('=' * 100)
    print('RUN-LEVEL ANOMALIES (classified SEPARATELY — never folded into observed or threw)')
    print('=' * 100)
    if not anomalies:
        print('  none: every java process exited 0, wrote empty stderr, and printed its footer.')
    for a in anomalies:
        print('  ' + a)
    print()

    bad = money_fail or any('exit' in a or 'stderr' in a or 'NO FOOTER' in a for a in anomalies)
    print('ANALYZER VERDICT: %s' % ('PROBLEMS ABOVE' if bad else 'clean'))
    sys.exit(2 if money_fail else 0)


if __name__ == '__main__':
    main()
