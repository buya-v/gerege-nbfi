#!/bin/sh
# ---------------------------------------------------------------------------------------------
# Path A capture recipe, PASS 3g — EXECUTABLE, and it FAILS THE RUN on any precondition breach.
# T21 audit `.softhouse/reviews/T21-capture-pass3-audit.md` §10 P0-4.
#
# PASS 3g IS PASS 3d's RIG WITH A NEW CASE LIST, closing T11's finding C-1 (P1). Task T39 captured
# sixteen schedules two fires ago through a DIFFERENT Path A harness (CapturePeriodRatio.java) and
# they were never promoted: eight periodRatio DRIFT shapes, four MONTH-END shapes and three
# on-lattice controls.
#
# T39's harness records FOUR fields on a DISBURSEMENT row — {type, fromDate, dueDate, principal} —
# and NOT that row's outstanding balance. A vector transcribed from it must withdraw that cell as
# unrecorded, and the harness's own self-test replay then answers 0 for it and the
# balance_roll_forward invariant reads the placeholder as a violation. That is a harness defect
# (finding T58-N2, a D-5-class defect one layer down), and the way to promote these shapes WITHOUT
# depending on its resolution and WITHOUT exempting an invariant is to RE-OBSERVE them through the
# pass-3b/3c/3d rig, which records outstandingLoanBalance on the disbursement row.
#
# These are the SAME REQUESTS T39 asked, field for field, so the observations are also an
# independent CROSS-HARNESS REPRODUCTION of a two-fire-old capture. This script does not perform
# that comparison; the promotion audit does, cell for cell.
#
# EVERY precondition check of pass 3d is preserved below, all twelve of them, and NOT ONE was
# weakened to get a capture out. All three rig calibrations are carried over unchanged.
#
# Run from the repo root:
#
#     sh .softhouse/capture/src/run-pass3g.sh
#
# It compiles Capture3g.java and the seam class against the pinned reference-oracle (Fineract) image
# and runs the embeddable progressive-loan schedule generator IN-PROCESS. It does NOT start the
# Fineract server and it opens NO database connection. (PostgreSQL remains the only permitted engine
# for this program; this seam simply reaches no database at all.)
#
# WHAT MAKES IT FAIL — every one of these exits non-zero and refuses to leave a capture behind that a
# later reader could mistake for a good one:
#
#   1. docker missing, or the image absent
#   2. image id != the pinned digest
#   3. pinned Fineract checkout missing, at the wrong commit, or with a dirty working tree
#   4. the committed seam class differs from the pinned original by even one byte
#   5. the container exits non-zero
#   6. stdout carries no JSON document, or the JSON does not parse
#   7. stderr is non-empty (a stack trace where a capture was expected)
#   8. any capture has "observed": null, or an "error" key, or the wrong count
#   9. the effective MathContext is not the ratified production (19, HALF_UP) / RoundingMode ordinal 4
#  10. NEW — either RIG CALIBRATION fails to reproduce the committed pass-3b observation of the same
#      id, cell for cell. P-CAL repeats pass 3b's P-CAL at (12, HALF_UP); P-CAL-P00 repeats pass 3b's
#      P-00 at the PRODUCTION (19, HALF_UP), i.e. at the precision the parity candidates run at.
#      A rig that cannot reproduce an already-known value is not trustworthy, and nothing else from
#      a run whose calibration drifted may be believed.
#  11. the committed pass-3b artefact this run calibrates against is itself missing or does
#      not match the sha256 recorded by the promotion of the eleven existing parity vectors.
#  12. NEW — the committed pass-3c artefact is missing or does not match its recorded sha256, or
#      the third calibration P-CAL-EMI6 fails to reproduce pass 3c's P-EMI-6-1M014632 cell for
#      cell. That case's observation is ALREADY a promoted parity vector, so a drift here would
#      mean the corpus and this run disagree about the same request.
#
# DEFECT CLASS DELIBERATELY AVOIDED (T22 P0-5, found on the Path B side): a shell glob in an output
# path cannot expand against a file that does not exist yet, so `-o out/X-*.json` makes the tool
# create a file named literally `X-*.json`. EVERY output path below is a literal filename. There is
# no `*`, no `?` and no unquoted expansion in any redirect target in this script.
# ---------------------------------------------------------------------------------------------
set -eu

# --- pinned facts. Changing one of these is a deliberate act, not a convenience. ----------------
EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="${PINNED_FINERACT:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

# The committed pass-3b artefact this pass CALIBRATES AGAINST. Its sha256 is the one recorded in the
# provenance block of all eleven already-promoted parity vectors, so calibrating against it
# calibrates against exactly the bytes the existing corpus was transcribed from.
REF3B_JSON="${REF3B_JSON:-.softhouse/capture/out/capture-prod3b-raw.json}"
EXPECTED_REF3B_SHA="8d23c48fa13c04677b51bacdf07d101d6a061c79815d76b4983eccdbac945c79"

# The committed pass-3c artefact the THIRD calibration checks against. Its sha256 is the one
# recorded in the provenance block of the two P-EMI parity vectors task T57 promoted, so
# calibrating against it calibrates against exactly the bytes an existing parity vector was
# transcribed from — in MNT, at production precision.
REF3C_JSON="${REF3C_JSON:-.softhouse/capture/out/capture-prod3c-raw.json}"
# The FOURTH calibration reference, added by pass 3g: pass 3e's own committed artefact, from
# which the eight P-DRIFT, four P-ME and two P-LAT parity vectors were transcribed.
REF3E_JSON="${REF3E_JSON:-.softhouse/capture/out/capture-prod3e-raw.json}"
EXPECTED_REF3C_SHA="cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec"
EXPECTED_REF3E_SHA="8822699cc4505236c12ddd1f8156b273e0a88eaffb1ef73f73f409fc05104fc0"

CAP_DIR=".softhouse/capture"
OUT_DIR="${CAP_OUT_DIR:-$CAP_DIR/out}"
RAW="$OUT_DIR/capture-prod3g-raw.txt"
JSON="$OUT_DIR/capture-prod3g-raw.json"
LOG="$OUT_DIR/capture-prod3g-log.txt"
ERR="$OUT_DIR/capture-prod3g-stderr.txt"
ATT="$OUT_DIR/capture-prod3g-attestation.json"
CPD="$OUT_DIR/capture-prod3g-classpath-sha256.txt"
SUMS="$OUT_DIR/capture-prod3g-sha256.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

# --- 0. we must be at the repo root -------------------------------------------------------------
[ -f "$CAP_DIR/src/Capture3g.java" ] || fail "run me from the repo root; $CAP_DIR/src/Capture3g.java not found from $(pwd)"
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
HARNESS_SHA=$(shasum -a 256 "$CAP_DIR/src/Capture3g.java" | cut -d' ' -f1)

# --- 11. the calibration reference must be present and be the bytes the corpus was built from ------
[ -f "$REF3B_JSON" ] || fail "calibration reference $REF3B_JSON not found; pass 3g cannot prove the rig reproduces an already-known value"
ACTUAL_REF3B_SHA=$(shasum -a 256 "$REF3B_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3B_SHA" = "$EXPECTED_REF3B_SHA" ] \
  || fail "calibration reference $REF3B_JSON is sha256 $ACTUAL_REF3B_SHA, expected $EXPECTED_REF3B_SHA — these are not the bytes the eleven promoted parity vectors were transcribed from"

# --- 12. the pass-3c calibration reference, same rule ---------------------------------------------
[ -f "$REF3C_JSON" ] || fail "calibration reference $REF3C_JSON not found; pass 3g cannot prove the rig reproduces an already-known MNT value at production precision"
ACTUAL_REF3C_SHA=$(shasum -a 256 "$REF3C_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3C_SHA" = "$EXPECTED_REF3C_SHA" ] \
  || fail "calibration reference $REF3C_JSON is sha256 $ACTUAL_REF3C_SHA, expected $EXPECTED_REF3C_SHA — these are not the bytes the two P-EMI parity vectors were transcribed from"

[ -f "$REF3E_JSON" ] || fail "calibration reference $REF3E_JSON not found; pass 3g cannot prove the rig reproduces the on-lattice MNT control its candidates differ from only in principal"
ACTUAL_REF3E_SHA=$(shasum -a 256 "$REF3E_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3E_SHA" = "$EXPECTED_REF3E_SHA" ] \
  || fail "calibration reference $REF3E_JSON is sha256 $ACTUAL_REF3E_SHA, expected $EXPECTED_REF3E_SHA — these are not the bytes the sixteen pass-3e parity vectors were transcribed from"

RUN_ID="pass3g-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image      %s\n  fineract   %s (clean)\n  seam sha   %s\n  harness    %s\n  cal ref    %s (%s)\n  run id     %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$HARNESS_SHA" "$REF3B_JSON" "$ACTUAL_REF3B_SHA" "$RUN_ID"

# --- 5. the run. Literal output paths only. -------------------------------------------------------
set +e
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" \
  -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" \
  -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" \
  -e ATTEST_SOURCES="/cap/src/Capture3g.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java" \
  -e ATTEST_CLASSPATH_OUT="/cap/out/capture-prod3g-classpath-sha256.txt" \
  -v "$PWD/$CAP_DIR:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/Capture3g.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" Capture3g
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

# --- 8/9. structural + settings validation, and the attestation sidecar ---------------------------
python3 - "$JSON" "$ATT" "$LOG" "$ACTUAL_IMAGE_ID" "$EXPECTED_IMAGE_REF" "$ACTUAL_COMMIT" "$PINNED_FINERACT" \
        "$SEAM_SHA" "$HARNESS_SHA" "$RUN_ID" "$CPD" "$ERR" "$RAW" "$REF3B_JSON" "$ACTUAL_REF3B_SHA" \
        "$REF3C_JSON" "$ACTUAL_REF3C_SHA" "$REF3E_JSON" "$ACTUAL_REF3E_SHA" <<'PY'
import hashlib, json, os, sys

(jsonp, attp, logp, image_id, image_ref, commit, pinned, seam_sha, harness_sha, run_id, cpd, errp,
 rawp, ref3b, ref3b_sha, ref3c, ref3c_sha, ref3e, ref3e_sha) = sys.argv[1:20]

raw = open(jsonp, 'rb').read()
try:
    doc = json.loads(raw.decode('utf-8'))
except Exception as e:
    sys.exit("RUN FAILED: capture JSON does not parse: %s" % e)

caps = doc.get('captures')
EXPECTED_IDS = ['P-CAL', 'P-CAL-P00', 'P-CAL-EMI6', 'P-CAL-LATQ0a', 'P-CAL-MNT50M',
                'P-CAL-DRIFTF',
                'T64-ZP-A', 'T64-ZP-B', 'T64-ZP-C', 'T64-ZP-D']
if not isinstance(caps, list) or len(caps) != len(EXPECTED_IDS):
    sys.exit("RUN FAILED: expected %d captures, got %r"
             % (len(EXPECTED_IDS), len(caps) if isinstance(caps, list) else caps))
if [c.get('id') for c in caps] != EXPECTED_IDS:
    sys.exit("RUN FAILED: capture ids are %r, expected %r" % ([c.get('id') for c in caps], EXPECTED_IDS))

# The two RIG CALIBRATIONS and the pass-3b case each reproduces. P-CAL runs at the shipped test's
# (12, HALF_UP); P-CAL-P00 runs at the PRODUCTION (19, HALF_UP), the precision the parity
# candidates run at, so the calibration covers the arithmetic the promotion will actually rest on.
# calibration case id -> (reference artefact, its sha256, the committed case id it must reproduce)
CALIBRATIONS = {
    'P-CAL':        (ref3b, ref3b_sha, 'P-CAL'),
    'P-CAL-P00':    (ref3b, ref3b_sha, 'P-00'),
    'P-CAL-EMI6':   (ref3c, ref3c_sha, 'P-EMI-6-1M014632'),
    'P-CAL-LATQ0a': (ref3e, ref3e_sha, 'P-LAT-Q0a'),
    # ADDED BY PASS 3g. The two axes this pass extends: the LONGEST TERM in the promoted corpus
    # (n=36) and the SMALLEST PRINCIPAL in it (MNT 1.00). A rig that reproduces both is calibrated
    # at the far end of both axes rather than merely somewhere nearby.
    'P-CAL-MNT50M': (ref3b, ref3b_sha, 'P-MNT-50M'),
    'P-CAL-DRIFTF': (ref3e, ref3e_sha, 'P-DRIFT-F'),
}
CAL_PRECISION = {'P-CAL': 12, 'P-CAL-P00': 19, 'P-CAL-EMI6': 19, 'P-CAL-LATQ0a': 19,
                 'P-CAL-MNT50M': 19, 'P-CAL-DRIFTF': 19}

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
    want = CAL_PRECISION.get(c.get('id'), 19)
    if i.get('mathContextPrecision') != want:
        bad.append("%s: must run at precision %s, got %s"
                   % (c.get('id'), want, i.get('mathContextPrecision')))
if bad:
    sys.exit("RUN FAILED: capture validation:\n  " + "\n  ".join(bad))

# --- 10. RIG CALIBRATION: reproduce values ALREADY OBSERVED in the committed corpus --------------
# Not a resemblance check and not a tolerance: the whole `observed` block of each calibration case,
# every cell, must equal the committed pass-3b observation of the case it repeats. If it does not,
# nothing else from this run is trustworthy and the run is refused outright.
_ref_cache = {}
def ref_cases_of(path, want_sha):
    if path not in _ref_cache:
        ref_raw = open(path, 'rb').read()
        if hashlib.sha256(ref_raw).hexdigest() != want_sha:
            sys.exit("RUN FAILED: calibration reference %s changed under the run" % path)
        _ref_cache[path] = {c['id']: c for c in json.loads(ref_raw.decode('utf-8'))['captures']}
    return _ref_cache[path]

here = {c['id']: c for c in caps}
cal_report = []
for mine in sorted(CALIBRATIONS):
    refpath, refsha, theirs = CALIBRATIONS[mine]
    ref_cases = ref_cases_of(refpath, refsha)
    if theirs not in ref_cases:
        sys.exit("RUN FAILED: calibration target %s is absent from %s" % (theirs, refpath))
    a = json.dumps(here[mine]['observed'], sort_keys=True, separators=(',', ':'))
    b = json.dumps(ref_cases[theirs]['observed'], sort_keys=True, separators=(',', ':'))
    if a != b:
        sys.exit("RUN FAILED: CALIBRATION DRIFT. %s does not reproduce %s of %s.\n"
                 "  this run: %s\n  committed: %s\n"
                 "A rig that cannot reproduce an already-known value is not trustworthy; NOTHING "
                 "else from this run may be believed." % (mine, theirs, refpath, a, b))
    # inputs are asserted identical too, tenant id included, so the reproduction is of the SAME
    # question and not merely of a similar one. Only the case id and purpose text may differ.
    ia = {k: v for k, v in here[mine]['inputs'].items()}
    ib = {k: v for k, v in ref_cases[theirs]['inputs'].items()}
    if ia != ib:
        diff = {k: (ia.get(k), ib.get(k)) for k in set(ia) | set(ib) if ia.get(k) != ib.get(k)}
        sys.exit("RUN FAILED: calibration %s asks a DIFFERENT question than %s: %r" % (mine, theirs, diff))
    cal_report.append({
        "calibrationCaptureId": mine,
        "reproducedCommittedCaptureId": theirs,
        "reproducedFrom": refpath,
        "reproducedFromSha256": refsha,
        "mathContextPrecision": here[mine]['inputs']['mathContextPrecision'],
        "inputsIdentical": True,
        "observedIdentical": True,
        "observedCanonicalSha256": hashlib.sha256(a.encode('utf-8')).hexdigest(),
    })

att = doc.get('attestation')
if not att:
    sys.exit("RUN FAILED: no attestation block in the capture")
mh = att['moneyHelper']
if not (mh['effectiveMathContextPrecision'] == 19 and mh['effectiveRoundingModeOrdinal'] == 4
        and mh['effectiveRoundingMode'] == 'HALF_UP' and mh['matchesRatifiedProductionSetting'] is True):
    sys.exit("RUN FAILED: effective MathContext is %r, not the ratified production (19, HALF_UP ordinal 4). "
             "The artefact is retained for inspection but MUST NOT be recorded as a production-settings capture."
             % (mh,))
if att['fineract']['gitCommitId'] != commit:
    sys.exit("RUN FAILED: the image was built from Fineract %s but the pinned checkout is %s"
             % (att['fineract']['gitCommitId'], commit))
if att['fineract']['gitDirty'] != 'false':
    sys.exit("RUN FAILED: the image was built from a DIRTY Fineract tree (git.dirty=%s)" % att['fineract']['gitDirty'])
rs = att['runnerSupplied']
if rs['dockerImageId'] != image_id or rs['pinnedFineractCommit'] != commit:
    sys.exit("RUN FAILED: runner-supplied attestation echo does not match what the runner measured")
srcs = {s['file']: s['sha256'] for s in att['sources']}
if srcs.get('/cap/src/Capture3g.java') != harness_sha:
    sys.exit("RUN FAILED: harness sha mismatch host %s vs container %s" % (harness_sha, srcs.get('/cap/src/Capture3g.java')))
if srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java') != seam_sha:
    sys.exit("RUN FAILED: seam sha mismatch host %s vs container %s" % (seam_sha, srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java')))

# A digest that IS stable across runs: the captures array only, canonicalised. The whole-file digest
# moves every run because the attestation carries a timestamp, so it cannot be the reproduction check.
canon = json.dumps(caps, sort_keys=True, separators=(',', ':')).encode('utf-8')
captures_digest = hashlib.sha256(canon).hexdigest()

logtext = open(logp, encoding='utf-8').read()
moneylines = [l for l in logtext.splitlines() if 'MoneyHelper' in l]

sidecar = {
    "artifact": "Path A capture pass 3g",
    "capturePath": att['capturePath'],
    "producedBy": ".softhouse/capture/src/run-pass3g.sh",
    "runId": run_id,
    "capturedAtUtc": att['capturedAtUtc'],
    "files": {p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
              for p in (jsonp, logp, errp, cpd, rawp) if os.path.isfile(p)},
    "filesNote": "sha256 of every output of this run except this sidecar itself. The capture JSON's "
                 "digest moves between runs because the attestation carries a UTC timestamp; use "
                 "capturesCanonicalSha256 to check a re-run.",
    "capturesCanonicalSha256": captures_digest,
    "capturesCanonicalSha256Definition":
        "sha256 of json.dumps(doc['captures'], sort_keys=True, separators=(',',':')).encode('utf-8') — "
        "stable across runs; the whole-file sha256 is NOT, because the attestation carries a UTC timestamp",
    "measuredByRunnerOnHost": {
        "dockerImageRef": image_ref,
        "dockerImageId": image_id,
        "pinnedFineractPath": pinned,
        "pinnedFineractCommit": commit,
        "pinnedFineractTreeClean": True,
        "seamClassSha256": seam_sha,
        "seamClassByteIdenticalToPinnedOriginal": True,
        "harnessSha256": harness_sha,
    },
    "measuredInsideContainer": att,
    "oracleOwnMoneyHelperLogLines": moneylines,
    "captureCount": len(caps),
    "captureIds": [c['id'] for c in caps],
    "productionSettingsCaptureIds": [c['id'] for c in caps if c['inputs']['mathContextPrecision'] == 19],
    "calibrationCaptureIds": [c['id'] for c in caps if c['inputs']['mathContextPrecision'] != 19],
    "calibrationCaptureIdsNote":
        "SAME DEFINITION AS PASS 3b AND 3c: keyed on MathContext precision != 19, so it lists the "
        "precision-12 calibration ONLY. Pass 3g also carries TWO calibrations AT the production "
        "precision (P-CAL-P00 and P-CAL-EMI6), which therefore appear under "
        "productionSettingsCaptureIds; calibrationRoleCaptureIds below lists calibrations BY ROLE, "
        "and parityCandidateCaptureIds lists what this pass actually offers for promotion.",
    "calibrationRoleCaptureIds": sorted(CALIBRATIONS),
    "parityCandidateCaptureIds": [c['id'] for c in caps if c['id'] not in CALIBRATIONS],
    "calibrationReport": cal_report,
    "admissibilityNote":
        "RAW OBSERVED. Attestation is present, but presence of an attestation does not promote anything. "
        "Promotion to the parity vector store is a separate, gated decision (DEC-1 is UNRATIFIED, gate G-1).",
}
open(attp, 'w', encoding='utf-8').write(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n")
print("validation OK — %d captures, attestation present, effective MathContext (19, HALF_UP ordinal 4)" % len(caps))
for r in cal_report:
    print("calibration OK — %s reproduced committed %s (%s) at precision %s, inputs and observed both identical"
          % (r['calibrationCaptureId'], r['reproducedCommittedCaptureId'], r['reproducedFrom'],
             r['mathContextPrecision']))
print("captures canonical sha256: %s" % captures_digest)
PY

# --- sha256 of every output, literal filenames, no globs -------------------------------------------
: > "$SUMS"
for f in "$JSON" "$LOG" "$ERR" "$ATT" "$CPD" "$RAW"; do
  [ -f "$f" ] && shasum -a 256 "$f" >> "$SUMS"
done
printf '\nsha256 of every output (also written to %s):\n' "$SUMS"
cat "$SUMS"
printf '\nDONE. Nothing here is promoted to the parity vector store; that is a separate gated decision.\n'
