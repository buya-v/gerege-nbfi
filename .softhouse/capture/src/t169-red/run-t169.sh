#!/bin/bash
# T169 rig probe. Same precondition set as T83's run-t83.sh, T84's run-t84.sh, T100's run-t100.sh,
# T117's run-t117.sh and T159's run-t159.sh (pinned image id, pinned Fineract commit + clean tree,
# seam byte-identity AND literal seam digest, pass-3g calibration reference digest), with ONE
# deliberate difference which is the subject of the task:
#
#   THIS RUNNER DOES NOT ABORT ON A NON-ZERO CONTAINER EXIT OR ON NON-EMPTY STDERR.
#
# It records both and hands them to the postcheck, because a run that DIED is the RESULT this probe
# is measuring, and a runner that exits before printing the integrity line is precisely how "0
# errored" stayed unfalsifiable. The postcheck still refuses a broken run: graded domain,
# (19, HALF_UP), the attestation pin and the two rig calibrations are all unrelaxed there.
#
# Reaches no database, starts no server, does not touch the running fineract-* containers: it
# launches a throw-away `docker run --rm` from the pinned image and calls the in-JVM Path A seam.
# "Oracle" here is the Fineract reference implementation, never Oracle Database (a prohibited
# product in this program).
#
# Usage: run-t169.sh <repo-root> <Pre|Post>
set -uo pipefail

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="/Users/buv/fineract"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"
REPO="$1"
VARIANT="$2"                      # Pre | Post
HARNESS="CaptureT169${VARIANT}"
REF3G_JSON="$REPO/.softhouse/capture/out/capture-prod3g-raw.json"
EXPECTED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"
CAP=/tmp/t169probe
OUT="$CAP/out-$VARIANT"
RAW="$OUT/stdout.txt"; JSON="$OUT/capture-t169-$VARIANT.json"
LOG="$OUT/oracle-log.txt"; ERR="$OUT/stderr.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

mkdir -p "$OUT"
[ "$VARIANT" = "Pre" ] || [ "$VARIANT" = "Post" ] || fail "variant must be Pre or Post"

ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}')
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] || fail "image id mismatch: $ACTUAL_IMAGE_ID"
ACTUAL_COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] || fail "pin is $ACTUAL_COMMIT"
[ -z "$(git -C "$PINNED_FINERACT" status --porcelain)" ] || fail "pinned checkout DIRTY"
cmp -s "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$PINNED_FINERACT/$SEAM_REL" || fail "seam drift"
SEAM_SHA=$(shasum -a 256 "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" | cut -d' ' -f1)
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] || fail "seam sha $SEAM_SHA"
[ "$(shasum -a 256 "$REF3G_JSON" | cut -d' ' -f1)" = "$EXPECTED_REF3G_SHA" ] || fail "calibration reference sha"
HARNESS_SHA=$(shasum -a 256 "$CAP/src/$HARNESS.java" | cut -d' ' -f1)

if [ "$VARIANT" = "Post" ]; then
  LIB_SHA=$(shasum -a 256 "$CAP/src/ThrewOutcome.java" | cut -d' ' -f1)
  SOURCES="/cap/src/$HARNESS.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java:/cap/src/ThrewOutcome.java"
  JAVAC_SRC="/cap/src/$HARNESS.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java /cap/src/ThrewOutcome.java"
else
  LIB_SHA="-"
  SOURCES="/cap/src/$HARNESS.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
  JAVAC_SRC="/cap/src/$HARNESS.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
fi

RUN_ID="t169-$VARIANT-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image %s\n  fineract %s (clean)\n  seam %s\n  harness %s %s\n  run %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$HARNESS" "$HARNESS_SHA" "$RUN_ID"

docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" \
  -e ATTEST_SOURCES="$SOURCES" \
  -e ATTEST_CLASSPATH_OUT="/cap/out-$VARIANT/classpath-sha256.txt" \
  -e HARNESS="$HARNESS" -e JAVAC_SRC="$JAVAC_SRC" \
  -v "$CAP:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes $JAVAC_SRC
java -cp "/work/classes:$CP" "$HARNESS"
' > "$RAW" 2> "$ERR"
RC=$?

printf 'container exit %s, stdout %s bytes, stderr %s bytes\n' \
  "$RC" "$(wc -c < "$RAW" | tr -d ' ')" "$(wc -c < "$ERR" | tr -d ' ')"

START=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
if [ -n "${START:-}" ]; then
  if [ "$START" -gt 1 ]; then head -n $((START - 1)) "$RAW" > "$LOG"; else : > "$LOG"; fi
  tail -n +"$START" "$RAW" > "$JSON"
else
  cp "$RAW" "$LOG"
  : > "$JSON"
fi

python3 "$CAP/src/postcheck_t169.py" "$JSON" "$REF3G_JSON" "$ACTUAL_COMMIT" "$HARNESS" \
  "$HARNESS_SHA" "$SEAM_SHA" "$LIB_SHA" /tmp/t169-ids.json "$RC" "$ERR"
