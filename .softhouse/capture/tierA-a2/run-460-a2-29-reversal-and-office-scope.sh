#!/bin/sh
# A2-29 / G-12 group E -- two more drift levers the task named:
#   E.1 a REVERSAL, and
#   E.2 the OFFICE-SCOPED recalculation, which writes a DIFFERENT set of columns from the
#       organisation-scoped one.
#
# E.2's hypothesis, from the pinned source and NOT from any expected value:
#   updateOfficeRunningBalance(officeId) runs `UPDATE acc_gl_journal_entry SET
#   office_running_balance=?, last_modified_by=?, last_modified_on_utc=? WHERE id=?`
#   [VERIFIED: JournalEntryRunningBalanceUpdateServiceImpl.java:211] -- it does NOT set
#   is_running_balance_calculated and it does NOT touch organization_running_balance,
#   where the organisation-scoped path sets all three [VERIFIED: same file:163-164].
#   So the two stored columns can be left describing different states of the same ledger.
# Whether that holds is decided by out/A2-46x-db-*.txt, not by this comment.
#
# THIS BATCH MUTATES THE ORACLE: one reversal (which is itself append-only -- new entries,
# the originals keep their amounts), and two recalculations.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C8="$DIR/cap8.sh"
C9="$DIR/cap9.sh"

# The transaction reversed is the drift probe's leg 1, whose id this fire observed as
# out/A2-432-je-while-asset.json -> transactionId.
TXN=$(python3 -c 'import decimal,json,sys
d=json.load(open(sys.argv[1]),parse_float=decimal.Decimal)
t=d.get("transactionId")
assert isinstance(t,str) and t, "REFUSING: no transactionId in %s" % sys.argv[1]
sys.stdout.write(t)' "$DIR/out/A2-432-je-while-asset.json")
echo "reversing transactionId $TXN"

sh "$C9" A2-460-je-reverse POST "/journalentries/$TXN?command=reverse" req/a2-29-je-reverse.json a2-29-rev-0001
cat "$DIR/out/A2-460-je-reverse.json"; echo

# E.2 -- OFFICE-scoped recalculation FIRST, while the reversal's rows are still
# is_running_balance_calculated = false.
sh "$C9" A2-461-recompute-office1 POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-office1.json a2-29-rb-off-0001

# STOP HERE. The office-scoped state is the measurement, and it is destroyed by the
# organisation-scoped run. out/A2-462-db-after-office-scope.txt is taken at this point;
# run-463-a2-29-recompute-org-after-reversal.sh then does the organisation-scoped run.
