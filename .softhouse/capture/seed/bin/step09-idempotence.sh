#!/usr/bin/env bash
# Step 9: run the whole rig a SECOND time and prove it creates nothing new.
# check-then-create is keyed on the SEED- prefix / external id / glCode / name.
set -uo pipefail

BIN="$(cd "$(dirname "$0")" && pwd)"
DB='gerege-oracle-db'
PSQL="docker exec -i $DB psql -U postgres -d fineract_gerege -t -A -F '|'"

snapshot() {
  $PSQL <<'SQL'
SELECT 'gl_accounts' k, count(*) n FROM acc_gl_account
UNION ALL SELECT 'gl_accounts_seed', count(*) FROM acc_gl_account WHERE gl_code LIKE 'SEED-%'
UNION ALL SELECT 'provisioning_criteria', count(*) FROM m_provisioning_criteria
UNION ALL SELECT 'clients', count(*) FROM m_client
UNION ALL SELECT 'clients_seed', count(*) FROM m_client WHERE external_id LIKE 'SEED-%'
UNION ALL SELECT 'loan_products_seed', count(*) FROM m_product_loan WHERE name LIKE 'SEED-%'
UNION ALL SELECT 'loans', count(*) FROM m_loan
UNION ALL SELECT 'loans_seed', count(*) FROM m_loan WHERE external_id LIKE 'SEED-%'
UNION ALL SELECT 'loans_disbursed', count(*) FROM m_loan WHERE loan_status_id=300
UNION ALL SELECT 'criteria_definitions', count(*) FROM m_provisioning_criteria_definition
ORDER BY k;
SQL
}

snapshot > /tmp/seed-snapshot-before.txt
"$BIN/run.sh" >/tmp/seed-second-run.log 2>&1
snapshot > /tmp/seed-snapshot-after.txt

if diff -u /tmp/seed-snapshot-before.txt /tmp/seed-snapshot-after.txt; then
  echo "IDEMPOTENT: second run created nothing new."
else
  echo "NOT IDEMPOTENT: see diff above." >&2
  exit 1
fi

# rounding-mode re-check
RM=$($PSQL -c "SELECT value FROM c_configuration WHERE name='rounding-mode';" | tr -d '[:space:]')
echo "rounding-mode = $RM (expect 4 = HALF_UP)"
[ "$RM" = "4" ] || { echo "rounding-mode changed!" >&2; exit 1; }
