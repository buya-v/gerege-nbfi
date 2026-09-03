package savings

// SavingsAccountSummary is the read-only projection of the reference oracle's
// per-account running totals, the Go port of Fineract's SavingsAccountSummary
// [VERIFIED: SavingsAccountSummary.java:36-87 — an @Embeddable, so in Fineract
// these are columns of m_savings_account, not of a table of their own].
//
// # THIS STRUCT CARRIES NO BALANCE, AND THAT IS THE POINT
//
// CLAUDE.md, first tier: "The ledger is double-entry and append-only. Balances
// are derived, never written." Fineract spells its balance columns
// `account_balance_derived` and `running_balance_derived` and then derives them
// BY WRITING THEM. This program adopts Fineract's PostgreSQL SCHEMA; it does not
// adopt Fineract's WRITE PATHS. Keeping the column and never writing it is
// consistent — writing it is not, because a stored balance is still a written
// balance (DEC-2 §4.4 I-3, §7: the m_trial_balance shape, refused).
//
// So there is no AccountBalance field here, no RunningBalance field on
// SavingsAccountTransaction, and no write path in postgres.go that populates
// either column. The balance is AccountBalanceOf below: a fold over the
// account's postings, computed on demand from the append-only transaction
// stream, held in nothing and stored nowhere.
//
// The twelve fields that remain are category totals, not balances, and this
// port only ever READS them (see PostgresSummaryRepository, which has no write
// method). During the strangler window they are written by Fineract; the Go
// module treats them as an inbound read model.
//
// The oracle's @Transient runningBalanceOnInterestPostingTillDate is also gone.
// It is a balance-shaped hole that nothing in this tree read and nothing wrote,
// and leaving one in a struct is an invitation to fill it. The daily-interest
// running balance is a per-posting-period derivation and belongs to the
// interest slice, which will fold it from the postings when it is ported.
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
}

// AccountBalanceOf derives the POSTED balance of an account from its postings,
// in integer minor units. It is the replacement for the deleted
// SavingsAccountSummary.AccountBalance field and for
// `account_balance_derived`: nothing stores this value, so nothing can be stale
// and nothing can be corrected other than by appending a transaction.
//
// The shape is the one the ledger guard names as lawful and the one
// nexus/internal/apps/ledger/money.go (DoubleEntryBalances) already uses: two
// bare local accumulators, one per entry side, differenced once at return. The
// two sides are summed separately rather than netted into a single running
// figure so that the derivation stays double-entry-shaped and a caller auditing
// it can see the debit and credit totals it is made of.
//
// HOLDS ARE EXCLUDED, AND THAT IS A NON-NEGOTIABLE, NOT AN OPTIMISATION.
// CLAUDE.md: "Holds are postings and alter `available` only, never posted
// `balance`." Fineract's SavingsAccountTransactionType does classify HOLD as a
// DEBIT and RELEASE as a CREDIT [VERIFIED: SavingsAccountTransactionType.java:
// 36-54, ported at transactiontype.go EntryType], so a naive fold over
// Effect() would let placing a hold REDUCE the posted balance. It does not
// here: the hold/release pair is skipped, and its effect appears only in
// AvailableOf.
//
// Amount is treated as a magnitude; the direction comes from the entry type, so
// a negative amount can never double-negate a debit. Types that carry no entry
// classification at all (WAIVE_CHARGES, ACCRUAL, the transfer sub-states,
// WRITTEN_OFF — EntryType returns the zero value) move neither side.
func AccountBalanceOf(txns []SavingsAccountTransaction) MinorUnits {
	var debit, credit MinorUnits
	for _, t := range txns {
		if t.Type.IsAmountHold() || t.Type.IsAmountRelease() {
			continue
		}
		switch e := t.Effect(); {
		case e < 0:
			debit += -e
		case e > 0:
			credit += e
		}
	}
	return credit - debit
}

// HeldOf derives the amount currently on hold: holds placed less holds
// released, in integer minor units. It never goes below zero — a release
// without a matching hold is a data defect, not a negative hold — and it is
// derived, like everything else here, rather than stored.
func HeldOf(txns []SavingsAccountTransaction) MinorUnits {
	var placed, released MinorUnits
	for _, t := range txns {
		amount := t.Amount
		if amount < 0 {
			amount = -amount
		}
		switch {
		case t.Type.IsAmountHold():
			placed += amount
		case t.Type.IsAmountRelease():
			released += amount
		}
	}
	if released > placed {
		return 0
	}
	return placed - released
}

// AvailableOf derives what the account holder may draw on: the posted balance
// less the outstanding holds. This is the ONLY figure a hold is permitted to
// move (CLAUDE.md: holds "alter `available` only, never posted `balance`"), and
// keeping it a separate derivation is what makes that rule checkable rather
// than merely stated.
func AvailableOf(txns []SavingsAccountTransaction) MinorUnits {
	return AccountBalanceOf(txns) - HeldOf(txns)
}

// RunningBalancesOf derives the posted balance as at each transaction in turn,
// returning one value per element of txns in the order given. It is the
// replacement for the deleted SavingsAccountTransaction.RunningBalance field
// and for `running_balance_derived`: a statement view gets its running column
// by asking for it, from the postings, at the moment it renders — never by
// reading back a number some earlier write path decided.
//
// The caller is responsible for passing the stream in the oracle's own order
// (PostgresTransactionRepository.FindByAccountID returns it ORDER BY id). A
// prefix fold of an unordered stream is a different number, so this function
// does not sort: silently reordering a caller's postings would hide the defect
// rather than surface it.
//
// A hold or release leaves the posted running balance unchanged, for the same
// reason AccountBalanceOf skips it.
func RunningBalancesOf(txns []SavingsAccountTransaction) []MinorUnits {
	out := make([]MinorUnits, 0, len(txns))
	var debit, credit MinorUnits
	for _, t := range txns {
		if !t.Type.IsAmountHold() && !t.Type.IsAmountRelease() {
			switch e := t.Effect(); {
			case e < 0:
				debit += -e
			case e > 0:
				credit += e
			}
		}
		out = append(out, credit-debit)
	}
	return out
}
