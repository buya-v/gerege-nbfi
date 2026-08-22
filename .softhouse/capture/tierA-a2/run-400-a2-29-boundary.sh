#!/bin/sh
# A2-29 / G-12 group A -- DOES THE STORED RUNNING BALANCE REACH A CONTRACT BOUNDARY?
#
# A2-26 found office_running_balance / organization_running_balance in a psql dump.
# A psql dump is NOT the contract boundary. This batch OBSERVES the live reference
# oracle's REST surface, because the task's whole point is that an entity-class reading
# is not an observation.
#
# Read-only: every request is a GET. Nothing is created, nothing is mutated.
#
# The two query parameters under test, both read from the pinned checkout:
#   /journalentries?runningBalance=true
#     [VERIFIED: fineract-provider/src/main/java/org/apache/fineract/accounting/
#      journalentry/api/JournalEntriesApiResource.java:130,179]
#   /glaccounts?fetchRunningBalance=true
#     [VERIFIED: fineract-accounting/src/main/java/org/apache/fineract/accounting/
#      glaccount/api/GLAccountsApiResource.java:145,170]
#
# Entry ids chosen from out/A2-410-db-running-balance-drift.txt, taken minutes earlier:
#   id 14 -- is_running_balance_calculated = TRUE, and its stored value already DISAGREES
#            with the derived prefix sum by 120000000 minor units.
#   id 25 -- is_running_balance_calculated = FALSE, stored 0.000000.
#   id  1 -- is_running_balance_calculated = TRUE and stored == derived.
# No expected value is written down anywhere in this script.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

# The list surface, with and without the parameter -- the pair is the measurement.
sh "$C" A2-401-journalentries-no-runningbalance GET "/journalentries?limit=3&orderBy=id&sortOrder=ASC"
sh "$C" A2-402-journalentries-runningbalance    GET "/journalentries?limit=3&orderBy=id&sortOrder=ASC&runningBalance=true"

# Single-entry reads.
sh "$C" A2-403-entry1-runningbalance   GET "/journalentries/1?runningBalance=true"
sh "$C" A2-404-entry14-runningbalance  GET "/journalentries/14?runningBalance=true"
sh "$C" A2-405-entry25-runningbalance  GET "/journalentries/25?runningBalance=true"
sh "$C" A2-406-entry14-no-param        GET "/journalentries/14"

# The GL-account surface. GLAccountReadPlatformServiceImpl:104 reads the column with
# rs.getLong(...) -- an integer read of a numeric(19,6) column. Observe what comes out.
sh "$C" A2-407-glaccounts-no-fetch          GET "/glaccounts"
sh "$C" A2-408-glaccounts-fetchrunningbal   GET "/glaccounts?fetchRunningBalance=true"
sh "$C" A2-409-glaccount4-fetchrunningbal   GET "/glaccounts/4?fetchRunningBalance=true"
