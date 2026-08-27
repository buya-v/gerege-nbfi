#!/bin/sh
# T305 -- SETUP CAMPAIGN on the THROWAWAY instance, so that POST
# /journalentries?command=defineOpeningBalance reaches the ACCEPTING side of
# JournalEntryWritePlatformServiceJpaRepositoryImpl.java:812 instead of one of the four
# refusals that precede it.
#
# EVERY STEP HERE IS A WRITE, AND THAT IS THE POINT OF DOING IT HERE. On the standing
# reference oracle each of these would be permanent: GLAccountWritePlatformServiceJpa
# RepositoryImpl.deleteGLAccount:191-212 refuses with TRANSACTIONS_LOGGED once any journal
# entry references an account, so the setup becomes undeletable the moment the capture
# succeeds. On a throwaway the teardown is `docker compose down -v`, which is the only
# perfect teardown there is.
#
# WHAT MUST BE TRUE FOR :812 TO FALL THROUGH, read off the source rather than guessed:
#   :706  validateForCreate       -> officeId, currencyCode, transactionDate, per-leg amounts
#   :708  financial activity 300  -> MUST be mapped (S-03 does it)
#   :764  contra account type     -> MUST be EQUITY (GLAccountType.EQUITY = 3), else
#                                    error.msg.configuration.opening.balance.contra.account
#                                    .value.is.invalid.account.type
#   :812  findNonContraTransactionIds EMPTY -> true by construction on a fresh tenant
#   :724  validateBusinessRulesForJournalEntries -> debits must equal credits, accounts must
#                                    permit manual entries, date not future, no closure
#   :776  organisationCurrencyRepository.findOneWithNotFoundDetection(currencyCode) -> MNT
#                                    must be an ORGANISATION currency (S-01 does it)
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"
OUT="$DIR/out"
mkdir -p "$OUT"

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

mkdir -p "$DIR/req"

# S-01 -- MNT as an ORGANISATION currency. m_currency already carries MNT (ISO 4217 numeric 496,
# decimal_places 2); m_organisation_currency carries only USD on a fresh tenant.
printf '%s' '{"currencies":["MNT"]}' > "$DIR/req/s01-currencies.json"
put S-01-currencies /currencies "$DIR/req/s01-currencies.json"

# S-02a -- the CONTRA account. type 3 = GLAccountType.EQUITY (:764 isEquityType), usage 1 = DETAIL.
printf '%s' '{"name":"T305 Opening Balances Contra","glCode":"T305-3000","manualEntriesAllowed":true,"type":3,"usage":1,"description":"T305 accepting-side capture: financial activity 300 contra account"}' > "$DIR/req/s02a-gl-contra.json"
post S-02a-gl-contra /glaccounts "$DIR/req/s02a-gl-contra.json"

# S-02b -- an ASSET detail account to carry the DEBIT legs.
printf '%s' '{"name":"T305 Cash On Hand","glCode":"T305-1000","manualEntriesAllowed":true,"type":1,"usage":1,"description":"T305 accepting-side capture: debit leg target"}' > "$DIR/req/s02b-gl-asset.json"
post S-02b-gl-asset /glaccounts "$DIR/req/s02b-gl-asset.json"

# S-02c -- a second ASSET detail account, so the capture can carry TWO debit legs of DIFFERENT
# amounts against ONE credit leg. That is deliberate: it is what distinguishes a port that
# writes ONE contra entry PER LEG (:791/:796 inside the per-leg loop) from one that writes a
# single summed contra entry, and a one-debit/one-credit body cannot tell those apart.
printf '%s' '{"name":"T305 Loans Receivable","glCode":"T305-1100","manualEntriesAllowed":true,"type":1,"usage":1,"description":"T305 accepting-side capture: second debit leg target"}' > "$DIR/req/s02c-gl-asset2.json"
post S-02c-gl-asset2 /glaccounts "$DIR/req/s02c-gl-asset2.json"

# S-02d -- a LIABILITY detail account to carry the CREDIT leg.
printf '%s' '{"name":"T305 Borrowings","glCode":"T305-2000","manualEntriesAllowed":true,"type":2,"usage":1,"description":"T305 accepting-side capture: credit leg target"}' > "$DIR/req/s02d-gl-liability.json"
post S-02d-gl-liability /glaccounts "$DIR/req/s02d-gl-liability.json"

echo ""
echo "GL accounts created (id | code | classification_enum | account_usage | manual_journal_entries_allowed | disabled):"
# The column is `manual_journal_entries_allowed`, NOT `manual_entries_allowed`; the first draft of
# this line guessed the shorter name from the API field and psql refused it. Column names are read
# from information_schema, never inferred from the JSON field they back.
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT id||' | '||gl_code||' | '||classification_enum||' | '||account_usage||' | '||manual_journal_entries_allowed||' | '||disabled FROM acc_gl_account ORDER BY id"

CONTRA=$(docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT id FROM acc_gl_account WHERE gl_code='T305-3000'")
[ -n "$CONTRA" ] || { echo "REFUSE: contra account was not created"; exit 1; }

# S-03 -- map financial activity 300 (OFFICE opening balances contra) onto the EQUITY account.
printf '{"financialActivityId":300,"glAccountId":%s}' "$CONTRA" > "$DIR/req/s03-financialactivity.json"
post S-03-financialactivity /financialactivityaccounts "$DIR/req/s03-financialactivity.json"

echo ""
echo "financial activity 300 ->"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc \
  "SELECT 'gl '||a.id||' code '||a.gl_code||' classification_enum '||a.classification_enum FROM acc_gl_financial_activity_account f JOIN acc_gl_account a ON a.id=f.gl_account_id WHERE f.financial_activity_type=300"
echo "journal entries before the capture:"
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc "SELECT count(*) FROM acc_gl_journal_entry"
