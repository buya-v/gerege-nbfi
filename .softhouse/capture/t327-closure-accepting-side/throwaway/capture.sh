#!/bin/sh
# T327 -- THE CLOSURE-BOUNDARY AND BUSINESS-DATE ACCEPTING-SIDE CAPTURE.
# T295 backlog B-1 and B-2, fired on a DISPOSABLE instance rather than on the standing oracle.
#
# WHY THIS EXISTS AT ALL. LDG-REFUSE-04 pins `transactionDate <= closingDate` REFUSED and
# LDG-REFUSE-05 pins `businessDate + 1` REFUSED. Both are refusals. **A PORT THAT REFUSES EVERY
# DATED ENTRY PASSES BOTH AND SURVIVES THE ENTIRE CORPUS** -- the same mutant shape T305 killed for
# opening balances (T296 arm A). Nothing in this store observes either rule ACCEPTING anything.
#
# WHY IT IS SAFE NOW WHEN T295 SAID IT WAS NOT. T295 declined for ONE stated reason: "two permanent
# acc_gl_journal_entry rows, je_rows 60 -> 62 ... it converts an [UNVERIFIED] into a vector at the
# price of CONTAMINATING THE ORACLE". A journal entry still cannot be deleted. AN INSTANCE CAN.
#
# THE FENCE IS ON THE TARGET, NOT ON THE BODY -- T305's finding, inherited verbatim. P-92's content
# fence (a body unbalanced by one minor unit, unpostable on its own content) IS NOT AVAILABLE to an
# accepting capture: a body that cannot post is not an accept. F1-F5, all fail-closed:
#   F1  base URL names port 8444 and the tenant header names `t327` (standing: 8443 / `gerege`)
#   F2  t327-oracle-app is RUNNING and t327-oracle-db answers
#   F3  the target's OWN tenant registry says identifier `t327`, database `fineract_t327`,
#       timezone Asia/Ulaanbaatar, rounding-mode 4 -- read FROM THE TARGET, not from this file
#   F4  the target's acc_gl_journal_entry AND acc_gl_closure are BOTH EMPTY
#   F5  the STANDING reference oracle's six counters equal the baseline recorded by
#       guard-throwaway-isolation.sh -- re-checked BEFORE and AFTER every accepting POST
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

say "T327 closure/business-date accepting-side capture -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say ""

# ---- F1 ---------------------------------------------------------------------------------
case "$B" in *:8444/fineract-provider/api/v1) ;; *) refuse "F1 base URL '$B' is not the throwaway's :8444 endpoint." ;; esac
case "$T" in "Fineract-Platform-TenantId: t327") ;; *) refuse "F1 tenant header '$T' is not 't327'." ;; esac
say "ok  F1 target is $B, tenant header '$T'."

# ---- F2 ---------------------------------------------------------------------------------
docker ps --format '{{.Names}}' | grep -qx t327-oracle-app || refuse "F2 t327-oracle-app is not running."
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT 1' >/dev/null 2>&1 || refuse "F2 $DBC/$DBNAME unreachable."
say "ok  F2 t327-oracle-app running, $DBC/$DBNAME reachable."

# ---- F3 -- read the target's own registry ------------------------------------------------
REG=$(docker exec -i "$DBC" psql -U "$DBUSER" -d fineract_tenants -At -F'|' -c \
  "SELECT t.identifier, t.timezone_id, c.schema_name FROM tenants t JOIN tenant_server_connections c ON c.id=t.oltp_id WHERE t.identifier='t327'")
[ "$REG" = "t327|Asia/Ulaanbaatar|fineract_t327" ] || refuse "F3 target registry reads '$REG', not 't327|Asia/Ulaanbaatar|fineract_t327'."
RM=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT value FROM c_configuration WHERE name='rounding-mode'")
[ "$RM" = "4" ] || refuse "F3 target rounding-mode is '$RM', not 4 (HALF_UP, CLAUDE.md-ratified)."
say "ok  F3 registry '$REG', rounding-mode 4 (HALF_UP) -- read from the target."
printf 'registry=%s\nrounding-mode=%s\n' "$REG" "$RM" > "$OUT/F3-target-registry.txt"

# ---- F4 ---------------------------------------------------------------------------------
JE=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_journal_entry")
[ "$JE" = "0" ] || refuse "F4 target already has $JE journal entries; this capture must start on an empty ledger."
CL=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_closure")
[ "$CL" = "0" ] || refuse "F4 target already has $CL GL closures; arm B2 requires none."
say "ok  F4 target ledger EMPTY (0 journal entries) and NO GL closure -- arm B2 is unconfounded."

# ---- F5 ---------------------------------------------------------------------------------
[ -f "$BASE" ] || refuse "F5 no standing baseline at $BASE. Run guard-throwaway-isolation.sh first."
check_standing() {
  phase=$1
  for q in \
    "acc_gl_journal_entry|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_journal_entry" \
    "acc_gl_closure|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure" \
    "distinct_transaction_id|SELECT count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry" \
    "m_portfolio_command_source|SELECT count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source" \
    "m_loan|SELECT count(*)::text FROM m_loan" \
    "m_office|SELECT count(*)::text FROM m_office" ; do
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
say "ok  F5 standing reference oracle, BEFORE anything is fired:"
check_standing before-any-post

# ---- THE DATES ---------------------------------------------------------------------------
# THE BUSINESS DATE IS DERIVED HERE AND THEN PROVED ON THE WIRE, AND THE DIFFERENCE MATTERS.
# `enable-business-date` is off on a fresh tenant, so BusinessDateReadPlatformServiceImpl:74-76
# seeds BUSINESS_DATE with `DateUtils.getLocalDateOfTenant()` = `LocalDate.now(tenant zone)`
# [DateUtils.java:70-72]. The tenant zone is Asia/Ulaanbaatar, verified from the TARGET at F3.
# So the DERIVED candidate is today in Asia/Ulaanbaatar -- but a derived value is not an
# observation (T305's own Unverified section says exactly that), so arms B2-ACCEPT-01 and
# B2-CTRL-02 together MEASURE it: BD accepted => businessDate >= BD; BD+1 refused => businessDate
# < BD+1; therefore businessDate == BD, from the wire.
#
# TODAY THAT ALSO SEPARATES THE TENANT ZONE FROM UTC, by luck of the hour: the run opens at
# roughly 17:30 UTC, so UTC's date is one day BEHIND Asia/Ulaanbaatar's. A port (or an instance)
# reading the business date in UTC would refuse BD as future. This is recorded because it is
# discriminating today and will not be discriminating at every hour.
BD=$(TZ=Asia/Ulaanbaatar date +%Y-%m-%d)
d() { python3 -c 'import sys,datetime; print(datetime.date.fromisoformat(sys.argv[1])+datetime.timedelta(days=int(sys.argv[2])))' "$BD" "$1"; }
BD1=$(d 1)     # business date + 1  -- must be REFUSED (future)
CLOSE=$(d -2)  # the GLClosure closing date D
DP1=$(d -1)    # D + 1 -- the B-1 acceptance; also <= BD, so :630 cannot answer first
DM1=$(d -3)    # D - 1 -- strictly before the closure; a free control for the args asymmetry

{
  printf 'derived-business-date-candidate (today in Asia/Ulaanbaatar) = %s\n' "$BD"
  printf 'business-date-plus-1                                        = %s\n' "$BD1"
  printf 'glclosure closing date D                                    = %s\n' "$CLOSE"
  printf 'D + 1 (the B-1 acceptance)                                  = %s\n' "$DP1"
  printf 'D - 1 (free control)                                        = %s\n' "$DM1"
  printf 'host UTC now                                                = %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'host UTC date                                               = %s\n' "$(date -u +%Y-%m-%d)"
  printf 'target db now()                                             = %s\n' \
    "$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT now()::text')"
  printf 'target enable-business-date row                             = %s\n' \
    "$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT coalesce((SELECT name||'='||value FROM c_configuration WHERE name='enable-business-date'),'(no such row)')")"
  printf 'target m_business_date row count                            = %s\n' \
    "$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT count(*) FROM m_business_date')"
} | tee "$OUT/DATES.txt"

# The endpoint's own view, read-only, for the record.
curl -sk -o "$OUT/S-07-businessdates.json" -w '%{http_code}' -X GET "$B/businessdates" -H "$A" -H "$T" > "$OUT/S-07-businessdates.status"
say "GET /businessdates -> HTTP $(cat "$OUT/S-07-businessdates.status") $(cat "$OUT/S-07-businessdates.json")"

# ---- account ids, read from the target ---------------------------------------------------
D1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T327-1000'")
D2=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T327-1100'")
C1=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T327-2000'")
for v in "$D1" "$D2" "$C1"; do [ -n "$v" ] || refuse "a target GL account id could not be read; run setup.sh first."; done
say "GL ids: debit1=$D1 debit2=$D2 credit=$C1"

# ---- the body builder --------------------------------------------------------------------
# THREE LEGS, TWO DEBITS AND ONE CREDIT, DIFFERENT AMOUNTS, NON-ZERO MINOR UNITS.
# Checked as INTEGER MINOR UNITS, which is the only arithmetic this program permits on money:
#   25000025 + 10000037 = 35000062.  The decimal characters below are the WIRE FORMAT the oracle's
#   own API speaks; nothing in this rig does floating-point arithmetic on them.
# The amounts are identical to T305's, deliberately, so a promoting task can compare an accepted
# plain manual entry against an accepted opening balance without a second variable moving.
mkbody() {  # mkbody <outfile> <transactionDate> <comment>
  cat > "$1" <<JSON
{
  "officeId": 1,
  "transactionDate": "$2",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en",
  "currencyCode": "MNT",
  "comments": "$3",
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
}

# fire <NAME> <bodyfile> <idempotency-key> <path> <human note>
fire() {
  NAME=$1; BODY=$2; IDEM=$3; PATH_=$4; NOTE=$5
  cp "$BODY" "$OUT/$NAME.req"
  say ""
  say "FIRING $NAME -- $NOTE"
  CODE=$(curl -sk -o "$OUT/$NAME.json" -w '%{http_code}' -X POST \
    "$B$PATH_" -H "$A" -H "$T" -H "$CT" -H "Idempotency-Key: $IDEM" \
    --data-binary "@$OUT/$NAME.req")
  printf '%s' "$CODE" > "$OUT/$NAME.status"
  say "HTTP $CODE"
  cat "$OUT/$NAME.json"; printf '\n'
  shasum -a 256 "$OUT/$NAME.req"  | awk '{print $1}' > "$OUT/$NAME.req.sha256"
  shasum -a 256 "$OUT/$NAME.json" | awk '{print $1}' > "$OUT/$NAME.json.sha256"
  CAPTURED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '%s\n' "$CAPTURED_AT" > "$OUT/$NAME.captured-at-utc"
  # THE .http SIDECAR, in the tierA-a2 rig's format. admit.go resolves a vector's
  # provenance.capture_case_id against the artefact's BYTES first and the sidecar SECOND, and
  # refuses a citation that resolves by FILE NAME ONLY. The oracle cannot put our case id in its
  # response; the rig can put it here, and this is the rig doing it AT CAPTURE TIME.
  {
    printf 'POST %s\n' "$PATH_"
    printf 'case-id: %s\n' "$NAME"
    printf 'instance: THROWAWAY t327-oracle-app, image fineract:latest (same image id as the standing fineract-fineract-1), port 8444\n'
    printf 'Fineract-Platform-TenantId: t327\n'
    printf 'Authorization: Basic <mifos:password>\n'
    printf 'Idempotency-Key: %s\n' "$IDEM"
    printf 'Content-Type: application/json\n'
    printf 'body-wire-bytes-artefact: %s.req\n' "$NAME"
    printf 'body-sha256: %s\n' "$(cat "$OUT/$NAME.req.sha256")"
    printf 'body-bytes: %s\n' "$(wc -c < "$OUT/$NAME.req" | tr -d ' ')"
    printf 'response-status: %s\n' "$CODE"
    printf 'response-sha256: %s\n' "$(cat "$OUT/$NAME.json.sha256")"
    printf 'business-date-candidate: %s (DERIVED today in Asia/Ulaanbaatar; MEASURED by B2-ACCEPT-01 + B2-CTRL-02)\n' "$BD"
    printf 'latest-closing-date-at-fire-time: %s\n' "$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT coalesce(max(closing_date)::text,'(none)') FROM acc_gl_closure WHERE office_id=1")"
    printf 'captured-at-utc: %s\n' "$CAPTURED_AT"
    printf 'note: %s\n' "$NOTE"
  } > "$OUT/$NAME.http"
}

# readback <NAME-PREFIX> <transactionId>
readback() {
  RBN=$1; TXN=$2
  RB="$RBN-readback-rest"
  curl -sk -o "$OUT/$RB.json" -w '%{http_code}' -X GET \
    "$B/journalentries?transactionId=$TXN&limit=50" -H "$A" -H "$T" > "$OUT/$RB.status"
  shasum -a 256 "$OUT/$RB.json" | awk '{print $1}' > "$OUT/$RB.json.sha256"
  say "readback REST: HTTP $(cat "$OUT/$RB.status")  transactionId=$TXN"
  {
    printf 'GET /journalentries?transactionId=%s&limit=50\n' "$TXN"
    printf 'case-id: %s\n' "$RB"
    printf 'Fineract-Platform-TenantId: t327\n'
    printf 'instance: THROWAWAY t327-oracle-app, port 8444\n'
    printf 'response-status: %s\n' "$(cat "$OUT/$RB.status")"
    printf 'response-sha256: %s\n' "$(cat "$OUT/$RB.json.sha256")"
    printf 'captured-at-utc: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/$RB.http"

  DB="$RBN-readback-db"
  docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -c \
    "SELECT json_agg(row_to_json(t) ORDER BY t.id)::text FROM (SELECT j.id, j.transaction_id, j.account_id, a.gl_code, a.classification_enum, j.type_enum, j.amount::text AS amount_major_text, j.entry_date::text, j.manual_entry, j.office_id, j.currency_code, j.reversed, j.reversal_id, j.is_running_balance_calculated FROM acc_gl_journal_entry j JOIN acc_gl_account a ON a.id=j.account_id WHERE j.transaction_id='$TXN' ORDER BY j.id) t" \
    > "$OUT/$DB.json"
  shasum -a 256 "$OUT/$DB.json" | awk '{print $1}' > "$OUT/$DB.json.sha256"
  {
    printf 'PSQL SELECT (seam ledger_db_readback)\n'
    printf 'case-id: %s\n' "$DB"
    printf 'container: %s   database: %s   tenant: t327\n' "$DBC" "$DBNAME"
    printf 'instance: THROWAWAY, destroyed by down.sh in the same run\n'
    printf 'query: json_agg over acc_gl_journal_entry JOIN acc_gl_account for one transaction_id, ordered by j.id, amounts as ::text at the STORED scale\n'
    printf 'transaction-id: %s\n' "$TXN"
    printf 'response-sha256: %s\n' "$(cat "$OUT/$DB.json.sha256")"
    printf 'captured-at-utc: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/$DB.http"
  say "readback DB written to out/$DB.json"
  cat "$OUT/$DB.json"; printf '\n'
}

# txnid <NAME> -- the transaction id of an accepted POST, from the response if it carries one and
# from the target database otherwise. NEVER invented: if neither yields one, the caller is told.
txnid() {
  t=$(python3 -c 'import json,sys
try:
    d=json.load(open(sys.argv[1]))
    print(d.get("transactionId") or "")
except Exception:
    print("")' "$OUT/$1.json" 2>/dev/null || echo "")
  printf '%s' "$t"
}

######################################################################################
# ARM B-2 -- THE STRICTNESS OF THE FUTURE-DATE COMPARISON
#
# LDG-REFUSE-05 pins businessDate + 1 REFUSED. It does NOT distinguish `>` from `>=`; a port
# using `>=` refuses that request too and survives. The capture that separates them is an entry
# dated ON the business date. T295: "the source is unambiguous (isAfter, strict) and the port
# implements the strict reading ... What is missing is a WIRE OBSERVATION, not an answer."
# `DateUtils.isAfter(LocalDate first, LocalDate second)` is `first.isAfter(second)`
# [DateUtils.java:300-302], strict. SO A 200 IS EXPECTED. A REFUSAL WOULD BE THE HEADLINE.
######################################################################################
mkbody "$REQ/b2-accept-01.json" "$BD" "T327 B-2: manual journal entry dated ON the business date, on the THROWAWAY instance (tenant t327, HALF_UP, Asia/Ulaanbaatar, empty ledger, NO GL closure). Balanced: 250000.25 + 100000.37 = 350000.62."
fire B2-ACCEPT-01-entry-on-business-date "$REQ/b2-accept-01.json" t327-b2-accept-01 /journalentries \
  "B-2: transactionDate == the (derived) business date $BD; :630 must NOT fire if isAfter is strict"

TXN1=$(txnid B2-ACCEPT-01-entry-on-business-date)
if [ -n "$TXN1" ]; then
  readback B2-ACCEPT-01 "$TXN1"
else
  say "NOTE: no transactionId in the B2-ACCEPT-01 response body; no read-back taken for it."
fi

say ""
say "ok  F5 standing reference oracle, AFTER the first accepting POST:"
check_standing after-B2-ACCEPT-01

mkbody "$REQ/b2-ctrl-02.json" "$BD1" "T327 B-2 CONTROL: manual journal entry dated ONE DAY AFTER the business date. Expected REFUSAL. Its purpose is to bound the business date from above so that B2-ACCEPT-01's 200 measures it exactly."
fire B2-CTRL-02-entry-one-day-after-business-date "$REQ/b2-ctrl-02.json" t327-b2-ctrl-02 /journalentries \
  "B-2 CONTROL: transactionDate == business date + 1 = $BD1; :630 FUTURE_DATE expected"

######################################################################################
# ARM B-1 -- THE ACCEPTANCE SIDE OF THE CLOSURE BOUNDARY
#
# Precondition: a GLClosure at office 1 with closingDate = D. T295 recorded a TRAP: on the STANDING
# oracle the next closure gets id = 2 because T287's create/delete left is_called = t on the
# sequence. ON A FRESH INSTANCE THAT IS NOT TRUE. The id below is OBSERVED, not predicted.
#
# D is chosen as businessDate - 2 so that D + 1 = businessDate - 1 is ALSO <= the business date.
# If it were not, :630 (FUTURE_DATE) would answer before :636 (ACCOUNTING_CLOSED) and the arm
# would be measuring the wrong rule.
######################################################################################
cat > "$REQ/b1-setup-03-create-closure.json" <<JSON
{
  "officeId": 1,
  "closingDate": "$CLOSE",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en",
  "comments": "T327 B-1 precondition: closure at office 1 so the closure boundary can be probed on both sides."
}
JSON
fire B1-SETUP-03-create-glclosure "$REQ/b1-setup-03-create-closure.json" t327-b1-setup-03 /glclosures \
  "B-1 precondition: GLClosure at office 1, closingDate $CLOSE"

say ""
say "acc_gl_closure on the TARGET after the create (id | office | closing_date) -- OBSERVED, not predicted:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT id||' | '||office_id||' | '||closing_date FROM acc_gl_closure ORDER BY id" | tee "$OUT/B1-closure-state.txt"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT 'last_value='||last_value||' is_called='||is_called FROM acc_gl_closure_id_seq" | tee -a "$OUT/B1-closure-state.txt" || true
curl -sk -o "$OUT/B1-glclosures-list.json" -w '%{http_code}' -X GET "$B/glclosures" -H "$A" -H "$T" > "$OUT/B1-glclosures-list.status"
say "GET /glclosures -> HTTP $(cat "$OUT/B1-glclosures-list.status")"
cat "$OUT/B1-glclosures-list.json"; printf '\n'

# B1-CTRL-04 -- ON the closing date. LDG-REFUSE-04's relation, re-derived on a FRESH instance
# whose acc_gl_closure sequence has never been touched. Expected 403 ACCOUNTING_CLOSED. This is
# the CALIBRATION (P-72, "a sweep is an INSTRUMENT; calibrate it on a known positive before you
# report its negatives"): it proves the closure is live and the boundary INCLUSIVE, which is what
# turns B1-ACCEPT-06's 200 into a statement about the boundary rather than about nothing.
mkbody "$REQ/b1-ctrl-04.json" "$CLOSE" "T327 B-1 CONTROL: manual journal entry dated ON the closing date. Expected REFUSAL (ACCOUNTING_CLOSED). Calibrates the instrument: it proves the closure at office 1 is live before the acceptance one day later is claimed to mean anything."
fire B1-CTRL-04-entry-on-closing-date "$REQ/b1-ctrl-04.json" t327-b1-ctrl-04 /journalentries \
  "B-1 CONTROL: transactionDate == closingDate $CLOSE; :636 ACCOUNTING_CLOSED expected (inclusive boundary)"

# B1-CTRL-05 -- STRICTLY BEFORE the closing date. Free (a refusal writes nothing). It supplies the
# bytes T295 filed as backlog B-3: ACCOUNTING_CLOSED echoes latestGLClosure.getClosingDate() (:637)
# and NOT the submitted transactionDate, so errors[0].args[0].value here must read $CLOSE and not
# $DM1. T287's A2-02 showed this on the standing oracle; this repeats it on a fresh instance.
mkbody "$REQ/b1-ctrl-05.json" "$DM1" "T327 B-1 CONTROL: manual journal entry dated STRICTLY BEFORE the closing date. Expected REFUSAL. Its errors[0].args[0].value is expected to echo the CLOSING date, not this request's transaction date (:637)."
fire B1-CTRL-05-entry-before-closing-date "$REQ/b1-ctrl-05.json" t327-b1-ctrl-05 /journalentries \
  "B-1 CONTROL: transactionDate $DM1 < closingDate $CLOSE; :636 ACCOUNTING_CLOSED expected, args echoing the CLOSING date"

say ""
say "ok  F5 standing reference oracle, BEFORE the second accepting POST:"
check_standing before-B1-ACCEPT-06

# B1-ACCEPT-06 -- THE ARM. D + 1, which is > the closing date AND <= the business date.
mkbody "$REQ/b1-accept-06.json" "$DP1" "T327 B-1: manual journal entry dated ONE DAY AFTER the closing date $CLOSE, and still on or before the business date $BD, on the THROWAWAY instance. Balanced: 250000.25 + 100000.37 = 350000.62."
fire B1-ACCEPT-06-entry-one-day-after-closing-date "$REQ/b1-accept-06.json" t327-b1-accept-06 /journalentries \
  "B-1: transactionDate $DP1 == closingDate + 1 and <= business date $BD; BOTH date rules must fall through"

TXN2=$(txnid B1-ACCEPT-06-entry-one-day-after-closing-date)
if [ -n "$TXN2" ]; then
  readback B1-ACCEPT-06 "$TXN2"
else
  say "NOTE: no transactionId in the B1-ACCEPT-06 response body; no read-back taken for it."
fi

# ---- the whole ledger, once ---------------------------------------------------------------
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -At -c \
  "SELECT json_agg(row_to_json(t) ORDER BY t.id)::text FROM (SELECT j.id, j.transaction_id, j.account_id, a.gl_code, a.classification_enum, j.type_enum, j.amount::text AS amount_major_text, j.entry_date::text, j.manual_entry, j.office_id, j.currency_code, j.reversed, j.reversal_id, j.is_running_balance_calculated, j.description FROM acc_gl_journal_entry j JOIN acc_gl_account a ON a.id=j.account_id ORDER BY j.id) t" \
  > "$OUT/FINAL-ledger-db.json"
shasum -a 256 "$OUT/FINAL-ledger-db.json" | awk '{print $1}' > "$OUT/FINAL-ledger-db.json.sha256"
say ""
say "FINAL ledger on the target:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -c \
  "SELECT j.id, j.transaction_id, j.account_id, a.gl_code, j.type_enum, j.amount::text, j.entry_date, j.manual_entry, j.reversed FROM acc_gl_journal_entry j JOIN acc_gl_account a ON a.id=j.account_id ORDER BY j.id" \
  | tee "$OUT/FINAL-ledger.txt"

say ""
# ***** LABEL CORRECTED AFTER THE RUN, AND THE ARTEFACT IT PRODUCED IS LEFT UNTOUCHED. *****
# This header used to read "DOUBLE-ENTRY INVARIANT, per transaction, in MNT MINOR UNITS (integer
# arithmetic only)". IT IS NOT. `sum(amount)` is a PostgreSQL NUMERIC sum in MAJOR units at the
# stored scale -- the run printed `350000.620000`, not `35000062`. The arithmetic was right and the
# LABEL was wrong, which is P-11 exactly: "the code can be RIGHT and its stated reason WRONG, and
# the reason is what the next contributor checks." out/FINAL-invariant.txt is left EXACTLY as the
# run produced it, because it records what was observed; the genuine integer minor-unit computation
# is invariant-minor-units.py, run from the committed bytes AFTER the instance was destroyed, and
# its residue rule is calibrated on known positives by red-drive-residue-rule.py (P-72).
say "PER-TRANSACTION SUMS, as PostgreSQL NUMERIC in MAJOR units at the stored scale (NOT minor units):"
# type_enum 1 = CREDIT, 2 = DEBIT [VERIFIED: fineract-core/.../journalentry/domain/JournalEntryType.java:23-24].
# Rather than assume, both are printed and the sums are compared per transaction id.
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT transaction_id||' | type_enum '||type_enum||' | sum '||sum(amount)::text||' | legs '||count(*) FROM acc_gl_journal_entry GROUP BY transaction_id, type_enum ORDER BY transaction_id, type_enum" \
  | tee "$OUT/FINAL-invariant.txt"

say ""
say "ok  F5 standing reference oracle, AFTER EVERYTHING:"
check_standing after-everything
say ""
say "CAPTURED. The instance that produced this is DISPOSABLE; run down.sh to destroy it."
