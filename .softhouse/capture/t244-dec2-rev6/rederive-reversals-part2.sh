#!/usr/bin/env bash
# T244 part 2 — the REVERSING legs are a DIFFERENT population from the reversed ORIGINALS.
# Q4 in part 1 returned 8, not 16, which proves `reversed` and `reversal_id` sit on the SAME
# rows (the originals). So "8 reversal rows" undercounts the reversal EVIDENCE on the oracle.
set -uo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 9
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || exit 9
[ -f "$ROOT/docs/adr/DEC-2-gl-accounting-adapter.md" ] || { echo "FATAL: wrong tree"; exit 9; }
echo "resolved root  : $ROOT"
echo "git HEAD       : $(git -C "$ROOT" rev-parse HEAD)"
echo "measured at    : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo "oracle health  : $(curl -sk --max-time 20 https://localhost:8443/fineract-provider/actuator/health)"
echo

Q() { docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc "$1"; }
T() { docker exec fineract-db-1 psql -U root -d fineract_gerege -c "$1"; }

echo "--- Q9  the REVERSING legs: rows whose id is pointed AT by some reversal_id ---"
echo "SQL: select count(*) from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null);"
Q "select count(*) from acc_gl_journal_entry where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null);"
echo
echo "--- Q10  those reversing legs, projected ---"
T "select id, account_id, transaction_id, reversed, reversal_id, type_enum, amount, entry_date, manual_entry, description
   from acc_gl_journal_entry
  where id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null)
  order by id;"
echo
echo "--- Q11  TOTAL reversal-related population: originals UNION reversing legs ---"
echo "SQL: originals(reversed or reversal_id not null) UNION legs(id in reversal_id set)"
Q "select count(*) from acc_gl_journal_entry
    where reversed = true or reversal_id is not null
       or id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null);"
echo
echo "--- Q12  PAIRING: does each original's reversing leg carry the SAME amount and the OPPOSITE type_enum? ---"
T "select o.id as orig_id, o.type_enum as orig_type, o.amount as orig_amount,
          r.id as rev_id,  r.type_enum as rev_type,  r.amount as rev_amount,
          (o.amount = r.amount) as amount_equal,
          (o.type_enum <> r.type_enum) as type_flipped
     from acc_gl_journal_entry o
     join acc_gl_journal_entry r on r.id = o.reversal_id
    where o.reversal_id is not null
    order by o.id;"
echo
echo "--- Q13  did any original row get MUTATED instead of reversed? (I-5's actual obligation) ---"
echo "rows where lastmodified_date > created_date, among reversal participants:"
T "select id, created_date, lastmodified_date, (lastmodified_date > created_date) as was_modified
     from acc_gl_journal_entry
    where reversed = true or reversal_id is not null
       or id in (select reversal_id from acc_gl_journal_entry where reversal_id is not null)
    order by id;"
