#!/usr/bin/env bash
#
# T46 -- run the M-5 RE-EMISSION (CaptureMathContext3) and PROVE, leaf by leaf, that every
# previously published value in out/t42-mathcontext.json is identical.
#
# `patterns.md`: "Re-emit a capture input-for-input before you add cases to it."  This run adds
# NO cases and NO shapes; it adds four attestation keys per case, read off the MathContext
# object handed to the generator, which T42's own ratified attestation rule 2 requires and
# capture 1 did not do (audit finding M-5).
#
# THE ADMISSIBILITY BAR, enforced below and non-negotiable:
#   * every case id in the committed payload is present in the re-emission, and vice versa;
#   * for every case, every key that the committed payload publishes has a BYTE-IDENTICAL
#     value in the re-emission -- inputs, observed, error and stackTrace alike;
#   * the ONLY difference permitted anywhere is the four ADDED keys and the `harness` label;
#   * the four added keys must AGREE with the two they supplement (object vs intent), which is
#     itself the M-5 result: if they ever disagreed, capture 1 would be mis-attested in value
#     and not merely in wording.
# If any of those fails the payload is moved aside and the run exits non-zero.  Nothing is
# published from a run that cannot prove identity.
#
# Throwaway container only (`docker run --rm`).  The running fineract-fineract-1 /
# fineract-db-1 are NOT started, stopped, restarted, re-tenanted, reconfigured or written to.
set -uo pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T42_FINERACT:-/Users/buv/fineract}"
EXPECT_COMMIT="${T42_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T42_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T42_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

PREFIX="t46-mathcontext3"
RAW="$CAPDIR/out/$PREFIX-raw.json"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
LOG="$CAPDIR/out/$PREFIX-log.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"
COMMITTED="$CAPDIR/out/t42-mathcontext.json"
PROOF="$CAPDIR/analysis/t46-m5-identity-proof.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- re-emission is not admissible and must not be published." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T46 re-emission of T42 capture 1, with the threaded MathContext echoed off the object =="
mkdir -p "$CAPDIR/out"

# ---- the pin ----------------------------------------------------------------------------
HEAD_SHA="$(git -C "$FINERACT" rev-parse HEAD 2>/dev/null)" || fail "cannot read the pinned checkout at $FINERACT"
[ "$HEAD_SHA" = "$EXPECT_COMMIT" ] || fail "pinned checkout is at $HEAD_SHA, expected $EXPECT_COMMIT"
ok "pinned commit $HEAD_SHA"
DIRT="$(git -C "$FINERACT" status --porcelain)"
[ -z "$DIRT" ] || fail "pinned checkout is DIRTY:
$DIRT"
ok "pinned checkout clean"

# ---- the image --------------------------------------------------------------------------
IMAGE_ID="$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)" || fail "image fineract:latest not present"
[ "$IMAGE_ID" = "$EXPECT_IMAGE" ] || fail "image id is $IMAGE_ID, expected $EXPECT_IMAGE"
ok "image $IMAGE_ID"

# ---- the seam class ---------------------------------------------------------------------
diff "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$FINERACT/$SEAM_REL" \
  || fail "seam class under src/ has DRIFTED from the pinned original"
SEAM_SHA="$(shasum -a 256 "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" | awk '{print $1}')"
[ "$SEAM_SHA" = "$EXPECT_SEAM_SHA" ] || fail "seam class sha256 is $SEAM_SHA, expected $EXPECT_SEAM_SHA"
ok "seam class byte-identical to the pin, sha256 $SEAM_SHA"

# ---- the harness is a GENERATED copy: regenerate and require no drift --------------------
cp "$CAPDIR/src/CaptureMathContext3.java" "$CAPDIR/out/.t46-capture3-before" 2>/dev/null
python3 "$CAPDIR/analysis/t46_make_capture3.py" >/dev/null || fail "cannot regenerate CaptureMathContext3.java"
if [ -f "$CAPDIR/out/.t46-capture3-before" ]; then
  diff "$CAPDIR/out/.t46-capture3-before" "$CAPDIR/src/CaptureMathContext3.java" \
    || fail "CaptureMathContext3.java is not what t46_make_capture3.py generates -- it was hand-edited"
  rm -f "$CAPDIR/out/.t46-capture3-before"
fi
ok "CaptureMathContext3.java regenerates identically from CaptureMathContext.java"

# ---- oracle identity, read FROM the oracle ----------------------------------------------
docker run --rm --user 0 --entrypoint sh \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
echo "== jar sha256"
sha256sum /app/fineract-provider.jar
echo "== java -version"
java -version 2>&1
echo "== jar git.properties"
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
find /work/jar -name git.properties | head -1 | xargs cat 2>/dev/null || echo "NO git.properties"
echo "== classpath entries"
ls /work/jar/BOOT-INF/lib/*.jar | sed "s#.*/##" | sort
' > "$IDENT" 2>&1 || fail "oracle-identity container exited non-zero (see $IDENT)"
ok "oracle identity captured into $(basename "$IDENT")"

sed -n '/== classpath entries/,$p' "$IDENT" | tail -n +2 > "$CPLIST"
ok "classpath: $(wc -l < "$CPLIST" | tr -d ' ') entries, digest $(shasum -a 256 "$CPLIST" | awk '{print $1}')"

BAD="$(grep -Eic 'ojdbc|oracle|mysql|mariadb' "$CPLIST" || true)"
[ "$BAD" = "0" ] || fail "classpath contains $BAD prohibited Oracle Database / MySQL / MariaDB entries"
ok "classpath has ZERO Oracle Database / MySQL / MariaDB entries"

# ---- the capture -------------------------------------------------------------------------
docker run --rm --user 0 --entrypoint sh \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CaptureMathContext3.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" CaptureMathContext3
' > "$RAW" 2> "$ERR"
RC=$?
[ "$RC" = "0" ] || fail "capture container exited $RC (stderr in $ERR)"
ok "container exit 0"
[ ! -s "$ERR" ] || fail "stderr was NON-EMPTY:
$(head -40 "$ERR")"
ok "stderr empty"

FIRST_BRACE="$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)"
[ -n "$FIRST_BRACE" ] || fail "stdout contains no JSON payload (see $RAW)"
if [ "$FIRST_BRACE" -gt 1 ]; then
  head -n "$((FIRST_BRACE - 1))" "$RAW" > "$LOG"
else
  : > "$LOG"
fi
tail -n "+$FIRST_BRACE" "$RAW" > "$JSON"
python3 -m json.tool "$JSON" > /dev/null || fail "JSON payload does not parse ($JSON)"
ok "JSON payload parses"

# ---- THE IDENTITY PROOF ------------------------------------------------------------------
python3 "$CAPDIR/analysis/t46_m5_identity.py" "$COMMITTED" "$JSON" | tee "$PROOF"
IRC="${PIPESTATUS[0]}"
if [ "$IRC" != "0" ]; then
  mv "$JSON" "$JSON.REJECTED"
  fail "the re-emission does NOT reproduce every previously published value; payload moved to $JSON.REJECTED and NOT published"
fi
ok "identity proof written to $PROOF"

echo "== PASS -- re-emission admissible.  payload: $JSON"
