#!/bin/sh
# A2-29 / G-12 group B -- DOES FINERACT'S OWN RECALCULATION PATH HEAL THE DRIFT?
#
# out/A2-410-db-running-balance-drift.txt records that, right now, 6 of the 20 rows that
# Fineract itself flags is_running_balance_calculated = TRUE store a value that DISAGREES
# with the derived prefix sum. This batch runs the oracle's own recalculation and measures
# again. NO expected outcome is written down here.
#
# The command exercised is the same code the ACCOUNTING_RUNNING_BALANCE_UPDATE scheduled
# job runs -- UpdateRunningBalanceCommandHandler:38 and AccountRunningBalanceUpdateTasklet:37
# both call JournalEntryRunningBalanceUpdateService, so this is the recalculation path, not
# a test-only shortcut [VERIFIED: pinned checkout 426a23544].
#
# An empty body {} means "no officeId", which routes to updateRunningBalance() -- the
# WHOLE-ORGANISATION path [VERIFIED: JournalEntryRunningBalanceUpdateServiceImpl.java:89-90].
#
# THIS BATCH MUTATES THE ORACLE. It rewrites office_running_balance /
# organization_running_balance / is_running_balance_calculated on existing rows. It writes
# no journal entry and moves no money: the SQL it runs is an UPDATE of exactly those three
# columns plus the audit pair [VERIFIED: same file:163-164].
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap9.sh"

sh "$C" A2-420-update-running-balance-org POST "/journalentries?command=updateRunningBalance" \
      req/a2-29-update-running-balance-org.json a2-29-rb-org-0001
cat "$DIR/out/A2-420-update-running-balance-org.json"; echo
