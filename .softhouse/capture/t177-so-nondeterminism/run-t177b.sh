#!/bin/bash
# T177 trial runner, VARIANT B. Identical to run-t177.sh except for three things, and nothing else:
#
#   1. it compiles BOTH CaptureT177.java (frozen — it produced the pilot and matrix-A evidence) and
#      the mechanically derived CaptureT177b.java;
#   2. the matrix gains an OPTIONAL 5th field naming the harness class, defaulting to CaptureT177;
#   3. it records the digests of both harnesses in the attestation.
#
# run-t177.sh is NOT edited, because it produced committed evidence (T114's standing ruling). The
# preconditions, the container invocation, the per-process stdout/stderr capture, the run index and
# the deliberate refusal to abort on a non-zero java exit or non-empty stderr are all unchanged.
#
# Reaches no database, starts no server, does not touch the running fineract-* containers. "Oracle"
# here is the Fineract reference implementation, never Oracle Database (a prohibited product).
#
# Usage: run-t177b.sh <repo-root> <matrix-file> <out-subdir>
set -uo pipefail

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="/Users/buv/fineract"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"

REPO="$1"
MATRIX="$2"
OUTSUB="$3"
CAP=/tmp/t177probe
RIG="$REPO/.softhouse/capture/t177-so-nondeterminism"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}')
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] || fail "image id mismatch: $ACTUAL_IMAGE_ID"
ACTUAL_COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] || fail "pin is $ACTUAL_COMMIT"
[ -z "$(git -C "$PINNED_FINERACT" status --porcelain)" ] || fail "pinned checkout DIRTY"

mkdir -p "$CAP/src" "$CAP/out/$OUTSUB/raw"
cp "$PINNED_FINERACT/$SEAM_REL" "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java"
cp "$REPO/.softhouse/capture/lib/ThrewOutcome.java" "$CAP/src/ThrewOutcome.java"
cp "$RIG/src/CaptureT177.java" "$CAP/src/CaptureT177.java"
cp "$RIG/src/CaptureT177b.java" "$CAP/src/CaptureT177b.java"
cp "$MATRIX" "$CAP/matrix.txt"

cmp -s "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$PINNED_FINERACT/$SEAM_REL" || fail "seam drift"
SEAM_SHA=$(shasum -a 256 "$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java" | cut -d' ' -f1)
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] || fail "seam sha $SEAM_SHA"
cmp -s "$CAP/src/ThrewOutcome.java" "$REPO/.softhouse/capture/lib/ThrewOutcome.java" || fail "lib drift"
LIB_SHA=$(shasum -a 256 "$CAP/src/ThrewOutcome.java" | cut -d' ' -f1)
HARNESS_SHA=$(shasum -a 256 "$CAP/src/CaptureT177.java" | cut -d' ' -f1)
HARNESS_B_SHA=$(shasum -a 256 "$CAP/src/CaptureT177b.java" | cut -d' ' -f1)
MATRIX_SHA=$(shasum -a 256 "$CAP/matrix.txt" | cut -d' ' -f1)

RUN_ID="t177b-$OUTSUB-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'preconditions OK\n  image    %s\n  fineract %s (clean)\n  seam     %s\n  lib      %s\n  harnessA %s\n  harnessB %s\n  matrix   %s\n  run      %s\n' \
  "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA" "$LIB_SHA" "$HARNESS_SHA" "$HARNESS_B_SHA" "$MATRIX_SHA" "$RUN_ID"

START_EPOCH=$(date -u +%s)
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" -e ATTEST_IMAGE_ID="$ACTUAL_IMAGE_ID" \
  -e ATTEST_PINNED_COMMIT="$ACTUAL_COMMIT" -e ATTEST_PINNED_PATH="$PINNED_FINERACT" \
  -e ATTEST_RUN_ID="$RUN_ID" -e ATTEST_HARNESS_SHA="$HARNESS_SHA" -e ATTEST_HARNESS_B_SHA="$HARNESS_B_SHA" \
  -e ATTEST_SEAM_SHA="$SEAM_SHA" -e ATTEST_LIB_SHA="$LIB_SHA" \
  -e OUTSUB="$OUTSUB" \
  -v "$CAP:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
OUT="/cap/out/$OUTSUB"
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
  /cap/src/CaptureT177.java /cap/src/CaptureT177b.java \
  /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java /cap/src/ThrewOutcome.java
java -version 2> "$OUT/java-version.txt"
: > "$OUT/run-index.txt"
set +e
while IFS="|" read -r SERIES RUNS PLAN FLAGS HARNESS; do
  case "$SERIES" in ""|\#*) continue ;; esac
  [ -n "$HARNESS" ] || HARNESS=CaptureT177
  i=0
  while [ "$i" -lt "$RUNS" ]; do
    SO="$OUT/raw/$SERIES-$i.stdout"; SE="$OUT/raw/$SERIES-$i.stderr"
    T0=$(date -u +%s)
    T177_SERIES="$SERIES" T177_RUN_IDX="$i" \
      java $FLAGS -cp "/work/classes:$CP" "$HARNESS" "$PLAN" > "$SO" 2> "$SE"
    RC=$?
    T1=$(date -u +%s)
    printf "RUN series=%s idx=%s plan=%s flags=[%s] harness=%s exit=%s wall_s=%s stdout_bytes=%s stderr_bytes=%s\n" \
      "$SERIES" "$i" "$PLAN" "$FLAGS" "$HARNESS" "$RC" "$((T1 - T0))" \
      "$(wc -c < "$SO" | tr -d " ")" "$(wc -c < "$SE" | tr -d " ")" >> "$OUT/run-index.txt"
    i=$((i + 1))
  done
done < /cap/matrix.txt
echo "MATRIX COMPLETE" >> "$OUT/run-index.txt"
' 2>&1 | tee "$CAP/out/$OUTSUB/container-console.txt"
DOCKER_RC=${PIPESTATUS[0]}
END_EPOCH=$(date -u +%s)

printf 'docker exit %s, wall %ss\n' "$DOCKER_RC" "$((END_EPOCH - START_EPOCH))"
printf '{"runId": "%s", "dockerExit": %s, "wallSeconds": %s, "imageId": "%s", "pinnedCommit": "%s", "seamSha256": "%s", "libSha256": "%s", "harnessSha256": "%s", "harnessBSha256": "%s", "matrixSha256": "%s"}\n' \
  "$RUN_ID" "$DOCKER_RC" "$((END_EPOCH - START_EPOCH))" "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" \
  "$SEAM_SHA" "$LIB_SHA" "$HARNESS_SHA" "$HARNESS_B_SHA" "$MATRIX_SHA" > "$CAP/out/$OUTSUB/attestation.json"
cat "$CAP/out/$OUTSUB/attestation.json"
exit "$DOCKER_RC"
