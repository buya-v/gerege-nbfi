#!/usr/bin/env python3
"""T100 — postconditions on the capture. Same checks run-t84.sh applied, split out into a file so
the runner needs no heredoc. Refuses the run if anything drifts."""
import json, sys, hashlib

jsonp, ref3g, commit, harness_sha, seam_sha, idsp = sys.argv[1:7]
doc = json.load(open(jsonp))
caps = doc['captures']
EXPECTED = ['P-CAL-ZPA', 'P-CAL-ZPB'] + json.load(open(idsp))
got = [c['id'] for c in caps]
if got != EXPECTED:
    sys.exit("RUN FAILED: id list differs. missing=%r extra=%r"
             % ([i for i in EXPECTED if i not in got][:10], [i for i in got if i not in EXPECTED][:10]))
bad = []
for c in caps:
    i = c.get('inputs', {})
    if c.get('observed') is None:
        bad.append("%s: observed null" % c['id'])
    if 'error' in c:
        bad.append("%s: error %s" % (c['id'], c['error']))
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
if bad:
    sys.exit("RUN FAILED:\n  " + "\n  ".join(bad[:30]))

ref = {c['id']: c for c in json.load(open(ref3g))['captures']}
here = {c['id']: c for c in caps}
for mine, theirs in (('P-CAL-ZPA', 'T64-ZP-A'), ('P-CAL-ZPB', 'T64-ZP-B')):
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',', ':'))
    b = json.dumps(ref[theirs]['observed'], sort_keys=True, separators=(',', ':'))
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
assert srcs['/cap/src/CaptureT100.java'] == harness_sha
assert srcs['/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java'] == seam_sha
canon = json.dumps(caps, sort_keys=True, separators=(',', ':')).encode()
print("capture OK: %d cases, canonical sha256 %s" % (len(caps), hashlib.sha256(canon).hexdigest()))
print("  calibrations P-CAL-ZPA/ZPB reproduce T64-ZP-A/B cell-for-cell, 0 input diffs")
