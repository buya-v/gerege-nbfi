#!/bin/sh
# =============================================================================================
# EXECUTABLE Path B capture recipe — running Fineract server over PostgreSQL.
#
# Applies the T22 audit P0 list (.softhouse/reviews/T22-pathb-capture-audit.md §10):
#   P0-4  every precondition FAILS THE RUN (exit non-zero); rounding-mode and timezone are asserted
#   P0-5  no shell glob in `curl -o` — filenames are written out — and the HTTP status is captured
#   P0-6  captures run on the `gerege` tenant (Asia/Ulaanbaatar, rounding-mode 4 = HALF_UP), never
#         on `default` (Asia/Kolkata, rounding-mode 6 = HALF_EVEN)
#   P0-3  a machine-readable attestation sidecar is written next to every capture
#
# Prove the preconditions can fail:
#     sh .softhouse/capture/pathb/capture.sh --selftest
#
# Usage:
#     sh .softhouse/capture/pathb/capture.sh [--tenant gerege] [--outdir <dir>]
#
# This script OBSERVES. It records what the server returned and what the environment was when it
# returned it. It never synthesises a value.
# =============================================================================================
set -u

EXPECT_IMAGE_DIGEST='sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'
EXPECT_ORACLE_COMMIT='426a23544e8426a38ae43ae404670a0a7e85b9eb'
# Ratified tenant parameters (CLAUDE.md): rounding mode HALF_UP == RoundingMode ordinal 4.
EXPECT_ROUNDING_MODE='4'
# CLAUDE.md: two time zones, no DST. Nothing else is acceptable for a Gerege capture tenant.
ALLOWED_TIMEZONES='Asia/Ulaanbaatar Asia/Hovd'

PB=$(cd "$(dirname "$0")" && pwd)
TENANT="${TENANT:-gerege}"
OUTDIR="${OUTDIR:-$PB/out}"
APP_CONTAINER="${APP_CONTAINER:-fineract-fineract-1}"
DB_CONTAINER="${DB_CONTAINER:-fineract-db-1}"
DB_USER="${DB_USER:-root}"
BASE="${BASE:-https://localhost:8443/fineract-provider/api/v1}"
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='   # mifos:password, stock demo credentials
CT='Content-Type: application/json'
SELFTEST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --tenant) TENANT="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --selftest) SELFTEST=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done

TENANT_HDR="Fineract-Platform-TenantId: $TENANT"
TENANT_DB="fineract_$TENANT"

fail() { echo "PRECONDITION FAILED: $*" >&2; exit 1; }
ok()   { echo "  ok   $*"; }

# CAP_SELFTEST_BREAK exists only to prove each precondition can fail; --selftest sets it.
case "${CAP_SELFTEST_BREAK:-}" in
  image)    EXPECT_IMAGE_DIGEST='sha256:0000000000000000000000000000000000000000000000000000000000000000' ;;
  commit)   EXPECT_ORACLE_COMMIT='0000000000000000000000000000000000000000' ;;
  rounding) EXPECT_ROUNDING_MODE='999' ;;
  timezone) ALLOWED_TIMEZONES='Antarctica/Troll' ;;
  "")       ;;
  *)        echo "unknown CAP_SELFTEST_BREAK: $CAP_SELFTEST_BREAK" >&2; exit 64 ;;
esac

# =============================================================================================
# PRECONDITIONS — every one of these exits non-zero. Nothing is captured until all of them pass.
# The two that decide the ARITHMETIC (rounding mode, precision) are asserted first-class; their
# absence is exactly what let a HALF_EVEN corpus be recorded as if it were parity-grade.
# =============================================================================================
preconditions() {
  echo "== preconditions (tenant=$TENANT) =="

  command -v docker >/dev/null 2>&1 || fail "docker is not on PATH"
  command -v curl   >/dev/null 2>&1 || fail "curl is not on PATH"

  # 1. the pinned image, by digest
  IMAGE_DIGEST=$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null) \
    || fail "image fineract:latest is not present"
  [ "$IMAGE_DIGEST" = "$EXPECT_IMAGE_DIGEST" ] \
    || fail "image digest is $IMAGE_DIGEST, expected $EXPECT_IMAGE_DIGEST"
  ok "image digest $IMAGE_DIGEST"

  # 2. the jar's OWN build attestation — the server must be the pinned commit, built clean
  GITPROPS=$(docker exec "$APP_CONTAINER" sh -c 'unzip -p /app/fineract-provider.jar BOOT-INF/classes/git.properties' 2>/dev/null) \
    || fail "cannot read git.properties out of the running provider jar"
  JAR_COMMIT=$(echo "$GITPROPS" | grep '^git.commit.id=' | head -1 | cut -d= -f2)
  JAR_DIRTY=$(echo "$GITPROPS"  | grep '^git.dirty='     | head -1 | cut -d= -f2)
  [ "$JAR_COMMIT" = "$EXPECT_ORACLE_COMMIT" ] \
    || fail "running server was built from $JAR_COMMIT, expected $EXPECT_ORACLE_COMMIT"
  [ "$JAR_DIRTY" = "false" ] || fail "running server was built from a DIRTY tree (git.dirty=$JAR_DIRTY)"
  ok "server jar git.commit.id $JAR_COMMIT, git.dirty=$JAR_DIRTY"

  # 3. PostgreSQL, and ONLY PostgreSQL — CLAUDE.md non-negotiable
  ENVDUMP=$(docker inspect "$APP_CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}')
  echo "$ENVDUMP" | grep -q 'org.postgresql.Driver' || fail "container driver is not org.postgresql.Driver"
  echo "$ENVDUMP" | grep -q 'jdbc:postgresql://'    || fail "container JDBC URL is not jdbc:postgresql://"
  BADENV=$(echo "$ENVDUMP" | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver' | tr -d ' ')
  [ "$BADENV" = "0" ] || fail "prohibited DB engine referenced in the container environment ($BADENV hits)"
  BADJAR=$(docker exec "$APP_CONTAINER" sh -c 'unzip -l /app/fineract-provider.jar | grep -icE "ojdbc|oracle\.jdbc|mysql|mariadb"' | tr -d ' ')
  [ "$BADJAR" = "0" ] || fail "prohibited DB driver bundled in the provider jar ($BADJAR hits)"
  PGVERSION=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -At -c 'select version();') \
    || fail "cannot reach PostgreSQL in $DB_CONTAINER"
  case "$PGVERSION" in PostgreSQL*) ;; *) fail "database is not PostgreSQL: $PGVERSION" ;; esac
  ok "PostgreSQL only — $(echo "$PGVERSION" | cut -c1-40)..."

  # 4. server healthy
  HEALTH=$(curl -sk "$(echo "$BASE" | sed 's#/api/v1##')/actuator/health") || fail "health endpoint unreachable"
  echo "$HEALTH" | grep -q '"status":"UP"' || fail "server is not UP: $HEALTH"
  ok "health $HEALTH"

  # 5. the tenant exists, with a MONGOLIAN timezone (CLAUDE.md: Asia/Ulaanbaatar or Asia/Hovd)
  TZ_ID=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d fineract_tenants -At \
      -c "select timezone_id from tenants where identifier='$TENANT';") || fail "cannot query the tenant store"
  [ -n "$TZ_ID" ] || fail "tenant '$TENANT' does not exist in the tenant store"
  TZ_OK=0
  for z in $ALLOWED_TIMEZONES; do [ "$TZ_ID" = "$z" ] && TZ_OK=1; done
  [ "$TZ_OK" = "1" ] || fail "tenant '$TENANT' timezone is $TZ_ID; allowed: $ALLOWED_TIMEZONES"
  ok "tenant timezone $TZ_ID"

  # 6. no MySQL-era JDBC parameters left on the tenant connection row
  CONNPARAMS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d fineract_tenants -At \
      -c "select coalesce(c.schema_connection_parameters,'') from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';")
  [ -z "$CONNPARAMS" ] || fail "tenant '$TENANT' carries JDBC connection parameters: $CONNPARAMS"
  ok "tenant connection parameters empty"

  # 7. THE ROUNDING MODE. This decides the arithmetic. HALF_UP == RoundingMode ordinal 4.
  ROUNDING=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$TENANT_DB" -At \
      -c "select value from c_configuration where name='rounding-mode' and enabled;") \
      || fail "cannot read c_configuration from $TENANT_DB"
  [ "$ROUNDING" = "$EXPECT_ROUNDING_MODE" ] \
    || fail "tenant '$TENANT' rounding-mode is $ROUNDING, expected $EXPECT_ROUNDING_MODE (HALF_UP)"
  ok "tenant rounding-mode $ROUNDING (HALF_UP)"

  # 8. and the mode the SERVER actually initialised for this tenant — MoneyHelper caches it at
  #    startup, so the config row alone is not proof. The server's own log line is.
  MODELOG=$(docker logs "$APP_CONTAINER" 2>&1 | grep "Initialized rounding mode for tenant \`$TENANT\`" | tail -1)
  [ -n "$MODELOG" ] || fail "server never logged a rounding mode for tenant '$TENANT' (restart required?)"
  echo "$MODELOG" | grep -q 'HALF_UP' \
    || fail "server initialised tenant '$TENANT' at a mode that is not HALF_UP: $MODELOG"
  ok "server log: $(echo "$MODELOG" | sed 's/.*MoneyHelper *: *//')"

  # 9. MoneyHelper.PRECISION, read out of the PINNED SOURCE (it is a compile-time constant, so it
  #    cannot be read back over the API; the source is the only honest place to observe it).
  MH="${FINERACT_CHECKOUT:-/Users/buv/fineract}/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java"
  [ -f "$MH" ] || fail "cannot find MoneyHelper.java at $MH"
  PRECISION=$(grep -E 'PRECISION *=' "$MH" | head -1 | tr -cd '0-9')
  [ "$PRECISION" = "19" ] || fail "MoneyHelper.PRECISION is $PRECISION, expected 19"
  ok "MoneyHelper.PRECISION $PRECISION (pinned source)"

  # 10. the four products the calc requests reference must exist AND carry the discriminating
  #     fields as PERSISTED VALUES — not as whatever the create response echoed back.
  PRODUCTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$TENANT_DB" -At -F '|' \
      -c "select id,coalesce(installment_amount_in_multiples_of::text,'NULL'),coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in (1,2,3,4) order by id;")
  EXPECTED_PRODUCTS='1|NULL|NULL
2|100.000000|NULL
3|NULL|FULL_LEAP_YEAR
4|NULL|FEB_29_PERIOD_ONLY'
  [ "$PRODUCTS" = "$EXPECTED_PRODUCTS" ] || fail "persisted products 1-4 are not the Path B fixture:
$PRODUCTS"
  ok "products 1-4 persisted with the expected discriminating fields"
}

# =============================================================================================
# SELF-TEST
# =============================================================================================
if [ "$SELFTEST" = "1" ]; then
  echo "== precondition self-test: every check below MUST fail, and MUST write no capture =="
  TMPD=$(mktemp -d)
  RC_ALL=0
  expect_fail() {
    LABEL="$1"; shift
    OUT=$("$@" 2>&1); RC=$?
    LAST=$(echo "$OUT" | tail -1)
    if [ "$RC" = "0" ]; then
      echo "  SELF-TEST FAILED: [$LABEL] exited 0 — that check cannot fail, so it is not a precondition"
      RC_ALL=1
    else
      echo "  ok  [$LABEL] exit $RC :: $LAST"
    fi
  }
  expect_fail "wrong image digest"   env CAP_SELFTEST_BREAK=image    sh "$0" --outdir "$TMPD"
  expect_fail "wrong oracle commit"  env CAP_SELFTEST_BREAK=commit   sh "$0" --outdir "$TMPD"
  expect_fail "wrong rounding mode"  env CAP_SELFTEST_BREAK=rounding sh "$0" --outdir "$TMPD"
  expect_fail "wrong timezone"       env CAP_SELFTEST_BREAK=timezone sh "$0" --outdir "$TMPD"
  expect_fail "HALF_EVEN tenant 'default'" sh "$0" --tenant default  --outdir "$TMPD"
  expect_fail "nonexistent tenant"   sh "$0" --tenant no_such_tenant --outdir "$TMPD"
  echo "-- nothing may have been written --"
  if ls "$TMPD"/*.json >/dev/null 2>&1; then
    echo "  SELF-TEST FAILED: a capture file was written despite a failed precondition"; RC_ALL=1
  else
    echo "  ok  no capture artefact was written"
  fi
  rm -rf "$TMPD"
  [ "$RC_ALL" = "0" ] && echo "== self-test PASSED: all 6 preconditions fail the run ==" \
                      || echo "== self-test FAILED =="
  exit "$RC_ALL"
fi

preconditions

# =============================================================================================
# CAPTURE — explicit filenames (no glob), HTTP status recorded, attestation sidecar per capture.
# =============================================================================================
mkdir -p "$OUTDIR"
RUN_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "== captures =="

set -- \
  'B-01-baseline:calc-B-01-baseline' \
  'B-02-multiplesof100:calc-B-02-multiplesof100' \
  'B-03-diycs-fullleapyear:calc-B-03-diycs-fullleapyear' \
  'B-04-diycs-feb29only:calc-B-04-diycs-feb29only'

for pair in "$@"; do
  ID=${pair%%:*}
  REQ=${pair#*:}
  REQ_FILE="$PB/req/$REQ.json"
  RAW="$OUTDIR/$ID-raw.json"
  ATT="$OUTDIR/$ID-attestation.json"
  [ -f "$REQ_FILE" ] || fail "request body missing: $REQ_FILE"

  STATUS=$(curl -sk -X POST "$BASE/loans?command=calculateLoanSchedule" \
      -H "$AUTH" -H "$TENANT_HDR" -H "$CT" -d @"$REQ_FILE" \
      -o "$RAW" -w '%{http_code}')
  CURL_RC=$?
  [ "$CURL_RC" = "0" ] || { echo "curl failed (rc=$CURL_RC) for $ID" >&2; exit 1; }
  # An HTTP error body must NEVER be mistaken for a capture.
  if [ "$STATUS" != "200" ]; then
    echo "HTTP $STATUS for $ID — this is NOT a capture. Body kept at $RAW.http-$STATUS" >&2
    mv "$RAW" "$RAW.http-$STATUS"
    exit 1
  fi
  python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$RAW" \
    || { echo "$ID response is not valid JSON" >&2; exit 1; }

  REQ_SHA=$(shasum -a 256 "$REQ_FILE" | cut -d' ' -f1)
  RSP_SHA=$(shasum -a 256 "$RAW"      | cut -d' ' -f1)
  # Read the product back FROM POSTGRESQL, not from whatever the create response echoed.
  PRODUCT_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["productId"])' "$REQ_FILE")
  PRODUCT_ROW=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$TENANT_DB" -At \
      -c "select to_jsonb(t)::text from m_product_loan t where id = $PRODUCT_ID;" 2>/dev/null)

  ATT_JSON="$ATT" ID="$ID" REQ_FILE="$REQ_FILE" RAW="$RAW" REQ_SHA="$REQ_SHA" RSP_SHA="$RSP_SHA" \
  PRODUCT_ID="$PRODUCT_ID" \
  STATUS="$STATUS" TENANT="$TENANT" TZ_ID="$TZ_ID" ROUNDING="$ROUNDING" PRECISION="$PRECISION" \
  IMAGE_DIGEST="$IMAGE_DIGEST" JAR_COMMIT="$JAR_COMMIT" JAR_DIRTY="$JAR_DIRTY" PGVERSION="$PGVERSION" \
  MODELOG="$MODELOG" RUN_UTC="$RUN_UTC" PRODUCT_ROW="$PRODUCT_ROW" python3 - <<'PY'
import json, os
from decimal import Decimal
o = os.environ
att = {
    "capture": o["ID"],
    "capturePath": "Path B - running Fineract server over PostgreSQL",
    "capturedAtUtc": o["RUN_UTC"],
    "runner": ".softhouse/capture/pathb/capture.sh",
    "endpoint": "POST /loans?command=calculateLoanSchedule",
    "httpStatus": int(o["STATUS"]),
    "request": {"file": os.path.basename(o["REQ_FILE"]), "sha256": o["REQ_SHA"], "productId": int(o["PRODUCT_ID"])},
    "response": {"file": os.path.basename(o["RAW"]), "sha256": o["RSP_SHA"]},
    "tenant": {
        "identifier": o["TENANT"],
        "timezoneId": o["TZ_ID"],
        "roundingModeOrdinal": int(o["ROUNDING"]),
        "roundingModeName": "HALF_UP",
        "roundingModeEvidence": o["MODELOG"].strip() or None,
    },
    "mathContext": {
        "precision": int(o["PRECISION"]),
        "precisionSource": "MoneyHelper.PRECISION, compile-time constant, read from the pinned source",
        "roundingMode": "HALF_UP",
        "effective": "(%s, HALF_UP)" % o["PRECISION"],
    },
    "oracle": {
        "imageDigest": o["IMAGE_DIGEST"],
        "jarGitCommitId": o["JAR_COMMIT"],
        "jarGitDirty": o["JAR_DIRTY"],
        "postgresqlVersion": o["PGVERSION"],
        "prohibitedDbEngines": "none present in container env or provider jar (asserted by the runner)",
    },
    "storageForm": "RAW OBSERVED server response bytes. NOT contract-shaped: gate G-1 is open.",
}
# The persisted product row, read back FROM PostgreSQL. Numeric columns are parsed as exact
# Decimal and re-emitted as exact decimal STRINGS: no binary float is ever constructed, which is
# a CLAUDE.md non-negotiable and matters here because these columns carry money.
row = o.get("PRODUCT_ROW", "").strip()


def dec_to_str(x):
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, dict):
        return {k: dec_to_str(v) for k, v in x.items()}
    if isinstance(x, list):
        return [dec_to_str(v) for v in x]
    return x


if row:
    try:
        att["productRowAsPersisted"] = dec_to_str(json.loads(row, parse_float=Decimal))
        att["productRowNote"] = ("read back from PostgreSQL m_product_loan via to_jsonb; numeric columns are"
                                 " exact decimal STRINGS (no float was constructed at any point)")
    except Exception as e:
        att["productRowAsPersisted"] = None
        att["productRowNote"] = "could not be read back as JSON at capture time: %s" % e
else:
    att["productRowAsPersisted"] = None
    att["productRowNote"] = "not read back at capture time"
with open(o["ATT_JSON"], "w") as f:
    json.dump(att, f, indent=2, sort_keys=False)
    f.write("\n")
PY
  echo "  $ID  HTTP $STATUS  $(wc -c < "$RAW" | tr -d ' ') bytes  sha256 $RSP_SHA"
done

echo "== done: captures + attestation sidecars in $OUTDIR =="
