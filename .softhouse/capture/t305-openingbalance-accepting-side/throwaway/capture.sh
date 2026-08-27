#!/bin/sh
# T305 -- THE ACCEPTING-SIDE CAPTURE. This is the ONE script in this program that fires a WRITE
# THAT CANNOT BE UNDONE: an accepted opening balance is a posted journal entry, and Fineract has
# NO delete path for a journal entry (no @DELETE anywhere under
# fineract-provider/src/main/java/org/apache/fineract/accounting/; the only undo is
# POST /journalentries/{transactionId}?command=reverse, which APPENDS reversing entries).
#
# SO THE FENCE HERE IS ON THE TARGET, NOT ON THE BODY. P-92's content fence -- the trick T294 used,
# a body unbalanced by one minor unit that cannot post whatever the tenant looks like -- IS NOT
# AVAILABLE TO AN ACCEPTING CAPTURE: a body that cannot post is not an accept. Five target
# conditions, ALL of which must hold, and every one of them fails closed:
#
#   F1  the base URL names port 8444 and the tenant header names `t305`  (the standing reference
#       oracle is 8443 / `gerege`, and no value of the environment can make those look alike)
#   F2  the container t305-oracle-app is RUNNING and t305-oracle-db answers
#   F3  the target's OWN tenant registry says identifier `t305`, database `fineract_t305`,
#       timezone Asia/Ulaanbaatar, rounding-mode 4 -- read from the target, not from this file
#   F4  the target's acc_gl_journal_entry is EMPTY (this is the accepting precondition itself:
#       :812 CollectionUtils.isEmpty(transactionIds)); a non-empty ledger means either the capture
#       already ran or the target is not what it claims
#   F5  the STANDING reference oracle's four counters equal the baseline recorded by
#       guard-throwaway-isolation.sh -- so a run that somehow reached the standing stack is
#       detected before, and again after, the POST
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"
OUT="$DIR/out"
REQ="$DIR/req"
mkdir -p "$OUT" "$REQ"
STANDING_DB=fineract-db-1
BASE="$OUT/STANDING-baseline.txt"

say() { printf '%s\n' "$*"; }
refuse() { say "REFUSE: $*"; exit 1; }

say "T305 accepting-side capture -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say ""

# ---- F1 ---------------------------------------------------------------------------------
case "$B" in *:8444/fineract-provider/api/v1) ;; *) refuse "F1 base URL '$B' is not the throwaway's :8444 endpoint." ;; esac
case "$T" in "Fineract-Platform-TenantId: t305") ;; *) refuse "F1 tenant header '$T' is not 't305'." ;; esac
say "ok  F1 target is $B, tenant header '$T'."

# ---- F2 ---------------------------------------------------------------------------------
docker ps --format '{{.Names}}' | grep -qx t305-oracle-app || refuse "F2 t305-oracle-app is not running."
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT 1' >/dev/null 2>&1 || refuse "F2 $DBC/$DBNAME unreachable."
say "ok  F2 t305-oracle-app running, $DBC/$DBNAME reachable."

# ---- F3 -- read the target's own registry ------------------------------------------------
REG=$(docker exec -i "$DBC" psql -U "$DBUSER" -d fineract_tenants -At -F'|' -c \
  "SELECT t.identifier, t.timezone_id, c.schema_name FROM tenants t JOIN tenant_server_connections c ON c.id=t.oltp_id ORDER BY t.id")
[ "$REG" = "t305|Asia/Ulaanbaatar|fineract_t305" ] || refuse "F3 target registry reads '$REG', not 't305|Asia/Ulaanbaatar|fineract_t305'."
RM=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT value FROM c_configuration WHERE name='rounding-mode'")
[ "$RM" = "4" ] || refuse "F3 target rounding-mode is '$RM', not 4 (HALF_UP, CLAUDE.md-ratified)."
say "ok  F3 registry '$REG', rounding-mode 4 (HALF_UP) -- read from the target."

# ---- F4 ---------------------------------------------------------------------------------
JE=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_journal_entry")
[ "$JE" = "0" ] || refuse "F4 target already has $JE journal entries; the accepting precondition (:812) does not hold."
say "ok  F4 target ledger is EMPTY -- findNonContraTransactionIds returns [] and :812 falls through."

# ---- F5 ---------------------------------------------------------------------------------
[ -f "$BASE" ] || refuse "F5 no standing baseline at $BASE. Run guard-throwaway-isolation.sh | tee out/STANDING-baseline.txt first."
check_standing() {
  phase=$1
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
    "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" ; do
    label=$(printf '%s' "$q" | cut -d'|' -f1)
    sql=$(printf '%s' "$q" | cut -d'|' -f2-)
    now=$(docker exec -i "$STANDING_DB" psql -U root -d fineract_gerege -Atc "$sql" 2>/dev/null)
    want=$(grep "gerege $label = " "$BASE" | sed "s/.*gerege $label = //")
    [ -n "$now" ] || refuse "F5 ($phase) could not read standing '$label'."
    [ -n "$want" ] || refuse "F5 ($phase) baseline carries no '$label'."
    [ "$now" = "$want" ] || refuse "F5 ($phase) STANDING ORACLE MOVED: $label baseline '$want', now '$now'."
    say "    standing $label = $now (== baseline)"
  done
}
say "ok  F5 standing reference oracle, BEFORE the POST:"
check_standing before

# ---- the body ----------------------------------------------------------------------------
# THREE LEGS, TWO DEBITS AND ONE CREDIT, WITH DIFFERENT AMOUNTS AND NON-ZERO MINOR UNITS.
# Not one debit and one credit, because :791/:796 write the leg entry AND its contra entry INSIDE
# the per-leg loop -- so a two-leg body cannot distinguish a port that writes one contra entry PER
# LEG from one that writes a single summed contra entry, and a three-leg body can.
# 250000.25 + 100000.37 = 350000.62 exactly, in MNT minor units: 25000025 + 10000037 = 35000062.
CONTRA=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-3000'")
D1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-1000'")
D2=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-1100'")
C1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-2000'")
for v in "$CONTRA" "$D1" "$D2" "$C1"; do [ -n "$v" ] || refuse "a target GL account id could not be read; run setup.sh first."; done
FA=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT gl_account_id FROM acc_gl_financial_activity_account WHERE financial_activity_type=300")
[ "$FA" = "$CONTRA" ] || refuse "financial activity 300 maps to '$FA', not the contra account $CONTRA."

cat > "$REQ/ob-accept-01.json" <<JSON
{
  "officeId": 1,
  "transactionDate": "2026-01-01",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en",
  "currencyCode": "MNT",
  "comments": "T305 accepting-side opening balance, captured on the THROWAWAY instance (tenant t305, HALF_UP, Asia/Ulaanbaatar, empty ledger). Balanced: 250000.25 + 100000.37 = 350000.62.",
  "debits": [
    {
      "glAccountId": $D1,
      "amount": 250000.25
    },
    {
      "glAccountId": $D2,
      "amount": 100000.37
    }
  ],
  "credits": [
    {
      "glAccountId": $C1,
      "amount": 350000.62
    }
  ]
}
JSON

NAME=OB-ACCEPT-01-openingbalance-empty-ledger
IDEM=t305-ob-accept-01
cp "$REQ/ob-accept-01.json" "$OUT/$NAME.req"
say ""
say "FIRING: POST /journalentries?command=defineOpeningBalance  (an IRREVERSIBLE write, on a DISPOSABLE instance)"
# Idempotency-Key on every money-movement POST -- CLAUDE.md non-negotiable, and the convention the
# tierA-a2 rig's own .http sidecars already follow. EACH ARM OF THIS RIG USES A DISTINCT KEY, which
# matters more here than anywhere else in the program: capture2.sh re-sends BYTE-IDENTICAL bodies
# expecting DIFFERENT answers, and a shared key would have Fineract return the FIRST arm's cached
# result instead of executing the second -- a dedupe that would look exactly like an observation.
CODE=$(curl -sk -o "$OUT/$NAME.json" -w '%{http_code}' -X POST \
  "$B/journalentries?command=defineOpeningBalance" -H "$A" -H "$T" -H "$CT" \
  -H "Idempotency-Key: $IDEM" \
  --data-binary "@$OUT/$NAME.req")
printf '%s' "$CODE" > "$OUT/$NAME.status"
say "HTTP $CODE"
cat "$OUT/$NAME.json"; printf '\n'
shasum -a 256 "$OUT/$NAME.req" | awk '{print $1}' > "$OUT/$NAME.req.sha256"
shasum -a 256 "$OUT/$NAME.json" | awk '{print $1}' > "$OUT/$NAME.json.sha256"
CAPTURED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' "$CAPTURED_AT" > "$OUT/$NAME.captured-at-utc"
# THE .http SIDECAR, in the tierA-a2 rig's format. admit.go resolves a vector's
# provenance.capture_case_id against the artefact's BYTES first and the sidecar SECOND, and refuses
# a citation that resolves by FILE NAME ONLY -- because that branch reads zero bytes of the
# artefact and passes whenever the ref was spelled from the case id. The oracle cannot put our case
# id in its response; the rig can put it here, and this is the rig doing it AT CAPTURE TIME.
{
  printf 'POST /journalentries?command=defineOpeningBalance\n'
  printf 'case-id: %s\n' "$NAME"
  printf 'instance: THROWAWAY t305-oracle-app, image fineract:latest (same image id as the standing fineract-fineract-1), port 8444\n'
  printf 'Fineract-Platform-TenantId: t305\n'
  printf 'Authorization: Basic <mifos:password>\n'
  printf 'Idempotency-Key: %s\n' "$IDEM"
  printf 'Content-Type: application/json\n'
  printf 'body-file: req/ob-accept-01.json\n'
  printf 'body-wire-bytes-artefact: %s.req\n' "$NAME"
  printf 'body-sha256: %s\n' "$(cat "$OUT/$NAME.req.sha256")"
  printf 'body-bytes: %s\n' "$(wc -c < "$OUT/$NAME.req" | tr -d ' ')"
  printf 'response-status: %s\n' "$CODE"
  printf 'captured-at-utc: %s\n' "$CAPTURED_AT"
} > "$OUT/$NAME.http"

# ---- the read-backs ----------------------------------------------------------------------
TXN=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("transactionId",""))' "$OUT/$NAME.json" 2>/dev/null || echo "")
if [ -n "$TXN" ]; then
  RB=OB-ACCEPT-01-readback-rest
  curl -sk -o "$OUT/$RB.json" -w '%{http_code}' -X GET \
    "$B/journalentries?transactionId=$TXN&limit=50" -H "$A" -H "$T" > "$OUT/$RB.status"
  shasum -a 256 "$OUT/$RB.json" | awk '{print $1}' > "$OUT/$RB.json.sha256"
  say "readback REST: HTTP $(cat "$OUT/$RB.status")  transactionId=$TXN"

  {
    printf 'GET /journalentries?transactionId=%s&limit=50\n' "$TXN"
    printf 'case-id: %s\n' "$RB"
    printf 'Fineract-Platform-TenantId: t305\n'
    printf 'instance: THROWAWAY t305-oracle-app, port 8444\n'
    printf 'response-status: %s\n' "$(cat "$OUT/$RB.status")"
    printf 'response-sha256: %s\n' "$(cat "$OUT/$RB.json.sha256")"
    printf 'captured-at-utc: %s\n' "$CAPTURED_AT"
  } > "$OUT/$RB.http"

  DB=OB-ACCEPT-01-readback-db
  docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -c \
    "SELECT json_agg(row_to_json(t) ORDER BY t.id)::text FROM (SELECT j.id, j.transaction_id, j.account_id, a.gl_code, a.classification_enum, j.type_enum, j.amount::text AS amount_major_text, j.entry_date::text, j.manual_entry, j.office_id, j.currency_code, j.reversed, j.reversal_id, j.is_running_balance_calculated FROM acc_gl_journal_entry j JOIN acc_gl_account a ON a.id=j.account_id ORDER BY j.id) t" \
    > "$OUT/$DB.json"
  shasum -a 256 "$OUT/$DB.json" | awk '{print $1}' > "$OUT/$DB.json.sha256"
  # The readback's own sidecar. A psql projection has no HTTP request to record, so what it records
  # is the SEAM and the QUERY -- which is what a reader re-deriving this artefact needs, and it is
  # the reason admit.go accepts a sidecar at all: the oracle cannot know our case id and the rig can.
  {
    printf 'PSQL SELECT (seam ledger_db_readback)\n'
    printf 'case-id: %s\n' "$DB"
    printf 'container: %s   database: %s   tenant: t305\n' "$DBC" "$DBNAME"
    printf 'instance: THROWAWAY, destroyed by down.sh in the same run\n'
    printf 'query: json_agg over acc_gl_journal_entry JOIN acc_gl_account, ordered by j.id, amounts as ::text at the stored scale of 6\n'
    printf 'transaction-id: %s\n' "$TXN"
    printf 'response-sha256: %s\n' "$(cat "$OUT/$DB.json.sha256")"
    printf 'captured-at-utc: %s\n' "$CAPTURED_AT"
  } > "$OUT/$DB.http"
  say "readback DB written to out/$DB.json"
fi

say ""
say "ok  F5 standing reference oracle, AFTER the POST:"
check_standing after
say ""
say "CAPTURED. The instance that produced this is DISPOSABLE; run down.sh to destroy it."
