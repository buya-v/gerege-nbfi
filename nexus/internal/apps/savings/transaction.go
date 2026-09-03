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
	// Type is transaction_type_enum. It is the ONLY input to the credit/debit
	// classification, exactly as in the oracle: SavingsAccountTransaction has
	// no entryType field and no entry-type column, and every classification
	// method on it delegates to getTransactionType()
	// [VERIFIED: SavingsAccountTransaction.java:790-799 — isCreditType() is
	// `getTransactionType().isCredit()`; the entity declares no entryType].
	//
	// T515 DELETED THE `Entry TransactionEntryType` FIELD THAT USED TO SIT
	// HERE. It was a cached copy of Type.EntryType() that the fold then
	// consulted instead of the type, which meant (a) the fold read the RAW
	// entry type rather than the folded classification — the T513 defect — and
	// (b) any caller could hand-build a transaction whose Entry disagreed with
	// its Type and get a silently wrong balance out of it. A derived value
	// stored beside the thing it is derived from is the same failure mode as a
	// stored balance, one type down.
	Type SavingsAccountTransactionType
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

// IsCreditType and IsDebitType are the row's TYPE-level classification, the
// port of SavingsAccountTransaction.isCreditType() / isDebitType()
// [VERIFIED: SavingsAccountTransaction.java:790-791, :798-799]:
//
//	isCreditType() = getTransactionType().isCredit()
//	isDebitType()  = getTransactionType().isDebit()
//
// Note which method on the enum they call: the FOLDED IsCredit/IsDebit in
// transactiontype.go, which subtract AMOUNT_RELEASE from credit and AMOUNT_HOLD
// and ESCHEAT from debit — not the raw EntryType field. Before T515 these two
// delegated to the raw field, and every derivation below inherited the error.
func (t SavingsAccountTransaction) IsCreditType() bool { return t.Type.IsCredit() }

// IsDebitType — see IsCreditType.
func (t SavingsAccountTransaction) IsDebitType() bool { return t.Type.IsDebit() }

// IsCredit and IsDebit are the port of SavingsAccountTransaction.isCredit() /
// isDebit() [VERIFIED: SavingsAccountTransaction.java:786-799]:
//
//	isCredit() = isCreditType() && !isReversed() && !isReversalTransaction()
//	isDebit()  = isDebitType()  && !isReversed() && !isReversalTransaction()
//
// Both conjuncts are load-bearing and they were added in different tasks: the
// void half by T510 (reversals are the correction mechanism), the type half by
// T515 (the three balance-neutral types). Together they are the complete
// classification, so a fold over Effect() needs no exclusion list of its own.
func (t SavingsAccountTransaction) IsCredit() bool { return t.IsCreditType() && !t.IsVoid() }

// IsDebit — see IsCredit.
func (t SavingsAccountTransaction) IsDebit() bool { return t.IsDebitType() && !t.IsVoid() }

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

// Effect returns the signed effect of this transaction on the POSTED balance,
// implied by the credit/debit classification and the amount. A credit adds, a
// debit subtracts; the amount is treated as a magnitude (absolute) so a
// negative sign never double-negates a debit. A row that is void (reversed, or
// a reversal) or balance-neutral by type (AMOUNT_HOLD, AMOUNT_RELEASE, ESCHEAT,
// or any type carrying no entry type) has no effect at all.
//
// It IS the posted-balance effect, in full — that changed in T515. Its callers
// used to skip the hold/release pair by hand before consulting it, because the
// classification underneath it was the raw entry type; now IsCredit()/IsDebit()
// are the oracle's own folded classification and there is no exclusion list
// left anywhere in this package. Still call the derivations in summary.go
// rather than summing Effect() by hand: the fold there keeps the two sides
// separate so it stays double-entry-shaped.
//
// THREE DEFECTS FIXED HERE, ALL FOUND BY REVIEW OF THE FOLD.
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
//	classification, so a reversed posting and its same-type reversal row both
//	counted, at full value, in the same direction. It now calls
//	IsCredit()/IsDebit(), which carry the two void conjuncts.
//
//	T515 — the TYPE half itself was the RAW entry type rather than the oracle's
//	folded SavingsAccountTransactionType.isCredit()/isDebit(). ESCHEAT was
//	therefore a debit here and debited the balance, where the oracle moves
//	nothing: measured against the live instance, an account escheated for
//	500,000.00 read 0 here and 500000.000000 in account_balance_derived. See
//	transactiontype.go IsCredit for the capture.
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
