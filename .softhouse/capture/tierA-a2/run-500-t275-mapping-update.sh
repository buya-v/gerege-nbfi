#!/bin/sh
# T275 / GROUP A -- CAPTURE-PLAN.md §5 ROW 1, THE ONE THE PREVIOUS FIRE CALLED CHEAP.
#
# §5, verbatim: "Mapping replacement (delete-then-recreate) on product update --
# req/upd-070-repoint-fundsource.json and req/upd-071-add-channel.json were written but
# not sent. Budget went to the resolution and delete-guard captures, which no other fire
# can take. Cheap next fire: PUT /loanproducts/23 and re-run sql/q2-product-mapping-rows.sql."
#
# Those two bodies are sent here EXACTLY AS THE EARLIER FIRE WROTE THEM. They are not
# regenerated, not reformatted and not touched -- mkreq-t275.py refuses to write any name
# that already exists, precisely so this cannot become another D-1.
#
# WHAT q2 CANNOT SEE, AND WHY THIS RUN USES q8 INSTEAD.
# sql/q2-product-mapping-rows.sql projects everything about a mapping row EXCEPT its
# primary key. "Updated in place" and "deleted and reinserted" produce IDENTICAL q2 output.
# The §5 row is named "delete-then-recreate" and that is exactly the distinction q2 erases,
# so sql/q8-t275-mapping-ids.sql selects m.id first and also reports max(id) over the whole
# table -- a recreate consumes identity values even when the row count does not move.
# q2 is still re-run at the end, as §5 asked, so its output is comparable with the
# pre-existing out/A2-072-db-product-mapping-rows.txt.
#
# TARGET. Loan product 23 "A2 Cash Mapping No Override", accounting_type 2 (CASH). Chosen
# by §5, and it is the right choice: product 22 carries a payment-channel override already,
# so on 22 the "add a channel" step could not distinguish an added row from a replaced one.
# 23 starts with NO channel row at all.
#
# ORDER MATTERS AND IS DELIBERATE:
#   1  repoint the GENERIC fund source          (does a value change reuse the row id?)
#   2  add a PAYMENT-CHANNEL row                (does adding one disturb the generic row?)
#   3  update a field with NO accounting content (is replacement scoped to the payload, or
#                                                 is it a property of the update command?)
#   4  send an EMPTY channel array              (delete-then-recreate and merge-by-key
#                                                 differ maximally here)
# Each step is followed by a DB read AND an API read-back, because the two need not agree:
# §4.2 already found a field (`hierarchy`) the DB has and the API never exposes.
#
# NOTHING HERE IS A MONEY MOVEMENT. No loan, no disbursement, no journal entry, no
# transaction -- these are product-configuration writes only, so no Idempotency-Key is
# required (CLAUDE.md scopes that rule to money-movement POSTs) and cap8.sh, which sends
# none, is the correct instrument. cap9/cap10 exist for the money-movement captures.
#
# A refusal is an observation: cap8.sh records a non-2xx as data. A TRANSPORT failure is
# not, and every call carries `|| exit 1` so the batch stops rather than reading a stale
# body as if it had just been observed (D-2).
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"
Q="$DIR/capsql.sh"

echo "== T275 group A: mapping replacement on loan product UPDATE =="

# --- 0. the pre-state. Everything below is only interpretable against this.
sh "$Q" A2-500-db-mapping-before sql/q8-t275-mapping-ids.sql || exit 1
sh "$C" A2-501-loanproduct23-before GET /loanproducts/23 || exit 1

# --- 1. repoint the generic fund source: GL 2 -> GL 16.  req/upd-070 as written by A2-3.
sh "$C" A2-502-p23-repoint-fundsource PUT /loanproducts/23 req/upd-070-repoint-fundsource.json || exit 1
cat "$DIR/out/A2-502-p23-repoint-fundsource.json"; echo
sh "$Q" A2-503-db-mapping-after-repoint sql/q8-t275-mapping-ids.sql || exit 1
sh "$C" A2-504-loanproduct23-after-repoint GET /loanproducts/23 || exit 1

# --- 2. add a payment-channel override for payment type 2.  req/upd-071 as written by A2-3.
sh "$C" A2-505-p23-add-channel PUT /loanproducts/23 req/upd-071-add-channel.json || exit 1
cat "$DIR/out/A2-505-p23-add-channel.json"; echo
sh "$Q" A2-506-db-mapping-after-channel sql/q8-t275-mapping-ids.sql || exit 1
sh "$C" A2-507-loanproduct23-after-channel GET /loanproducts/23 || exit 1

# --- 3. an update carrying NO accounting parameter whatsoever.
sh "$C" A2-508-p23-description-only PUT /loanproducts/23 req/t275-072-p23-description-only.json || exit 1
cat "$DIR/out/A2-508-p23-description-only.json"; echo
sh "$Q" A2-509-db-mapping-after-description sql/q8-t275-mapping-ids.sql || exit 1

# --- 4. an EMPTY paymentChannelToFundSourceMappings array.
sh "$C" A2-510-p23-channel-empty PUT /loanproducts/23 req/t275-073-p23-channel-empty.json || exit 1
cat "$DIR/out/A2-510-p23-channel-empty.json"; echo
sh "$Q" A2-511-db-mapping-after-channel-empty sql/q8-t275-mapping-ids.sql || exit 1
sh "$C" A2-512-loanproduct23-final GET /loanproducts/23 || exit 1

# --- 5. §5 asked for q2 specifically. Run it, so this fire's output is directly
#        comparable with out/A2-072-db-product-mapping-rows.txt from the earlier fire.
sh "$Q" A2-513-db-q2-product-mapping-rows sql/q2-product-mapping-rows.sql || exit 1

echo "== group A complete =="
