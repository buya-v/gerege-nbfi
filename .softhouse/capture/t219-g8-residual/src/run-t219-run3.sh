#!/bin/bash
# T219 G-8 RESIDUAL-RECORD probe. T229's run-t223.sh with T219's case list and nothing else changed:
# same pinned image id, same pinned Fineract commit + clean-tree check, same seam byte-identity AND
# literal seam digest, same empty-stderr rule, same ThrewOutcome digest, same calibration reference.
#
# The oracle is the Fineract reference implementation. Oracle Database is a prohibited product in
# this program and appears nowhere in this work: this reaches no database, starts no server, and
# does not touch the running fineract-fineract-1 / fineract-db-1 containers -- it launches a
# throw-away `docker run --rm` from the pinned image and calls the in-JVM Path A seam.
set -euo pipefail

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="/Users/buv/fineract"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"
EXPECTED_THREW_SHA="de816eb330441d62e47f524d5b4e2ec297485512bf1b287c2fba5cd6b033465e"
REPO="$1"
REF3G_JSON="$REPO/.softhouse/capture/out/capture-prod3g-raw.json"
EXPECTED_REF3G_SHA="6e0c37019095cf8664b18b643bafb8e59014b47f2d4a8a82ce43463e41827d91"
CAP=/tmp/t219probe3
RAW="$CAP/out/stdout.txt"; JSON="$CAP/out/capture-t219-run3-raw.json"
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
HARNESS_SHA=$(shasum -a 256 "$CAP/src/CaptureT219X.java" | cut -d' ' -f1)
THREW_SHA=$(shasum -a 256 "$CAP/src/ThrewOutcome.java" | cut -d' ' -f1)
[ "$THREW_SHA" = "$EXPECTED_THREW_SHA" ] || fail "ThrewOutcome.java sha $THREW_SHA"
RUN_ID="t219-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image %s\n  fineract %s (clean)\n  seam %s\n  harness %s\n  ThrewOutcome %s\n  run %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$HARNESS_SHA" "$THREW_SHA" "$RUN_ID"

set +e
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" \
  -e ATTEST_SOURCES="/cap/src/CaptureT219X.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java:/cap/src/ThrewOutcome.java" \
  -e ATTEST_CLASSPATH_OUT="/cap/out/classpath-sha256.txt" \
  -v "$CAP:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/CaptureT219X.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java /cap/src/ThrewOutcome.java
java -Xss16m -cp "/work/classes:$CP" CaptureT219X
' > "$RAW" 2> "$ERR"
RC=$?
set -e
[ "$RC" -eq 0 ] || { printf 'RUN FAILED: container exited %s\n' "$RC" >&2; tail -50 "$ERR" >&2; exit 1; }

START=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
[ -n "${START:-}" ] || fail "no JSON on stdout"
if [ "$START" -gt 1 ]; then head -n $((START - 1)) "$RAW" > "$LOG"; else : > "$LOG"; fi
tail -n +"$START" "$RAW" > "$JSON"
[ -s "$ERR" ] && { printf 'RUN FAILED: stderr NOT empty:\n' >&2; cat "$ERR" >&2; exit 1; } || true
printf 'capture written: %s\n' "$JSON"
