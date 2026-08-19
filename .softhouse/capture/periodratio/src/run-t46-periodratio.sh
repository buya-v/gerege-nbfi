#!/usr/bin/env bash
#
# T46 -- runnable recipe for the corrections pass over the T39 periodRatio capture set.
#
# Same failure discipline as T39's run-periodratio.sh, with three changes made because of
# T44's findings:
#
#   F39-3  assertion 10 now compares the THREADED MathContext read OFF THE OBJECT handed to
#          generate() -- `threadedMathContextPrecision` / `threadedMathContextRoundingMode`,
#          emitted from mc.getPrecision() / mc.getRoundingMode() -- not the case record's
#          intent fields.  The intent fields are still emitted and still asserted, so a drift
#          between intent and object would be caught as a breach too.
#   F39-3  assertion 9's breach text says AMBIENT, never "effective".  The ambient MoneyHelper
#          context is not the arithmetic on Path A.
#   F39-2  the oracle's SLF4J rounding-mode lines are recorded as ONE AMBIENT WITNESS, not as
#          a second independent one: MoneyHelper.java:59-64 emits that log line from the same
#          local it writes into roundingModeCache, which :74-82 then reads back.  The
#          behavioural evidence about the arithmetic is the THREADED negative leg (N7-style),
#          not this log.
#
# Breaches detected (exit 1, "BREACH:" on stderr, no half-valid capture left behind):
#   1 pinned checkout at the wrong commit          7 stdout carried no parseable JSON
#   2 pinned checkout DIRTY                        8 a case came back null / errored unexpectedly
#   3 docker image id not the pinned one           9 the AMBIENT MoneyHelper context is not (19, HALF_UP)
#   4 seam class under src/ drifted               10 a case ran at a THREADED precision/mode other than ratified
#   5 container exited non-zero                   11 a negative-test override was left set
#   6 stderr non-empty                            12 classpath carries an Oracle Database / MySQL / MariaDB driver
#
# The `arms` set is allowed to contain cases that THROW -- that is the observation being
# taken (calculateRateFactorPerPeriodBasedOnRepaymentFrequency has no YEARS arm and throws at
# ProgressiveEMICalculator.java:1609).  Set T46_ALLOW_ERRORS=1 for that pass; the ids that
# errored are printed, so a silently-empty pass is still a breach.
#
# CONTAINER DISCIPLINE.  docker run --rm only, mounting ONLY this task's own directory.  The
# shared fineract-fineract-1 / fineract-db-1 containers are never started, stopped,
# reconfigured or written to.
#
# PostgreSQL-only rule: this seam reaches no database at all; assertion 12 nonetheless proves
# no prohibited driver is even on the classpath.

set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T46_FINERACT_DIR:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

EXPECT_COMMIT="${T46_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T46_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T46_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
EXPECT_MC="${T46_EXPECT_MC:-precision=19 roundingMode=HALF_UP}"
EXPECT_PRECISION="${T46_EXPECT_PRECISION:-19}"
EXPECT_MODE="${T46_EXPECT_MODE:-HALF_UP}"
EXPECT_TENANT_ORDINAL="${T46_EXPECT_TENANT_ORDINAL:-4}"
JAVA_PROPS="${T46_JAVA_PROPS:-}"
SET="${T46_SET:-reemit}"
ALLOW_ERRORS="${T46_ALLOW_ERRORS:-0}"
PREFIX="${T46_OUT_PREFIX:-t46-periodratio-$SET}"

RAW="$CAPDIR/out/$PREFIX-raw.json"
LOG="$CAPDIR/out/$PREFIX-log.txt"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T46 periodRatio corrections capture, set=$SET =="
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
  || fail "seam class under src/ has DRIFTED from the pinned original"
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
  -e "T46_JAVA_PROPS=$JAVA_PROPS" -e "T46_SET=$SET" \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CapturePeriodRatio2.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
# shellcheck disable=SC2086
java -Dt46.set="$T46_SET" $T46_JAVA_PROPS -cp "/work/classes:$CP" CapturePeriodRatio2
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
ok "JSON payload parses; $(wc -l < "$LOG" | tr -d ' ') oracle log lines split into $(basename "$LOG")"

# ---- 8/9/10/11. the payload's own testimony --------------------------------------------
EXPECT_MC="$EXPECT_MC" EXPECT_PRECISION="$EXPECT_PRECISION" EXPECT_MODE="$EXPECT_MODE" \
EXPECT_TENANT_ORDINAL="$EXPECT_TENANT_ORDINAL" ALLOW_ERRORS="$ALLOW_ERRORS" python3 - "$JSON" <<'PY' || fail "payload assertions failed"
import json, os, sys

doc = json.load(open(sys.argv[1]))
bad = []
allow_errors = os.environ.get("ALLOW_ERRORS") == "1"

for k, label in (("negativeTestTenantRoundingModeOrdinalOverride", "tenant rounding"),
                 ("negativeTestMathContextPrecisionOverride", "precision"),
                 ("negativeTestMathContextRoundingModeOverride", "threaded rounding-mode")):
    if doc.get(k) is not None:
        bad.append(f"negative-test {label} override was LEFT SET: {doc[k]}")
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

errored = []
for c in caps:
    cid = c.get("id", "?")
    inp = c["inputs"]

    # --- assertion 9: the AMBIENT MoneyHelper context.  NOT the arithmetic on Path A.
    if inp.get("ambientMoneyHelperMathContext") != exp_mc:
        bad.append(f"{cid}: AMBIENT MoneyHelper MathContext is "
                   f"{inp.get('ambientMoneyHelperMathContext')!r}, expected {exp_mc!r}")
    if inp.get("tenantRoundingModeOrdinal") != exp_ord:
        bad.append(f"{cid}: tenant rounding ordinal {inp.get('tenantRoundingModeOrdinal')}, "
                   f"expected {exp_ord}")

    # --- assertion 10: the THREADED MathContext, READ OFF THE OBJECT (T44 F39-3).
    tmode = inp.get("threadedMathContextRoundingMode")
    tprec = inp.get("threadedMathContextPrecision")
    tstr = inp.get("threadedMathContext")
    if tmode is None or tprec is None or tstr is None:
        bad.append(f"{cid}: payload carries no threadedMathContext* object echo")
        continue
    if tstr != f"precision={tprec} roundingMode={tmode}":
        bad.append(f"{cid}: mc.toString() {tstr!r} disagrees with its own getters "
                   f"({tprec}, {tmode})")
    if tmode != exp_mode:
        bad.append(f"{cid}: THREADED rounding mode {tmode}, expected {exp_mode}")
    if cid == "T39-CAL":
        if tprec != 12:
            bad.append("T39-CAL: calibration must run at threaded precision 12, got " + str(tprec))
    elif tprec != exp_prec:
        bad.append(f"{cid}: THREADED precision {tprec}, expected {exp_prec}")
    # intent must not have drifted from the object
    if inp.get("mathContextPrecision") != tprec:
        bad.append(f"{cid}: intent precision {inp.get('mathContextPrecision')} != object precision {tprec}")
    if inp.get("mathContextRoundingMode") != tmode:
        bad.append(f"{cid}: intent mode {inp.get('mathContextRoundingMode')} != object mode {tmode}")
    if not str(inp.get("wiring", "")).startswith("PATH_A"):
        bad.append(f"{cid}: wiring field missing or not PATH_A")

    # --- assertion 8: observations
    if c.get("observed") is None:
        errored.append(f"{cid}: {c.get('error')}")
        if not allow_errors:
            bad.append(f"{cid}: observation is NULL ({c.get('error')})")
        continue
    for p in c["observed"]["periods"]:
        for k, v in p.items():
            if v is None or v == "null":
                bad.append(f"{cid}: period column {k} is null")

if allow_errors and len(errored) == len(caps):
    bad.append("EVERY case errored -- this pass observed nothing")

if bad:
    for b in bad:
        print("BREACH: " + b, file=sys.stderr)
    sys.exit(1)
print(f"  ok  {len(caps)} captures: threaded MathContext asserted OFF THE OBJECT; "
      f"{len(caps) - len(errored)} generated, {len(errored)} threw")
for e in errored:
    print("  observed THROW  " + e)
PY

# ---- the oracle's SLF4J rounding-mode lines: ONE AMBIENT witness, so labelled -----------
MODE_LINES="$(grep -c "Initialized rounding mode for tenant" "$LOG" || true)"
WRONG_MODE="$(grep "Initialized rounding mode for tenant" "$LOG" | grep -vc ": $EXPECT_MODE" || true)"
[ "$MODE_LINES" != "0" ] || fail "the oracle logged NO rounding-mode line"
[ "$WRONG_MODE" = "0" ] || fail "$WRONG_MODE of $MODE_LINES oracle rounding-mode log lines are not $EXPECT_MODE"
ok "AMBIENT witness (one, not two -- MoneyHelper.java:59-64 logs the same local it caches):"
ok "  oracle log: $MODE_LINES of $MODE_LINES rounding-mode lines are $EXPECT_MODE"

echo "== PASS -- capture admissible. payload: $JSON"
