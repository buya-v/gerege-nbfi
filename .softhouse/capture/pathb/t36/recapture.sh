#!/bin/sh
# T36 — re-capture the four Path B sets against a PRODUCTION-SETTINGS tenant.  Closes T22 P0-6.
# HARDENED by T80 after T77 P0-T77-2.  See "the two properties" below.
#
# Tenant `gerege`: timezone Asia/Ulaanbaatar (+08, no DST — the ZONE is asserted, never an offset),
# c_configuration.rounding-mode = 4 (HALF_UP), MoneyHelper.PRECISION = 19 (deployed bytecode).
# Effective MathContext therefore (19, HALF_UP) — the ratified production setting.
#
# Additive only.  Creates no tenant, restarts nothing, drops nothing: another worker may be running
# captures against this same server for the whole fire.  Products 1-4 already exist in `gerege` from
# the committed byte-verbatim payloads (t22-audit/fresh-tenant.sh); this run reuses them so the calc
# requests can be sent BYTE-VERBATIM from req/, productId included.
#
# ---------------------------------------------------------------------------------------------
# THE TWO PROPERTIES THIS SCRIPT MUST HAVE.  Both were false until T80; both are now proved by an
# attack transcript in ../t80/out/, not asserted here.
#
#  1. PRECONDITIONS ARE FAIL-THE-RUN.  Until T80 this was a comment, not a fact: preconditions.sh
#     writes every FAIL to STDERR, and this script tee'd only STDOUT and then grepped the tee'd
#     file for '^  FAIL'.  The count was therefore ALWAYS 0 and the ABORT was UNREACHABLE.  T77 ran
#     `TENANT=default sh recapture.sh` and got five breached preconditions — including a canary that
#     404'd, i.e. the rounding mode in force was never established at all — no abort, all four
#     captures taken, exit 0.  The gate now tests the EXIT STATUS of preconditions.sh (the signal
#     the script actually emits) and, independently, greps a transcript that now contains BOTH
#     streams.  Two operands, either of which aborts.  `attest.py:96-101` already did it this way;
#     this is the same shape, deliberately.
#
#  2. A CAPTURE IS FILED UNDER THE TENANT IT WAS TAKEN FROM, STRUCTURALLY.  Until T80 the output
#     directory was the hard-coded literal `out/recapture-gerege` while the tenant was a variable,
#     so T77's `default` run wrote default-tenant bytes into a directory named for `gerege` — and
#     the four response bodies are byte-identical across modes, so NOTHING downstream could tell.
#     The directory now DERIVES from $TENANT; an explicit RECAPTURE_OUT override must still be
#     named for the tenant in use; and the run drops a provenance stamp that a later run of a
#     different tenant refuses to overwrite.
# ---------------------------------------------------------------------------------------------
#
# Usage:   sh recapture.sh                 # tenant gerege -> out/recapture-gerege
#          TENANT=x sh recapture.sh        # tenant x      -> out/recapture-x
#          RECAPTURE_OUT=<dir> sh …        # explicit dir, which must be named for $TENANT
# Exit:    0 = every precondition held and all four captures returned HTTP 200
#          1 = anything else, and in that case NOTHING was captured
set -u

D=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$D/.." && pwd)

die() { printf 'ABORT: %s\n' "$1" >&2; exit 1; }

TENANT=${TENANT:-gerege}
# A tenant identifier becomes a directory name below, so it is validated as one path segment.
case "$TENANT" in
  '' | *[!a-z0-9_-]* ) die "TENANT='$TENANT' is not a valid tenant identifier (expected [a-z0-9_-]+)." ;;
esac

# --- property 2: the output directory derives from the tenant actually used ---------------------
O=${RECAPTURE_OUT:-$D/out/recapture-$TENANT}
Obase=$(basename "$O")
case "$Obase" in
  "$TENANT" | *-"$TENANT" ) : ;;
  * ) die "output directory '$O' is not named for tenant '$TENANT'. A capture must be filed under the tenant it was taken from; refusing to write '$TENANT' bytes into a directory called '$Obase'." ;;
esac

STAMP=$O/CAPTURED-FROM-TENANT
if [ -f "$STAMP" ]; then
  prev=$(head -1 "$STAMP" | tr -d '\r')
  [ "$prev" = "$TENANT" ] || die "'$O' already holds a capture set taken from tenant '$prev' (see $STAMP); refusing to overwrite it with a '$TENANT' capture."
fi
mkdir -p "$O" || die "cannot create output directory '$O'"
printf '%s\n' "$TENANT" > "$STAMP"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T="Fineract-Platform-TenantId: $TENANT"
CT='Content-Type: application/json'

echo "### tenant '$TENANT'  ->  output directory $O"
echo
echo "### preconditions (T22 P0-4) — a breach ABORTS before any capture"
prestatus=0
CANARY_REQ="$W/t22-audit/req/calc-pmode2-gerege.json" \
  sh "$D/preconditions.sh" "$TENANT" > "$O/preconditions.txt" 2>&1 || prestatus=$?
cat "$O/preconditions.txt"
# Operand 1: the exit status preconditions.sh actually emits.
# Operand 2: FAIL lines in a transcript that now captures BOTH streams (the bug T77 found was that
# it captured only stdout, where a FAIL line never appears).  Either one aborts.
prefails=$(grep -c '^  FAIL' "$O/preconditions.txt" || true)
if [ "$prestatus" -ne 0 ] || [ "$prefails" != "0" ]; then
  echo >&2
  die "preconditions breached — exit status $prestatus, $prefails FAIL line(s) in $O/preconditions.txt. NOTHING WAS CAPTURED. Any file already in '$O' is from an earlier run and is NOT an observation of this environment."
fi

echo
echo "### product persistence read-back, from PostgreSQL rows not from the create response"
SCHEMA=$(docker exec fineract-db-1 psql -U root -d fineract_tenants -At \
  -c "select c.schema_name from tenants t join tenant_server_connections c on c.id=t.oltp_id where t.identifier='$TENANT';" | tr -d '\r')
[ -n "$SCHEMA" ] || die "no schema_name for tenant '$TENANT' — cannot read the product rows back."
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select to_jsonb(t) from m_product_loan t where id in (1,2,3,4) order by id;" > "$O/products-asrow.jsonl"
docker exec fineract-db-1 psql -U root -d "$SCHEMA" -At \
  -c "select id, coalesce(installment_amount_in_multiples_of::text,'NULL'), coalesce(days_in_year_custom_strategy,'NULL') from m_product_loan where id in (1,2,3,4) order by id;"

echo
echo "### captures — explicit filenames, HTTP status checked, non-200 fails the run"
set -e
for pair in "01:calc-B-01-baseline:B-01-baseline" \
            "02:calc-B-02-multiplesof100:B-02-multiplesof100" \
            "03:calc-B-03-diycs-fullleapyear:B-03-diycs-fullleapyear" \
            "04:calc-B-04-diycs-feb29only:B-04-diycs-feb29only"; do
  n=${pair%%:*}; rest=${pair#*:}; req=${rest%%:*}; outname=${rest#*:}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
              -H "$A" -H "$T" -H "$CT" -d @"$W/req/$req.json" \
              -o "$O/$outname-raw.json" -w '%{http_code}')
  echo "B-$n  HTTP $code  -> $O/$outname-raw.json"
  if [ "$code" != "200" ]; then
    echo "CAPTURE FAILED: B-$n returned HTTP $code — the file is an ERROR BODY, not a capture." >&2
    exit 1
  fi
done

echo
shasum -a 256 "$O"/B-0*-raw.json
echo
echo "captured from tenant '$TENANT' (stamped in $STAMP)"
