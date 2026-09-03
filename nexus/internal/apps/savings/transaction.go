package savings

// SavingsAccountTransaction is the Go port of a single savings-account
// transaction's core identity: what happened, which way it moved money, by how
// much, and WHETHER IT COUNTS. It is the read model a posting slice consumes,
// not the double-entry posting itself (that belongs to tierA-gl-accounting).
//
// Reference: SavingsAccountTransaction.java
// [fineract-savings/.../savings/domain/SavingsAccountTransaction.java],
// reduced to the fields a later ledger bridge needs.
type SavingsAccountTransaction struct {
	// ID is m_savings_account_transaction.id. Zero means not-yet-persisted,
	// the same sentinel SavingsAccount.ID uses.
	ID int64
	// AccountID is m_savings_account_transaction.savings_account_id.
	AccountID int64
	// Type is transaction_type_enum.
	Type SavingsAccountTransactionType
	// Entry is the in-account CREDIT/DEBIT classification.
	Entry TransactionEntryType
	// Amount is the signed minor-unit amount of the transaction.
	Amount MinorUnits

	// Reversed is m_savings_account_transaction.is_reversed — the flag
	// undoTransaction sets on the ORIGINAL row [VERIFIED: schema
	// 0001_initial_schema.xml:3852-3854, `<constraints nullable="false"/>`;
	// SavingsAccountTransaction.java:390-392 isReversed()].
	Reversed bool
	// Reversal is m_savings_account_transaction.is_reversal — the flag set on
	// the APPENDED correction row [VERIFIED: schema
	// 0005_savings_transaction_reversal.xml:27-30, BOOLEAN DEFAULT false
	// NOT NULL; SavingsAccountTransaction.java:133-134, :502-504
	// isReversalTransaction()].
	Reversal bool

	// ReleaseIDOfHoldAmount is m_savings_account_transaction
	// .release_id_of_hold_amount: on an AMOUNT_HOLD row, the id of the
	// AMOUNT_RELEASE row that released it. Zero means "not released" (the
	// column is nullable and Fineract tests it with `== null`)
	// [VERIFIED: schema :3871 nullable; SavingsAccountTransaction.java:127-128,
	// :466-468 updateReleaseId, :898-899 isAmountOnHoldNotReleased;
	// written at SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953
	// and InteropServiceImpl.java:451,494].
	ReleaseIDOfHoldAmount int64
}

// NO RunningBalance FIELD, DELIBERATELY. Fineract carries
// `running_balance_derived` on this row and derives it by writing it; CLAUDE.md
// forbids that ("Balances are derived, never written") and DEC-2 §4.4 I-3 / §7
// refuse the shape. The running balance as at any transaction is
// RunningBalancesOf(stream)[i] — a fold over the append-only postings, computed
// when asked for. A read-back decode of that column would be no better: it
// would put a number this port did not derive into a field callers would then
// trust, which is the same defect arriving through the SELECT instead of the
// INSERT. So the column is neither written nor read here.
//
// Reversed / Reversal / ReleaseIDOfHoldAmount are NOT that shape and the
// distinction is the whole of T510. They are not sums, not balances and not
// derivable from anything else in the row: they are the FACTS about the posting
// that decide whether it counts. Reading a fact is what a fold over an
// append-only stream is made of; reading a total is what I-3 refuses.

// IsVoid reports whether this posting contributes to no derivation at all —
// either it was reversed, or it IS the reversal of another.
//
// It is the conjunction Fineract carries on every one of the twelve calculators
// in SavingsAccountTransactionSummaryWrapper (`isNotReversed() &&
// !isReversalTransaction()`) and the first branch of the running-balance loop
// [VERIFIED: SavingsAccount.java:897-898, which calls zeroBalanceFields() on
// exactly this predicate].
//
// WHY BOTH FLAGS, AND WHY THIS IS NOT DOUBLE-COUNTING. Fineract's undo appends
// a correction row that is a SAME-TYPE, SAME-AMOUNT copy of the original —
// reversal() is copyTransaction() with reversed = false and
// reversalTransaction = true [VERIFIED: SavingsAccountTransaction.java:352-358].
// A DEPOSIT undone therefore leaves TWO DEPOSIT rows in the table, and a fold
// that honours neither flag does not cancel the error, it DOUBLES it.
func (t SavingsAccountTransaction) IsVoid() bool { return t.Reversed || t.Reversal }

// IsCredit and IsDebit are the port of SavingsAccountTransaction.isCredit() /
// isDebit() [VERIFIED: SavingsAccountTransaction.java:786-799]:
//
//	isCredit() = isCreditType() && !isReversed() && !isReversalTransaction()
//	isDebit()  = isDebitType()  && !isReversed() && !isReversalTransaction()
//
// The TYPE half alone (Entry.IsCredit() / Entry.IsDebit(), i.e. Fineract's
// isCreditType() / isDebitType()) is NOT the classification any Fineract
// balance derivation folds over, and using it alone was T510's defect.
func (t SavingsAccountTransaction) IsCredit() bool { return t.Entry.IsCredit() && !t.IsVoid() }

// IsDebit — see IsCredit.
func (t SavingsAccountTransaction) IsDebit() bool { return t.Entry.IsDebit() && !t.IsVoid() }

// IsHoldNotReleased reports whether this row is an AMOUNT_HOLD that is still
// holding funds: a hold, not voided, with no release row pointing back at it.
//
// It is the port of isAmountOnHoldNotReleased() [VERIFIED:
// SavingsAccountTransaction.java:898-899], with the void conjunct added. The
// added conjunct is oracle-grounded rather than invented: recalculateDailyBalances
// tests isReversed()/isReversalTransaction() BEFORE the isAmountOnHold() branch
// and zeroes the row instead [VERIFIED: SavingsAccount.java:897-912], so a
// reversed hold moves nothing in Fineract's own derivation either.
//
// Pairing is by identity, not by arithmetic. Fineract writes the release row's
// id onto the HOLD row (`holdTransaction.updateReleaseId(transaction.getId())`)
// and its validator refuses a second release against an already-paired hold
// [VERIFIED: SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953;
// SavingsAccountTransactionDataValidator.java:321].
func (t SavingsAccountTransaction) IsHoldNotReleased() bool {
	return t.Type.IsAmountHold() && !t.IsVoid() && t.ReleaseIDOfHoldAmount == 0
}

// Effect returns the signed effect of this transaction on the account's
// AVAILABLE amount, implied by the credit/debit classification and the amount.
// A credit adds, a debit subtracts; the amount is treated as a magnitude
// (absolute) so a negative sign never double-negates a debit. A VOID row
// (reversed, or a reversal) has no effect at all.
//
// It is NOT, on its own, the effect on the POSTED balance: Fineract classifies
// HOLD as a debit and RELEASE as a credit, and CLAUDE.md is explicit that holds
// "alter `available` only, never posted `balance`". AccountBalanceOf therefore
// skips the hold/release pair before it consults this method. Call one of the
// derivations in summary.go rather than summing Effect() by hand.
//
// TWO DEFECTS FIXED HERE, BOTH FOUND BY REVIEW OF THE FOLD.
//
//	T501 — the body was `if t.Entry.IsDebit() { return -amount }; return amount`:
//	an if/else over a THREE-valued classification, so every type carrying NO
//	entry type fell through to the credit arm and INCREASED the balance.
//	INVALID(0), WAIVE_CHARGES(6), ACCRUAL(10), the four transfer sub-states and
//	WRITTEN_OFF(16) all return the zero TransactionEntryType
//	[transactiontype.go EntryType, default arm]. The switch below is exhaustive
//	on the classification and the unclassified case is explicitly zero.
//
//	T510 — the switch still consulted only the TYPE half of Fineract's
//	classification (isCreditType/isDebitType), so a reversed posting and its
//	same-type reversal row both counted, at full value, in the same direction.
//	It now calls IsCredit()/IsDebit(), which carry the two void conjuncts.
func (t SavingsAccountTransaction) Effect() MinorUnits {
	amount := t.Amount
	if amount < 0 {
		amount = -amount
	}
	switch {
	case t.IsDebit():
		return -amount
	case t.IsCredit():
		return amount
	default:
		return 0
	}
}
