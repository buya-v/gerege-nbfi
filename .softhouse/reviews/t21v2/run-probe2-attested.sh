#!/bin/sh
# T35 / RC-5 — re-emit t21v2-probe2-oracle-out.txt WITH a provenance header.
#
# Run from the repo root:   sh .softhouse/reviews/t21v2/run-probe2-attested.sh
#
# Fails the run on: docker missing, image id mismatch, pinned checkout missing/wrong/dirty, seam-class
# drift, non-zero container exit, no rows produced, or a data row that differs from the committed
# transcript (a changed oracle number would be a finding, and this script refuses to overwrite the
# record with one silently).
#
# Every output path below is a literal filename — no glob can be created as a literally-named file
# (the T22 P0-5 defect class).
set -eu

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="${PINNED_FINERACT:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

DIR=".softhouse/reviews/t21v2"
OUT="$DIR/t21v2-probe2-oracle-out.txt"
WORK="${RC5_WORK:-/tmp/t35-rc5}"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

[ -f "$DIR/T21v2Probe2.java" ] || fail "run me from the repo root; $DIR/T21v2Probe2.java not found from $(pwd)"
command -v docker >/dev/null 2>&1 || fail "docker not on PATH"
IMG=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}' 2>/dev/null) || fail "image absent"
[ "$IMG" = "$EXPECTED_IMAGE_ID" ] || fail "image id mismatch: $IMG"
COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] || fail "pinned checkout at $COMMIT"
[ -z "$(git -C "$PINNED_FINERACT" status --porcelain)" ] || fail "pinned checkout is dirty"
cmp -s ".softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$PINNED_FINERACT/$SEAM_REL" \
  || fail "seam class drift versus the pinned original"

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/out"
cp "$DIR/T21v2Probe2.java" "$DIR/T21v2Probe2Attested.java" "$WORK/src/"
cp ".softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$WORK/src/"

set +e
docker run --rm --user 0 --entrypoint sh \
  -e ATTEST_IMAGE_REF="$EXPECTED_IMAGE_REF" \
  -e ATTEST_IMAGE_ID="$IMG" \
  -e ATTEST_PINNED_COMMIT="$COMMIT" \
  -e ATTEST_SOURCES="/cap/src/T21v2Probe2.java:/cap/src/T21v2Probe2Attested.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java" \
  -v "$WORK:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/T21v2Probe2.java /cap/src/T21v2Probe2Attested.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" T21v2Probe2Attested
' > "$WORK/out/raw.txt" 2> "$WORK/out/stderr.txt"
RC=$?
set -e
[ "$RC" -eq 0 ] || { printf 'RUN FAILED: container exited %s\n' "$RC" >&2; cat "$WORK/out/stderr.txt" >&2; exit 1; }
[ -s "$WORK/out/stderr.txt" ] && { printf 'RUN FAILED: stderr not empty:\n' >&2; cat "$WORK/out/stderr.txt" >&2; exit 1; }

# data rows = everything that is neither a provenance comment nor one of the oracle's own log lines
grep -v '^#' "$WORK/out/raw.txt" | grep -v 'MoneyHelper' | grep -v '^[[:space:]]*$' > "$WORK/out/rows.txt"
ROWS=$(wc -l < "$WORK/out/rows.txt" | tr -d ' ')
[ "$ROWS" -eq 17 ] || fail "expected 17 data rows, got $ROWS"

if [ -f "$OUT" ]; then
  grep -v '^#' "$OUT" | grep -v 'MoneyHelper' | grep -v '^[[:space:]]*$' > "$WORK/out/rows-committed.txt"
  if ! diff -u "$WORK/out/rows-committed.txt" "$WORK/out/rows.txt" > "$WORK/out/rows.diff"; then
    printf 'FINDING — the re-run produced DIFFERENT data rows than the committed transcript.\n' >&2
    printf 'This is not something to reconcile. Refusing to overwrite. Diff:\n' >&2
    cat "$WORK/out/rows.diff" >&2
    exit 1
  fi
  printf 'data rows are byte-identical to the committed transcript (%s rows)\n' "$ROWS"
fi

cp "$WORK/out/raw.txt" "$OUT"
shasum -a 256 "$OUT"
printf 'DONE — %s re-emitted with a provenance header. Nothing promoted.\n' "$OUT"
