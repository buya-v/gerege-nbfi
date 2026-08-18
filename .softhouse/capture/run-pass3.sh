#!/bin/sh
# =============================================================================================
# EXECUTABLE pass-3 capture recipe — Path A (embeddable seam, in-process, no database).
#
# T21 audit P0-4: "Commit a pass-3 run recipe as an executable script, with the seam byte-identity
# check as a PRECONDITION STEP THAT FAILS THE RUN rather than a prose instruction."
# A precondition that cannot fail is not a precondition. Every check below exits non-zero on
# mismatch and the capture never starts. Prove that for yourself:
#
#     sh .softhouse/capture/run-pass3.sh --selftest      # deliberately breaks each precondition
#
# Usage, from the repository root:
#     sh .softhouse/capture/run-pass3.sh [--out-tag TAG]
#
# Default TAG is "prod-v2"; artefacts land in .softhouse/capture/out/capture-$TAG-{raw.json,log.txt,stderr.txt}.
#
# This script OBSERVES. It asserts provenance, then records exactly what the oracle emitted.
# It never synthesises a value, and it never repairs one.
# =============================================================================================
set -u

# ---- pinned provenance, the only literals this script is allowed to assert against -----------
EXPECT_IMAGE_DIGEST='sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'
EXPECT_FINERACT_COMMIT='426a23544e8426a38ae43ae404670a0a7e85b9eb'
FINERACT_CHECKOUT="${FINERACT_CHECKOUT:-/Users/buv/fineract}"
SEAM_REL='fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java'

# Resolve paths from the SCRIPT's own location, never from the caller's cwd.
CAP=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$CAP/../.." && pwd)
SEAM_COPY="${SEAM_COPY:-$CAP/src/EmbeddableProgressiveLoanScheduleGenerator.java}"
SEAM_PINNED="${SEAM_PINNED:-$FINERACT_CHECKOUT/$SEAM_REL}"
HARNESS="${HARNESS:-$CAP/src/Capture3.java}"
TAG='prod-v2'
SELFTEST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --out-tag) TAG="$2"; shift 2 ;;
    --selftest) SELFTEST=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done

fail() { echo "PRECONDITION FAILED: $*" >&2; exit 1; }
ok()   { echo "  ok   $*"; }

# CAP_SELFTEST_BREAK exists for ONE purpose: to prove each precondition can actually fail.
# It is set only by --selftest below, and it never writes a capture.
case "${CAP_SELFTEST_BREAK:-}" in
  image)  echo "SELF-TEST: expected image digest deliberately corrupted"  >&2
          EXPECT_IMAGE_DIGEST='sha256:0000000000000000000000000000000000000000000000000000000000000000' ;;
  commit) echo "SELF-TEST: expected oracle commit deliberately corrupted" >&2
          EXPECT_FINERACT_COMMIT='0000000000000000000000000000000000000000' ;;
  "")     ;;
  *)      echo "unknown CAP_SELFTEST_BREAK: $CAP_SELFTEST_BREAK" >&2; exit 64 ;;
esac

# =============================================================================================
# PRECONDITIONS — each one exits non-zero. Nothing is captured until all of them pass.
# =============================================================================================
preconditions() {
  echo "== preconditions =="

  # 1. Docker present and the PINNED image, by digest.
  command -v docker >/dev/null 2>&1 || fail "docker is not on PATH"
  IMAGE_DIGEST=$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null) \
    || fail "image fineract:latest is not present"
  [ "$IMAGE_DIGEST" = "$EXPECT_IMAGE_DIGEST" ] \
    || fail "image digest is $IMAGE_DIGEST, expected $EXPECT_IMAGE_DIGEST"
  ok "image digest $IMAGE_DIGEST"

  # 2. The pinned Fineract checkout, at the pinned commit, with a clean worktree.
  [ -d "$FINERACT_CHECKOUT/.git" ] || fail "no git checkout at $FINERACT_CHECKOUT"
  FINERACT_COMMIT=$(git -C "$FINERACT_CHECKOUT" rev-parse HEAD) || fail "cannot read $FINERACT_CHECKOUT HEAD"
  [ "$FINERACT_COMMIT" = "$EXPECT_FINERACT_COMMIT" ] \
    || fail "reference oracle checkout is at $FINERACT_COMMIT, expected $EXPECT_FINERACT_COMMIT"
  FINERACT_DIRTY=$(git -C "$FINERACT_CHECKOUT" status --porcelain | wc -l | tr -d ' ')
  [ "$FINERACT_DIRTY" = "0" ] || fail "reference oracle checkout is DIRTY ($FINERACT_DIRTY changed paths)"
  ok "reference oracle checkout $FINERACT_COMMIT, clean"
  FINERACT_CLEAN=true

  # 3. THE SEAM BYTE-IDENTITY CHECK. The seam class is NOT bundled in /app/fineract-provider.jar,
  #    so it is compiled from this copy. If the copy is not byte-identical to the pinned original,
  #    the run does not execute the oracle's code and every number it prints is worthless.
  [ -f "$SEAM_COPY" ]   || fail "seam copy missing: $SEAM_COPY"
  [ -f "$SEAM_PINNED" ] || fail "pinned seam missing: $SEAM_PINNED"
  SEAM_COPY_SHA=$(shasum -a 256 "$SEAM_COPY"   | cut -d' ' -f1)
  SEAM_PIN_SHA=$( shasum -a 256 "$SEAM_PINNED" | cut -d' ' -f1)
  [ "$SEAM_COPY_SHA" = "$SEAM_PIN_SHA" ] || fail \
    "SEAM IS NOT BYTE-IDENTICAL TO THE PINNED ORACLE. copy=$SEAM_COPY_SHA pinned=$SEAM_PIN_SHA -- this capture would not be an observation of the oracle"
  ok "seam byte-identity $SEAM_COPY_SHA"
  SEAM_IDENTITY="byte-identical to pinned original, sha256=$SEAM_COPY_SHA"

  # 4. The harness itself exists.
  [ -f "$HARNESS" ] || fail "harness missing: $HARNESS"
  ok "harness $(shasum -a 256 "$HARNESS" | cut -d' ' -f1)"

  # 5. PostgreSQL-only rule, asserted on the image this capture will run: the classpath must carry
  #    no prohibited driver. (Path A opens no connection at all; the assertion is still cheap.)
  PROHIBITED=$(docker run --rm --entrypoint sh fineract:latest -c \
      'unzip -l /app/fineract-provider.jar | grep -icE "ojdbc|oracle\.jdbc|mysql|mariadb"' 2>/dev/null | tr -d ' ')
  [ "$PROHIBITED" = "0" ] || fail "prohibited DB driver present in the provider jar ($PROHIBITED matches)"
  ok "no prohibited DB driver in the provider jar"
}

# =============================================================================================
# SELF-TEST — demonstrates every precondition can actually fail. Captures nothing.
# =============================================================================================
if [ "$SELFTEST" = "1" ]; then
  echo "== precondition self-test: every check below MUST fail, and MUST write no capture =="
  TMPD=$(mktemp -d)
  RC_ALL=0
  expect_fail() {
    LABEL="$1"; shift
    OUT=$("$@" 2>&1)
    RC=$?
    LAST=$(echo "$OUT" | tail -1)
    if [ "$RC" = "0" ]; then
      echo "  SELF-TEST FAILED: [$LABEL] exited 0 — this precondition CANNOT fail, so it is not a precondition"
      RC_ALL=1
    else
      echo "  ok  [$LABEL] exit $RC :: $LAST"
    fi
  }

  # 1. seam copy that is NOT byte-identical to the pinned oracle
  cp "$SEAM_COPY" "$TMPD/seam.java"
  printf '\n// T25 self-test: deliberately NOT the pinned oracle seam\n' >> "$TMPD/seam.java"
  expect_fail "mutated seam" env SEAM_COPY="$TMPD/seam.java" sh "$0" --out-tag selftest-never-written

  # 2. seam copy missing entirely
  expect_fail "missing seam" env SEAM_COPY="$TMPD/absent.java" sh "$0" --out-tag selftest-never-written

  # 3. wrong image digest
  expect_fail "wrong image digest" env CAP_SELFTEST_BREAK=image sh "$0" --out-tag selftest-never-written

  # 4. wrong reference-oracle commit
  expect_fail "wrong oracle commit" env CAP_SELFTEST_BREAK=commit sh "$0" --out-tag selftest-never-written

  # 5. reference-oracle checkout at a path that is not a git checkout
  expect_fail "no oracle checkout" env FINERACT_CHECKOUT="$TMPD" sh "$0" --out-tag selftest-never-written

  # 6. missing harness
  expect_fail "missing harness" env HARNESS="$TMPD/absent.java" sh "$0" --out-tag selftest-never-written

  echo "-- nothing may have been written --"
  if ls "$CAP"/out/capture-selftest-never-written-* >/dev/null 2>&1; then
    echo "  SELF-TEST FAILED: a capture file was written despite a failed precondition"
    RC_ALL=1
  else
    echo "  ok  no capture-selftest-never-written-* artefact exists"
  fi
  rm -rf "$TMPD"
  if [ "$RC_ALL" = "0" ]; then
    echo "== self-test PASSED: all 6 preconditions fail the run =="
  else
    echo "== self-test FAILED =="
  fi
  exit "$RC_ALL"
fi

preconditions

# =============================================================================================
# CAPTURE
# =============================================================================================
RAW="$CAP/out/capture-$TAG-raw.json"
LOG="$CAP/out/capture-$TAG-log.txt"
ERR="$CAP/out/capture-$TAG-stderr.txt"
mkdir -p "$CAP/out"
HOST_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "== capture (tag=$TAG) =="
docker run --rm --user 0 --entrypoint sh \
  -e H_IMAGE="$IMAGE_DIGEST" \
  -e H_COMMIT="$FINERACT_COMMIT" \
  -e H_CLEAN="$FINERACT_CLEAN" \
  -e H_SEAM="$SEAM_IDENTITY" \
  -e H_UTC="$HOST_UTC" \
  -v "$CAP:/cap" fineract:latest -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/Capture3.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" \
     -Dcap.host.imageDigest="$H_IMAGE" \
     -Dcap.host.fineractCommit="$H_COMMIT" \
     -Dcap.host.fineractWorktreeClean="$H_CLEAN" \
     -Dcap.host.seamByteIdentity="$H_SEAM" \
     -Dcap.host.runnerScript=".softhouse/capture/run-pass3.sh" \
     -Dcap.host.capturedAtUtc="$H_UTC" \
     Capture3
' > "$RAW" 2> "$ERR"
RC=$?
[ "$RC" = "0" ] || { echo "CAPTURE FAILED (exit $RC); see $ERR" >&2; exit "$RC"; }

# The oracle's own SLF4J logger writes MoneyHelper initialisation lines to STDOUT, ahead of the
# JSON. They are EVIDENCE (they independently corroborate which rounding mode each tenant got), so
# split them out and keep them; never discard them.
S=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
[ -n "$S" ] || { echo "no JSON found in $RAW" >&2; exit 1; }
head -n $((S - 1)) "$RAW" > "$LOG"
tail -n +"$S" "$RAW" > "$RAW.tmp" && mv "$RAW.tmp" "$RAW"

python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$RAW" \
  || { echo "captured file is not valid JSON: $RAW" >&2; exit 1; }

echo "== captured =="
echo "  $RAW  ($(wc -c < "$RAW" | tr -d ' ') bytes, sha256 $(shasum -a 256 "$RAW" | cut -d' ' -f1))"
echo "  $LOG  ($(wc -l < "$LOG" | tr -d ' ') log lines)"
echo "  $ERR  ($(wc -c < "$ERR" | tr -d ' ') bytes)"
echo "Attestation is INSIDE $RAW under the top-level \"attestation\" key."
