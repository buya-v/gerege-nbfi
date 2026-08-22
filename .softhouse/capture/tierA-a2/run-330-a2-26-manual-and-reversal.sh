#!/bin/sh
# A2-26 / group D -- THE LEDGER SURFACE THE CORPUS NEVER TOUCHED AT ALL.
#
# WHAT THE CENSUS FOUND: the endpoint histogram over all 147 HTTP observations contains
# NINE `GET /journalentries` and ZERO `POST /journalentries`. Every journal entry in the
# corpus is a SIDE EFFECT of a loan command; not one was posted directly, none was ever
# reversed, and `reversed` is false on every row in the corpus. So three of this
# project's own non-negotiables --
#
#     "the ledger is double-entry and append-only"
#     "corrections are reversing entries"
#     "balances are derived, never written"
#
# -- have no observation behind them anywhere in slice A2. This script posts directly at
# the ledger, which is the only surface on which those sentences are testable.
#
# Amounts are deliberately NOT round: 100000.25 + 25000.30 = 125000.55 in MNT minor
# units. Every existing ledger amount in the corpus is a whole tugrik, so the corpus has
# no discriminating power over minor-unit handling at all; a leg that lost its cents
# would be byte-indistinguishable from a correct one on every capture taken before today.
#
# A refusal is an observation. The three refusal probes are not failures of this script:
# an oracle-faithful port must refuse the same inputs in the same words, and DEC-2's
# contract-refusal vector class has, today, no observed refusal on the ledger surface to
# be built from.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

# --- the accounts these probes point at, as the oracle describes them right now.
sh "$C" A2-340-glaccount21-liability-detail GET /glaccounts/21 || exit 1
sh "$C" A2-341-glaccount18-nomanual        GET /glaccounts/18 || exit 1
sh "$C" A2-342-glaccount1-header           GET /glaccounts/1  || exit 1

# --- probe 1: a THREE-LEG balanced manual entry with non-round minor units.
sh "$C" A2-343-manual-je-3leg POST /journalentries req/a2-26-manual-je-balanced-3leg.json || exit 1
cat "$DIR/out/A2-343-manual-je-3leg.json"; echo

# --- probe 2: debits exceed credits by exactly one minor unit.
sh "$C" A2-344-manual-je-unbalanced POST /journalentries \
   req/a2-26-manual-je-unbalanced-one-minor-unit.json || exit 1
cat "$DIR/out/A2-344-manual-je-unbalanced.json"; echo

# --- probe 3: a leg pointing at a HEADER account.
sh "$C" A2-345-manual-je-header POST /journalentries req/a2-26-manual-je-header-account.json || exit 1
cat "$DIR/out/A2-345-manual-je-header.json"; echo

# --- probe 4: a leg pointing at an account that forbids manual entries.
sh "$C" A2-346-manual-je-nomanual POST /journalentries req/a2-26-manual-je-manual-disallowed.json || exit 1
cat "$DIR/out/A2-346-manual-je-nomanual.json"; echo

# --- read back what probe 1 actually wrote, before anything reverses it.
TXN=$(python3 -c 'import json,sys,decimal;d=json.load(open(sys.argv[1]),parse_float=decimal.Decimal);print(d.get("transactionId",""))' \
      "$DIR/out/A2-343-manual-je-3leg.json")
echo "observed manual transactionId = ${TXN:-<none>}"
[ -n "$TXN" ] || { echo "probe 1 wrote no transactionId -- the reversal leg cannot run" >&2; exit 1; }

sh "$C" A2-347-je-manual-readback GET "/journalentries?transactionId=$TXN&limit=50" || exit 1

# --- probe 5: REVERSE it. Does the oracle mutate the rows, or append reversing rows?
sh "$C" A2-348-je-reverse POST "/journalentries/$TXN?command=reverse" req/a2-26-je-reverse.json || exit 1
cat "$DIR/out/A2-348-je-reverse.json"; echo

# --- the whole picture after the reversal: original rows, their reversed flag, and
#     whatever new rows the reversal appended.
sh "$C" A2-349-je-manual-after-reverse GET "/journalentries?transactionId=$TXN&limit=50" || exit 1
sh "$C" A2-350-je-office1-june GET "/journalentries?officeId=1&fromDate=01%20June%202026&toDate=30%20June%202026&locale=en&dateFormat=dd%20MMMM%20yyyy&limit=100" || exit 1
