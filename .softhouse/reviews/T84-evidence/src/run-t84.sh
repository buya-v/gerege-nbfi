#!/bin/sh
# T84 independent re-probe of gate G-8. Same preconditions as T83's recipe (pinned image id,
# pinned Fineract commit + clean tree, seam byte-identity AND literal seam digest, empty stderr,
# flat precision-19 check, graded-domain check on every unvaried field, and the same two rig
# calibrations against pass 3g's committed capture) -- but a DIFFERENT case list, written to
# attack T83's conclusions rather than repeat its sweep.
#
# Reaches no database and starts no server. "Oracle" here is the Fineract reference
# implementation, never Oracle Database.
set -eu

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="/Users/buv/fineract"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"
REPO="$1"
REF3G_JSON="$REPO/.softhouse/capture/out/capture-prod3g-raw.json"
EXPECTED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"
CAP=/tmp/t84probe
RAW="$CAP/out/stdout.txt"; JSON="$CAP/out/capture-t84-raw.json"
LOG="$CAP/out/oracle-log.txt"; ERR="$CAP/out/stderr.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}')
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] || fail "image id mismatch: $ACTUAL_IMAGE_ID"
ACTUAL_COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] || fail "pin is $ACTUAL_COMMIT"
[ -z "$(git -C "$PINNED_FINERACT" status --porcelain)" ] || fail "pinned checkout DIRTY"
cmp -s "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$PINNED_FINERACT/$SEAM_REL" || fail "seam drift"
SEAM_SHA=$(shasum -a 256 "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" | cut -d' ' -f1)
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] || fail "seam sha $SEAM_SHA"
[ "$(shasum -a 256 "$REF3G_JSON" | cut -d' ' -f1)" = "$EXPECTED_REF3G_SHA" ] || fail "calibration reference sha"
HARNESS_SHA=$(shasum -a 256 "$CAP/src/CaptureT84.java" | cut -d' ' -f1)
RUN_ID="t84-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image %s\n  fineract %s (clean)\n  seam %s\n  harness %s\n  run %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$HARNESS_SHA" "$RUN_ID"

set +e
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" \
  -e ATTEST_SOURCES="/cap/src/CaptureT84.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java" \
  -e ATTEST_CLASSPATH_OUT="/cap/out/classpath-sha256.txt" \
  -v "$CAP:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/CaptureT84.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" CaptureT84
' > "$RAW" 2> "$ERR"
RC=$?
set -e
[ "$RC" -eq 0 ] || { printf 'RUN FAILED: container exited %s\n' "$RC" >&2; cat "$ERR" >&2; exit 1; }

START=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
[ -n "${START:-}" ] || fail "no JSON on stdout"
if [ "$START" -gt 1 ]; then head -n $((START - 1)) "$RAW" > "$LOG"; else : > "$LOG"; fi
tail -n +"$START" "$RAW" > "$JSON"
[ -s "$ERR" ] && { printf 'RUN FAILED: stderr NOT empty:\n' >&2; cat "$ERR" >&2; exit 1; } || true

python3 - "$JSON" "$REF3G_JSON" "$ACTUAL_COMMIT" "$HARNESS_SHA" "$SEAM_SHA" /tmp/t84-ids.json <<'PY'
import json, sys, hashlib
jsonp, ref3g, commit, harness_sha, seam_sha, idsp = sys.argv[1:7]
doc = json.load(open(jsonp)); caps = doc['captures']
EXPECTED = ['P-CAL-ZPA', 'P-CAL-ZPB'] + json.load(open(idsp))
got = [c['id'] for c in caps]
if got != EXPECTED:
    sys.exit("RUN FAILED: id list differs. missing=%r extra=%r"
             % ([i for i in EXPECTED if i not in got][:10], [i for i in got if i not in EXPECTED][:10]))
bad = []
for c in caps:
    i = c.get('inputs', {})
    if c.get('observed') is None: bad.append("%s: observed null" % c['id'])
    if 'error' in c: bad.append("%s: error %s" % (c['id'], c['error']))
    if i.get('mathContextPrecision') != 19 or i.get('mathContextRoundingModeOrdinal') != 4:
        bad.append("%s: not (19, HALF_UP)" % c['id'])
    if i.get('ambientMoneyHelperPrecision') != 19 or i.get('ambientMoneyHelperRoundingModeOrdinal') != 4:
        bad.append("%s: ambient not (19, ordinal 4)" % c['id'])
    for k, want in (('currencyDecimalPlaces',2),('currencyCode','MNT'),('currencyInMultiplesOf',None),
                    ('installmentAmountInMultiplesOf',None),('fixedLength',None),('daysInMonth','DAYS_30'),
                    ('daysInYear','DAYS_360'),('daysInYearCustomStrategy',None),('downPaymentEnabled',False),
                    ('interestMethod','DECLINING_BALANCE'),('repaymentFrequency',1),
                    ('repaymentFrequencyType','MONTHS'),('allowFullTermForTranche',False),
                    ('allowPartialPeriodInterestCalculation',True),
                    ('interestRecognitionOnDisbursementDate',False)):
        if i.get(k) != want: bad.append("%s: %s=%r outside graded domain" % (c['id'], k, i.get(k)))
if bad: sys.exit("RUN FAILED:\n  " + "\n  ".join(bad[:30]))

ref = {c['id']: c for c in json.load(open(ref3g))['captures']}
here = {c['id']: c for c in caps}
for mine, theirs in (('P-CAL-ZPA','T64-ZP-A'), ('P-CAL-ZPB','T64-ZP-B')):
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',',':'))
    b = json.dumps(ref[theirs]['observed'], sort_keys=True, separators=(',',':'))
    if a != b: sys.exit("RUN FAILED: CALIBRATION DRIFT %s vs %s" % (mine, theirs))
    if here[mine]['inputs'] != ref[theirs]['inputs']: sys.exit("RUN FAILED: calibration inputs differ %s" % mine)
att = doc['attestation']; mh = att['moneyHelper']
assert mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingMode'] == 'HALF_UP' \
    and mh['effectiveRoundingModeOrdinal'] == 4 and mh['matchesRatifiedProductionSetting'] is True, mh
assert att['fineract']['gitCommitId'] == commit and att['fineract']['gitDirty'] == 'false'
srcs = {s['file']: s['sha256'] for s in att['sources']}
assert srcs['/cap/src/CaptureT84.java'] == harness_sha
assert srcs['/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java'] == seam_sha
canon = json.dumps(caps, sort_keys=True, separators=(',',':')).encode()
print("capture OK: %d cases, canonical sha256 %s" % (len(caps), hashlib.sha256(canon).hexdigest()))
print("  calibrations P-CAL-ZPA/ZPB reproduce T64-ZP-A/B cell-for-cell, 0 input diffs")
PY
