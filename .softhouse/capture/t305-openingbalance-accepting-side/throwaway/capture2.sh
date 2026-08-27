#!/bin/sh
# T305 -- THE STATE-TRANSITION SEQUENCE, taken on the SAME throwaway instance immediately after
# capture.sh, because the first capture CHANGES THE TENANT'S STATE and the change is the thing
# worth observing.
#
# THE THREE ARMS, IN ORDER, AND WHAT EACH ONE IS FOR:
#
#   A2  OB-ACCEPT-02  -- the SAME REQUEST BYTES capture.sh fired, re-fired now that six journal
#       entries exist. THE FIRST DRAFT OF THIS SCRIPT NAMED THIS ARM `OB-REFUSE-02` AND PREDICTED
#       A 403. IT GOT HTTP 200. That prediction failure is the largest finding of this task and it
#       is recorded here rather than tidied away: `findNonContraTransactionIds(contraId)` EXCLUDES
#       every transaction that touches the CONTRA account, and every entry an opening balance
#       writes touches it (:796 writes the contra leg). So an opening balance does not block the
#       next opening balance -- the oracle REVERSES the previous one (:726-735
#       findNonReversedContraTransactionIds -> revertJournalEntry) and posts the new one.
#       THE RULE IS NOT "ONCE ANY JOURNAL ENTRY HAS BEEN POSTED", which is what the oracle's own
#       message at :814 says and what this corpus repeated. It is "once any NON-CONTRA journal
#       entry has been posted".
#
#   A3  MJE-ACCEPT-01 -- a PLAIN manual journal entry (no ?command=), balanced. It is the first
#       NON-CONTRA transaction on this tenant, so it both (i) is accepted while opening balances
#       exist -- the shape T296 arm B (refuse whenever the id list is non-empty, never read the
#       command) refuses -- and (ii) ARMS the refusal that A4 then observes.
#
#   A4  OB-REFUSE-03 -- the SAME REQUEST BYTES again, now that one non-contra transaction exists.
#       HTTP 403, error.msg.journalentry.defining.openingbalance.not.allowed, and errors[0].args
#       carries EXACTLY the one transaction id A3 created. Same bytes, same tenant, same instance,
#       three answers in sequence: ACCEPT, ACCEPT-with-reversal, REFUSE. The predicate is the
#       LEDGER'S CONTENT, not the command and not the tenant.
#
# SAME FENCES AS capture.sh, one INVERTED: F4' requires the ledger to be NON-EMPTY.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"
OUT="$DIR/out"; REQ="$DIR/req"; mkdir -p "$OUT" "$REQ"
STANDING_DB=fineract-db-1
BASE="$OUT/STANDING-baseline.txt"
say() { printf '%s\n' "$*"; }
refuse() { say "REFUSE: $*"; exit 1; }

say "T305 state-transition captures -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
case "$B" in *:8444/fineract-provider/api/v1) ;; *) refuse "F1 base URL '$B' is not the throwaway's :8444 endpoint." ;; esac
case "$T" in "Fineract-Platform-TenantId: t305") ;; *) refuse "F1 tenant header '$T' is not 't305'." ;; esac
docker ps --format '{{.Names}}' | grep -qx t305-oracle-app || refuse "F2 t305-oracle-app is not running."
REG=$(docker exec -i "$DBC" psql -U "$DBUSER" -d fineract_tenants -At -F'|' -c \
  "SELECT t.identifier, t.timezone_id, c.schema_name FROM tenants t JOIN tenant_server_connections c ON c.id=t.oltp_id ORDER BY t.id")
[ "$REG" = "t305|Asia/Ulaanbaatar|fineract_t305" ] || refuse "F3 target registry reads '$REG'."
JE=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_journal_entry")
[ "$JE" -gt 0 ] || refuse "F4' the target ledger is EMPTY; run capture.sh first."
say "ok  F1/F2/F3 target is the throwaway; F4' ledger carries $JE entries."
[ -f "$BASE" ] || refuse "F5 no standing baseline at $BASE."
check_standing() {
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" ; do
    label=$(printf '%s' "$q" | cut -d'|' -f1); sql=$(printf '%s' "$q" | cut -d'|' -f2-)
    now=$(docker exec -i "$STANDING_DB" psql -U root -d fineract_gerege -Atc "$sql" 2>/dev/null)
    want=$(grep "gerege $label = " "$BASE" | sed "s/.*gerege $label = //")
    [ "$now" = "$want" ] || refuse "F5 ($1) STANDING ORACLE MOVED: $label baseline '$want', now '$now'."
    say "ok  F5 ($1) standing $label = $now (== baseline)"
  done
}
check_standing before

fire() {  # fire <name> <path> <bodyfile> <idempotency-key>
  name=$1; path=$2; body=$3; idem=$4
  cp "$body" "$OUT/$name.req"
  # A DISTINCT Idempotency-Key PER ARM IS LOAD-BEARING HERE, not hygiene. A2 and A4 re-send bytes
  # IDENTICAL to capture.sh's, expecting different answers; sharing a key would have Fineract
  # return the first arm's CACHED result and the transcript would look like an observation.
  code=$(curl -sk -o "$OUT/$name.json" -w '%{http_code}' -X POST "$B$path" -H "$A" -H "$T" -H "$CT" \
    -H "Idempotency-Key: $idem" --data-binary "@$OUT/$name.req")
  printf '%s' "$code" > "$OUT/$name.status"
  shasum -a 256 "$OUT/$name.req"  | awk '{print $1}' > "$OUT/$name.req.sha256"
  shasum -a 256 "$OUT/$name.json" | awk '{print $1}' > "$OUT/$name.json.sha256"
  at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '%s\n' "$at" > "$OUT/$name.captured-at-utc"
  {
    printf 'POST %s\n' "$path"
    printf 'case-id: %s\n' "$name"
    printf 'instance: THROWAWAY t305-oracle-app, port 8444, destroyed by down.sh in the same run\n'
    printf 'Fineract-Platform-TenantId: t305\n'
    printf 'Authorization: Basic <mifos:password>\n'
    printf 'Idempotency-Key: %s\n' "$idem"
    printf 'Content-Type: application/json\n'
    printf 'body-wire-bytes-artefact: %s.req\n' "$name"
    printf 'body-sha256: %s\n' "$(cat "$OUT/$name.req.sha256")"
    printf 'body-bytes: %s\n' "$(wc -c < "$OUT/$name.req" | tr -d ' ')"
    printf 'response-status: %s\n' "$code"
    printf 'captured-at-utc: %s\n' "$at"
  } > "$OUT/$name.http"
  say ""
  say "$name"
  say "  POST $path -> HTTP $code"
  cat "$OUT/$name.json"; printf '\n'
}

PREV="$OUT/OB-ACCEPT-01-openingbalance-empty-ledger.req"
[ -f "$PREV" ] || refuse "capture.sh's request bytes are missing; the point of A2 and A4 is that the bytes are IDENTICAL."

# ---- A2 --------------------------------------------------------------------------------------
fire OB-ACCEPT-02-openingbalance-after-own-openingbalance "/journalentries?command=defineOpeningBalance" "$PREV" t305-ob-accept-02
cmp "$PREV" "$OUT/OB-ACCEPT-02-openingbalance-after-own-openingbalance.req" \
  && say "  cmp silent: byte-identical request to OB-ACCEPT-01."

# ---- A3 --------------------------------------------------------------------------------------
D1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-1000'")
C1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-2000'")
cat > "$REQ/mje-accept-01.json" <<JSON
{
  "officeId": 1,
  "transactionDate": "2026-01-02",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en",
  "currencyCode": "MNT",
  "comments": "T305 companion capture: a PLAIN manual journal entry posted while opening-balance transactions already exist. Balanced: debit 500000.11 = credit 500000.11.",
  "debits": [
    {
      "glAccountId": $D1,
      "amount": 500000.11
    }
  ],
  "credits": [
    {
      "glAccountId": $C1,
      "amount": 500000.11
    }
  ]
}
JSON
fire MJE-ACCEPT-01-manual-entry-alongside-openingbalance "/journalentries" "$REQ/mje-accept-01.json" t305-mje-accept-01

say ""
say "findNonContraTransactionIds on the target NOW (this is what A4 is fired against):"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT DISTINCT j.transaction_id FROM acc_gl_journal_entry j WHERE j.transaction_id NOT IN (SELECT DISTINCT je.transaction_id FROM acc_gl_journal_entry je WHERE je.account_id = (SELECT gl_account_id FROM acc_gl_financial_activity_account WHERE financial_activity_type=300)) ORDER BY 1" \
  | tee "$OUT/NONCONTRA-ids-before-A4.txt"

# ---- A4 --------------------------------------------------------------------------------------
fire OB-REFUSE-03-openingbalance-after-noncontra-entry "/journalentries?command=defineOpeningBalance" "$PREV" t305-ob-refuse-03
cmp "$PREV" "$OUT/OB-REFUSE-03-openingbalance-after-noncontra-entry.req" \
  && say "  cmp silent: byte-identical request to OB-ACCEPT-01 AND to OB-ACCEPT-02 -- three answers, one body."

# ---- the state all three were taken against ---------------------------------------------------
say ""
say "audit rows this instance wrote (id | action | entity | resource_id | status):"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -F'|' -c \
  "SELECT id, action_name, entity_name, coalesce(resource_id::text,'NULL'), status FROM m_portfolio_command_source ORDER BY id" \
  | tee "$OUT/COMMAND-SOURCE-audit.txt"
say ""
say "final ledger (id | transaction | account | type_enum | amount | reversed | reversal_id):"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -F'|' -c \
  "SELECT id, transaction_id, account_id, type_enum, amount::text, reversed, coalesce(reversal_id::text,'NULL') FROM acc_gl_journal_entry ORDER BY id" \
  | tee "$OUT/FINAL-ledger.txt"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -c \
  "SELECT json_agg(row_to_json(t) ORDER BY t.id)::text FROM (SELECT j.id, j.transaction_id, j.account_id, a.gl_code, a.classification_enum, j.type_enum, j.amount::text AS amount_major_text, j.entry_date::text, j.manual_entry, j.office_id, j.currency_code, j.reversed, j.reversal_id FROM acc_gl_journal_entry j JOIN acc_gl_account a ON a.id=j.account_id ORDER BY j.id) t" \
  > "$OUT/FINAL-ledger-db.json"
shasum -a 256 "$OUT/FINAL-ledger-db.json" | awk '{print $1}' > "$OUT/FINAL-ledger-db.json.sha256"

say ""
check_standing after
