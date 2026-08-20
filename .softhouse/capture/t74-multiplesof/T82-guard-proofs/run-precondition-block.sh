#!/bin/bash
# ---------------------------------------------------------------------------------------------
# T82 guard-proof driver.
#
# WHAT THIS IS. `run-pass3i.sh` cannot be re-run without docker, the pinned image and the pinned
# Fineract checkout — and re-running it would produce a NEW capture, which is not what a defect fix
# needs to demonstrate. What a defect fix needs to demonstrate is that the PRECONDITION BLOCK goes
# RED on an input that should make it go red.
#
# So this driver does NOT re-implement the preconditions. It SLICES the `python3 - ... <<'PY' ... PY`
# heredoc out of `run-pass3i.sh` BYTE FOR BYTE and runs that exact text, with the same 21 argv the
# script passes it, against a chosen capture JSON. Nothing is transcribed, nothing is paraphrased:
# if the block in the script changes, this driver runs the changed block on the next invocation.
#
# It writes its attestation sidecar to a scratch path, so a demo run cannot overwrite the committed
# `capture-prod3i-attestation.json`.
#
#   usage: bash run-precondition-block.sh <capture-json> <scratch-attestation-out>
#
# Exit status is the precondition block's own. 0 = every check passed, 1 = a check went RED.
#
# NO ORACLE, NO DOCKER, NO DATABASE. This reads committed artefacts only. (PostgreSQL remains the
# only permitted engine in this program; this driver reaches no database at all.)
# ---------------------------------------------------------------------------------------------
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
# $T82_SCRIPT lets a proof run the block out of a MUTATED COPY of run-pass3i.sh, which is how the
# "someone adds a case and forgets the table" edit is simulated without editing the committed script.
SCRIPT="${T82_SCRIPT:-$ROOT/.softhouse/capture/src/run-pass3i.sh}"
OUT="$ROOT/.softhouse/capture/out"

JSON="${1:?usage: run-precondition-block.sh <capture-json> <scratch-attestation-out>}"
ATT="${2:?usage: run-precondition-block.sh <capture-json> <scratch-attestation-out>}"

# --- slice the heredoc out of the script, byte for byte ------------------------------------------
PYFILE="$(mktemp -t t82precond)"
trap 'rm -f "$PYFILE"' EXIT
START=$(grep -n "<<'PY'" "$SCRIPT" | head -1 | cut -d: -f1)
END=$(grep -n '^PY$' "$SCRIPT" | head -1 | cut -d: -f1)
sed -n "$((START + 1)),$((END - 1))p" "$SCRIPT" > "$PYFILE"
echo "# precondition block: lines $((START + 1))..$((END - 1)) of run-pass3i.sh, $(wc -l < "$PYFILE" | tr -d ' ') lines, sha256 $(shasum -a 256 "$PYFILE" | cut -d' ' -f1)"
echo "# capture under test: $JSON"

# --- the same pinned facts the script itself passes ----------------------------------------------
# These are read OUT OF THE SCRIPT rather than copied, so they cannot drift from it.
val() { grep -m1 "^$1=" "$SCRIPT" | sed -e "s/^$1=//" -e 's/^"//' -e 's/".*$//'; }
IMAGE_REF=$(val EXPECTED_IMAGE_REF)
IMAGE_ID=$(val EXPECTED_IMAGE_ID)
COMMIT=$(val EXPECTED_FINERACT_COMMIT)
SEAM_SHA=$(val EXPECTED_SEAM_SHA)
REF3B_SHA=$(val EXPECTED_REF3B_SHA)
REF3C_SHA=$(val EXPECTED_REF3C_SHA)
REF3E_SHA=$(val EXPECTED_REF3E_SHA)
REF3G_SHA=$(val EXPECTED_REF3G_SHA)
PINNED="${PINNED_FINERACT:-/Users/buv/fineract}"

# The harness sha is not a literal in the script (it is measured with shasum at run time), so it is
# measured here the same way, off the committed harness source.
HARNESS_SHA=$(shasum -a 256 "$ROOT/.softhouse/capture/src/Capture3i.java" | cut -d' ' -f1)

# The run id the committed artefact carries, so the sidecar the block writes is comparable.
RUN_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["attestation"]["runnerSupplied"]["runId"])' "$JSON")

python3 "$PYFILE" \
  "$JSON" \
  "$ATT" \
  "$OUT/capture-prod3i-log.txt" \
  "$IMAGE_ID" \
  "$IMAGE_REF" \
  "$COMMIT" \
  "$PINNED" \
  "$SEAM_SHA" \
  "$HARNESS_SHA" \
  "$RUN_ID" \
  "$OUT/capture-prod3i-classpath-sha256.txt" \
  "$OUT/capture-prod3i-stderr.txt" \
  "$OUT/capture-prod3i-raw.txt" \
  "$OUT/capture-prod3b-raw.json" "$REF3B_SHA" \
  "$OUT/capture-prod3c-raw.json" "$REF3C_SHA" \
  "$OUT/capture-prod3e-raw.json" "$REF3E_SHA" \
  "$OUT/capture-prod3g-raw.json" "$REF3G_SHA"
