#!/bin/sh
# T275 / GROUP A2 -- THE PROBE THIS FIRE'S OWN RESULT CREATED.
#
# run-500 answered §5 row 1 and, in answering it, REFUTED §5's framing on the generic
# slots: A2-503 shows mapping row id 12 SURVIVING a fundSourceAccountId change (gl 2 ->
# gl 16) with the table's max(id) unmoved at 94. That is an UPDATE IN PLACE, not a
# delete-then-recreate. A2-509 further shows that an update carrying no accounting
# parameter at all disturbs no mapping row: 11 ids in, 11 ids out.
#
# So the delete-then-recreate question is not answered, it has MOVED -- to the LIST-VALUED
# dimension. A2-506 (add a channel) created id 95 and A2-511 (empty array) deleted it with
# nothing recreated, which is consistent with BOTH a full replace-the-list AND a
# reconcile-by-key. The two only separate when an EXISTING list entry CHANGES VALUE:
#
#   reconcile-by-key  -> id 96 survives, its gl_account_id moves 16 -> 17
#   replace-the-list  -> id 96 is deleted and id 97 appears at the same paymentTypeId
#
# Three steps, in this order, because each is a control for the next:
#   1  re-add the channel                       (establishes a known live row id)
#   2  re-send the IDENTICAL body               (does an UNCHANGED list churn identity?)
#   3  re-point that channel to another account (the discriminator above)
#
# Step 2 is not padding. If an unchanged list churns the row id, then any port that
# reconciles by key diverges from the oracle on every no-op save -- and a caller replaying
# a PUT (the ordinary retry case) would burn identity values on the oracle. That is worth
# an observation of its own.
#
# Not a money movement: product configuration only. cap8.sh, no Idempotency-Key.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"
Q="$DIR/capsql.sh"

echo "== T275 group A2: payment-channel mapping row IDENTITY under update =="

# --- 1. re-add. req/upd-071-add-channel.json is the SAME body run-500 step 2 used; it is
#        reused rather than duplicated, so nothing new can drift away from it.
sh "$C" A2-514-p23-channel-readd PUT /loanproducts/23 req/upd-071-add-channel.json || exit 1
cat "$DIR/out/A2-514-p23-channel-readd.json"; echo
sh "$Q" A2-515-db-mapping-after-readd sql/q8-t275-mapping-ids.sql || exit 1

# --- 2. the IDENTICAL body again. Byte-for-byte the same request; the only variable is
#        that the oracle's state now already satisfies it.
sh "$C" A2-516-p23-channel-resend-identical PUT /loanproducts/23 req/upd-071-add-channel.json || exit 1
cat "$DIR/out/A2-516-p23-channel-resend-identical.json"; echo
sh "$Q" A2-517-db-mapping-after-resend sql/q8-t275-mapping-ids.sql || exit 1

# --- 3. the discriminator: same paymentTypeId, different fund source account.
sh "$C" A2-518-p23-channel-repoint PUT /loanproducts/23 req/t275-075-p23-channel-repoint.json || exit 1
cat "$DIR/out/A2-518-p23-channel-repoint.json"; echo
sh "$Q" A2-519-db-mapping-after-channel-repoint sql/q8-t275-mapping-ids.sql || exit 1

sh "$C" A2-521-loanproduct23-after-channel-repoint GET /loanproducts/23 || exit 1

echo "== group A2 complete =="
