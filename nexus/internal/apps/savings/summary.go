package savings

// SavingsAccountSummary is the derived running-total block of a savings
// account, the Go port of Fineract's SavingsAccountSummary
// [VERIFIED: SavingsAccountSummary.java:39-87].
//
// # derive-don't-store
//
// Every field here is a *_derived column recomputed from the account's
// transaction stream; nothing is a primary write target. The zero value is the
// correct empty summary, matching the oracle's BigDecimal.ZERO defaults on the
// non-column running-balance fields.
type SavingsAccountSummary struct {
	// TotalDeposits is total_deposits_derived.
	TotalDeposits MinorUnits
	// TotalWithdrawals is total_withdrawals_derived.
	TotalWithdrawals MinorUnits
	// TotalInterestEarned is total_interest_earned_derived.
	TotalInterestEarned MinorUnits
	// TotalInterestPosted is total_interest_posted_derived.
	TotalInterestPosted MinorUnits
	// TotalWithdrawalFees is total_withdrawal_fees_derived.
	TotalWithdrawalFees MinorUnits
	// TotalFeeCharge is total_fees_charge_derived.
	TotalFeeCharge MinorUnits
	// TotalPenaltyCharge is total_penalty_charge_derived.
	TotalPenaltyCharge MinorUnits
	// TotalAnnualFees is total_annual_fees_derived.
	TotalAnnualFees MinorUnits
	// TotalFeeChargesWaived is total_fee_charges_waived_derived (transient in
	// the oracle).
	TotalFeeChargesWaived MinorUnits
	// TotalPenaltyChargesWaived is total_penalty_charges_waived_derived
	// (transient in the oracle).
	TotalPenaltyChargesWaived MinorUnits
	// TotalOverdraftInterestDerived is total_overdraft_interest_derived.
	TotalOverdraftInterestDerived MinorUnits
	// TotalWithholdTax is total_withhold_tax_derived.
	TotalWithholdTax MinorUnits
	// AccountBalance is account_balance_derived.
	AccountBalance MinorUnits
	// RunningBalanceOnInterestPostingTillDate is the oracle's transient
	// runningBalanceOnInterestPostingTillDate, the balance used by a daily
	// interest calculation and reset after each posting.
	RunningBalanceOnInterestPostingTillDate MinorUnits
}

// Add applies the signed effect of one posting to the summary. The effect is
// positive for a credit, negative for a debit; the caller classifies the
// transaction type and passes the signed amount. This keeps the summary a pure
// fold over postings rather than embedding transaction-type knowledge.
func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary {
	s.AccountBalance += effect
	return s
}
