#!/bin/sh
# ---------------------------------------------------------------------------------------------
# T83 capture recipe — EXECUTABLE, and it FAILS THE RUN on any precondition breach. Gate G-8.
#
# WHAT IT DOES. Compiles CaptureT83.java and the pinned seam class against the pinned
# reference-oracle (Fineract) image and runs the embeddable progressive-loan schedule generator
# IN-PROCESS. It does NOT start the Fineract server and it opens NO database connection.
# (PostgreSQL remains the only permitted engine for this program; this seam reaches no database at
# all, and "the oracle" here is the Fineract reference implementation, never Oracle Database.) It
# writes NOTHING to the running reference-oracle container, its PostgreSQL database, its
# `c_configuration` or any tenant — including tenant `gerege`, which a sibling worker owns this
# fire.
#
# Run from the repo root:
#
#     sh .softhouse/capture/t83-nonamortizing/src/run-t83.sh
#
# WHAT MAKES IT FAIL — every one exits non-zero and refuses to leave a capture behind that a later
# reader could mistake for a good one:
#
#   1. docker missing, or the image absent
#   2. image id != the pinned digest
#   3. pinned Fineract checkout missing, at the wrong commit, or with a dirty working tree
#   4. the committed seam class differs from the pinned original by even one byte
#   4b. the committed seam class does not have the sha256 PINNED AS A LITERAL IN THIS SCRIPT.
#       Check 4 has two operands and a caller controls both (the repo copy and $PINNED_FINERACT), so
#       two files mutated the same way compare EQUAL. A literal digest has no such operand.
#   5. the container exits non-zero
#   6. stdout carries no JSON document, or the JSON does not parse
#   7. stderr is non-empty (a stack trace where a capture was expected)
#   8. any capture has "observed": null, or an "error" key, or the wrong count, or the wrong ids —
#      and the EXPECTED ID LIST IS REGENERATED HERE from the same rate/term/range table the harness
#      uses, so a silently truncated sweep is a failure rather than a smaller boundary
#   9. the effective MathContext rounding mode is not the ratified HALF_UP / RoundingMode ordinal 4,
#      or the ambient MoneyHelper precision is not 19, on ANY case. Every case in this pass runs at
#      production precision 19; there are no precision-12 companions, so the precision check is a
#      flat equality and not a table lookup that could silently default.
#  10. RIG CALIBRATION — P-CAL-ZPA / P-CAL-ZPB fail to reproduce pass 3g's committed T64-ZP-A /
#      T64-ZP-B cell for cell, INPUTS INCLUDED AND TENANT ID INCLUDED
#  11. the pass-3g calibration reference is missing or at the wrong sha256
#
# WHAT IT DOES NOT DO. It does not classify a case as amortizing or not, does not count failures and
# does not compare anything to the prediction. classify-boundary.py does that, afterwards, from the
# emitted JSON, and it is a separate file so that the capture cannot be shaped by the classification.
#
# DEFECT CLASS DELIBERATELY AVOIDED (T22 P0-5): a shell glob in an output path cannot expand against
# a file that does not exist yet. EVERY output path below is a literal filename.
# ---------------------------------------------------------------------------------------------
set -eu

# --- pinned facts. Changing one of these is a deliberate act, not a convenience. ----------------
EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="${PINNED_FINERACT:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

# The sha256 of the seam source at the pinned Fineract commit, recorded independently by T18, T21,
# T21-v2 and every pass from 3b to 3i.
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"

# The committed pass-3g artefact this pass CALIBRATES AGAINST. Its sha256 is the one recorded in the
# provenance block of the four promoted T64-ZP parity vectors, so calibrating against it calibrates
# against exactly the bytes the nearest committed neighbours of this region were transcribed from.
REF3G_JSON="${REF3G_JSON:-.softhouse/capture/out/capture-prod3g-raw.json}"
EXPECTED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"

CAP_DIR=".softhouse/capture/t83-nonamortizing"
OUT_DIR="$CAP_DIR/out"
RAW="$OUT_DIR/capture-t83-stdout.txt"
JSON="$OUT_DIR/capture-t83-raw.json"
LOG="$OUT_DIR/capture-t83-oracle-log.txt"
ERR="$OUT_DIR/capture-t83-stderr.txt"
ATT="$OUT_DIR/capture-t83-attestation.json"
CPD="$OUT_DIR/capture-t83-classpath-sha256.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

# --- 0. we must be at the repo root -------------------------------------------------------------
[ -f "$CAP_DIR/src/CaptureT83.java" ] || fail "run me from the repo root; $CAP_DIR/src/CaptureT83.java not found from $(pwd)"
[ -d "$OUT_DIR" ] || mkdir -p "$OUT_DIR"

# --- 1/2. the image ------------------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || fail "docker not on PATH"
ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}' 2>/dev/null) \
  || fail "image $EXPECTED_IMAGE_REF not present"
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] \
  || fail "image id mismatch. expected $EXPECTED_IMAGE_ID, got $ACTUAL_IMAGE_ID. A capture from a different image is not a capture from the pinned reference oracle."

# --- 3. the pinned checkout ----------------------------------------------------------------------
[ -d "$PINNED_FINERACT/.git" ] || fail "pinned Fineract checkout not found at $PINNED_FINERACT"
ACTUAL_COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] \
  || fail "pinned checkout is at $ACTUAL_COMMIT, expected $EXPECTED_FINERACT_COMMIT"
DIRTY=$(git -C "$PINNED_FINERACT" status --porcelain)
[ -z "$DIRTY" ] || fail "pinned checkout working tree is DIRTY; the seam source under it cannot be trusted"

# --- 4. seam-class byte identity (the capture is void without this) -------------------------------
SEAM_LOCAL="$CAP_DIR/src/EmbeddableProgressiveLoanScheduleGenerator.java"
SEAM_PINNED="$PINNED_FINERACT/$SEAM_REL"
[ -f "$SEAM_PINNED" ] || fail "pinned seam source not found at $SEAM_PINNED"
cmp -s "$SEAM_LOCAL" "$SEAM_PINNED" \
  || fail "seam class DRIFT: $SEAM_LOCAL differs from the pinned original $SEAM_PINNED. The run would not be executing the oracle's code."
SEAM_SHA=$(shasum -a 256 "$SEAM_LOCAL" | cut -d' ' -f1)
# --- 4b. and it must be THE pinned digest, not merely equal to a file a caller can reach ----------
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] \
  || fail "seam class sha256 is $SEAM_SHA, expected the pinned $EXPECTED_SEAM_SHA. Two files mutated the same way compare equal under cmp; this check is the one that cannot be defeated by editing a file."
HARNESS_SHA=$(shasum -a 256 "$CAP_DIR/src/CaptureT83.java" | cut -d' ' -f1)

# --- 11. the calibration reference must be the bytes the corpus was built from --------------------
[ -f "$REF3G_JSON" ] || fail "calibration reference $REF3G_JSON not found; T83 cannot prove its rig reproduces an already-known value"
ACTUAL_REF3G_SHA=$(shasum -a 256 "$REF3G_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3G_SHA" = "$EXPECTED_REF3G_SHA" ] \
  || fail "calibration reference $REF3G_JSON is sha256 $ACTUAL_REF3G_SHA, expected $EXPECTED_REF3G_SHA — these are not the bytes the four T64-ZP parity vectors were transcribed from"

RUN_ID="t83-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image      %s\n  fineract   %s (clean)\n  seam sha   %s\n  harness    %s\n  cal ref    %s (%s)\n  run id     %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$HARNESS_SHA" "$REF3G_JSON" "$ACTUAL_REF3G_SHA" "$RUN_ID"

# --- 5. the run. Literal output paths only. -------------------------------------------------------
set +e
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" \
  -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" \
  -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" \
  -e ATTEST_SOURCES="/cap/src/CaptureT83.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java" \
  -e ATTEST_CLASSPATH_OUT="/cap/out/capture-t83-classpath-sha256.txt" \
  -v "$PWD/$CAP_DIR:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/CaptureT83.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" CaptureT83
' > "$RAW" 2> "$ERR"
RC=$?
set -e
[ "$RC" -eq 0 ] || { printf 'RUN FAILED: container exited %s. stderr:\n' "$RC" >&2; cat "$ERR" >&2; exit 1; }

# --- 6/7. split the oracle's own SLF4J lines off the front, then validate --------------------------
# The lines are KEPT, not discarded: they independently corroborate the rounding mode per tenant.
START=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
[ -n "${START:-}" ] || { printf 'RUN FAILED: no JSON document on stdout. Raw output retained at %s\n' "$RAW" >&2; exit 1; }
if [ "$START" -gt 1 ]; then
  head -n $((START - 1)) "$RAW" > "$LOG"
else
  : > "$LOG"
fi
tail -n +"$START" "$RAW" > "$JSON"

if [ -s "$ERR" ]; then
  printf 'RUN FAILED: stderr is NOT empty — a stack trace was written where a clean capture was expected:\n' >&2
  cat "$ERR" >&2
  exit 1
fi

# --- 8/9/10. structural + settings validation, calibration, and the attestation sidecar -----------
python3 - "$JSON" "$ATT" "$LOG" "$ACTUAL_IMAGE_ID" "$EXPECTED_IMAGE_REF" "$ACTUAL_COMMIT" "$PINNED_FINERACT" \
        "$SEAM_SHA" "$HARNESS_SHA" "$RUN_ID" "$CPD" "$ERR" "$RAW" "$REF3G_JSON" "$ACTUAL_REF3G_SHA" <<'PY'
import hashlib, json, os, sys

(jsonp, attp, logp, image_id, image_ref, commit, pinned, seam_sha, harness_sha, run_id, cpd, errp,
 rawp, ref3g, ref3g_sha) = sys.argv[1:16]

raw = open(jsonp, 'rb').read()
try:
    doc = json.loads(raw.decode('utf-8'))
except Exception as e:
    sys.exit("RUN FAILED: capture JSON does not parse: %s" % e)

# The expected id list is REGENERATED here from the same rate/term/range table the harness carries.
# It is duplicated on purpose: a harness that silently dropped part of the sweep would otherwise
# emit a smaller, self-consistent capture and a reader would see a boundary rather than a bug.
RATES = ["21.6", "7.0", "16.8", "36.0"]
TERMS = [2, 3, 4, 6, 12, 24, 36, 56]
SWEEP_TO = [
    [5, 5, 5, 6, 9, 13, 17, 21],
    [5, 5, 5, 6, 9, 15, 20, 27],
    [5, 5, 5, 6, 9, 14, 18, 23],
    [5, 5, 5, 6, 8, 12, 14, 17],
]
EXPECTED_IDS = ['P-CAL-ZPA', 'P-CAL-ZPB']
for ri, rate in enumerate(RATES):
    for ti, n in enumerate(TERMS):
        for minor in range(1, SWEEP_TO[ri][ti] + 1):
            EXPECTED_IDS.append("T83-SW-R%s-N%d-B%d" % (rate.replace('.', 'p'), n, minor))

caps = doc.get('captures')
if not isinstance(caps, list) or len(caps) != len(EXPECTED_IDS):
    sys.exit("RUN FAILED: expected %d captures, got %r"
             % (len(EXPECTED_IDS), len(caps) if isinstance(caps, list) else caps))
if [c.get('id') for c in caps] != EXPECTED_IDS:
    got = [c.get('id') for c in caps]
    missing = [i for i in EXPECTED_IDS if i not in got]
    extra = [i for i in got if i not in EXPECTED_IDS]
    sys.exit("RUN FAILED: capture id list differs. missing=%r extra=%r" % (missing[:20], extra[:20]))

bad = []
for c in caps:
    if c.get('observed') is None:
        bad.append("%s: observed is null" % c.get('id'))
    if 'error' in c:
        bad.append("%s: error key present -> %s" % (c.get('id'), c.get('error')))
    i = c.get('inputs', {})
    if i.get('ambientMoneyHelperPrecision') != 19 or i.get('ambientMoneyHelperRoundingModeOrdinal') != 4:
        bad.append("%s: ambient MoneyHelper is (%s, ordinal %s), not (19, ordinal 4)"
                   % (c.get('id'), i.get('ambientMoneyHelperPrecision'), i.get('ambientMoneyHelperRoundingModeOrdinal')))
    if i.get('mathContextRoundingModeOrdinal') != 4:
        bad.append("%s: threaded rounding mode ordinal is %s, not HALF_UP ordinal 4"
                   % (c.get('id'), i.get('mathContextRoundingModeOrdinal')))
    # EVERY case in this pass runs at production precision. Flat equality, not a defaulted lookup.
    if i.get('mathContextPrecision') != 19:
        bad.append("%s: must run at precision 19, got %s" % (c.get('id'), i.get('mathContextPrecision')))
    # and every case must be inside the graded domain on the fields this pass does not vary
    for k, want in (('currencyDecimalPlaces', 2), ('currencyCode', 'MNT'), ('currencyInMultiplesOf', None),
                    ('installmentAmountInMultiplesOf', None), ('fixedLength', None),
                    ('daysInMonth', 'DAYS_30'), ('daysInYear', 'DAYS_360'),
                    ('daysInYearCustomStrategy', None), ('downPaymentEnabled', False),
                    ('interestMethod', 'DECLINING_BALANCE'), ('repaymentFrequency', 1),
                    ('repaymentFrequencyType', 'MONTHS'), ('allowFullTermForTranche', False),
                    ('allowPartialPeriodInterestCalculation', True),
                    ('interestRecognitionOnDisbursementDate', False)):
        if i.get(k) != want:
            bad.append("%s: %s is %r, outside the graded domain this pass claims to sample (want %r)"
                       % (c.get('id'), k, i.get(k), want))
if bad:
    sys.exit("RUN FAILED: capture validation:\n  " + "\n  ".join(bad[:40]))

# --- RIG CALIBRATION ------------------------------------------------------------------------------
# Not a resemblance check and not a tolerance: the whole `observed` block of each calibration case,
# every cell, must equal pass 3g's committed observation of the case it repeats, and the `inputs`
# block must be identical too — tenant id included — so the reproduction is of the SAME question.
CALIBRATIONS = {'P-CAL-ZPA': 'T64-ZP-A', 'P-CAL-ZPB': 'T64-ZP-B'}
ref_raw = open(ref3g, 'rb').read()
if hashlib.sha256(ref_raw).hexdigest() != ref3g_sha:
    sys.exit("RUN FAILED: calibration reference %s changed under the run" % ref3g)
ref_cases = {c['id']: c for c in json.loads(ref_raw.decode('utf-8'))['captures']}

here = {c['id']: c for c in caps}
cal_report = []
for mine in sorted(CALIBRATIONS):
    theirs = CALIBRATIONS[mine]
    if theirs not in ref_cases:
        sys.exit("RUN FAILED: calibration target %s is absent from %s" % (theirs, ref3g))
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',', ':'))
    b = json.dumps(ref_cases[theirs]['observed'], sort_keys=True, separators=(',', ':'))
    if a != b:
        sys.exit("RUN FAILED: CALIBRATION DRIFT. %s does not reproduce %s of %s.\n"
                 "  this run: %s\n  committed: %s\n"
                 "A rig that cannot reproduce an already-known value is not trustworthy; NOTHING "
                 "else from this run may be believed." % (mine, theirs, ref3g, a, b))
    ia = dict(here[mine]['inputs'])
    ib = dict(ref_cases[theirs]['inputs'])
    if ia != ib:
        diff = {k: (ia.get(k), ib.get(k)) for k in set(ia) | set(ib) if ia.get(k) != ib.get(k)}
        sys.exit("RUN FAILED: calibration %s asks a DIFFERENT question than %s: %r" % (mine, theirs, diff))
    cal_report.append({
        "calibrationCaptureId": mine,
        "reproducedCommittedCaptureId": theirs,
        "reproducedFrom": ref3g,
        "reproducedFromSha256": ref3g_sha,
        "mathContextPrecision": here[mine]['inputs']['mathContextPrecision'],
        "inputsIdentical": True,
        "inputDiffCount": 0,
        "observedIdentical": True,
        "observedCanonicalSha256": hashlib.sha256(a.encode('utf-8')).hexdigest(),
    })

att = doc.get('attestation')
if not att:
    sys.exit("RUN FAILED: no attestation block in the capture")
mh = att['moneyHelper']
if not (mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingModeOrdinal'] == 4
        and mh['effectiveRoundingMode'] == 'HALF_UP' and mh['matchesRatifiedProductionSetting'] is True):
    sys.exit("RUN FAILED: effective MathContext is %r, not the ratified production (19, HALF_UP ordinal 4)." % (mh,))
if att['fineract']['gitCommitId'] != commit:
    sys.exit("RUN FAILED: the image was built from Fineract %s but the pinned checkout is %s"
             % (att['fineract']['gitCommitId'], commit))
if att['fineract']['gitDirty'] != 'false':
    sys.exit("RUN FAILED: the image was built from a DIRTY Fineract tree (git.dirty=%s)" % att['fineract']['gitDirty'])
rs = att['runnerSupplied']
if rs['dockerImageId'] != image_id or rs['pinnedFineractCommit'] != commit:
    sys.exit("RUN FAILED: runner-supplied attestation echo does not match what the runner measured")
srcs = {s['file']: s['sha256'] for s in att['sources']}
if srcs.get('/cap/src/CaptureT83.java') != harness_sha:
    sys.exit("RUN FAILED: harness sha mismatch host %s vs container %s" % (harness_sha, srcs.get('/cap/src/CaptureT83.java')))
if srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java') != seam_sha:
    sys.exit("RUN FAILED: seam sha mismatch host %s vs container %s"
             % (seam_sha, srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java')))

# A digest that IS stable across runs: the captures array only, canonicalised.
canon = json.dumps(caps, sort_keys=True, separators=(',', ':')).encode('utf-8')
captures_digest = hashlib.sha256(canon).hexdigest()

logtext = open(logp, encoding='utf-8').read()
moneylines = [l for l in logtext.splitlines() if 'MoneyHelper' in l]

sidecar = {
    "artifact": "Path A capture T83 (gate G-8 boundary sweep)",
    "capturePath": att['capturePath'],
    "producedBy": ".softhouse/capture/t83-nonamortizing/src/run-t83.sh",
    "runId": run_id,
    "capturedAtUtc": att['capturedAtUtc'],
    "files": {p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
              for p in (jsonp, logp, errp, cpd, rawp) if os.path.isfile(p)},
    "filesNote": "sha256 of every output of this run except this sidecar itself. The capture JSON's "
                 "digest moves between runs because the attestation carries a UTC timestamp; use "
                 "capturesCanonicalSha256 to check a re-run.",
    "capturesCanonicalSha256": captures_digest,
    "captureCount": len(caps),
    "calibrations": cal_report,
    "calibrationNote": "Both calibrations reproduce an ALREADY-PROMOTED parity vector cell for cell "
                       "with zero input differences, tenant id included. An uncalibrated probe "
                       "measuring a novel region is a rig bug indistinguishable from a finding.",
    "sweepCaptureIds": [c['id'] for c in caps if c['id'].startswith('T83-SW-')],
    "neverPromotableCaptureIds": sorted(CALIBRATIONS),
    "classificationNote": "This capture classifies NOTHING. Whether a case amortizes to zero is "
                          "decided afterwards by classify-boundary.py reading only these rows.",
    "oracleLogMoneyHelperLines": moneylines,
    "roundingModeAttestation": {
        "threadedMathContextPerCase": "inputs.mathContextPrecision / mathContextRoundingModeOrdinal",
        "ambientMoneyHelperPerCase": "inputs.ambientMoneyHelper*",
        "allCasesAtProductionSetting": True,
    },
}
with open(attp, 'w', encoding='utf-8') as f:
    json.dump(sidecar, f, indent=1, sort_keys=True)
    f.write("\n")

print("capture OK: %d cases, canonical sha256 %s" % (len(caps), captures_digest))
for c in cal_report:
    print("  calibration %s reproduces %s cell-for-cell, 0 input diffs" % (c['calibrationCaptureId'], c['reproducedCommittedCaptureId']))
PY

printf 'wrote:\n  %s\n  %s\n  %s\n  %s\n  %s\n' "$JSON" "$ATT" "$LOG" "$ERR" "$CPD"
