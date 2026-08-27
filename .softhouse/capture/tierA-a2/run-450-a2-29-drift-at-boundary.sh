#!/bin/sh
# A2-29 / G-12 group D -- DOES THE DRIFT REACH THE CONTRACT BOUNDARY?
#
# out/A2-441-db-after-retype-and-recompute.txt records, in the DATABASE, that entries 59
# and 62 store a running balance 200000000 minor units away from the derived sum, and that
# both are flagged is_running_balance_calculated = TRUE after four recomputes. A database
# row is not the boundary. This batch asks the REST surface what it serves for those two
# entries and for the account they sit on.
#
# Read-only: every request is a GET.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

sh "$C" A2-450-entry59-runningbalance GET "/journalentries/59?runningBalance=true"
sh "$C" A2-451-entry60-runningbalance GET "/journalentries/60?runningBalance=true"
sh "$C" A2-452-entry62-runningbalance GET "/journalentries/62?runningBalance=true"

# GLAccountReadPlatformServiceImpl.retrieveGLAccountById serves the stored
# organization_running_balance of the LATEST is_running_balance_calculated=true entry,
# read with rs.getLong(...) on a numeric(19,6) column
# [VERIFIED: fineract-accounting/.../GLAccountReadPlatformServiceImpl.java:104,202-204].
sh "$C" A2-453-glaccount33-fetchrunningbal GET "/glaccounts/33?fetchRunningBalance=true"
sh "$C" A2-454-glaccount34-fetchrunningbal GET "/glaccounts/34?fetchRunningBalance=true"

# The LIST form of the same read. A2-408 already recorded HTTP 500 on this oracle; repeat
# it here so the boundary evidence for this account pair is self-contained.
sh "$C" A2-455-glaccounts-list-fetchrunningbal GET "/glaccounts?fetchRunningBalance=true"
