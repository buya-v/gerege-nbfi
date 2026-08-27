#!/bin/sh
# A2-7 leg 1 — REST read-back of every GL account the nine mandatory loan-product slots
# are filled from, plus the whole chart.
#
# WHY this exists. The only read-back of stored GL account state anywhere in the A2
# corpus before this task was out/A2-019-db-glaccount-rows.txt (a psql dump taken BEFORE
# run-020-accounts.sh ran, so it shows 4 rows) and the four REST reads
# A2-012/013/015/018, all of ASSET accounts. The fourteen accounts created by
# run-020-accounts.sh returned only {"resourceId":N} — no type, no usage, no hierarchy.
# So the corpus recorded that non-ASSET accounts were CREATED and never once recorded
# what the oracle STORED for them. These captures close that.
#
# NOT set -e for the loop, because a refusal is an observation; but every cap.sh call
# carries `|| exit 1` so a TRANSPORT failure stops the batch instead of letting the next
# `cat` print stale bytes as if freshly observed (the A2-5 fix for D-2).
DIR=$(cd "$(dirname "$0")" && pwd)

sh "$DIR/cap.sh" A2-201-read-gl16-fundsource        GET /glaccounts/16 || exit 1
sh "$DIR/cap.sh" A2-202-read-gl4-loanportfolio      GET /glaccounts/4  || exit 1
sh "$DIR/cap.sh" A2-203-read-gl17-transferssuspense GET /glaccounts/17 || exit 1
sh "$DIR/cap.sh" A2-204-read-gl8-interestonloans    GET /glaccounts/8  || exit 1
sh "$DIR/cap.sh" A2-205-read-gl9-incomefromfees     GET /glaccounts/9  || exit 1
sh "$DIR/cap.sh" A2-206-read-gl10-incomefrompenalty GET /glaccounts/10 || exit 1
sh "$DIR/cap.sh" A2-207-read-gl11-incomefromrecov   GET /glaccounts/11 || exit 1
sh "$DIR/cap.sh" A2-208-read-gl13-losseswrittenoff  GET /glaccounts/13 || exit 1
sh "$DIR/cap.sh" A2-209-read-gl6-overpayment        GET /glaccounts/6  || exit 1
sh "$DIR/cap.sh" A2-209b-read-gl2-retyped-fundsrc   GET /glaccounts/2  || exit 1
sh "$DIR/cap.sh" A2-209c-loanproducts-template      GET /loanproducts/template || exit 1
