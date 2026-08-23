#!/bin/bash
# T296 — NON-VACUITY BY MUTATION, four arms.
#
# T294 registered ONE wrong implementation beside LDG-REFUSE-03 and showed it
# dies. The brief's question is the harder one: does the vector kill defects the
# author did NOT ship beside it? Each arm below perturbs the PORT (GoPoster's
# STEP 1.5) and re-grades the committed ledger corpus. A green arm is a defect the
# vector cannot see.
#
#   BASE  the merged port, unmodified                       expect GREEN
#   A     drop `len(req.PostedNonContraTransactionIDs) > 0` expect ???
#         -> a port that refuses EVERY defineOpeningBalance command, on an empty
#            ledger too, where the oracle ACCEPTS (:812 CollectionUtils.isEmpty)
#   B     drop `req.Command == "defineOpeningBalance"`      expect ???
#   E     move the rule BELOW the balance check             expect RED
#         -> the precedence flip, which is what the vector claims to grade
#
# The port is restored from a backup after every arm and the tree is left clean.
set -uo pipefail
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac0c499f54ea397f9
. "$W/.softhouse/bin/go-env.sh"
IMPL="$W/nexus/internal/apps/ledger/conformance/impl.go"
BAK=$(mktemp "${TMPDIR:-/tmp}/t296-impl.XXXXXXXX.go") || exit 1
cp "$IMPL" "$BAK"
restore() { cp "$BAK" "$IMPL"; }
trap restore EXIT

cd "$W/nexus" || exit 1
BIN=$(mktemp "${TMPDIR:-/tmp}/t296-conf.XXXXXXXX") || exit 1

grade() {
  go build -o "$BIN" ./internal/apps/loanschedule/conformance/cmd/conformance || {
    echo "  BUILD FAILED"; return 1; }
  "$BIN" -oracle-probe=up -context=ledger 2>&1 \
    | grep -E "^    (LDG-REFUSE-03|ledger (parity|oracle-refusal))" \
    | sed 's/  */ /g'
}

echo "=== BASE — the merged port, unmodified ==="
restore; grade

echo
echo '=== ARM A — predicate becomes `req.Command == "defineOpeningBalance"` ==='
echo '           (the lifted transaction-id list is no longer read at all)'
restore
LC_ALL=C sed -i '' \
  's|if req.Command == "defineOpeningBalance" \&\& len(req.PostedNonContraTransactionIDs) > 0 {|if req.Command == "defineOpeningBalance" {|' \
  "$IMPL"
grade

echo
echo '=== ARM B — predicate becomes `len(req.PostedNonContraTransactionIDs) > 0` ==='
echo '           (the command is no longer read at all)'
restore
LC_ALL=C sed -i '' \
  's|if req.Command == "defineOpeningBalance" \&\& len(req.PostedNonContraTransactionIDs) > 0 {|if len(req.PostedNonContraTransactionIDs) > 0 {|' \
  "$IMPL"
grade

echo
echo "=== ARM E — the PRECEDENCE FLIP: balance rule moved ahead of the OB rule ==="
restore
python3 - "$IMPL" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
ob = '''	if req.Command == "defineOpeningBalance" && len(req.PostedNonContraTransactionIDs) > 0 {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       "error.msg.journalentry.defining.openingbalance.not.allowed",
			Message:    "Defining Opening balances not allowed after journal entries posted",
		}, nil
	}
'''
bal = '''	if err := ledger.DoubleEntryBalances(legs); err != nil {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403,
			Code:       "error.msg.glJournalEntry.invalid.mismatch.debits.credits",
			Message:    "Sum of All Debits must equal the sum of all Credits for a Journal Entry",
		}, nil
	}
'''
assert ob in s and bal in s, "the port no longer has the shape this probe perturbs"
s = s.replace(ob, bal, 1)
j = s.index(bal, s.index(bal) + 1)
s = s[:j] + ob + s[j + len(bal):]
open(p, "w").write(s)
PY
grade

echo
restore
echo "=== port restored; git diff over impl.go: ==="
git -C "$W" diff --stat -- nexus/internal/apps/ledger/conformance/impl.go
echo "(empty means the tree is clean)"
