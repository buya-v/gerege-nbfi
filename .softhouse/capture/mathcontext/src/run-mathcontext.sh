#!/usr/bin/env bash
#
# T42 -- runnable recipe for the "which MathContext is actually in force" captures.
#
# This script FAILS THE RUN LOUDLY.  Every breach prints "BREACH:" and exits non-zero.
# Breaches it detects:
#
#   1. the pinned Fineract checkout is at the wrong commit
#   2. the pinned Fineract checkout is DIRTY
#   3. the docker image id is not the pinned one
#   4. the seam class under src/ has drifted from the pinned original
#   5. the container exited non-zero
#   6. stderr was non-empty
#   7. stdout did not contain parseable JSON
#   8. the ABSENCE PROBE IS VACUOUS -- MoneyHelper.getMathContext() did NOT throw on a tenant
#      it was never initialised for.  If that ever stops throwing, every "-D" case in the
#      payload proves nothing and the whole run must be rejected.
#   9. any case echoes a threaded MathContext other than the one its id declares
#  10. any case echoes an ambient reading inconsistent with its declared tenant ordinal
#  11. the four CONTROL cases or the CALIBRATION case failed to produce an observation
#  12. the classpath contains an Oracle Database, MySQL or MariaDB driver
#
# PROVING IT IS FAILABLE.  Every expectation is overridable from the environment so the suite
# can be run against a deliberately wrong setting and watched to exit non-zero.  See
# ../NEGATIVE-TESTS.md for the recorded negative runs.
#
#   T42_EXPECT_COMMIT T42_EXPECT_IMAGE T42_EXPECT_SEAM_SHA T42_EXPECT_CANARY_THROWS
#   T42_OUT_PREFIX    output basename, so a negative or determinism run does not overwrite
#                     the recorded capture
#
# CONTAINER DISCIPLINE.  docker run --rm only, mounting ONLY this task's own directory.
# The shared fineract-fineract-1 / fineract-db-1 containers are never started, stopped,
# reconfigured or written to.
#
# PostgreSQL-only rule: this seam reaches no database at all.  Assertion 12 nonetheless proves
# no prohibited driver is even on the classpath.

set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T42_FINERACT_DIR:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

EXPECT_COMMIT="${T42_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T42_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T42_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
EXPECT_CANARY_THROWS="${T42_EXPECT_CANARY_THROWS:-1}"
PREFIX="${T42_OUT_PREFIX:-t42-mathcontext}"

RAW="$CAPDIR/out/$PREFIX-raw.json"
LOG="$CAPDIR/out/$PREFIX-log.txt"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T42 MathContext-in-force capture =="
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
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CaptureMathContext.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" CaptureMathContext
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
EXPECT_CANARY_THROWS="$EXPECT_CANARY_THROWS" python3 - "$JSON" <<'PY' || fail "payload assertions failed"
import json, os, sys

doc = json.load(open(sys.argv[1]))
bad = []

# 8. THE ABSENCE PROBE MUST BE LIVE.
canary = doc.get("ambientCanary", "")
must_throw = os.environ["EXPECT_CANARY_THROWS"] == "1"
if must_throw and not canary.startswith("THREW java.lang.IllegalStateException"):
    bad.append("the ambient-absence probe is VACUOUS: MoneyHelper.getMathContext() on an "
               "uninitialised tenant returned " + repr(canary)
               + " instead of throwing IllegalStateException.  Every ABSENCE case is meaningless.")
if not must_throw and canary.startswith("THREW"):
    bad.append("negative run: the canary DID throw when the run asserted it would not: " + repr(canary))

if doc.get("moneyHelperPrecisionConstant") != 19:
    bad.append("MoneyHelper.PRECISION read from the running oracle is "
               + str(doc.get("moneyHelperPrecisionConstant")) + ", expected 19")

caps = doc.get("captures") or []
if not caps:
    bad.append("payload contains no captures")

MODE_BY_ORDINAL = {0: "UP", 1: "DOWN", 2: "CEILING", 3: "FLOOR", 4: "HALF_UP", 5: "HALF_DOWN", 6: "HALF_EVEN"}

n_absent = 0
for c in caps:
    cid = c.get("id", "?")
    inp = c["inputs"]

    # 9. the threaded context the id declares must be the one the case ran at
    if cid.endswith("-p19") and inp["threadedMathContextPrecision"] != 19:
        bad.append(f"{cid}: declares p19 but ran at {inp['threadedMathContextPrecision']}")
    if cid.endswith("-p12") and inp["threadedMathContextPrecision"] != 12:
        bad.append(f"{cid}: declares p12 but ran at {inp['threadedMathContextPrecision']}")
    if cid.endswith("-p8") and inp["threadedMathContextPrecision"] != 8:
        bad.append(f"{cid}: declares p8 but ran at {inp['threadedMathContextPrecision']}")
    if cid == "T42-CAL" and inp["threadedMathContextPrecision"] != 12:
        bad.append("T42-CAL: calibration must run at threaded precision 12")
    if c["family"] in ("CONTROL",) and (inp["threadedMathContextPrecision"] != 19
                                        or inp["threadedMathContextRoundingMode"] != "HALF_UP"):
        bad.append(f"{cid}: a CONTROL must run at the ratified threaded (19, HALF_UP)")

    # 10. the ambient reading must be consistent with the declared tenant ordinal
    ordinal = inp["tenantRoundingModeOrdinal"]
    ambient = inp["ambientMoneyHelperMathContext"]
    if ordinal is None:
        n_absent += 1
        if not ambient.startswith("THREW java.lang.IllegalStateException"):
            bad.append(f"{cid}: declares AMBIENT ABSENT but the ambient read returned {ambient!r}")
    else:
        expected = f"precision=19 roundingMode={MODE_BY_ORDINAL[ordinal]}"
        if ambient != expected:
            bad.append(f"{cid}: ambient reading is {ambient!r}, expected {expected!r} for ordinal {ordinal}")

    # 11. controls and the calibration must have produced an observation
    if c["family"] in ("CONTROL", "CALIBRATION") and c.get("observed") is None:
        bad.append(f"{cid}: a {c['family']} case produced NO observation: {c.get('error')}")

    if c.get("observed") is not None:
        for p in c["observed"]["periods"]:
            for k, v in p.items():
                if v is None or v == "null":
                    bad.append(f"{cid}: period column {k} is null")

if must_throw and n_absent == 0:
    bad.append("no ABSENCE cases in the payload -- the central experiment did not run")

if bad:
    for b in bad:
        print("BREACH: " + b, file=sys.stderr)
    sys.exit(1)
print(f"  ok  {len(caps)} captures, {n_absent} of them ambient-ABSENT; every case's threaded and "
      f"ambient context matches what its id declares")
PY

echo "== PASS -- capture admissible. payload: $JSON"
