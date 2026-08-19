#!/usr/bin/env bash
#
# T46 -- run the exhaustive month-difference sweep INSIDE the pinned oracle image, so the
# java.time semantics measured are the ones the reference oracle (Fineract) itself runs on.
#
# Container discipline: docker run --rm, mounts only this capture set's directory.
# The shared fineract-fineract-1 / fineract-db-1 containers are not touched.
set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECT_IMAGE="${T46_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
OUT="$CAPDIR/analysis/t46_monthdiff_exhaustive-output.txt"

fail() { echo "BREACH: $*" >&2; exit 1; }

IMAGE_ID="$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)" || fail "image fineract:latest not present"
[ "$IMAGE_ID" = "$EXPECT_IMAGE" ] || fail "image id is $IMAGE_ID, expected $EXPECT_IMAGE"

{
  echo "== image      : $IMAGE_ID"
  echo "== source sha : $(shasum -a 256 "$CAPDIR/analysis/T46MonthDiffExhaustive.java" | awk '{print $1}')"
} > "$OUT"

docker run --rm --user 0 --entrypoint sh -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work/classes
javac -nowarn -d /work/classes /cap/analysis/T46MonthDiffExhaustive.java
java -Xmx1g -cp /work/classes T46MonthDiffExhaustive
' >> "$OUT" 2>&1 || fail "sweep container exited non-zero (see $OUT)"

echo "== done -> $OUT"
cat "$OUT"
