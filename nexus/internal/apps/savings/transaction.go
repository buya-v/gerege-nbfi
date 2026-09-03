package savings

// SavingsAccountTransaction is the Go port of a single savings-account
// transaction's core identity: what happened, which way it moved money, and by
// how much. It is the read model a posting slice consumes, not the double-entry
// posting itself (that belongs to tierA-gl-accounting).
//
// Reference: SavingsAccountTransaction.java
// [fineract-savings/.../savings/domain/SavingsAccountTransaction.java],
// reduced to the fields a later ledger bridge needs.
type SavingsAccountTransaction struct {
	// ID is m_savings_account_transaction.id.
	ID int64
	// AccountID is m_savings_account_transaction.savings_account_id.
	AccountID int64
	// Type is transaction_type_enum.
	Type SavingsAccountTransactionType
	// Entry is the in-account CREDIT/DEBIT classification.
	Entry TransactionEntryType
	// Amount is the signed minor-unit amount of the transaction.
	Amount MinorUnits
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

// Effect returns the signed effect of this transaction on the account's
// AVAILABLE amount, implied by the entry classification and the amount. A
// credit adds, a debit subtracts; the amount is treated as a magnitude
// (absolute) so a negative sign never double-negates a debit.
//
// It is NOT, on its own, the effect on the POSTED balance: Fineract classifies
// HOLD as a debit and RELEASE as a credit, and CLAUDE.md is explicit that holds
// "alter `available` only, never posted `balance`". AccountBalanceOf therefore
// skips the hold/release pair before it consults this method; AvailableOf does
// not. Call one of those rather than summing Effect() by hand.
// DEFECT FIXED HERE, FOUND BY THE FOLD (T501). The previous body was
// `if t.Entry.IsDebit() { return -amount }; return amount` — an `if/else` over a
// THREE-valued classification, so every type that carries NO entry type at all
// fell through to the credit arm and INCREASED the balance. ACCRUAL,
// WAIVE_CHARGES, the transfer sub-states and WRITTEN_OFF all return the zero
// TransactionEntryType [transactiontype.go EntryType, default arm], and
// transactiontype.go's own doc already called them "balance-neutral and
// non-posting". They were not neutral. The switch below is exhaustive on the
// classification, and the unclassified case is explicitly zero rather than
// implicitly a credit.
func (t SavingsAccountTransaction) Effect() MinorUnits {
	amount := t.Amount
	if amount < 0 {
		amount = -amount
	}
	switch {
	case t.Entry.IsDebit():
		return -amount
	case t.Entry.IsCredit():
		return amount
	default:
		return 0
	}
}
