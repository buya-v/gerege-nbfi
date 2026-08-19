#!/usr/bin/env bash
#
# T50 TIER 1 -- separate the AMBIENT rounding mode from the THREADED one, in process.
#
# This is a PRECONDITION SCRIPT, not a wrapper.  Any breach prints `BREACH: ...` and exits 1.
# A run that does not print `== PASS -- capture admissible` produced NOTHING admissible.
#
# Throwaway container only (`docker run --rm`).  The running fineract-fineract-1 / fineract-db-1
# are NOT started, stopped, restarted, re-tenanted, reconfigured, read or written; no HTTP request
# is made to localhost:8443 and no PostgreSQL connection is opened.  This seam reaches no database.
#
# Every path is derived from THIS SCRIPT'S OWN LOCATION (T44 finding A-7), so the recipe survives
# the worktree being pruned or moved.
set -uo pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T50_FINERACT:-/Users/buv/fineract}"
EXPECT_COMMIT="${T50_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T50_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"

PREFIX="${T50_OUT_PREFIX:-t50-tier1}"
RAW="$CAPDIR/out/$PREFIX-raw.json"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
LOG="$CAPDIR/out/$PREFIX-log.txt"
IDENT="$CAPDIR/out/$PREFIX-oracle-identity.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"
CLASSDIGESTS="$CAPDIR/out/$PREFIX-class-digests.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible and must not be published." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T50 Tier 1: ambient vs threaded RoundingMode, in process, throwaway container =="
mkdir -p "$CAPDIR/out"

# ---- 1. the pin ---------------------------------------------------------------------------
HEAD_SHA="$(git -C "$FINERACT" rev-parse HEAD 2>/dev/null)" || fail "cannot read the pinned checkout at $FINERACT"
[ "$HEAD_SHA" = "$EXPECT_COMMIT" ] || fail "pinned checkout is at $HEAD_SHA, expected $EXPECT_COMMIT"
ok "pinned commit $HEAD_SHA"
DIRT="$(git -C "$FINERACT" status --porcelain)"
[ -z "$DIRT" ] || fail "pinned checkout is DIRTY:
$DIRT"
ok "pinned checkout clean"

# ---- 2. the image -------------------------------------------------------------------------
IMAGE_ID="$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)" || fail "image fineract:latest not present"
[ "$IMAGE_ID" = "$EXPECT_IMAGE" ] || fail "image id is $IMAGE_ID, expected $EXPECT_IMAGE"
ok "image $IMAGE_ID"

# ---- 3. the harness compiles only ITSELF; everything else comes from the jar ---------------
# T42 had to copy one Fineract source file (the embeddable seam is not bundled).  T50 copies
# NONE: Money, MoneyHelper, MathUtil and CurrencyData all live in the shipped jar, so the bytes
# executed are the oracle's own.  Assert that no Fineract source is compiled alongside.
grep -q "package org.apache.fineract" "$CAPDIR/src/CaptureT50Ambient.java" \
  && fail "harness declares a Fineract package -- it must be a plain top-level class"
ok "harness compiles no Fineract source; every probed class is loaded from the jar"

# ---- 4. oracle identity, read FROM the oracle ----------------------------------------------
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
echo "== probed class digests"
for c in \
  org/apache/fineract/organisation/monetary/domain/Money.class \
  org/apache/fineract/organisation/monetary/domain/MoneyHelper.class \
  org/apache/fineract/infrastructure/core/service/MathUtil.class \
  org/apache/fineract/organisation/monetary/data/CurrencyData.class \
  org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.class \
  org/apache/fineract/portfolio/loanaccount/loanschedule/domain/PrincipalInterest.class \
  org/apache/fineract/portfolio/loanaccount/domain/LoanCharge.class \
  org/apache/fineract/portfolio/charge/domain/ChargeCalculationType.class ; do
  if [ -f "/work/jar/BOOT-INF/classes/$c" ]; then sha256sum "/work/jar/BOOT-INF/classes/$c"; else echo "MISSING $c"; fi
done
echo "== classpath entries"
ls /work/jar/BOOT-INF/lib/*.jar | sed "s#.*/##" | sort
' > "$IDENT" 2>&1 || fail "oracle-identity container exited non-zero (see $IDENT)"
ok "oracle identity captured into $(basename "$IDENT")"

sed -n '/== probed class digests/,/== classpath entries/p' "$IDENT" | sed '1d;$d' > "$CLASSDIGESTS"
grep -q "MISSING" "$CLASSDIGESTS" && fail "a probed class is NOT in the oracle jar:
$(grep MISSING "$CLASSDIGESTS")"
ok "all 8 probed classes present in the jar; digests in $(basename "$CLASSDIGESTS")"

sed -n '/== classpath entries/,$p' "$IDENT" | tail -n +2 > "$CPLIST"
ok "classpath: $(wc -l < "$CPLIST" | tr -d ' ') entries, digest $(shasum -a 256 "$CPLIST" | awk '{print $1}')"

BAD="$(grep -Eic 'ojdbc|oracle|mysql|mariadb' "$CPLIST" || true)"
[ "$BAD" = "0" ] || fail "classpath contains $BAD prohibited Oracle Database / MySQL / MariaDB entries"
ok "classpath has ZERO Oracle Database / MySQL / MariaDB entries"

# ---- 5. the capture -------------------------------------------------------------------------
docker run --rm --user 0 --entrypoint sh \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/CaptureT50Ambient.java
java -cp "/work/classes:$CP" CaptureT50Ambient
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

# ---- 6. THE ADMISSIBILITY ASSERTIONS -------------------------------------------------------
# Delegated to a python checker so every assertion is readable and each prints its cell counts.
python3 "$CAPDIR/analysis/t50_assert_tier1.py" "$JSON"
ARC=$?
if [ "$ARC" != "0" ]; then
  mv "$JSON" "$JSON.REJECTED"
  fail "admissibility assertions FAILED; payload moved to $JSON.REJECTED and NOT published"
fi

echo "== PASS -- capture admissible.  payload: $JSON"
