#!/bin/bash
# OH-TBCAP-Y step 0 -- READ-ONLY baseline. No writes here.
# Oracle REST: tenant gerege ONLY. SQL: gerege-oracle-db (NOT fineract-db-1), SELECT only.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
RAW="$DIR/raw"
EV="$DIR/evidence"
REST="https://localhost:8443/fineract-provider/api/v1"
AUTH="mifos:password"
TEN="Fineract-Platform-TenantId: gerege"
PSQL="docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -At -c"

q() { # q <file> <sql>
  $PSQL "$2" > "$1" 2> "$1.err"
}

get() { # get <file> <path>
  code=$(curl -k -s -o "$1" -w '%{http_code}' -u "$AUTH" -H "$TEN" "$REST$2")
  printf '%s' "$code" > "$1.status"
}

mkdir -p "$RAW" "$EV"

# --- read-only SQL: the tenant's own state -------------------------------------
q "$RAW/00-mtb-count.txt"            "SELECT count(*) FROM m_trial_balance;"
q "$RAW/00-mtb-all.txt"              "SELECT office_id, account_id, amount, entry_date, created_date, closing_balance FROM m_trial_balance;"
q "$RAW/00-mtb-columns.txt"          "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='m_trial_balance' ORDER BY ordinal_position;"
q "$RAW/00-je-count-maxid.txt"       "SELECT count(*), max(id) FROM acc_gl_journal_entry;"
q "$RAW/00-je-entry-date-range.txt"  "SELECT min(entry_date), max(entry_date) FROM acc_gl_journal_entry;"
q "$RAW/00-je-distinct-entry-dates.txt" "SELECT DISTINCT entry_date FROM acc_gl_journal_entry ORDER BY entry_date;"
q "$RAW/00-je-created-on-utc-range.txt"  "SELECT min(created_on_utc), max(created_on_utc) FROM acc_gl_journal_entry;"
q "$RAW/00-je-created-by-entry-date.txt" "SELECT entry_date, min(created_on_utc), max(created_on_utc), count(*) FROM acc_gl_journal_entry GROUP BY entry_date ORDER BY entry_date;"
q "$RAW/00-gl-manual-accounts.txt"   "SELECT id, name, gl_code, manual_journal_entries_allowed, disabled, classification_enum FROM acc_gl_account WHERE manual_journal_entries_allowed = true ORDER BY id;"
q "$RAW/00-gl-accounts-all.txt"      "SELECT id, name, gl_code, manual_journal_entries_allowed, disabled, classification_enum FROM acc_gl_account ORDER BY id;"
q "$RAW/00-businessdate-sql.txt"     "SELECT * FROM m_business_date;"

# --- REST: business date, closures, job 30 -------------------------------------
get "$RAW/00-businessdate.json"        "/businessdate"
get "$RAW/00-glclosures.json"          "/glclosures"
get "$RAW/00-job30.json"               "/jobs/30"
get "$RAW/00-job30-runhistory.json"    "/jobs/30/runhistory"
get "$RAW/00-journalentries-rest.json" "/journalentries?limit=500"

echo "step00 done"
