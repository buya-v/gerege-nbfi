#!/bin/sh
# T36 — Path B FAIL-THE-RUN preconditions.  Closes T22 P0-4.
#
# Every assertion below was written against the RUNNING server and its PostgreSQL
# rows on fire 20260818-230002, not drafted blind.  A breach of ANY of them means
# the run did not execute the pinned reference oracle (Fineract), or did not
# execute it at the ratified tenant settings, and the capture it produces is NOT
# an observation of the oracle.  This script therefore EXITS NON-ZERO on a breach
# and names the breach.  REPRODUCE.md sources it before capturing.
#
# Usage:   sh preconditions.sh [tenant-identifier]        (default: gerege)
# Exit:    0 = every precondition holds; 1 = at least one breached (details on stderr)
#
# PostgreSQL is the only permitted engine.  Oracle Database, MySQL and MariaDB are
# prohibited; assertions P5/P6/P7 below fail the run if any trace of them appears.
set -u

TENANT=${1:-gerege}
PIN_IMAGE=sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a
PIN_COMMIT=426a23544e8426a38ae43ae404670a0a7e85b9eb
PIN_PG_MAJOR_MINOR='PostgreSQL 18.3'
WANT_ROUNDING_ORDINAL=4          # RoundingMode.valueOf(4) = HALF_UP  (ratified, CLAUDE.md)
WANT_PRECISION=19                # MoneyHelper.PRECISION, compile-time
FIN=fineract-fineract-1
DB=fineract-db-1
BASE=https://localhost:8443/fineract-provider
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='

# The effective-rounding-mode canary.  A DB row saying `rounding-mode = 4` is NOT
# proof: MoneyHelper caches the mode per tenant at JVM startup, so a row edited
# after boot is inert.  This request has an exact half-cent tie in period 1
# (principal 1,162,502.50 x 0.018 = 20,925.045), so the RUNNING process must
# answer 20925.05 under HALF_UP and 20925.04 under HALF_EVEN.
# T22 observed both, one per tenant (t22-audit/out-modeprobe2/).
CANARY_REQ=${CANARY_REQ:-}
# HARDENED by T76.  CANARY_EXPECT used to be env-overridable, which meant the single
# strongest assertion in this script could be TALKED OUT OF FAILING:
#   CANARY_EXPECT=20925.04 sh preconditions.sh default
# would have printed "PASS effective rounding mode canary" while the process ran
# HALF_EVEN.  The expectation is now a constant, and an attempt to override it from
# the environment is itself a breach.
CANARY_EXPECT=20925.05
CANARY_EXPECT_ENV_ATTEMPT=${CANARY_EXPECT_OVERRIDE:-}

fails=0
ok()   { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1" >&2; fails=$((fails+1)); }

echo "== T36 Path B preconditions, tenant '$TENANT' =="

# ---------------------------------------------------------------- P1 image pin
got=$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)
[ "$got" = "$PIN_IMAGE" ] && ok "image digest $got" \
  || bad "image digest is '$got', pin is '$PIN_IMAGE' — this is NOT the pinned oracle"

# ------------------------------------------------- P2 jar build attestation
gp=$(docker exec "$FIN" sh -c 'unzip -p /app/fineract-provider.jar BOOT-INF/classes/git.properties' 2>/dev/null)
cid=$(printf '%s\n' "$gp" | sed -n 's/^git\.commit\.id=\(.*\)$/\1/p' | tr -d '\r')
dirty=$(printf '%s\n' "$gp" | sed -n 's/^git\.dirty=\(.*\)$/\1/p' | tr -d '\r')
[ "$cid" = "$PIN_COMMIT" ] && ok "jar git.commit.id $cid" \
  || bad "jar git.commit.id is '$cid', pin is '$PIN_COMMIT'"
[ "$dirty" = "false" ] && ok "jar git.dirty=false" \
  || bad "jar git.dirty='$dirty' — the oracle was built from a dirty tree"

# ------------------------------------------------------- P3 MoneyHelper.PRECISION
# Read from the DEPLOYED bytecode in the running container, not from source.
docker exec "$FIN" sh -c 'mkdir -p /tmp/t36pc && cd /tmp/t36pc && unzip -o -q /app/fineract-provider.jar "BOOT-INF/lib/fineract-core-*.jar"' 2>/dev/null
prec=$(docker exec -e JAVA_TOOL_OPTIONS= "$FIN" sh -c \
  'cd /tmp/t36pc && javap -p -constants -cp BOOT-INF/lib/fineract-core-*.jar org.apache.fineract.organisation.monetary.domain.MoneyHelper' 2>/dev/null \
  | sed -n 's/.*public static final int PRECISION = \([0-9]*\);.*/\1/p')
[ "$prec" = "$WANT_PRECISION" ] && ok "MoneyHelper.PRECISION = $prec (deployed bytecode)" \
  || bad "MoneyHelper.PRECISION is '$prec', ratified MathContext needs $WANT_PRECISION"

# ------------------------------------------------------- P4 server health
h=$(curl -sk "$BASE/actuator/health" 2>/dev/null)
case "$h" in *'"status":"UP"'*) ok "actuator/health UP" ;;
             *) bad "actuator/health did not report UP: '$h'" ;; esac

# -------------------------------------------- P5 PostgreSQL-only: container env
env_jdbc=$(docker inspect "$FIN" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -iE 'driver|jdbc')
case "$env_jdbc" in *org.postgresql.Driver*) ok "driverClassName org.postgresql.Driver" ;;
                    *) bad "container env does not carry org.postgresql.Driver" ;; esac
case "$env_jdbc" in *jdbc:postgresql://*) ok "JDBC URL is jdbc:postgresql://…" ;;
                    *) bad "container env does not carry a jdbc:postgresql URL" ;; esac
banned=$(docker inspect "$FIN" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
         | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver')
[ "$banned" = "0" ] && ok "0 prohibited-engine hits in container env" \
  || bad "$banned prohibited-engine hits in container env (Oracle Database / MySQL / MariaDB are prohibited)"

# ------------------------------------------------ P6 PostgreSQL-only: the jar
jarhits=$(docker exec "$FIN" sh -c 'unzip -l /app/fineract-provider.jar' 2>/dev/null \
          | grep -icE 'ojdbc|oracle-jdbc|mysql-connector|mariadb-java')
[ "$jarhits" = "0" ] && ok "0 prohibited driver jars in fineract-provider.jar" \
  || bad "$jarhits prohibited driver jars inside fineract-provider.jar"
pgdrv=$(docker exec "$FIN" sh -c 'unzip -l /app/fineract-provider.jar' 2>/dev/null \
        | grep -c 'BOOT-INF/lib/postgresql-')
[ "$pgdrv" -ge 1 ] && ok "PostgreSQL JDBC driver present in the jar" \
  || bad "no PostgreSQL JDBC driver in the jar"

# ------------------------------------------------- P7 PostgreSQL server version
pgv=$(docker exec "$DB" psql -U root -t -c 'select version();' 2>/dev/null | tr -d '\r' | sed -n '1s/^ *//p')
case "$pgv" in "$PIN_PG_MAJOR_MINOR"*) ok "PostgreSQL version: $pgv" ;;
               *) bad "PostgreSQL version is '$pgv', pin is '$PIN_PG_MAJOR_MINOR…'" ;; esac

# --------------------------------------------------------- P8 tenant row exists
tzid=$(docker exec "$DB" psql -U root -d fineract_tenants -At \
        -c "select timezone_id from tenants where identifier='$TENANT';" 2>/dev/null | tr -d '\r')
[ -n "$tzid" ] && ok "tenant '$TENANT' exists" || bad "tenant '$TENANT' has no row in fineract_tenants.tenants"

# ------------------------------------------------------------- P9 tenant timezone
# Gerege operates in two zones, both +08/+07 with NO DST.  Never hard-code an offset:
# this asserts the zone ID, and the JVM resolves the offset from the tz database.
case "$tzid" in
  Asia/Ulaanbaatar|Asia/Hovd) ok "tenant timezone_id = $tzid" ;;
  *) bad "tenant timezone_id = '$tzid' — must be Asia/Ulaanbaatar or Asia/Hovd (CLAUDE.md)" ;;
esac

# ------------------------------------------- P10 tenant rounding mode, DB row
schema=$(docker exec "$DB" psql -U root -d fineract_tenants -At \
  -c "select c.schema_name from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" 2>/dev/null | tr -d '\r')
rm_val=$(docker exec "$DB" psql -U root -d "$schema" -At \
  -c "select value from c_configuration where name='rounding-mode';" 2>/dev/null | tr -d '\r')
rm_en=$(docker exec "$DB" psql -U root -d "$schema" -At \
  -c "select enabled from c_configuration where name='rounding-mode';" 2>/dev/null | tr -d '\r')
[ "$rm_val" = "$WANT_ROUNDING_ORDINAL" ] && ok "c_configuration.rounding-mode = $rm_val (HALF_UP)" \
  || bad "c_configuration.rounding-mode = '$rm_val' in $schema — ratified value is $WANT_ROUNDING_ORDINAL (HALF_UP); 6 is HALF_EVEN and is NOT production-representative"
[ "$rm_en" = "t" ] && ok "rounding-mode row enabled" || bad "rounding-mode row is not enabled (enabled='$rm_en')"

# --------------------------- P11 schema_connection_parameters must be EMPTY
# The stock `default` row carries MySQL-era JDBC parameters
# (serverTimezone=…&useLegacyDatetimeCode=…&sessionVariables=time_zone=…).
# pgjdbc ignores them, but MySQL-shaped config must not sit on a capture tenant.
scp=$(docker exec "$DB" psql -U root -d fineract_tenants -At \
  -c "select coalesce(c.schema_connection_parameters,'') from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" 2>/dev/null | tr -d '\r')
[ -z "$scp" ] && ok "schema_connection_parameters is empty" \
  || bad "schema_connection_parameters = '$scp' — must be empty on a capture tenant"

# ------------------------------- P12 tenant connection points at PostgreSQL:5432
port=$(docker exec "$DB" psql -U root -d fineract_tenants -At \
  -c "select c.schema_server_port from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" 2>/dev/null | tr -d '\r')
[ "$port" = "5432" ] && ok "tenant schema_server_port = 5432" \
  || bad "tenant schema_server_port = '$port' — 5432 expected; 1521 would be Oracle Database (prohibited), 3306 MySQL (prohibited)"

# --------------------- P13 the running JVM logged HALF_UP for this tenant
# MoneyHelper caches per tenant at startup, so what matters is what THIS process
# initialized — read it back from the container's own log, after StartedAt.
started=$(docker inspect "$FIN" --format '{{.State.StartedAt}}' 2>/dev/null)
logline=$(docker logs --since "$started" "$FIN" 2>&1 | grep -F "Initialized rounding mode for tenant \`$TENANT\`" | tail -1)
case "$logline" in *HALF_UP) ok "running JVM initialized tenant '$TENANT' at HALF_UP" ;;
  '') bad "no MoneyHelper init line for tenant '$TENANT' since container start ($started) — the mode in force is unproven" ;;
  *)  bad "running JVM initialized tenant '$TENANT' at a mode other than HALF_UP: $logline" ;;
esac

# ------------------- P14 EFFECTIVE-mode canary: ask the running server
# Strongest of the lot: it is the arithmetic itself answering, not configuration.
if [ -n "$CANARY_EXPECT_ENV_ATTEMPT" ]; then
  bad "CANARY_EXPECT_OVERRIDE is set ('$CANARY_EXPECT_ENV_ATTEMPT') — the canary expectation is a CONSTANT (20925.05). Refusing to grade the arithmetic against a value supplied by the runner."
fi

# P14b (T76): the canary REQUEST is pinned by content, not merely by path.  Without this
# a runner could point CANARY_REQ at any request that happens to return 20925.05 under
# EITHER mode -- e.g. a principal that is not a half-minor-unit tie -- and the strongest
# assertion in the script would degrade into a tautology.  The tie is a property of these
# four literals: 1,162,502.50 x 0.018 = 20,925.045 exactly.
if [ -n "$CANARY_REQ" ] && [ -f "$CANARY_REQ" ]; then
  creqsha=$(shasum -a 256 "$CANARY_REQ" | cut -d' ' -f1)
  cmiss=''
  for lit in '"principal": 1162502.5' '"interestRatePerPeriod": 21.6' \
             '"numberOfRepayments": 12' '"interestCalculationPeriodType": 1'; do
    grep -qF "$lit" "$CANARY_REQ" || cmiss="$cmiss [$lit]"
  done
  if [ -n "$cmiss" ]; then
    bad "canary request $CANARY_REQ (sha256 $creqsha) is not the pinned half-cent tie; missing:$cmiss"
  else
    ok "canary request pinned by content (half-cent tie 1162502.50 x 0.018 = 20925.045), sha256 $creqsha"
  fi
fi

if [ -n "$CANARY_REQ" ] && [ -f "$CANARY_REQ" ]; then
  cbody=$(curl -sk -X POST "$BASE/api/v1/loans?command=calculateLoanSchedule" \
    -H "$AUTH" -H "Fineract-Platform-TenantId: $TENANT" -H 'Content-Type: application/json' \
    -d @"$CANARY_REQ" -w '\n%{http_code}' 2>/dev/null)
  ccode=$(printf '%s' "$cbody" | tail -1)
  cjson=$(printf '%s' "$cbody" | sed '$d')
  if [ "$ccode" != "200" ]; then
    bad "rounding-mode canary returned HTTP $ccode, not 200"
  else
    p1=$(printf '%s' "$cjson" | tr ',' '\n' | grep -m1 '"interestOriginalDue"' | sed 's/.*://')
    [ "$p1" = "$CANARY_EXPECT" ] && ok "effective rounding mode canary: period-1 interest $p1 (= HALF_UP)" \
      || bad "effective rounding-mode canary returned period-1 interest '$p1', expected '$CANARY_EXPECT'; 20925.04 would mean the process is running HALF_EVEN"
  fi
else
  bad "rounding-mode canary NOT run (set CANARY_REQ to the committed half-cent request). A DB row is not proof of the mode in force."
fi

# ---------------------------------------------------------------- P15 MNT currency
mnt=$(docker exec "$DB" psql -U root -d "$schema" -At \
  -c "select decimal_places from m_currency where code='MNT';" 2>/dev/null | tr -d '\r')
[ "$mnt" = "2" ] && ok "MNT seeded with decimal_places=2 (ISO 4217 496, minor unit 2)" \
  || bad "MNT decimal_places = '$mnt' in $schema, expected 2"
mnt_on=$(docker exec "$DB" psql -U root -d "$schema" -At \
  -c "select count(*) from m_organisation_currency where code='MNT';" 2>/dev/null | tr -d '\r')
[ "$mnt_on" = "1" ] && ok "MNT enabled for the tenant" || bad "MNT is not enabled for tenant '$TENANT'"

echo
if [ "$fails" -ne 0 ]; then
  echo "PRECONDITIONS BREACHED: $fails. DO NOT CAPTURE. Any file produced now is NOT an observation" >&2
  echo "of the pinned reference oracle at the ratified (19, HALF_UP) settings — do not commit it, do not" >&2
  echo "treat it as a vector, and do not 'normalise' it. Fix the environment and re-run." >&2
  exit 1
fi
echo "ALL PRECONDITIONS HOLD — tenant '$TENANT' at MathContext(19, HALF_UP), PostgreSQL only."
exit 0
