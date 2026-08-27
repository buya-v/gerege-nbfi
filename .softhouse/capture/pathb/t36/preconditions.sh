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

PCD=$(cd "$(dirname "$0")" && pwd)
# The sha256 instrument, hardened by T99.  P14b's digest pin used the bare word `shasum`, resolved
# through $PATH; a `shasum` earlier on $PATH that prints the pinned constant made the comparison a
# tautology again AND LEFT NO DIFF TRACE.  sha256.sh resolves the tools by absolute path in
# root-owned system directories, known-answer-tests each one, and requires two independent
# implementations to agree.  See sha256.sh's header and t99/prove-f2.sh.
. "$PCD/sha256.sh"

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
# The canary request is pinned by DIGEST, not by path and not by substring.  T77 broke
# T76's substring pin with a one-character edit (principal 1162502.5 -> 1162502.55, which
# is NOT a half-minor-unit tie and therefore answers 20925.05 under EITHER mode) and drove
# this script to "PASS effective rounding mode canary (= HALF_UP)" on the HALF_EVEN
# `default` tenant.  A check has two operands; if the caller controls both, it is not a
# check.  The two operands here are (a) the sha256 of the file this script is about to
# POST, computed at run time, and (b) this literal, which the caller cannot reach without
# editing the recipe itself.  Mismatch is a BREACH and the canary is NOT SENT.
PIN_CANARY_SHA256=2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154
# HARDENED by T76, corrected by T80.  CANARY_EXPECT used to be env-overridable, which meant
# the single strongest assertion in this script could be TALKED OUT OF FAILING:
#   CANARY_EXPECT=20925.04 sh preconditions.sh default
# would have printed "PASS effective rounding mode canary" while the process ran HALF_EVEN.
# T76 made the expectation a constant but pointed the tripwire at CANARY_EXPECT_OVERRIDE --
# a name no attacker uses, so the documented attack did not reproduce (T77 P1-T77-3).  The
# tripwire now watches CANARY_EXPECT ITSELF: the inherited value is captured HERE, one line
# BEFORE the constant assignment that overwrites it.
CANARY_EXPECT_ENV_ATTEMPT=${CANARY_EXPECT:-}
CANARY_EXPECT=20925.05

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
#
# T99b CORRECTION — A PROHIBITION COUNTED OVER NO INPUT IS ZERO.  P5's `banned` and P6's `jarhits`
# below asserted an ABSENCE (`[ "$banned" = "0" ]`), and `grep -icE` over an EMPTY stream returns
# `0`.  So when `docker` produced nothing at all — it is not installed, the container is gone, the
# daemon is down, or a $PATH-poisoned `docker` refuses — this script printed
#     PASS  0 prohibited-engine hits in container env
#     PASS  0 prohibited driver jars in fineract-provider.jar
# HAVING SCANNED NOTHING.  These are the Oracle-Database / MySQL / MariaDB prohibition assertions,
# a CLAUDE.md non-negotiable, and they were structurally incapable of failing for the reason they
# exist.  Measured on main's bytes with docker stubbed to refuse: both PASS lines printed, 18 FAIL.
# This is the F-3 defect class (P-22) in a different file; T99's own sweep did not see it because
# its grep pattern was `grep -c\|grep -ac\|wc -l` and these two lines use `grep -icE`.
#
# The remedy is a LIVENESS OPERAND: the scan output is captured once, and a count of 0 is only
# allowed to mean "clean" after the input has been shown to be non-empty.  Empty input is a FAIL
# that says the scan did not happen, never a PASS.
env_dump=$(docker inspect "$FIN" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null)
env_lines=$(printf '%s\n' "$env_dump" | LC_ALL=C grep -c . || true)
env_jdbc=$(printf '%s\n' "$env_dump" | grep -iE 'driver|jdbc')
case "$env_jdbc" in *org.postgresql.Driver*) ok "driverClassName org.postgresql.Driver" ;;
                    *) bad "container env does not carry org.postgresql.Driver" ;; esac
case "$env_jdbc" in *jdbc:postgresql://*) ok "JDBC URL is jdbc:postgresql://…" ;;
                    *) bad "container env does not carry a jdbc:postgresql URL" ;; esac
if [ -z "$env_dump" ]; then
  bad "prohibited-engine scan of the container env INSPECTED NOTHING: \`docker inspect $FIN\` returned no environment at all, so a count of 0 would mean 'not looked', not 'clean'. The Oracle Database / MySQL / MariaDB prohibition is UNPROVEN for this container."
else
  banned=$(printf '%s\n' "$env_dump" | grep -icE 'ojdbc|oracle\.jdbc|:1521|com\.mysql\.cj|mariadb|go-sql-driver')
  [ "$banned" = "0" ] && ok "0 prohibited-engine hits in container env ($env_lines env line(s) actually scanned)" \
    || bad "$banned prohibited-engine hits in container env (Oracle Database / MySQL / MariaDB are prohibited)"
fi

# ------------------------------------------------ P6 PostgreSQL-only: the jar
# Same liveness operand, and the listing is taken ONCE so the prohibition scan and the
# positive-presence scan below cannot disagree about which listing they read.
jarlist=$(docker exec "$FIN" sh -c 'unzip -l /app/fineract-provider.jar' 2>/dev/null)
jarlines=$(printf '%s\n' "$jarlist" | LC_ALL=C grep -c . || true)
if [ -z "$jarlist" ]; then
  bad "prohibited-driver-jar scan INSPECTED NOTHING: \`unzip -l /app/fineract-provider.jar\` in $FIN returned no listing at all, so a count of 0 would mean 'not looked', not 'clean'. The Oracle Database / MySQL / MariaDB prohibition is UNPROVEN for this jar."
else
  jarhits=$(printf '%s\n' "$jarlist" | grep -icE 'ojdbc|oracle-jdbc|mysql-connector|mariadb-java')
  [ "$jarhits" = "0" ] && ok "0 prohibited driver jars in fineract-provider.jar ($jarlines jar entry line(s) actually scanned)" \
    || bad "$jarhits prohibited driver jars inside fineract-provider.jar"
fi
pgdrv=$(printf '%s\n' "$jarlist" | grep -c 'BOOT-INF/lib/postgresql-')
[ "$pgdrv" -ge 1 ] && ok "PostgreSQL JDBC driver present in the jar" \
  || bad "no PostgreSQL JDBC driver in the jar"

# ------------------------------------------------- P7 PostgreSQL server version
pgv=$(docker exec "$DB" psql -U root -t -c 'select version();' 2>/dev/null | tr -d '\r' | sed -n '1s/^ *//p')
case "$pgv" in "$PIN_PG_MAJOR_MINOR"*) ok "PostgreSQL version: $pgv" ;;
               *) bad "PostgreSQL version is '$pgv', pin is '${PIN_PG_MAJOR_MINOR}…'" ;; esac
# ^ THE BRACES ARE LOAD-BEARING (T85 F-2).  Without them the variable reference runs straight into
# the ellipsis U+2026 (bytes e2 80 a6); bash reads 0xe2 as part of the identifier, and under `set -u`
# the whole script DIES here.  Measured effect of the unbraced form when P7 fails: 7 FAIL lines
# instead of 16, P8-P15 never executed -- INCLUDING THE ENTIRE ROUNDING-MODE CANARY -- no
# "PRECONDITIONS BREACHED: n" summary, and attest.py crashing with a UnicodeDecodeError on the
# truncated multibyte name.  It failed CLOSED (exit 1), so it was never a false pass; but a guard
# that dies instead of reporting takes the strongest assertion in the script down with it.

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
#
# T99b CORRECTION — the SAME "absence counted over no input" shape, third instance.  This asserted
# `[ -z "$scp" ]`, and a psql that never ran returns the empty string too, so a dead database, a
# missing container or a $PATH-poisoned `docker` printed "PASS  schema_connection_parameters is
# empty" having read no row.  Measured on main's bytes with docker stubbed: the PASS was printed.
# The query is now WRAPPED IN BRACKETS, which makes the two cases distinguishable: a live row that
# is genuinely empty answers `[]`, a query that did not run answers nothing at all.
scp=$(docker exec "$DB" psql -U root -d fineract_tenants -At \
  -c "select '['||coalesce(c.schema_connection_parameters,'')||']' from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" 2>/dev/null | tr -d '\r')
case "$scp" in
  '')   bad "schema_connection_parameters check INSPECTED NOTHING: the query against fineract_tenants returned no row at all for tenant '$TENANT', so 'empty' would mean 'not read', not 'empty'. MySQL-era JDBC parameters on this tenant are UNPROVEN absent." ;;
  '[]') ok "schema_connection_parameters is empty (a row was returned and its value is the empty string)" ;;
  *)    scp_val=${scp#[}; scp_val=${scp_val%]}
        bad "schema_connection_parameters = '$scp_val' — must be empty on a capture tenant" ;;
esac

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
# Precisely because it is the strongest, it is the one worth neutering, so it is pinned
# twice over: the EXPECTATION is a constant (P14a) and the REQUEST is pinned by digest
# comparison (P14b).  If either pin is breached the canary is NOT SENT at all -- the
# sentence "PASS effective rounding mode canary" must be unreachable except on the exact
# pinned half-cent tie, because a reader believes that sentence.

# ---- P14a: the expectation is a constant, and an override attempt is itself a breach
if [ -n "$CANARY_EXPECT_ENV_ATTEMPT" ]; then
  bad "CANARY_EXPECT was set in the environment ('$CANARY_EXPECT_ENV_ATTEMPT') — the canary expectation is a CONSTANT ($CANARY_EXPECT). Refusing to grade the arithmetic against a value supplied by the runner."
fi

# ---- P14b: the canary REQUEST is pinned by DIGEST COMPARISON, not by path, not by
# substring.  Substring matching is what T77 defeated: grep -qF '"principal": 1162502.5'
# also matches 1162502.55, which is not a tie, so the canary answered 20925.05 under both
# HALF_UP and HALF_EVEN and the assertion became a tautology.  A digest has no prefix.
#
# THIRD ITERATION (T99).  A digest has no prefix, but `shasum` had no ADDRESS: T80 computed it with
# a bare word resolved through $PATH, so a `shasum` earlier on $PATH that prints the pinned constant
# restored the tautology — worse than before, because the rig now LOOKS hardened and the attack
# LEAVES NO DIFF TRACE.  Reproduced against main's bytes in t99/out/f2-prefix-*.  The digest is now
# computed by sha256.sh: absolute-path tools in root-owned system directories, each one
# known-answer-tested every run, and two independent implementations required to agree.  The
# instrument is an operand too, and a failure of the instrument is a BREACH, never a silent pass.
canary_pinned=0
if [ -z "$CANARY_REQ" ]; then
  bad "rounding-mode canary NOT run: CANARY_REQ is unset. Set it to the committed half-cent request (t22-audit/req/calc-pmode2-gerege.json, sha256 $PIN_CANARY_SHA256). A DB row is not proof of the mode in force."
elif [ ! -f "$CANARY_REQ" ]; then
  bad "rounding-mode canary NOT run: CANARY_REQ='$CANARY_REQ' is not a readable file. A DB row is not proof of the mode in force."
elif ! sha256_init; then
  # T99: the INSTRUMENT is now an operand too.  If fewer than two independent, known-answer-tested
  # sha256 implementations are available, this script does not know what a digest is and must not
  # pretend the pin held.
  bad "rounding-mode canary NOT run: the sha256 instrument is not trustworthy — $SHA256_ERROR. THE CANARY WAS NOT SENT and the effective rounding mode is UNPROVEN."
elif ! sha256_file "$CANARY_REQ"; then
  bad "rounding-mode canary NOT run: refusing to trust a digest of '$CANARY_REQ' — $SHA256_ERROR. THE CANARY WAS NOT SENT and the effective rounding mode is UNPROVEN."
else
  creqsha=$SHA256_RESULT
  if [ "$creqsha" = "$PIN_CANARY_SHA256" ]; then
    canary_pinned=1
    ok "canary request pinned by DIGEST COMPARISON: computed sha256 $creqsha == pinned sha256 $PIN_CANARY_SHA256 ($CANARY_REQ) — the exact half-cent tie, 1,162,502.50 x 0.018 = 20,925.045 [instrument: $SHA256_USED, absolute-path tools, known-answer tested, cross-checked]"
  else
    bad "canary request DIGEST MISMATCH — computed sha256 '$creqsha' for '$CANARY_REQ', pinned sha256 is '$PIN_CANARY_SHA256'. That file is NOT the pinned half-cent tie (principal 1,162,502.50 x 0.018 = 20,925.045 exactly). A request that is not an exact half-minor-unit tie answers the same under HALF_UP and HALF_EVEN, so grading it would certify nothing. THE CANARY WAS NOT SENT and the effective rounding mode is UNPROVEN."
  fi
fi

# ---- P14c: send it, only if BOTH pins held.
if [ "$canary_pinned" = "1" ]; then
  cbody=$(curl -sk -X POST "$BASE/api/v1/loans?command=calculateLoanSchedule" \
    -H "$AUTH" -H "Fineract-Platform-TenantId: $TENANT" -H 'Content-Type: application/json' \
    -d @"$CANARY_REQ" -w '\n%{http_code}' 2>/dev/null)
  ccode=$(printf '%s' "$cbody" | tail -1)
  cjson=$(printf '%s' "$cbody" | sed '$d')
  if [ "$ccode" != "200" ]; then
    bad "rounding-mode canary returned HTTP $ccode, not 200 — the mode in force was never established"
  else
    p1=$(printf '%s' "$cjson" | tr ',' '\n' | grep -m1 '"interestOriginalDue"' | sed 's/.*://')
    [ "$p1" = "$CANARY_EXPECT" ] && ok "effective rounding mode canary: period-1 interest $p1 (= HALF_UP)" \
      || bad "effective rounding-mode canary returned period-1 interest '$p1', expected '$CANARY_EXPECT'; 20925.04 would mean the process is running HALF_EVEN"
  fi
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
