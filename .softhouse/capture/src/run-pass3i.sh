#!/bin/sh
# ---------------------------------------------------------------------------------------------
# Path A capture recipe, PASS 3i — EXECUTABLE, and it FAILS THE RUN on any precondition breach.
# This script is the closure of T21 audit `.softhouse/reviews/T21-capture-pass3-audit.md` §10 P0-4
# for the Path A seam: the seam byte-identity check below is a PRECONDITION STEP THAT EXITS
# NON-ZERO, not a prose instruction, and the log/JSON split is built in.
#
# PASS 3i IS PASS 3h's RIG WITH ONE STRUCTURAL FIX AND A NEW CASE LIST — task T74.
#
# THE FIX. T21 required change P1-8 (which is T19 required change 10, unfixed since pass 2): every
# harness from Capture3.java to Capture3h.java spent ONE field, `installmentMultiplesOf`, on THREE
# things — the 4th argument of `new CurrencyData(...)`, which is `CurrencyData.inMultiplesOf`; the
# 12th argument of `LoanRepaymentScheduleModelData`, which is `installmentAmountInMultiplesOf`; and
# BOTH emitted JSON keys. Two unrelated rounding mechanisms shared one slot, so no capture taken
# through those harnesses could attribute an observed difference to either of them. Capture3i.java
# gives them separate components, separate constructor arguments and separate emitted keys.
#
# WHY IT MATTERS. T21's auditor OBSERVED, through this same seam at (19, HALF_UP), that
# MNT 5,000,000 / 18 x 18.5% with currencyDecimalPlaces = 0 emits total interest 763994 at
# CurrencyData.inMultiplesOf = null and 764100 at 100, all eighteen periods differing. That is
# money moving on an input the corpus does not grade and the harness could not name.
#
# THE TWO MECHANISMS, from the pinned source:
#   channel 1  Money.java:48-51, in the PRIVATE CONSTRUCTOR, gated on the CURRENCY having zero
#              decimal places; rounds EVERY Money the calculation builds to the nearest multiple
#              under the TENANT rounding mode (:150-157); NO zero-guard.
#   channel 2  ProgressiveEMICalculator.java:1761-1776, gated on the SCHEDULE MODEL's
#              installmentAmountInMultiplesOf; rounds the EQUAL MONTHLY INSTALLMENT ONLY
#              (Money.java:159-170); HAS a zero-guard — a rounding that would zero a positive EMI
#              is discarded and the unrounded EMI kept (:1772-1774).
#
# THE CASE LIST. Nine RIG CALIBRATIONS (all eight of pass 3h's carried over unchanged, plus
# P-CAL-MNT5M reproducing pass 3b's P-MNT-5M). Then a 2x2 factorial over the two inputs at
# currencyDecimalPlaces 0 (group A) and the same at the production currencyDecimalPlaces 2
# (group B); five gate-and-rule probes for channel 1 (group C); a three-case zero-guard separator
# (group D); and the 36 x 16.8% small-principal shape T21 required change P1-11 asked for, each at
# production precision with a precision-12 companion (group E).
#
# EVERY precondition check of pass 3h is preserved below and NOT ONE was weakened to get a capture
# out. All eight of its rig calibrations are carried over unchanged; three checks are ADDED and one
# existing check is REPLACED BY A STRICTLY STRONGER FORM.
#
# Run from the repo root:
#
#     sh .softhouse/capture/src/run-pass3i.sh
#
# It compiles Capture3i.java and the seam class against the pinned reference-oracle (Fineract) image
# and runs the embeddable progressive-loan schedule generator IN-PROCESS. It does NOT start the
# Fineract server and it opens NO database connection. (PostgreSQL remains the only permitted engine
# for this program; this seam simply reaches no database at all.) It writes NOTHING to the running
# reference-oracle container, its PostgreSQL database, its `c_configuration` or any tenant.
#
# WHAT MAKES IT FAIL — every one of these exits non-zero and refuses to leave a capture behind that a
# later reader could mistake for a good one:
#
#   1. docker missing, or the image absent
#   2. image id != the pinned digest
#   3. pinned Fineract checkout missing, at the wrong commit, or with a dirty working tree
#   4. the committed seam class differs from the pinned original by even one byte
#   4b. ADDED BY PASS 3i — the committed seam class does not have the sha256 PINNED AS A LITERAL IN
#       THIS SCRIPT. Check 4 compares two files, and both of its operands are reachable by a caller:
#       the local copy is in the repo and the pinned copy is under $PINNED_FINERACT, which is an
#       environment variable. Two mutated-in-the-same-way files compare EQUAL. A literal digest has
#       no such operand, so a mutated seam fails here even if every other file agrees with it.
#   5. the container exits non-zero
#   6. stdout carries no JSON document, or the JSON does not parse
#   7. stderr is non-empty (a stack trace where a capture was expected)
#   8. any capture has "observed": null, or an "error" key, or the wrong count, or the wrong ids
#   9. the effective MathContext rounding mode is not the ratified HALF_UP / RoundingMode ordinal 4,
#      or the ambient MoneyHelper precision is not 19, on ANY case
#  10. any RIG CALIBRATION fails to reproduce the committed observation of the case it repeats, cell
#      for cell, inputs included and tenant id included
#  11-13. any calibration reference artefact missing or at the wrong sha256 (pass 3b, 3c, 3e, 3g)
#  14. PATH IDENTITY — any case whose instrumented plan differs from the pristine seam's plan
#  15. any case with "mechanism": null, "modelCaptured": false, or an empty mechanism period list
#  16. ADDED BY PASS 3i — FIELD SEPARATION. The emitted `currencyInMultiplesOf` and
#      `installmentAmountInMultiplesOf` must match an EXPECTED PER-ID TABLE, and the run is refused
#      unless the capture contains at least one case with (currency set, installment null) AND at
#      least one with (currency null, installment set). If a later edit re-aliases the two fields —
#      the exact defect this pass exists to fix — those two cases collapse onto one another and this
#      check goes red. A guard that cannot go red is decoration (pattern P-15), so this one is
#      written to be falsified by the very regression it guards.
#  17. ADDED BY PASS 3i, REPLACING A WEAKER CHECK — MathContext precision is validated against a
#      HAND-WRITTEN per-id table, and an id absent from that table FAILS THE RUN, as does a table
#      entry this run does not capture. Pass 3h used `CAL_PRECISION.get(id, 19)`, which silently
#      accepted 19 for any id nobody had registered. Pass 3i carries deliberate precision-12
#      companions, so a defaulted lookup would have let a probe be mistaken for a parity candidate.
#      CORRECTED BY T82: pass 3i's first form BUILT the table from EXPECTED_IDS by id suffix, which
#      is the same default one layer down and left the "unregistered id" exit unreachable. The table
#      is now literal, so the exit is reachable and has been DEMONSTRATED red — see
#      `.softhouse/capture/t74-multiplesof/T82-guard-proofs/`.
#  18. ADDED BY PASS 3i — every case whose id ends in `-p12` must actually run below precision 19,
#      and every case actually running below precision 19 must be named `-p12`; the sidecar records
#      those as DISCRIMINATION PROBES, separately from parityCandidateCaptureIds. CORRECTED BY T82
#      (T75 defect N4/E-2): two further checks here intersected `probe_ids` with `parity_ids`, which
#      is DEFINED as the complement of `probe_ids` — empty by construction, dead by structure. They
#      are removed; the falsifiable half is kept and demonstrated red.
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

# ADDED BY PASS 3i — precondition 4b. The sha256 of the seam source at the pinned Fineract commit
# 426a23544e8426a38ae43ae404670a0a7e85b9eb, recorded independently by T18, T21, T21-v2 and every
# pass from 3b to 3h. Check 4 (`cmp`) has TWO operands and a caller controls both — the local copy
# through the repo and the pinned copy through $PINNED_FINERACT — so two files mutated the same way
# compare equal and the run proceeds on code that is not the oracle's. A literal digest has no such
# operand. This is the check a reviewer trying to make a mutated seam pass has to defeat, and it
# cannot be defeated by editing a file.
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"

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
# The FOURTH calibration reference, added by pass 3h: pass 3e's own committed artefact, from
# which the eight P-DRIFT, four P-ME and two P-LAT parity vectors were transcribed.
REF3E_JSON="${REF3E_JSON:-.softhouse/capture/out/capture-prod3e-raw.json}"
EXPECTED_REF3C_SHA="cae566d3ba99c69704fdb5dca21e247b3ec7d20c2e5ccc4e50b97721e8c92dec"
EXPECTED_REF3E_SHA="8822699cc4505236c12ddd1f8156b273e0a88eaffb1ef73f73f409fc05104fc0"
# The FIFTH calibration reference, added by pass 3h: pass 3g's own committed artefact, from which
# the four T64-ZP parity vectors were transcribed. T64-ZP-B is the ONLY shape in the whole
# committed corpus whose schedule carries a ZERO-EMI TAIL, and that is precisely the precondition
# half this pass exists to interrogate — so the rig is calibrated ON the shape under study.
REF3G_JSON="${REF3G_JSON:-.softhouse/capture/out/capture-prod3g-raw.json}"
EXPECTED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"

CAP_DIR=".softhouse/capture"
OUT_DIR="${CAP_OUT_DIR:-$CAP_DIR/out}"
RAW="$OUT_DIR/capture-prod3i-raw.txt"
JSON="$OUT_DIR/capture-prod3i-raw.json"
LOG="$OUT_DIR/capture-prod3i-log.txt"
ERR="$OUT_DIR/capture-prod3i-stderr.txt"
ATT="$OUT_DIR/capture-prod3i-attestation.json"
CPD="$OUT_DIR/capture-prod3i-classpath-sha256.txt"
SUMS="$OUT_DIR/capture-prod3i-sha256.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

# --- 0. we must be at the repo root -------------------------------------------------------------
[ -f "$CAP_DIR/src/Capture3i.java" ] || fail "run me from the repo root; $CAP_DIR/src/Capture3i.java not found from $(pwd)"
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
HARNESS_SHA=$(shasum -a 256 "$CAP_DIR/src/Capture3i.java" | cut -d' ' -f1)

# --- 4b. ADDED BY PASS 3i: the seam digest is PINNED AS A LITERAL, on BOTH copies. --------------
# Check 4 above proves the two files agree with each other. These two prove they agree with the
# oracle. Mutating the seam — in the repo, in the pinned checkout, or in both at once — fails here.
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] \
  || fail "seam class $SEAM_LOCAL is sha256 $SEAM_SHA, expected the pinned $EXPECTED_SEAM_SHA. The run would not be executing the reference oracle's code."
SEAM_PINNED_SHA=$(shasum -a 256 "$SEAM_PINNED" | cut -d' ' -f1)
[ "$SEAM_PINNED_SHA" = "$EXPECTED_SEAM_SHA" ] \
  || fail "pinned seam source $SEAM_PINNED is sha256 $SEAM_PINNED_SHA, expected $EXPECTED_SEAM_SHA"

# --- 11. the calibration reference must be present and be the bytes the corpus was built from ------
[ -f "$REF3B_JSON" ] || fail "calibration reference $REF3B_JSON not found; pass 3i cannot prove the rig reproduces an already-known value"
ACTUAL_REF3B_SHA=$(shasum -a 256 "$REF3B_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3B_SHA" = "$EXPECTED_REF3B_SHA" ] \
  || fail "calibration reference $REF3B_JSON is sha256 $ACTUAL_REF3B_SHA, expected $EXPECTED_REF3B_SHA — these are not the bytes the eleven promoted parity vectors were transcribed from"

# --- 12. the pass-3c calibration reference, same rule ---------------------------------------------
[ -f "$REF3C_JSON" ] || fail "calibration reference $REF3C_JSON not found; pass 3i cannot prove the rig reproduces an already-known MNT value at production precision"
ACTUAL_REF3C_SHA=$(shasum -a 256 "$REF3C_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3C_SHA" = "$EXPECTED_REF3C_SHA" ] \
  || fail "calibration reference $REF3C_JSON is sha256 $ACTUAL_REF3C_SHA, expected $EXPECTED_REF3C_SHA — these are not the bytes the two P-EMI parity vectors were transcribed from"

[ -f "$REF3E_JSON" ] || fail "calibration reference $REF3E_JSON not found; pass 3i cannot prove the rig reproduces the on-lattice MNT control its candidates differ from only in principal"
ACTUAL_REF3E_SHA=$(shasum -a 256 "$REF3E_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3E_SHA" = "$EXPECTED_REF3E_SHA" ] \
  || fail "calibration reference $REF3E_JSON is sha256 $ACTUAL_REF3E_SHA, expected $EXPECTED_REF3E_SHA — these are not the bytes the sixteen pass-3e parity vectors were transcribed from"

# --- 13. NEW IN PASS 3h: the pass-3g calibration reference, same rule. It carries T64-ZP-B, the
#         only committed shape with a ZERO-EMI TAIL, which is the precondition half under study.
[ -f "$REF3G_JSON" ] || fail "calibration reference $REF3G_JSON not found; pass 3i cannot prove the rig reproduces the ZERO-EMI-TAIL shape it exists to interrogate"
ACTUAL_REF3G_SHA=$(shasum -a 256 "$REF3G_JSON" | cut -d' ' -f1)
[ "$ACTUAL_REF3G_SHA" = "$EXPECTED_REF3G_SHA" ] \
  || fail "calibration reference $REF3G_JSON is sha256 $ACTUAL_REF3G_SHA, expected $EXPECTED_REF3G_SHA — these are not the bytes the four T64-ZP parity vectors were transcribed from"

RUN_ID="pass3i-$(date -u +%Y%m%dT%H%M%SZ)"
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
  -e ATTEST_SOURCES="/cap/src/Capture3i.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java" \
  -e ATTEST_CLASSPATH_OUT="/cap/out/capture-prod3i-classpath-sha256.txt" \
  -v "$PWD/$CAP_DIR:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/Capture3i.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" Capture3i
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
        "$REF3C_JSON" "$ACTUAL_REF3C_SHA" "$REF3E_JSON" "$ACTUAL_REF3E_SHA" \
        "$REF3G_JSON" "$ACTUAL_REF3G_SHA" <<'PY'
import hashlib, json, os, sys

(jsonp, attp, logp, image_id, image_ref, commit, pinned, seam_sha, harness_sha, run_id, cpd, errp,
 rawp, ref3b, ref3b_sha, ref3c, ref3c_sha, ref3e, ref3e_sha,
 ref3g, ref3g_sha) = sys.argv[1:22]

raw = open(jsonp, 'rb').read()
try:
    doc = json.loads(raw.decode('utf-8'))
except Exception as e:
    sys.exit("RUN FAILED: capture JSON does not parse: %s" % e)

caps = doc.get('captures')
EXPECTED_IDS = ['P-CAL', 'P-CAL-P00', 'P-CAL-EMI6', 'P-CAL-LATQ0a', 'P-CAL-MNT50M',
                'P-CAL-DRIFTF', 'P-CAL-ZPA', 'P-CAL-ZPB', 'P-CAL-MNT5M',
                'T74-A0-DP0-NONE', 'T74-A1-DP0-CUR100', 'T74-A2-DP0-INST100', 'T74-A3-DP0-BOTH100',
                'T74-B1-DP2-CUR100', 'T74-B2-DP2-INST100', 'T74-B3-DP2-BOTH100',
                'T74-C1-DP0-CUR1', 'T74-C2-DP0-CUR0', 'T74-C3-DP0-CURNEG', 'T74-C4-DP0-CUR7',
                'T74-C5-DP0-CUR1000',
                'T74-D0-DP0-SMALL-NONE', 'T74-D1-DP0-SMALL-CUR1000', 'T74-D2-DP0-SMALL-INST1000',
                'T74-E-P4', 'T74-E-P4-p12', 'T74-E-P59', 'T74-E-P59-p12',
                'T74-E-P72', 'T74-E-P72-p12', 'T74-E-P340', 'T74-E-P340-p12',
                'T74-E-P426', 'T74-E-P426-p12', 'T74-E-P6940', 'T74-E-P6940-p12']
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
    # ADDED BY PASS 3h. The two axes this pass extends: the LONGEST TERM in the promoted corpus
    # (n=36) and the SMALLEST PRINCIPAL in it (MNT 1.00). A rig that reproduces both is calibrated
    # at the far end of both axes rather than merely somewhere nearby.
    'P-CAL-MNT50M': (ref3b, ref3b_sha, 'P-MNT-50M'),
    'P-CAL-DRIFTF': (ref3e, ref3e_sha, 'P-DRIFT-F'),
    # ADDED BY PASS 3h. Both are already-promoted parity vectors; ZP-B is the ONLY committed
    # shape carrying a ZERO-EMI TAIL, the precondition half T63 could not test.
    'P-CAL-ZPA':    (ref3g, ref3g_sha, 'T64-ZP-A'),
    'P-CAL-ZPB':    (ref3g, ref3g_sha, 'T64-ZP-B'),
    # ADDED BY PASS 3i. P-MNT-5M is the dp = 2 / no-multiples-of control that the whole T74-A and
    # T74-B family is read against: same principal, same term, same rate, same dates, same currency
    # code, same MathContext, differing only in currencyDecimalPlaces and the two multiples-of
    # inputs. Its observation is already a promoted parity vector, so this calibrates the rig ON the
    # arithmetic the group A/B comparisons rest on rather than merely near it.
    'P-CAL-MNT5M':  (ref3b, ref3b_sha, 'P-MNT-5M'),
}

# --- 17. ADDED BY PASS 3i, REPLACING A WEAKER CHECK -----------------------------------------------
# Pass 3h wrote `CAL_PRECISION.get(id, 19)`: an id nobody had registered silently defaulted to the
# production precision and passed. Pass 3i deliberately carries precision-12 companions, so a
# defaulted lookup would let a discrimination probe be validated as though it were a parity
# candidate.
#
# CORRECTED BY T82 (T75 defect N4). The first pass-3i form of this check BUILT the table by looping
# over EXPECTED_IDS and filling every missing entry from the id's own suffix
# (`endswith('-p12') -> 12, else 19`). That is the SAME DEFAULT pass 3h had, merely keyed on a string
# suffix instead of on `.get`'s second argument — and it made `_unregistered` empty by construction,
# so the `sys.exit` below was UNREACHABLE while the header advertised it as the fix. A guard that
# cannot go red is decoration (pattern P-15), and a decoration that advertises itself as the cure for
# defaulting is worse than the defaulting.
#
# The table is therefore WRITTEN OUT, one line per case, as `FIELD_SEPARATION` below already is.
# There is no default and no derivation: an id present in EXPECTED_IDS but missing here FAILS THE
# RUN, and an id registered here that EXPECTED_IDS does not carry FAILS THE RUN TOO — a stale entry
# is how a table stops describing the run it is validating.
CASE_PRECISION = {
    # the nine rig calibrations. P-CAL reproduces the SHIPPED TEST's (12, HALF_UP); the other eight
    # reproduce committed parity observations and therefore run at the production 19.
    'P-CAL':                     12,
    'P-CAL-P00':                 19,
    'P-CAL-EMI6':                19,
    'P-CAL-LATQ0a':              19,
    'P-CAL-MNT50M':              19,
    'P-CAL-DRIFTF':              19,
    'P-CAL-ZPA':                 19,
    'P-CAL-ZPB':                 19,
    'P-CAL-MNT5M':               19,
    # groups A-D, the multiples-of factorials and probes: all at the production precision.
    'T74-A0-DP0-NONE':           19,
    'T74-A1-DP0-CUR100':         19,
    'T74-A2-DP0-INST100':        19,
    'T74-A3-DP0-BOTH100':        19,
    'T74-B1-DP2-CUR100':         19,
    'T74-B2-DP2-INST100':        19,
    'T74-B3-DP2-BOTH100':        19,
    'T74-C1-DP0-CUR1':           19,
    'T74-C2-DP0-CUR0':           19,
    'T74-C3-DP0-CURNEG':         19,
    'T74-C4-DP0-CUR7':           19,
    'T74-C5-DP0-CUR1000':        19,
    'T74-D0-DP0-SMALL-NONE':     19,
    'T74-D1-DP0-SMALL-CUR1000':  19,
    'T74-D2-DP0-SMALL-INST1000': 19,
    # group E: each parity candidate at the ratified 19, each with a DELIBERATE precision-12
    # companion. The pair is the counterfactual, so the 12 here is load-bearing, not incidental.
    'T74-E-P4':                  19,
    'T74-E-P4-p12':              12,
    'T74-E-P59':                 19,
    'T74-E-P59-p12':             12,
    'T74-E-P72':                 19,
    'T74-E-P72-p12':             12,
    'T74-E-P340':                19,
    'T74-E-P340-p12':            12,
    'T74-E-P426':                19,
    'T74-E-P426-p12':            12,
    'T74-E-P6940':               19,
    'T74-E-P6940-p12':           12,
}
_unregistered = [i for i in EXPECTED_IDS if i not in CASE_PRECISION]
if _unregistered:
    sys.exit("RUN FAILED: no expected MathContext precision registered for %r. Add the case to "
             "CASE_PRECISION by hand — there is deliberately no default, because a defaulted "
             "precision is how a discrimination probe gets validated as a parity candidate."
             % _unregistered)
_stale = [i for i in CASE_PRECISION if i not in EXPECTED_IDS]
if _stale:
    sys.exit("RUN FAILED: CASE_PRECISION registers %r, which this run does not capture. A table that "
             "outlives the cases it describes stops being a check." % sorted(_stale))

# --- 16. ADDED BY PASS 3i: FIELD SEPARATION -------------------------------------------------------
# The defect this pass exists to fix is that ONE harness field fed BOTH `CurrencyData.inMultiplesOf`
# and `installmentAmountInMultiplesOf` and BOTH emitted JSON keys. This table names, per case id, the
# exact pair the run must emit, together with the currency's decimal places, because at
# currencyDecimalPlaces != 0 the Money.java:48 gate is shut and a reader must be able to see which
# arm a case is on without re-deriving it. If a later edit re-aliases the two fields, every case in
# groups A2/B2/D2 emits the currency value in the installment slot (or vice versa) and this check
# goes red. Written this way ON PURPOSE: an assertion that cannot fail converts "not checked" into
# "checked and fine" (pattern P-15).
#                          id                       -> (decimalPlaces, currencyInMultiplesOf, installmentAmountInMultiplesOf)
FIELD_SEPARATION = {
    'T74-A0-DP0-NONE':           (0, None, None),
    'T74-A1-DP0-CUR100':         (0, 100,  None),
    'T74-A2-DP0-INST100':        (0, None, 100),
    'T74-A3-DP0-BOTH100':        (0, 100,  100),
    'T74-B1-DP2-CUR100':         (2, 100,  None),
    'T74-B2-DP2-INST100':        (2, None, 100),
    'T74-B3-DP2-BOTH100':        (2, 100,  100),
    'T74-C1-DP0-CUR1':           (0, 1,    None),
    'T74-C2-DP0-CUR0':           (0, 0,    None),
    'T74-C3-DP0-CURNEG':         (0, -100, None),
    'T74-C4-DP0-CUR7':           (0, 7,    None),
    'T74-C5-DP0-CUR1000':        (0, 1000, None),
    'T74-D0-DP0-SMALL-NONE':     (0, None, None),
    'T74-D1-DP0-SMALL-CUR1000':  (0, 1000, None),
    'T74-D2-DP0-SMALL-INST1000': (0, None, 1000),
}

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
    if c.get('id') not in CASE_PRECISION:
        bad.append("%s: no expected MathContext precision registered for this id" % c.get('id'))
    else:
        want = CASE_PRECISION[c.get('id')]
        if i.get('mathContextPrecision') != want:
            bad.append("%s: must run at precision %s, got %s"
                       % (c.get('id'), want, i.get('mathContextPrecision')))
    # --- 16. FIELD SEPARATION, per case ---
    if c.get('id') in FIELD_SEPARATION:
        want_dp, want_cur, want_inst = FIELD_SEPARATION[c.get('id')]
        got = (i.get('currencyDecimalPlaces'), i.get('currencyInMultiplesOf'),
               i.get('installmentAmountInMultiplesOf'))
        if got != (want_dp, want_cur, want_inst):
            bad.append("%s: emitted (decimalPlaces, currencyInMultiplesOf, "
                       "installmentAmountInMultiplesOf) = %r, expected %r"
                       % (c.get('id'), got, (want_dp, want_cur, want_inst)))
if bad:
    sys.exit("RUN FAILED: capture validation:\n  " + "\n  ".join(bad))

# --- 16b. THE TWO FIELDS MUST BE DEMONSTRABLY INDEPENDENT IN THE EMITTED JSON ---------------------
# Not "the table matched" — that could be satisfied by a table someone edited to fit an aliased
# harness. This asks the capture itself: does it contain a case where ONLY the currency field is set
# and another where ONLY the installment field is set? An aliased harness cannot produce both,
# because one field would be printed into both keys.
_cur_only = [c['id'] for c in caps
             if c['inputs'].get('currencyInMultiplesOf') is not None
             and c['inputs'].get('installmentAmountInMultiplesOf') is None]
_inst_only = [c['id'] for c in caps
              if c['inputs'].get('currencyInMultiplesOf') is None
              and c['inputs'].get('installmentAmountInMultiplesOf') is not None]
if not _cur_only or not _inst_only:
    sys.exit("RUN FAILED: FIELD SEPARATION. currencyInMultiplesOf and installmentAmountInMultiplesOf "
             "are not demonstrably independent in this capture: currency-only cases %r, "
             "installment-only cases %r. This is T21 required change P1-8 regressing — the two "
             "inputs reach two different mechanisms (Money.java:48-51 and "
             "ProgressiveEMICalculator.java:1761-1776) and a capture that cannot tell them apart "
             "cannot attribute a difference to either." % (_cur_only, _inst_only))

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

# --- 14/15. ADDED BY PASS 3h: PATH IDENTITY and mechanism presence -------------------------------
# Path identity is what licenses reading the mechanism columns as evidence about the seam. It is a
# whole-plan string comparison built by ONE renderer applied to BOTH plans, so it cannot pass by
# comparing a value with itself under two different formatters.
path_bad = []
mech_bad = []
mech_report = []
for c in caps:
    pid = c.get('pathIdentity')
    if not isinstance(pid, dict) or pid.get('identical') is not True:
        path_bad.append("%s: pathIdentity=%r" % (c.get('id'), pid))
    elif pid.get('seamPlan') != pid.get('instrumentedPlan'):
        path_bad.append("%s: pathIdentity claims identical but the two renderings differ" % c.get('id'))
    m = c.get('mechanism')
    if not isinstance(m, dict):
        mech_bad.append("%s: mechanism is %r" % (c.get('id'), m))
        continue
    if m.get('modelCaptured') is not True:
        mech_bad.append("%s: modelCaptured is not true" % c.get('id'))
        continue
    ps = m.get('periods')
    if not isinstance(ps, list) or not ps:
        mech_bad.append("%s: mechanism.periods is empty" % c.get('id'))
        continue
    for k in ('futureUnrecognizedInterest', 'interestMovedUpward', 'unrecognizedInterest',
              'calculatedDueInterest', 'dueInterest', 'emi', 'isFullyPaid'):
        if any(k not in row for row in ps):
            mech_bad.append("%s: mechanism rows are missing column %s" % (c.get('id'), k))
    # A summary, computed from what was printed. It ASSERTS NOTHING about what the value should be.
    fui_nonzero = [r['idx'] for r in ps if r.get('futureUnrecognizedInterest') not in ('0', '0.00', '0.0')]
    imu_true = [r['idx'] for r in ps if r.get('interestMovedUpward') is True]
    unrec_nonzero = [r['idx'] for r in ps if r.get('unrecognizedInterest') not in ('0', '0.00', '0.0')]
    zero_emi = [r['idx'] for r in ps if r.get('emi') in ('0', '0.00', '0.0')]
    fully_paid = [r['idx'] for r in ps if r.get('isFullyPaid') is True]
    mech_report.append({
        "id": c.get('id'),
        "periodCount": len(ps),
        "periodsWithNonZeroFutureUnrecognizedInterest": fui_nonzero,
        "periodsWithInterestMovedUpward": imu_true,
        "periodsWithNonZeroUnrecognizedInterest": unrec_nonzero,
        "zeroEmiPeriods": zero_emi,
        "vacuouslyFullyPaidPeriods": fully_paid,
        "lastNotFullyPaidPeriodIndex": (max([r['idx'] for r in ps if r.get('isFullyPaid') is not True])
                                        if any(r.get('isFullyPaid') is not True for r in ps) else None),
    })
if path_bad:
    sys.exit("RUN FAILED: PATH IDENTITY. The instrumented generator did not reproduce the pristine "
             "seam's plan:\n  " + "\n  ".join(path_bad))
if mech_bad:
    sys.exit("RUN FAILED: mechanism columns absent or incomplete:\n  " + "\n  ".join(mech_bad))

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
if srcs.get('/cap/src/Capture3i.java') != harness_sha:
    sys.exit("RUN FAILED: harness sha mismatch host %s vs container %s" % (harness_sha, srcs.get('/cap/src/Capture3i.java')))
if srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java') != seam_sha:
    sys.exit("RUN FAILED: seam sha mismatch host %s vs container %s" % (seam_sha, srcs.get('/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java')))

# A digest that IS stable across runs: the captures array only, canonicalised. The whole-file digest
# moves every run because the attestation carries a timestamp, so it cannot be the reproduction check.
canon = json.dumps(caps, sort_keys=True, separators=(',', ':')).encode('utf-8')
captures_digest = hashlib.sha256(canon).hexdigest()

# --- 18. ADDED BY PASS 3i: the precision-12 companions are classified as PROBES, in the artefact --
# A capture is read by people who did not run it. If the only place a `-p12` case is distinguishable
# from a parity candidate is its id, somebody will eventually promote one. So the classification is
# written into the sidecar, and the run FAILS if a probe would land in the parity list.
probe_ids = [c['id'] for c in caps if c['inputs']['mathContextPrecision'] != 19
             and c['id'] not in CALIBRATIONS]
parity_ids = [c['id'] for c in caps if c['id'] not in CALIBRATIONS and c['id'] not in probe_ids]

# CORRECTED BY T82 (T75 defect N4 / E-2). Two checks stood here and BOTH were structurally dead:
#
#     _misfiled = sorted(set(probe_ids) & set(parity_ids))            # -> always []
#     for _pid in probe_ids:
#         if _pid in parity_ids: ...                                  # -> never true
#
# `parity_ids` is DEFINED one line above as "not a calibration AND NOT IN probe_ids". Intersecting a
# set with its own complement is empty whatever the capture contains: no edit to the harness, to
# CASE_PRECISION, to EXPECTED_IDS or to the capture JSON can make either fire. They asserted a
# property of the two list comprehensions, not a property of the run — and a guard that cannot go red
# converts "not checked" into "checked and fine" (pattern P-15). Removed rather than repaired,
# because the property they were reaching for is already enforced, falsifiably, by the check below.
#
# THE LIVE HALF, KEPT. This one compares two INDEPENDENTLY DERIVED sets — the ids that PROMISE
# precision 12 by their name, and the ids that were OBSERVED running below 19 in this capture's own
# `inputs`. Nothing defines either in terms of the other, so they can disagree, and they do disagree
# the moment CASE_PRECISION registers a non-`-p12` case below 19 or a `-p12` case at 19.
# DEMONSTRATED RED by T82 — see `.softhouse/capture/t74-multiplesof/T82-guard-proofs/`.
_p12_named = [c['id'] for c in caps if c['id'].endswith('-p12')]
if sorted(_p12_named) != sorted(probe_ids):
    sys.exit("RUN FAILED: the cases named `-p12` are %r but the cases actually running below "
             "precision 19 are %r. An id that promises a precision it does not run is worse than "
             "no id at all." % (sorted(_p12_named), sorted(probe_ids)))

logtext = open(logp, encoding='utf-8').read()
moneylines = [l for l in logtext.splitlines() if 'MoneyHelper' in l]

sidecar = {
    "artifact": "Path A capture pass 3i",
    "capturePath": att['capturePath'],
    "producedBy": ".softhouse/capture/src/run-pass3i.sh",
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
        "KEYED ON MathContext precision != 19, the same definition passes 3b..3h used. READ IT WITH "
        "CARE ON THIS PASS: it now catches THREE different roles at once — the precision-12 rig "
        "calibration P-CAL, and pass 3i's SIX group-E DISCRIMINATION PROBES, which are neither "
        "calibrations nor parity candidates. Seven of the nine calibrations run AT the production "
        "precision and therefore appear under productionSettingsCaptureIds instead. Use "
        "calibrationRoleCaptureIds for calibrations BY ROLE, discriminationProbeCaptureIds for the "
        "probes, and parityCandidateCaptureIds for what this pass actually offers for promotion.",
    "calibrationRoleCaptureIds": sorted(CALIBRATIONS),
    "discriminationProbeCaptureIds": sorted(probe_ids),
    "discriminationProbeCaptureIdsNote":
        "NEVER PROMOTABLE. These carry the SAME REQUEST as their production-precision twin but run "
        "at MathContext precision 12, a precision production never runs (MoneyHelper.PRECISION = 19 "
        "is a compile-time constant, MoneyHelper.java:35). They exist so the margin between a port "
        "at the ratified 19 significant digits and one that quietly runs at 12 is MEASURED FROM THE "
        "ORACLE rather than modelled. Their ids belong on PIN.json's never_promotable list.",
    "parityCandidateCaptureIds": sorted(parity_ids),
    "calibrationReport": cal_report,
    "fieldSeparation": {
        "note":
            "T21 required change P1-8 / T19 required change 10, closed by this pass. Up to pass 3h "
            "ONE harness field fed CurrencyData.inMultiplesOf, installmentAmountInMultiplesOf and "
            "BOTH emitted JSON keys, so no capture could attribute a difference to either input. "
            "These two lists are the mechanical proof that the fields are independent in THIS "
            "artefact: an aliased harness cannot populate both, because one value would be printed "
            "into both keys.",
        "currencyOnlyCaptureIds": _cur_only,
        "installmentOnlyCaptureIds": _inst_only,
        "bothSetCaptureIds": [c['id'] for c in caps
                              if c['inputs'].get('currencyInMultiplesOf') is not None
                              and c['inputs'].get('installmentAmountInMultiplesOf') is not None],
    },
    "admissibilityNote":
        "RAW OBSERVED. Attestation is present, but presence of an attestation does not promote anything. "
        "Promotion to the parity vector store is a separate, gated decision, and it is refused outright "
        "for any input the FROZEN CONTRACT does not carry or that .softhouse/vectors/capabilities.json "
        "does not mark 'exercised' for this seam.",
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
