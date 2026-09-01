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
	// RunningBalance is account_balance_derived as at this transaction.
	RunningBalance MinorUnits
}

// Effect returns the signed balance effect implied by the entry and amount.
// A credit adds, a debit subtracts; the amount is treated as a magnitude
// (absolute) so a negative sign never double-negates a debit.
func (t SavingsAccountTransaction) Effect() MinorUnits {
	if t.Amount < 0 {
		t.Amount = -t.Amount
	}
	if t.Entry.IsDebit() {
		return -t.Amount
	}
	return t.Amount
}
