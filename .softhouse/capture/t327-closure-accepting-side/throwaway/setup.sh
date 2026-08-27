#!/bin/sh
# T327 -- SETUP CAMPAIGN on the THROWAWAY instance, so that a plain
# POST /journalentries reaches validateBusinessRulesForJournalEntries (:626) and then the
# ACCEPTING path, instead of being refused for a reason that has nothing to do with a date.
#
# ADAPTED FROM T305's setup.sh. WHAT WAS DROPPED AND WHY: T305 needed financial activity 300
# mapped onto an EQUITY contra account, because `defineOpeningBalance` reads it at :764/:791/:796.
# THIS capture fires the PLAIN create path (`createJournalEntry`, :146), which never touches
# financial activity 300 and writes no contra entry -- so S-02a (the contra account) and S-03 (the
# mapping) are not created here. Dropping them is deliberate and is what makes this capture's leg
# count EXACTLY the request's leg count, with no expansion to reason about.
#
# EVERY STEP HERE IS A WRITE, AND THAT IS THE POINT OF DOING IT HERE. On the standing reference
# oracle each would be permanent: GLAccountWritePlatformServiceJpaRepositoryImpl.deleteGLAccount
# refuses with TRANSACTIONS_LOGGED once any journal entry references an account, so the setup
# becomes undeletable the moment the capture succeeds. On a throwaway the teardown is
# `docker compose down -v`.
#
# WHAT MUST BE TRUE FOR THE ACCEPT TO HAPPEN, read off the pinned source rather than guessed:
#   :156  validateForCreate         -> officeId, currencyCode, transactionDate, per-leg amounts
#   :626  validateBusinessRulesForJournalEntries
#           :630 FUTURE_DATE       -> transactionDate must NOT be after the business date
#           :636 ACCOUNTING_CLOSED -> transactionDate must be STRICTLY AFTER the latest closure
#           :647 NO_DEBITS_OR_CREDITS, :651 checkDebitAndCreditAmounts -> debits must equal credits
#   saveAllDebitOrCreditEntries     -> the currency must be an ORGANISATION currency (S-01 does it),
#                                      and each account must be DETAIL and manual-entry-permitted
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"
OUT="$DIR/out"
REQ="$DIR/req"
mkdir -p "$OUT" "$REQ"

post() {  # post <name> <path> <bodyfile>
  name=$1; path=$2; body=$3
  cp "$body" "$OUT/$name.req"
  code=$(curl -sk -o "$OUT/$name.json" -w '%{http_code}' -X POST "$B$path" -H "$A" -H "$T" -H "$CT" --data-binary "@$body")
  printf '%s' "$code" > "$OUT/$name.status"
  printf '%-28s POST %-46s -> %s\n' "$name" "$path" "$code"
  cat "$OUT/$name.json"; printf '\n'
}
put() {   # put <name> <path> <bodyfile>
  name=$1; path=$2; body=$3
  cp "$body" "$OUT/$name.req"
  code=$(curl -sk -o "$OUT/$name.json" -w '%{http_code}' -X PUT "$B$path" -H "$A" -H "$T" -H "$CT" --data-binary "@$body")
  printf '%s' "$code" > "$OUT/$name.status"
  printf '%-28s PUT  %-46s -> %s\n' "$name" "$path" "$code"
  cat "$OUT/$name.json"; printf '\n'
}

# S-01 -- MNT as an ORGANISATION currency. m_currency already carries MNT (ISO 4217 numeric 496,
# decimal_places 2); m_organisation_currency carries only USD on a fresh tenant.
printf '%s' '{"currencies":["MNT"]}' > "$REQ/s01-currencies.json"
put S-01-currencies /currencies "$REQ/s01-currencies.json"

# S-02a -- an ASSET detail account to carry the FIRST debit leg. type 1 = ASSET, usage 1 = DETAIL.
printf '%s' '{"name":"T327 Cash On Hand","glCode":"T327-1000","manualEntriesAllowed":true,"type":1,"usage":1,"description":"T327 accepting-side capture: first debit leg target"}' > "$REQ/s02a-gl-asset1.json"
post S-02a-gl-asset1 /glaccounts "$REQ/s02a-gl-asset1.json"

# S-02b -- a second ASSET detail account, so the body carries TWO debit legs of DIFFERENT amounts
# against ONE credit leg. Three legs of three different amounts is what lets a promoting task grade
# per-leg amounts rather than a single number that a summing port would also produce.
printf '%s' '{"name":"T327 Loans Receivable","glCode":"T327-1100","manualEntriesAllowed":true,"type":1,"usage":1,"description":"T327 accepting-side capture: second debit leg target"}' > "$REQ/s02b-gl-asset2.json"
post S-02b-gl-asset2 /glaccounts "$REQ/s02b-gl-asset2.json"

# S-02c -- a LIABILITY detail account to carry the CREDIT leg. type 2 = LIABILITY.
printf '%s' '{"name":"T327 Borrowings","glCode":"T327-2000","manualEntriesAllowed":true,"type":2,"usage":1,"description":"T327 accepting-side capture: credit leg target"}' > "$REQ/s02c-gl-liability.json"
post S-02c-gl-liability /glaccounts "$REQ/s02c-gl-liability.json"

echo ""
echo "GL accounts created (id | code | classification_enum | account_usage | manual_journal_entries_allowed | disabled):"
# The column is `manual_journal_entries_allowed`, NOT `manual_entries_allowed`; T305 recorded that
# the shorter name guessed from the API field is not the column name. Read from the database.
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT id||' | '||gl_code||' | '||classification_enum||' | '||account_usage||' | '||manual_journal_entries_allowed||' | '||disabled FROM acc_gl_account ORDER BY id" \
  | tee "$OUT/S-04-gl-accounts.txt"

for code in T327-1000 T327-1100 T327-2000; do
  v=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='$code'")
  [ -n "$v" ] || { echo "REFUSE: GL account $code was not created"; exit 1; }
done

echo ""
echo "organisation currencies:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT code||' decimal_places='||decimal_places FROM m_organisation_currency ORDER BY code" | tee "$OUT/S-05-org-currencies.txt"
echo "MNT in m_currency (ISO 4217 numeric / decimal places):"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT code||' | decimal_places='||decimal_places||' | name='||name FROM m_currency WHERE code='MNT'" | tee -a "$OUT/S-05-org-currencies.txt"

echo ""
echo "journal entries before the capture:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_journal_entry"
echo "GL closures before the capture:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_closure"
echo "acc_gl_closure id sequence state (T295 recorded that on the STANDING oracle a create/delete"
echo "left is_called = t, so the NEXT closure there would get id 2; on a FRESH instance it should"
echo "not be. This is the reading, before anything is created:)"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT 'last_value='||last_value||' is_called='||is_called FROM acc_gl_closure_id_seq" \
  | tee "$OUT/S-06-closure-sequence-before.txt" || echo "(sequence not readable under that name)"
