#!/usr/bin/env bash
# T244 — re-derive DEC-2 §4.4 I-5's evidential reason against the LIVE oracle.
# P-69: stamp every measurement with the commit it was measured at.
# Fail-OPEN dead-`cd` guard (RESUME HEADLINE 5): this script does NOT hard-`cd` into a
# path that may have been deleted. It resolves the repo root from its own location and
# then PRINTS it plus the HEAD sha, so a reader can see where the instrument actually ran.
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || { echo "FATAL: cannot resolve own dir"; exit 9; }
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || { echo "FATAL: cannot resolve repo root"; exit 9; }
[ -d "$ROOT/.git" ] || [ -f "$ROOT/.git" ] || { echo "FATAL: $ROOT is not a git tree — refusing to report"; exit 9; }
[ -f "$ROOT/docs/adr/DEC-2-gl-accounting-adapter.md" ] || { echo "FATAL: DEC-2 not found under $ROOT — wrong tree"; exit 9; }

echo "instrument     : ${BASH_SOURCE[0]}"
echo "resolved root  : $ROOT"
echo "git HEAD       : $(git -C "$ROOT" rev-parse HEAD)"
echo "git branch     : $(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
echo "origin/main    : $(git -C "$ROOT" rev-parse origin/main)"
echo "worktree dirty : $(git -C "$ROOT" status --porcelain | wc -l | tr -d ' ') path(s)"
echo "measured at    : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo "fineract pin   : $(git -C /Users/buv/fineract rev-parse HEAD 2>/dev/null)"
echo "oracle health  : $(curl -sk --max-time 20 https://localhost:8443/fineract-provider/actuator/health)"
echo

Q() { docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc "$1"; }
T() { docker exec fineract-db-1 psql -U root -d fineract_gerege -c "$1"; }

echo "--- Q1  total journal-entry rows ---"
echo "SQL: select count(*) from acc_gl_journal_entry;"
Q "select count(*) from acc_gl_journal_entry;"
echo
echo "--- Q2  rows flagged reversed = true (the ORIGINALS that have been reversed) ---"
echo "SQL: select count(*) from acc_gl_journal_entry where reversed = true;"
Q "select count(*) from acc_gl_journal_entry where reversed = true;"
echo
echo "--- Q3  rows carrying reversal_id IS NOT NULL (the REVERSING legs) ---"
echo "SQL: select count(*) from acc_gl_journal_entry where reversal_id is not null;"
Q "select count(*) from acc_gl_journal_entry where reversal_id is not null;"
echo
echo "--- Q4  UNION: rows participating in a reversal either way ---"
echo "SQL: select count(*) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
Q "select count(*) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
echo
echo "--- Q5  the rows themselves (full projection of the reversal columns) ---"
T "select id, account_id, transaction_id, reversed, reversal_id, type_enum, amount, entry_date, manual_entry
   from acc_gl_journal_entry
  where reversed = true or reversal_id is not null
  order by id;"
echo
echo "--- Q6  distinct transactions touched by a reversal ---"
echo "SQL: select count(distinct transaction_id) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
Q "select count(distinct transaction_id) from acc_gl_journal_entry where reversed = true or reversal_id is not null;"
echo
echo "--- Q7  double-entry check on those rows: debits vs credits, MNT minor units (scale 2) ---"
T "select transaction_id,
        sum(case when type_enum = 2 then round(amount*100) else 0 end) as debit_minor,
        sum(case when type_enum = 1 then round(amount*100) else 0 end) as credit_minor,
        count(*) as legs
   from acc_gl_journal_entry
  where reversed = true or reversal_id is not null
  group by transaction_id order by transaction_id;"
echo
echo "--- Q8  CALIBRATION: the same query shape against a predicate known to be FALSE ---"
echo "SQL: select count(*) from acc_gl_journal_entry where reversed = true and reversed = false;"
Q "select count(*) from acc_gl_journal_entry where reversed = true and reversed = false;"
echo "(a zero here proves the instrument CAN return zero, so the non-zero above is a measurement)"
