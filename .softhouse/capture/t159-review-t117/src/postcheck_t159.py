#!/usr/bin/env python3
"""T159 — postconditions on the capture. Derived from T100's committed postcheck.py (copied, not
edited in place — T114's standing ruling), with the harness filename changed and TWO additions:

  * the id list is required to match /tmp/t159-ids.json EXACTLY AND IN ORDER, and any mismatch is
    reported as missing / extra / reordered rather than as a bare failure;
  * money is read as INTEGER MINOR UNITS from JSON strings, and json.load is called with
    parse_float=Decimal so that a numeric money literal, if one ever appeared, could not become a
    binary double (P-25). Nothing here compares money in a float.

Refuses the run if anything drifts.
"""
import json
import sys
import hashlib
from decimal import Decimal

jsonp, ref3g, commit, harness_sha, seam_sha, idsp = sys.argv[1:7]


def load(path):
    with open(path) as fh:
        return json.load(fh, parse_float=Decimal)


doc = load(jsonp)
caps = doc['captures']
EXPECTED = ['P-CAL-ZPA', 'P-CAL-ZPB'] + json.load(open(idsp))
got = [c['id'] for c in caps]
if got != EXPECTED:
    missing = [i for i in EXPECTED if i not in got]
    extra = [i for i in got if i not in EXPECTED]
    sys.exit("RUN FAILED: id list differs (asked %d, got %d). missing=%d %r extra=%d %r reordered=%s"
             % (len(EXPECTED), len(got), len(missing), missing[:10], len(extra), extra[:10],
                (not missing and not extra)))

# T159 CHANGE, and the reason for it. T117's rig treats ANY errored cell as a rig failure and
# refuses the run. That is right when an error means the rig is broken; it is wrong here, because
# T159 is deliberately asking the oracle for terms nobody has asked before and AN ORACLE REFUSAL IS
# THE FINDING (the brief says so in as many words). So an errored cell is RECORDED, COUNTED and
# NAMED (P-40 -- an enumerator must count what it skipped and say so), the graded-domain checks
# still run on its `inputs`, and only the row-count check is skipped because there are no rows.
# Nothing else in the postcheck is relaxed: the id list must still match exactly and in order, the
# calibrations must still reproduce pass 3g cell for cell, and the attestation must still pin.
errored = []
bad = []
for c in caps:
    i = c.get('inputs', {})
    if c.get('observed') is None or 'error' in c:
        errored.append((c['id'], c.get('error'), (c.get('errorStackTop') or [None])[0]))
    if i.get('mathContextPrecision') != 19 or i.get('mathContextRoundingModeOrdinal') != 4:
        bad.append("%s: not (19, HALF_UP)" % c['id'])
    if i.get('ambientMoneyHelperPrecision') != 19 or i.get('ambientMoneyHelperRoundingModeOrdinal') != 4:
        bad.append("%s: ambient not (19, ordinal 4)" % c['id'])
    for k, want in (('currencyDecimalPlaces', 2), ('currencyCode', 'MNT'), ('currencyInMultiplesOf', None),
                    ('installmentAmountInMultiplesOf', None), ('fixedLength', None), ('daysInMonth', 'DAYS_30'),
                    ('daysInYear', 'DAYS_360'), ('daysInYearCustomStrategy', None), ('downPaymentEnabled', False),
                    ('interestMethod', 'DECLINING_BALANCE'), ('repaymentFrequency', 1),
                    ('repaymentFrequencyType', 'MONTHS'), ('allowFullTermForTranche', False),
                    ('allowPartialPeriodInterestCalculation', True),
                    ('interestRecognitionOnDisbursementDate', False)):
        if i.get(k) != want:
            bad.append("%s: %s=%r outside graded domain" % (c['id'], k, i.get(k)))
    # every REPAYMENT row asked for must be present: n rows + 1 disbursement row
    obs = c.get('observed')
    if obs is not None:
        rep = sum(1 for p in obs['periods'] if p['type'] == 'REPAYMENT')
        if rep != i.get('numberOfRepayments'):
            bad.append("%s: %d REPAYMENT rows for numberOfRepayments=%s"
                       % (c['id'], rep, i.get('numberOfRepayments')))
if bad:
    sys.exit("RUN FAILED (%d breaches):\n  %s" % (len(bad), "\n  ".join(bad[:30])))

ref = load(ref3g)
ref = {c['id']: c for c in ref['captures']}
here = {c['id']: c for c in caps}
for mine, theirs in (('P-CAL-ZPA', 'T64-ZP-A'), ('P-CAL-ZPB', 'T64-ZP-B')):
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',', ':'), default=str)
    b = json.dumps(ref[theirs]['observed'], sort_keys=True, separators=(',', ':'), default=str)
    if a != b:
        sys.exit("RUN FAILED: CALIBRATION DRIFT %s vs %s" % (mine, theirs))
    if here[mine]['inputs'] != ref[theirs]['inputs']:
        sys.exit("RUN FAILED: calibration inputs differ %s" % mine)

att = doc['attestation']
mh = att['moneyHelper']
assert mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingMode'] == 'HALF_UP' \
    and mh['effectiveRoundingModeOrdinal'] == 4 and mh['matchesRatifiedProductionSetting'] is True, mh
assert att['fineract']['gitCommitId'] == commit and att['fineract']['gitDirty'] == 'false'
srcs = {s['file']: s['sha256'] for s in att['sources']}
assert srcs['/cap/src/CaptureT159.java'] == harness_sha
assert srcs['/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java'] == seam_sha

canon = json.dumps(caps, sort_keys=True, separators=(',', ':'), default=str).encode()
rows = sum(len(c['observed']['periods']) for c in caps if c.get('observed') is not None)
print("capture OK: %d cases, %d emitted period rows, canonical sha256 %s"
      % (len(caps), rows, hashlib.sha256(canon).hexdigest()))
print("  id list matches the registered list exactly and IN ORDER: %d ids" % len(EXPECTED))
print("  calibrations P-CAL-ZPA/ZPB reproduce T64-ZP-A/B cell-for-cell, 0 input diffs")
print("  asked %d / observed %d / ERRORED %d / missing 0 / silently skipped 0"
      % (len(EXPECTED), len(caps) - len(errored), len(errored)))
for eid, emsg, etop in errored:
    print("    ERRORED %s -> %s | top frame %s" % (eid, emsg, etop))
