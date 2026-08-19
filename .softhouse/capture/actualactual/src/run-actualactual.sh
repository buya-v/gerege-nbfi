#!/usr/bin/env bash
#
# T48 -- runnable recipe for the ACTUAL/ACTUAL cross-year partial-period captures.
#
# IT IS A PRECONDITION SCRIPT, NOT A WRAPPER.  Any breach prints "BREACH: ..." on stderr and
# exits 1, leaving no half-valid capture behind.  A run that does not print
# "== PASS -- capture admissible" produced nothing admissible.
#
# Breaches detected:
#    1 pinned checkout at the wrong commit        8 a case came back null / errored unexpectedly
#    2 pinned checkout DIRTY                      9 the AMBIENT MoneyHelper context is not (19, HALF_UP)
#    3 docker image id not the pinned one        10 a case ran at a THREADED precision/mode other
#    4 seam class under src/ drifted                than the one its family declares
#    5 container exited non-zero                 11 a negative-test override was left set
#    6 stderr non-empty                          12 classpath carries an Oracle Database /
#    7 stdout carried no parseable JSON             MySQL / MariaDB driver
#   13 a published money value is rendered in scientific notation or as a float literal
#
# PROVED FAILABLE -- see ../NEGATIVE-TESTS.md.
#
# CONTAINER DISCIPLINE.  `docker run --rm` only, mounting ONLY this task's own directory.  The
# shared fineract-fineract-1 / fineract-db-1 containers are never started, stopped,
# reconfigured or written to by this script.
#
# PostgreSQL-only rule: these seams reach no database at all; assertion 12 nonetheless proves
# no prohibited driver is even on the classpath.  "The oracle" here is the Fineract reference
# implementation, never Oracle Database.

set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T48_FINERACT_DIR:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

EXPECT_COMMIT="${T48_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T48_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T48_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
EXPECT_MC="${T48_EXPECT_MC:-precision=19 roundingMode=HALF_UP}"
EXPECT_PRECISION="${T48_EXPECT_PRECISION:-19}"
EXPECT_MODE="${T48_EXPECT_MODE:-HALF_UP}"
EXPECT_TENANT_ORDINAL="${T48_EXPECT_TENANT_ORDINAL:-4}"
JAVA_PROPS="${T48_JAVA_PROPS:-}"
SET="${T48_SET:-seam}"
PREFIX="${T48_OUT_PREFIX:-t48}-$SET"

RAW="$CAPDIR/out/$PREFIX-raw.json"
LOG="$CAPDIR/out/$PREFIX-log.txt"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T48 ACTUAL/ACTUAL partial-period capture, set=$SET =="
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
  -e "T48_JAVA_PROPS=$JAVA_PROPS" -e "T48_SET=$SET" \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CaptureActualActual.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
# shellcheck disable=SC2086
java -Dt48.set="$T48_SET" $T48_JAVA_PROPS -cp "/work/classes:$CP" CaptureActualActual
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

# ---- 8/9/10/11/13. the payload's own testimony -----------------------------------------
EXPECT_MC="$EXPECT_MC" EXPECT_PRECISION="$EXPECT_PRECISION" EXPECT_MODE="$EXPECT_MODE" \
EXPECT_TENANT_ORDINAL="$EXPECT_TENANT_ORDINAL" python3 - "$JSON" <<'PY' || fail "payload assertions failed"
import json, os, re, sys

doc = json.load(open(sys.argv[1]))
bad = []

for k, label in (("negativeTestTenantRoundingModeOrdinalOverride", "tenant rounding"),
                 ("negativeTestMathContextPrecisionOverride", "precision"),
                 ("negativeTestMathContextRoundingModeOverride", "threaded rounding-mode")):
    if doc.get(k) is not None:
        bad.append("negative-test %s override was LEFT SET: %s" % (label, doc[k]))
if doc.get("moneyHelperPrecisionConstant") != 19:
    bad.append("MoneyHelper.PRECISION read from the running oracle is %s, expected 19"
               % doc.get("moneyHelperPrecisionConstant"))

exp_mc = os.environ["EXPECT_MC"]
exp_prec = int(os.environ["EXPECT_PRECISION"])
exp_mode = os.environ["EXPECT_MODE"]
exp_ord = int(os.environ["EXPECT_TENANT_ORDINAL"])

caps = doc.get("captures") or []
if not caps:
    bad.append("payload contains no captures")

# every published money-ish string must be plain: no scientific notation anywhere.
SCI = re.compile(r"^-?\d+(\.\d+)?[eE][-+]?\d+$")
def scan(node, path):
    if isinstance(node, dict):
        for k, v in node.items():
            scan(v, path + "." + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            scan(v, "%s[%d]" % (path, i))
    elif isinstance(node, float):
        bad.append("%s is a JSON FLOAT (%r) -- money and ratios must be exact text" % (path, node))
    elif isinstance(node, str) and SCI.match(node):
        bad.append("%s is in scientific notation (%r)" % (path, node))

errored = []
for c in caps:
    cid = c.get("id", "?")
    fam = c.get("family")
    inp = c["inputs"]
    scan(c.get("observed"), cid)

    if fam == "EXACTNESS-CANARY":
        # a local construction, deliberately not an oracle observation
        continue

    # --- assertion 9: the AMBIENT MoneyHelper context.  NOT the arithmetic on either seam.
    tord = inp.get("tenantRoundingModeOrdinal")
    tprec = inp.get("threadedMathContextPrecision")
    tmode = inp.get("threadedMathContextRoundingMode")
    tstr = inp.get("threadedMathContext")
    if tmode is None or tprec is None or tstr is None:
        bad.append("%s: payload carries no threadedMathContext* object echo" % cid)
        continue
    if tstr != "precision=%s roundingMode=%s" % (tprec, tmode):
        bad.append("%s: mc.toString() %r disagrees with its own getters (%s, %s)"
                   % (cid, tstr, tprec, tmode))
    if inp.get("mathContextPrecision") not in (None, tprec):
        bad.append("%s: intent precision %s != object precision %s"
                   % (cid, inp.get("mathContextPrecision"), tprec))
    if inp.get("mathContextRoundingMode") not in (None, tmode):
        bad.append("%s: intent mode %s != object mode %s"
                   % (cid, inp.get("mathContextRoundingMode"), tmode))
    if not str(inp.get("wiring", "")).startswith("PATH_A"):
        bad.append("%s: wiring field missing or does not name a Path A seam" % cid)

    # --- assertion 10: CALIBRATION families run at the shipped test's settings and say so;
    #     everything else must be at the ratified production threaded context.
    if fam == "CALIBRATION":
        if (tprec, tmode) not in ((12, "HALF_UP"), (12, "HALF_EVEN")):
            bad.append("%s: CALIBRATION ran at (%s, %s); the shipped tests are at "
                       "(12, HALF_UP) [embeddable seam] or (12, HALF_EVEN) [EMICalculator]"
                       % (cid, tprec, tmode))
        expected_ambient_mode = "HALF_UP" if tmode == "HALF_UP" else "HALF_EVEN"
        if tord not in (4, 6):
            bad.append("%s: CALIBRATION tenant rounding ordinal %s; the shipped tests use "
                       "HALF_UP (4) or HALF_EVEN (6)" % (cid, tord))
        if inp.get("ambientMoneyHelperMathContext") != "precision=19 roundingMode=%s" % expected_ambient_mode:
            bad.append("%s: AMBIENT context is %r, expected precision=19 roundingMode=%s"
                       % (cid, inp.get("ambientMoneyHelperMathContext"), expected_ambient_mode))
    else:
        if tprec != exp_prec:
            bad.append("%s: THREADED precision %s, expected %s" % (cid, tprec, exp_prec))
        if tmode != exp_mode:
            bad.append("%s: THREADED rounding mode %s, expected %s" % (cid, tmode, exp_mode))
        if inp.get("ambientMoneyHelperMathContext") != exp_mc:
            bad.append("%s: AMBIENT MoneyHelper MathContext is %r, expected %r"
                       % (cid, inp.get("ambientMoneyHelperMathContext"), exp_mc))
        if tord != exp_ord:
            bad.append("%s: tenant rounding ordinal %s, expected %s" % (cid, tord, exp_ord))

    # --- assertion 8: observations
    if c.get("observed") is None:
        errored.append("%s: %s" % (cid, c.get("error")))
        bad.append("%s: observation is NULL (%s)" % (cid, c.get("error")))

if bad:
    for b in bad:
        print("BREACH: " + b, file=sys.stderr)
    sys.exit(1)
print("  ok  %d captures: threaded MathContext asserted OFF THE OBJECT; no JSON float, "
      "no scientific notation anywhere in the observations" % len(caps))
PY

# ---- the oracle's SLF4J rounding-mode lines: ONE AMBIENT witness, so labelled -----------
# MoneyHelper.java:59-64 logs the same local it writes into roundingModeCache, which :74-82
# reads back.  That is ONE witness counted once, never two independent ones (T44 F39-2).
MODE_LINES="$(grep -c "Initialized rounding mode for tenant" "$LOG" || true)"
[ "$MODE_LINES" != "0" ] || fail "the oracle logged NO rounding-mode line"
ok "AMBIENT witness (one, not two): $MODE_LINES oracle rounding-mode log lines"
grep "Initialized rounding mode for tenant" "$LOG" | sed 's/^/      /' | head -30

echo "== PASS -- capture admissible. payload: $JSON"
