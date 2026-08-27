#!/usr/bin/env python3
"""T169 — postconditions on the pre-fix / post-fix pair, and the two integrity lines side by side.

Derived from T117's committed postcheck.py (COPIED, not edited in place — T114's standing ruling)
with three changes:

  1. it does not abort when a cell threw; it counts and names it, through the shared
     `.softhouse/capture/lib/sweep_integrity.py`;
  2. it prints the integrity line in the T169 form — `asked / observed / threw / skipped`;
  3. it ALSO prints, and labels, what the PRE-T169 counter would have said about the same run. That
     second line is the whole point of the pair: on the pre-fix run it says `0 errored` while a cell
     is known to have thrown, and it says so because there is no cell for it to count.

It is a POSTCHECK, so it must still refuse a run that is broken rather than merely incomplete: the
graded-domain fields, the (19, HALF_UP) MathContext, the attestation pin and the two pass-3g rig
calibrations are all unrelaxed, and any of them failing exits non-zero.

Money is read as INTEGER MINOR UNIT strings and `json.load` runs with `parse_float=Decimal`, so a
numeric money literal could not become a binary double (P-25). Nothing here compares money at all.

Usage:
  postcheck_t169.py <capture.json|-> <ref3g.json> <commit> <harness-name> <harness-sha> <seam-sha>
                    <lib-sha> <ids.json> <container-rc> <stderr-path>
"""
import hashlib
import json
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
# The shared library lives at .softhouse/capture/lib/ in the repo, and is staged next to this
# script's parent when the runner copies the rig into a scratch tree. Both are tried, and if
# NEITHER is found this exits — it does not fall back to a private copy of the counter.
_CANDIDATES = [os.path.join(os.path.dirname(os.path.dirname(HERE)), 'lib'),
               os.path.join(os.path.dirname(HERE), 'lib')]
LIB = next((p for p in _CANDIDATES if os.path.exists(os.path.join(p, 'sweep_integrity.py'))), None)
if LIB is None:
    sys.exit('sweep_integrity.py not found in %r — refusing to run without the shared counter' % _CANDIDATES)
sys.path.insert(0, LIB)
import sweep_integrity  # noqa: E402

(jsonp, ref3g, commit, harness_name, harness_sha, seam_sha, lib_sha, idsp, rc, errp) = sys.argv[1:11]
rc = int(rc)

EXPECTED = ['P-CAL-ZPA', 'P-CAL-ZPB'] + json.load(open(idsp))


def load(path):
    with open(path) as fh:
        return json.load(fh, parse_float=Decimal)


# ---- 0. THE RUN RECORD. A dead run is a RESULT, and it is reported, not hidden. -----------------
err_bytes = os.path.getsize(errp) if os.path.exists(errp) else 0
have_json = os.path.exists(jsonp) and os.path.getsize(jsonp) > 0
doc = None
parse_error = None
if have_json:
    try:
        doc = load(jsonp)
    except ValueError as exc:          # json.JSONDecodeError subclasses ValueError
        parse_error = str(exc)         # recorded and reported; NEVER swallowed and continued past
        doc = None

caps = (doc or {}).get('captures', [])

print('RUN RECORD')
print('  harness              : %s' % harness_name)
print('  container exit code  : %d' % rc)
print('  stderr bytes         : %d' % err_bytes)
print('  capture JSON present : %s' % ('yes, %d bytes' % os.path.getsize(jsonp) if have_json else 'NO'))
if parse_error:
    print('  capture JSON parse   : FAILED — %s' % parse_error)
print()

# ---- 1. THE TWO INTEGRITY LINES ----------------------------------------------------------------
tally = sweep_integrity.tally(caps, EXPECTED)
print('T169 INTEGRITY LINE (four outcomes, mutually exclusive and exhaustive)')
for line in tally.report().split('\n'):
    print('  ' + line)
print()

# The pre-T169 counter, reproduced faithfully: it counted cells that CAME BACK carrying an error,
# over the cells that CAME BACK. It had no term for an id that never produced a cell at all.
legacy_errored = sum(1 for c in caps if c.get('observed') is None or 'error' in c)
print('PRE-T169 COUNTER over the same run (what every published sweep line in this program said)')
print('  %d asked / %d observed / %d errored / 0 skipped'
      % (len(EXPECTED), len(caps) - legacy_errored, legacy_errored))
print('  (it enumerates the cells the rig EMITTED. An id that produced no cell has no term in it.)')
print()

# ---- 2. Unrelaxed postconditions, but only over cells that exist ---------------------------------
bad = []
for c in caps:
    i = c.get('inputs', {})
    if i.get('mathContextPrecision') != 19 or i.get('mathContextRoundingModeOrdinal') != 4:
        bad.append('%s: not (19, HALF_UP)' % c['id'])
    if i.get('ambientMoneyHelperPrecision') != 19 or i.get('ambientMoneyHelperRoundingModeOrdinal') != 4:
        bad.append('%s: ambient not (19, ordinal 4)' % c['id'])
    for k, want in (('currencyDecimalPlaces', 2), ('currencyCode', 'MNT'), ('currencyInMultiplesOf', None),
                    ('installmentAmountInMultiplesOf', None), ('fixedLength', None), ('daysInMonth', 'DAYS_30'),
                    ('daysInYear', 'DAYS_360'), ('daysInYearCustomStrategy', None), ('downPaymentEnabled', False),
                    ('interestMethod', 'DECLINING_BALANCE'), ('repaymentFrequency', 1),
                    ('repaymentFrequencyType', 'MONTHS'), ('allowFullTermForTranche', False),
                    ('allowPartialPeriodInterestCalculation', True),
                    ('interestRecognitionOnDisbursementDate', False)):
        if i.get(k) != want:
            bad.append('%s: %s=%r outside graded domain' % (c['id'], k, i.get(k)))
    obs = c.get('observed')
    if obs is not None:
        rep = sum(1 for p in obs['periods'] if p['type'] == 'REPAYMENT')
        if rep != i.get('numberOfRepayments'):
            bad.append('%s: %d REPAYMENT rows for numberOfRepayments=%s'
                       % (c['id'], rep, i.get('numberOfRepayments')))
if bad:
    sys.exit('RUN FAILED (%d breaches):\n  %s' % (len(bad), '\n  '.join(bad[:30])))

# ---- 3. A THREW CELL MAY NOT BE GRADED. Drive it: try to grade every OBSERVED cell. -------------
observed_ids = [cid for cid in EXPECTED if cid not in tally.threw_ids and cid not in tally.skipped_ids]
if observed_ids:
    sweep_integrity.assert_not_graded_as_observed(caps, observed_ids)
    print('GRADEABILITY: %d cell(s) are gradeable; %d threw and %d are absent, and neither is '
          'gradeable.' % (len(observed_ids), tally.threw, tally.skipped))
    print()

# ---- 4. The rig calibrations, the attestation pin — only meaningful if the run produced a capture -
if doc is None:
    print('CALIBRATION / ATTESTATION: NOT CHECKABLE — this run produced no capture.')
    print()
    sys.exit(1 if (tally.threw + tally.skipped) or rc != 0 else 0)

ref = {c['id']: c for c in load(ref3g)['captures']}
here = {c['id']: c for c in caps}
for mine, theirs in (('P-CAL-ZPA', 'T64-ZP-A'), ('P-CAL-ZPB', 'T64-ZP-B')):
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',', ':'), default=str)
    b = json.dumps(ref[theirs]['observed'], sort_keys=True, separators=(',', ':'), default=str)
    if a != b:
        sys.exit('RUN FAILED: CALIBRATION DRIFT %s vs %s' % (mine, theirs))
    if here[mine]['inputs'] != ref[theirs]['inputs']:
        sys.exit('RUN FAILED: calibration inputs differ %s' % mine)

att = doc['attestation']
mh = att['moneyHelper']
assert mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingMode'] == 'HALF_UP' \
    and mh['effectiveRoundingModeOrdinal'] == 4 and mh['matchesRatifiedProductionSetting'] is True, mh
assert att['fineract']['gitCommitId'] == commit and att['fineract']['gitDirty'] == 'false'
srcs = {s['file']: s['sha256'] for s in att['sources']}
assert srcs['/cap/src/%s.java' % harness_name] == harness_sha, srcs
assert srcs['/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java'] == seam_sha
if lib_sha != '-':
    assert srcs['/cap/src/ThrewOutcome.java'] == lib_sha, srcs

canon = json.dumps(caps, sort_keys=True, separators=(',', ':'), default=str).encode()
rows = sum(len(c['observed']['periods']) for c in caps if c.get('observed') is not None)
print('CALIBRATIONS P-CAL-ZPA/ZPB reproduce pass 3g T64-ZP-A/B cell-for-cell, 0 input diffs')
print('  -> the handler change moved NO number.')
print('ATTESTATION pinned: fineract %s clean, MathContext (19, HALF_UP), harness sha matches.' % commit[:12])
print('capture: %d cells, %d emitted period rows, canonical sha256 %s'
      % (len(caps), rows, hashlib.sha256(canon).hexdigest()))
sys.exit(0)
