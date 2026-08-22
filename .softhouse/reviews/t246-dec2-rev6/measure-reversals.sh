#!/usr/bin/env bash
# T246 — INDEPENDENT re-measurement of the reversal population on the LIVE reference oracle (Fineract).
# Oracle pin 426a23544 | PostgreSQL localhost:5432 | database fineract_gerege | TENANT id=2 'gerege' (Asia/Ulaanbaatar)
# Fail-CLOSED by construction: set -euo pipefail, and a known-FALSE calibration that must return 0
# plus a known-TRUE calibration that must equal the table total. If the DB is unreachable psql exits
# non-zero and the whole script dies -- it cannot print "(no hits)" and exit 0 (the T238 fail-OPEN class).
set -euo pipefail

DB=fineract_gerege
CT=fineract-db-1

Q() { docker exec "$CT" psql -U root -d "$DB" -Atc "$1"; }
L() { printf '%-58s %s\n' "$1" "$(Q "$2")"; }

echo "=== T246 reversal-population re-measurement ==="
echo "container=$CT db=$DB tenant=2 'gerege' Asia/Ulaanbaatar"
echo "oracle pin: 426a23544e8426a38ae43ae404670a0a7e85b9eb"
echo

echo "--- CALIBRATION (fail-closed) ---"
L "known-FALSE  where 1=0                 [MUST be 0]" "select count(*) from acc_gl_journal_entry where 1=0;"
L "known-FALSE  reversed and not reversed [MUST be 0]" "select count(*) from acc_gl_journal_entry where reversed = true and reversed = false;"
L "known-FALSE  transaction_id='NOSUCHTX' [MUST be 0]" "select count(*) from acc_gl_journal_entry where transaction_id = 'NOSUCHTX-T246';"
L "known-TRUE   where true                [= total ]" "select count(*) from acc_gl_journal_entry where true;"
L "TOTAL rows in acc_gl_journal_entry               " "select count(*) from acc_gl_journal_entry;"
echo

echo "--- TERM 1: the two flags ---"
L "A  reversed = true" "select count(*) from acc_gl_journal_entry where reversed = true;"
L "B  reversal_id is not null" "select count(*) from acc_gl_journal_entry where reversal_id is not null;"
echo

echo "--- TERM 2: the UNION test (T244 claims 8, NOT 16) ---"
L "A OR B   (union)" "select count(*) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
L "A AND B  (intersection)" "select count(*) from acc_gl_journal_entry where reversed = true and reversal_id is not null;"
L "A AND NOT B" "select count(*) from acc_gl_journal_entry where reversed = true and reversal_id is null;"
L "B AND NOT A" "select count(*) from acc_gl_journal_entry where (reversed = false or reversed is null) and reversal_id is not null;"
echo

echo "--- TERM 3: the reversing legs (targets of reversal_id) ---"
L "distinct reversal_id values" "select count(distinct reversal_id) from acc_gl_journal_entry where reversal_id is not null;"
L "rows that ARE a reversal target (id in reversal_id set)" "select count(*) from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null);"
L "targets that themselves have reversed=true" "select count(*) from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null) and reversed = true;"
L "targets that themselves have reversal_id not null" "select count(*) from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null) and reversal_id is not null;"
L "UNION of originals + targets  (T244 claims 16)" "select count(*) from (select id from acc_gl_journal_entry where reversed = true or reversal_id is not null union select id from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null)) u;"
echo

echo "--- TERM 4: transaction ids and pairing ---"
L "distinct transaction_id over originals" "select count(distinct transaction_id) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
L "distinct transaction_id over originals+targets (T244: 6)" "select count(distinct transaction_id) from (select transaction_id from acc_gl_journal_entry where reversed = true or reversal_id is not null union all select transaction_id from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null)) u;"
echo
echo "distinct transaction_ids in the whole reversal population:"
Q "select distinct transaction_id from (select transaction_id from acc_gl_journal_entry where reversed = true or reversal_id is not null union all select transaction_id from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null)) u order by 1;"
echo

echo "--- TERM 5: leg-by-leg equal amount / flipped type_enum (T244: 8 of 8) ---"
echo "orig_id|orig_tx|orig_type|orig_amount||rev_id|rev_tx|rev_type|rev_amount|amount_equal|type_flipped"
Q "select o.id||'|'||o.transaction_id||'|'||o.type_enum||'|'||o.amount||'||'||r.id||'|'||r.transaction_id||'|'||r.type_enum||'|'||r.amount||'|'||(o.amount = r.amount)||'|'||(o.type_enum <> r.type_enum and o.type_enum in (1,2) and r.type_enum in (1,2)) from acc_gl_journal_entry o join acc_gl_journal_entry r on r.id = o.reversal_id order by o.id;"
echo
L "pairs with amount EQUAL          [expect = A]" "select count(*) from acc_gl_journal_entry o join acc_gl_journal_entry r on r.id = o.reversal_id where o.amount = r.amount;"
L "pairs with type_enum FLIPPED     [expect = A]" "select count(*) from acc_gl_journal_entry o join acc_gl_journal_entry r on r.id = o.reversal_id where o.type_enum <> r.type_enum;"
L "pairs with amount NOT equal      [MUST be 0]" "select count(*) from acc_gl_journal_entry o join acc_gl_journal_entry r on r.id = o.reversal_id where o.amount <> r.amount;"
L "pairs with type_enum NOT flipped [MUST be 0]" "select count(*) from acc_gl_journal_entry o join acc_gl_journal_entry r on r.id = o.reversal_id where o.type_enum = r.type_enum;"
echo

echo "--- TERM 6: the full population dumped (independent of any pairing assumption) ---"
echo "id|tx|type|amount|reversed|reversal_id|manual|entry_date|account_id|office_id"
Q "select id||'|'||transaction_id||'|'||type_enum||'|'||amount||'|'||reversed||'|'||coalesce(reversal_id::text,'-')||'|'||manual_entry||'|'||entry_date||'|'||account_id||'|'||office_id from acc_gl_journal_entry where reversed = true or reversal_id is not null or id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null) order by transaction_id, id;"
echo
echo "--- TERM 7: does the OTHER tenant database have reversals too? (population scope, P-66) ---"
printf '%-58s %s\n' "fineract_default reversed=true" "$(docker exec "$CT" psql -U root -d fineract_default -Atc "select count(*) from acc_gl_journal_entry where reversed = true;")"
printf '%-58s %s\n' "fineract_default total journal rows" "$(docker exec "$CT" psql -U root -d fineract_default -Atc "select count(*) from acc_gl_journal_entry;")"
echo
echo "=== END ==="
