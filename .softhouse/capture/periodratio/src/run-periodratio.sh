#!/usr/bin/env bash
#
# T39 -- runnable recipe for the periodRatio observation captures.
#
# This script FAILS THE RUN LOUDLY.  It does not warn, it does not degrade, and it never
# leaves a half-valid capture behind: every breach prints "BREACH:" with the reason and
# exits non-zero.  Breaches it detects:
#
#   1. the pinned Fineract checkout is at the wrong commit
#   2. the pinned Fineract checkout is DIRTY
#   3. the docker image id is not the pinned one
#   4. the seam class under src/ has drifted from the pinned original
#   5. the container exited non-zero
#   6. stderr was non-empty
#   7. stdout did not contain parseable JSON
#   8. any case came back with a null observation or an error
#   9. the EFFECTIVE MathContext, on the oracle's own testimony, is not (19, HALF_UP)
#  10. any case ran at a threaded precision / rounding mode / tenant ordinal other than the
#      ratified one (the labelled calibration T39-CAL is the sole, explicitly named exception)
#  11. a negative-test override was left set
#  12. the classpath contains an Oracle Database, MySQL or MariaDB driver
#
# PROVING IT IS FAILABLE.  Every expectation below is overridable from the environment,
# and the harness accepts three negative-test system properties, so the suite can be run
# against a deliberately wrong setting and watched to exit non-zero.  See
# ../NEGATIVE-TESTS.md for the recorded negative runs and their output.
#
#   T39_EXPECT_COMMIT T39_EXPECT_IMAGE T39_EXPECT_SEAM_SHA T39_EXPECT_MC
#   T39_EXPECT_PRECISION T39_EXPECT_MODE T39_EXPECT_TENANT_ORDINAL
#   T39_JAVA_PROPS        extra -D flags handed to the JVM (negative tests only)
#   T39_OUT_PREFIX        output basename, so a negative or determinism run does not
#                         overwrite the recorded capture
#
# CONTAINER DISCIPLINE.  docker run --rm only, mounting ONLY this task's own directory.
# The shared fineract-fineract-1 / fineract-db-1 containers are never started, stopped,
# reconfigured or written to -- another worker owns them.
#
# PostgreSQL-only rule: this seam reaches no database at all, so no driver is selected here;
# assertion 12 nonetheless proves no prohibited driver is even on the classpath.

set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T39_FINERACT_DIR:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

EXPECT_COMMIT="${T39_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T39_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T39_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
EXPECT_MC="${T39_EXPECT_MC:-precision=19 roundingMode=HALF_UP}"
EXPECT_PRECISION="${T39_EXPECT_PRECISION:-19}"
EXPECT_MODE="${T39_EXPECT_MODE:-HALF_UP}"
EXPECT_TENANT_ORDINAL="${T39_EXPECT_TENANT_ORDINAL:-4}"
JAVA_PROPS="${T39_JAVA_PROPS:-}"
PREFIX="${T39_OUT_PREFIX:-t39-periodratio}"

RAW="$CAPDIR/out/$PREFIX-raw.json"
LOG="$CAPDIR/out/$PREFIX-log.txt"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T39 periodRatio capture =="
mkdir -p "$CAPDIR/out"

# ---- 1/2. the pin ---------------------------------------------------------------------
HEAD_SHA="$(git -C "$FINERACT" rev-parse HEAD 2>/dev/null)" || fail "cannot read the pinned checkout at $FINERACT"
[ "$HEAD_SHA" = "$EXPECT_COMMIT" ] || fail "pinned checkout is at $HEAD_SHA, expected $EXPECT_COMMIT"
ok "pinned commit $HEAD_SHA"
DIRT="$(git -C "$FINERACT" status --porcelain)"
[ -z "$DIRT" ] || fail "pinned checkout is DIRTY:
$DIRT"
ok "pinned checkout clean"

# ---- 3. the image ---------------------------------------------------------------------
IMAGE_ID="$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)" || fail "image fineract:latest not present"
[ "$IMAGE_ID" = "$EXPECT_IMAGE" ] || fail "image id is $IMAGE_ID, expected $EXPECT_IMAGE"
ok "image $IMAGE_ID"

# ---- 4. the seam class ----------------------------------------------------------------
diff "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$FINERACT/$SEAM_REL" \
  || fail "seam class under src/ has DRIFTED from the pinned original -- the run would not have executed the oracle's code"
SEAM_SHA="$(shasum -a 256 "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" | awk '{print $1}')"
[ "$SEAM_SHA" = "$EXPECT_SEAM_SHA" ] || fail "seam class sha256 is $SEAM_SHA, expected $EXPECT_SEAM_SHA"
ok "seam class byte-identical to the pin, sha256 $SEAM_SHA"

# ---- oracle identity, read FROM the oracle --------------------------------------------
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
CP_COUNT="$(wc -l < "$CPLIST" | tr -d ' ')"
CP_DIGEST="$(shasum -a 256 "$CPLIST" | awk '{print $1}')"
ok "classpath: $CP_COUNT entries, digest $CP_DIGEST"

# ---- 12. prohibited database drivers ---------------------------------------------------
BAD="$(grep -Eic 'ojdbc|oracle|mysql|mariadb' "$CPLIST" || true)"
[ "$BAD" = "0" ] || fail "classpath contains $BAD prohibited Oracle Database / MySQL / MariaDB entries:
$(grep -Ei 'ojdbc|oracle|mysql|mariadb' "$CPLIST")"
ok "classpath has ZERO Oracle Database / MySQL / MariaDB entries"

# ---- the capture ------------------------------------------------------------------------
docker run --rm --user 0 --entrypoint sh \
  -e "T39_JAVA_PROPS=$JAVA_PROPS" \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CapturePeriodRatio.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
# shellcheck disable=SC2086
java $T39_JAVA_PROPS -cp "/work/classes:$CP" CapturePeriodRatio
' > "$RAW" 2> "$ERR"
RC=$?

# ---- 5. exit code -----------------------------------------------------------------------
[ "$RC" = "0" ] || fail "capture container exited $RC (stderr in $ERR)"
ok "container exit 0"

# ---- 6. stderr --------------------------------------------------------------------------
[ ! -s "$ERR" ] || fail "stderr was NON-EMPTY:
$(head -40 "$ERR")"
ok "stderr empty"

# ---- 7. split the oracle's own log off the front, and KEEP it ---------------------------
FIRST_BRACE="$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)"
[ -n "$FIRST_BRACE" ] || fail "stdout contains no JSON payload (see $RAW)"
if [ "$FIRST_BRACE" -gt 1 ]; then
  head -n "$((FIRST_BRACE - 1))" "$RAW" > "$LOG"
else
  : > "$LOG"
fi
tail -n "+$FIRST_BRACE" "$RAW" > "$JSON"
python3 -m json.tool "$JSON" > /dev/null || fail "JSON payload does not parse ($JSON)"
ok "JSON payload parses; $(wc -l < "$LOG" | tr -d ' ') oracle log lines split into $(basename "$LOG")"

# ---- 8/9/10/11. the payload's own testimony --------------------------------------------
EXPECT_MC="$EXPECT_MC" EXPECT_PRECISION="$EXPECT_PRECISION" EXPECT_MODE="$EXPECT_MODE" \
EXPECT_TENANT_ORDINAL="$EXPECT_TENANT_ORDINAL" python3 - "$JSON" <<'PY' || fail "payload assertions failed"
import json, os, sys

doc = json.load(open(sys.argv[1]))
bad = []

if doc.get("negativeTestTenantRoundingModeOrdinalOverride") is not None:
    bad.append("negative-test tenant rounding override was LEFT SET: "
               + str(doc["negativeTestTenantRoundingModeOrdinalOverride"]))
if doc.get("negativeTestMathContextPrecisionOverride") is not None:
    bad.append("negative-test precision override was LEFT SET: "
               + str(doc["negativeTestMathContextPrecisionOverride"]))
if doc.get("negativeTestMathContextRoundingModeOverride") is not None:
    bad.append("negative-test threaded rounding-mode override was LEFT SET: "
               + str(doc["negativeTestMathContextRoundingModeOverride"]))
if doc.get("moneyHelperPrecisionConstant") != 19:
    bad.append("MoneyHelper.PRECISION read from the running oracle is "
               + str(doc.get("moneyHelperPrecisionConstant")) + ", expected 19")

exp_mc = os.environ["EXPECT_MC"]
exp_prec = int(os.environ["EXPECT_PRECISION"])
exp_mode = os.environ["EXPECT_MODE"]
exp_ord = int(os.environ["EXPECT_TENANT_ORDINAL"])

caps = doc.get("captures") or []
if not caps:
    bad.append("payload contains no captures")

for c in caps:
    cid = c.get("id", "?")
    if c.get("observed") is None:
        bad.append(f"{cid}: observation is NULL ({c.get('error')})")
        continue
    if c.get("error"):
        bad.append(f"{cid}: error {c['error']}")
    inp = c["inputs"]
    # the oracle's own testimony about the ambient MoneyHelper context
    if inp.get("ambientMoneyHelperMathContext") != exp_mc:
        bad.append(f"{cid}: effective MoneyHelper MathContext is "
                   f"{inp.get('ambientMoneyHelperMathContext')!r}, expected {exp_mc!r}")
    if inp.get("tenantRoundingModeOrdinal") != exp_ord:
        bad.append(f"{cid}: tenant rounding ordinal {inp.get('tenantRoundingModeOrdinal')}, "
                   f"expected {exp_ord}")
    if inp.get("mathContextRoundingMode") != exp_mode:
        bad.append(f"{cid}: threaded rounding mode {inp.get('mathContextRoundingMode')}, "
                   f"expected {exp_mode}")
    # the labelled calibration is the SOLE exception, and only on threaded precision
    if cid == "T39-CAL":
        if inp.get("mathContextPrecision") != 12:
            bad.append("T39-CAL: calibration must run at threaded precision 12, got "
                       + str(inp.get("mathContextPrecision")))
    elif inp.get("mathContextPrecision") != exp_prec:
        bad.append(f"{cid}: threaded precision {inp.get('mathContextPrecision')}, expected {exp_prec}")
    for p in c["observed"]["periods"]:
        for k, v in p.items():
            if v is None or v == "null":
                bad.append(f"{cid}: period column {k} is null")

if bad:
    for b in bad:
        print("BREACH: " + b, file=sys.stderr)
    sys.exit(1)
print(f"  ok  {len(caps)} captures: all observed, all at the asserted MathContext")
PY

# ---- the oracle's SLF4J rounding-mode lines, a second independent witness ---------------
MODE_LINES="$(grep -c "Initialized rounding mode for tenant" "$LOG" || true)"
WRONG_MODE="$(grep "Initialized rounding mode for tenant" "$LOG" | grep -vc ": $EXPECT_MODE" || true)"
[ "$MODE_LINES" != "0" ] || fail "the oracle logged NO rounding-mode line -- second witness missing"
[ "$WRONG_MODE" = "0" ] || fail "$WRONG_MODE of $MODE_LINES oracle rounding-mode log lines are not $EXPECT_MODE"
ok "oracle's own log: $MODE_LINES of $MODE_LINES rounding-mode lines are $EXPECT_MODE"

echo "== PASS -- capture admissible. payload: $JSON"
