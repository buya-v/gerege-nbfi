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
	// [VERIFIED: SavingsAccountTransaction.java:790-799].
	Type SavingsAccountTransactionType
	// Amount is the signed minor-unit amount of the transaction.
	Amount MinorUnits

	// Reversed is m_savings_account_transaction.is_reversed — the flag
	// undoTransaction sets on the ORIGINAL row [VERIFIED: SavingsAccountTransaction.java:390-392].
	Reversed bool
	// Reversal is m_savings_account_transaction.is_reversal — the flag set on
	// the APPENDED correction row [VERIFIED: SavingsAccountTransaction.java:133-134, :502-504].
	Reversal bool
}

// NO RunningBalance FIELD, AND NO Entry FIELD, DELIBERATELY.
//
// Fineract carries `running_balance_derived` on this row and derives it by
// writing it; CLAUDE.md forbids that ("Balances are derived, never written"),
// so the column is neither written nor read here — the running balance as at any
// transaction is RunningBalancesOf(stream)[i], a fold over the append-only
// postings. A read-back decode of that column would put a number this port did
// not derive into a field callers would then trust, which is the same defect
// arriving through the SELECT instead of the INSERT.
//
// The former `Entry TransactionEntryType` field is gone for the same reason one
// type down: it was a cached copy of Type.EntryType() that the fold then
// consulted instead of the type, so a caller could hand-build a transaction
// whose Entry disagreed with its Type and read a silently wrong balance. A
// derived value stored beside the thing it is derived from is the same failure
// mode as a stored balance. The classification is Type.IsCredit()/IsDebit(),
// computed on demand.

// IsVoid reports whether this posting contributes to no derivation at all —
// either it was reversed, or it IS the reversal of another.
//
// WHY BOTH FLAGS. Fineract's undo appends a correction row that is a SAME-TYPE,
// SAME-AMOUNT copy of the original [VERIFIED: SavingsAccountTransaction.java:352-358].
// A DEPOSIT undone therefore leaves TWO DEPOSIT rows in the table, and a fold
// that honours neither flag doubles the error instead of cancelling it.
func (t SavingsAccountTransaction) IsVoid() bool { return t.Reversed || t.Reversal }

// IsCreditType and IsDebitType are the row's TYPE-level classification, the
// port of SavingsAccountTransaction.isCreditType() / isDebitType()
// [VERIFIED: SavingsAccountTransaction.java:790-791, :798-799]. They call the
// FOLDED IsCredit/IsDebit on transactiontype.go, not the raw EntryType field.
func (t SavingsAccountTransaction) IsCreditType() bool { return t.Type.IsCredit() }

// IsDebitType — see IsCreditType.
func (t SavingsAccountTransaction) IsDebitType() bool { return t.Type.IsDebit() }

// IsCredit and IsDebit are the port of SavingsAccountTransaction.isCredit() /
// isDebit() [VERIFIED: SavingsAccountTransaction.java:786-799]:
//
//	isCredit() = isCreditType() && !isReversed() && !isReversalTransaction()
//	isDebit()  = isDebitType()  && !isReversed() && !isReversalTransaction()
//
// Both conjuncts are load-bearing: the type half subtracts the three
// balance-neutral types, the void half makes reversals the correction mechanism.
func (t SavingsAccountTransaction) IsCredit() bool { return t.IsCreditType() && !t.IsVoid() }

// IsDebit — see IsCredit.
func (t SavingsAccountTransaction) IsDebit() bool { return t.IsDebitType() && !t.IsVoid() }

// Effect returns the signed effect of this transaction on the POSTED balance,
// implied by the credit/debit classification and the amount. A credit adds, a
// debit subtracts; the amount is treated as a magnitude (absolute) so a
// negative sign never double-negates a debit. A row that is void (reversed, or
// a reversal) or balance-neutral by type (AMOUNT_HOLD, AMOUNT_RELEASE, ESCHEAT,
// or any type carrying no entry type) has no effect at all.
//
// THREE DEFECTS FIXED HERE, ALL FOUND BY REVIEW OF THE FOLD.
//
//	(a) the old body was `if t.Entry.IsDebit() { return -amount }; return amount`
//	    — an if/else over a THREE-valued classification, so every type carrying
//	    NO entry type fell through to the credit arm and INCREASED the balance.
//	    The switch is exhaustive and the unclassified case is explicitly zero.
//	(b) the old body consulted the RAW entry type, so AMOUNT_HOLD/AMOUNT_RELEASE
//	    came back as debit/credit and had to be excluded by a hand-written list
//	    at each fold site, and ESCHEAT (which the oracle excludes on the same
//	    line as AMOUNT_HOLD) was missing from that list. IsCredit()/IsDebit()
//	    carry the oracle's folded classification, so no list is needed.
//	(c) a reversed posting and its same-type reversal row used to both count, at
//	    full value, in the same direction. IsCredit()/IsDebit() carry the void
//	    conjuncts.
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
