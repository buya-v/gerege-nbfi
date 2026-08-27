#!/usr/bin/env bash
# T246 — re-derive the ONE remaining assertion revision 6's Hunk A makes that I had not yet
# measured: "all 16 rows show last_modified_on_utc > created_on_utc, so a snapshot cannot tell
# 'flags and adds' from 'flags and rewrites'". Do NOT inherit it from T244 (the cardinal rule).
# db fineract_gerege | TENANT id=2 'gerege' Asia/Ulaanbaatar | oracle pin 426a23544
set -euo pipefail
CT=fineract-db-1; DB=fineract_gerege
Q() { docker exec "$CT" psql -U root -d "$DB" -Atc "$1"; }
L() { printf '%-62s %s\n' "$1" "$(Q "$2")"; }

POP="(reversed = true or reversal_id is not null or id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null))"

echo "=== CALIBRATION (fail-closed) ==="
L "known-FALSE 1=0                              [MUST be 0]" "select count(*) from acc_gl_journal_entry where $POP and 1=0;"
L "population size                              [expect 16]" "select count(*) from acc_gl_journal_entry where $POP;"
echo
echo "=== THE MUTATION CLAIM ==="
L "rows with last_modified_on_utc > created_on_utc" "select count(*) from acc_gl_journal_entry where $POP and last_modified_on_utc > created_on_utc;"
L "rows with last_modified_on_utc = created_on_utc" "select count(*) from acc_gl_journal_entry where $POP and last_modified_on_utc = created_on_utc;"
L "rows with either UTC column NULL" "select count(*) from acc_gl_journal_entry where $POP and (last_modified_on_utc is null or created_on_utc is null);"
L "rows with legacy created_date NOT null" "select count(*) from acc_gl_journal_entry where $POP and created_date is not null;"
L "rows with legacy lastmodified_date NOT null" "select count(*) from acc_gl_journal_entry where $POP and lastmodified_date is not null;"
echo
echo "=== And the SAME question over the WHOLE table, for scope (P-66) ==="
L "all rows" "select count(*) from acc_gl_journal_entry;"
L "all rows with last_modified_on_utc > created_on_utc" "select count(*) from acc_gl_journal_entry where last_modified_on_utc > created_on_utc;"
echo
echo "=== per-row detail ==="
echo "id|tx|reversed|created_on_utc|last_modified_on_utc|modified_after_insert"
Q "select id||'|'||transaction_id||'|'||reversed||'|'||created_on_utc||'|'||last_modified_on_utc||'|'||(last_modified_on_utc > created_on_utc) from acc_gl_journal_entry where $POP order by id;"
echo
echo "=== double-entry balance per reversal-participating transaction, in MINOR UNITS (int) ==="
echo "tx|legs|debit_minor|credit_minor|balanced"
Q "select transaction_id||'|'||count(*)||'|'||sum(case when type_enum=2 then round(amount*100)::bigint else 0 end)||'|'||sum(case when type_enum=1 then round(amount*100)::bigint else 0 end)||'|'||(sum(case when type_enum=2 then round(amount*100)::bigint else 0 end) = sum(case when type_enum=1 then round(amount*100)::bigint else 0 end)) from acc_gl_journal_entry where $POP group by transaction_id order by 1;"
echo
echo "=== END ==="
