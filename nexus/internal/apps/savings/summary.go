package savings

// SavingsAccountSummary is the read-only projection of the reference oracle's
// per-account running totals, the Go port of Fineract's SavingsAccountSummary
// [VERIFIED: SavingsAccountSummary.java:39-87].
//
// # THIS STRUCT CARRIES NO BALANCE, AND THAT IS THE POINT
//
// CLAUDE.md, first tier: "The ledger is double-entry and append-only. Balances
// are derived, never written." Fineract spells its balance columns
// `account_balance_derived` and `running_balance_derived` and then derives them
// BY WRITING THEM. This program adopts Fineract's PostgreSQL SCHEMA; it does not
// adopt Fineract's WRITE PATHS. Keeping the column and never writing it is
// consistent — writing it is not, because a stored balance is still a written
// balance (DEC-2 §4.4 I-3).
//
// So there is no AccountBalance field here, no RunningBalance field on
// SavingsAccountTransaction, and no write path in postgres.go that populates
// either column. The balance is AccountBalanceOf below: a fold over the
// account's postings, computed on demand from the append-only transaction
// stream, held in nothing and stored nowhere.
//
// The twelve fields that remain are category totals, not balances, and this
// port only ever READS them (PostgresSummaryRepository has no write method).
// During the strangler window they are written by Fineract; the Go module treats
// them as an inbound read model.
//
// The oracle's @Transient runningBalanceOnInterestPostingTillDate is also gone.
// It is a balance-shaped hole that nothing in this tree read and nothing wrote,
// and leaving one in a struct is an invitation to fill it.
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
// figure so the derivation stays double-entry-shaped and a caller auditing it
// can see the debit and credit totals it is made of.
//
// REVERSALS ARE THE CORRECTION MECHANISM AND THEY CANCEL HERE. Effect() is zero
// for any row that is reversed or is itself a reversal, so an undone deposit
// contributes nothing from EITHER of the two rows Fineract leaves behind.
//
// HOLDS AND ESCHEATS MOVE NOTHING HERE, AND THERE IS NO EXCLUSION LIST SAYING
// SO. CLAUDE.md: "Holds are postings and alter `available` only, never posted
// `balance`." AMOUNT_HOLD, AMOUNT_RELEASE and ESCHEAT are excluded by
// SavingsAccountTransactionType.IsCredit/IsDebit, which is where Fineract
// excludes them, so this fold is a plain sum over Effect() with no
// type-specific knowledge in it at all.
//
// Amount is treated as a magnitude; the direction comes from the classification,
// so a negative amount can never double-negate a debit. Types that carry no
// entry classification at all (INVALID, WAIVE_CHARGES, ACCRUAL, the transfer
// sub-states, WRITTEN_OFF) move neither side.
func AccountBalanceOf(txns []SavingsAccountTransaction) MinorUnits {
	var debit, credit MinorUnits
	for _, t := range txns {
		switch e := t.Effect(); {
		case e < 0:
			debit += -e
		case e > 0:
			credit += e
		}
	}
	return credit - debit
}

// HeldOf derives the amount currently on hold: holds placed less holds released,
// in integer minor units. It never goes below zero — a release without a
// matching hold is a data defect, not a negative hold — and it is derived, like
// everything else here, rather than stored.
//
// KNOWN LIMITATIONS (folded to T507, recorded here so a reader is not misled).
// This is an aggregate fold: it pairs holds and releases by TOTAL, not by
// Fineract's release_id_of_hold_amount link [SavingsAccountTransaction.java
// release_id_of_hold_amount; SavingsAccount.java:898-899
// isAmountOnHoldNotReleased]. A duplicated release row (a retry that bypassed
// Idempotency-Key) therefore cannot be distinguished from a genuine release,
// and a release with no matching hold is silently clamped to zero, which reads
// as "all available" when the correct answer is "this data is inconsistent".
// Until the release_id link is carried on the row, HeldOf is a best-effort
// aggregate, not a per-hold reconciliation.
func HeldOf(txns []SavingsAccountTransaction) MinorUnits {
	var placed, released MinorUnits
	for _, t := range txns {
		if t.IsVoid() {
			continue
		}
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

// AvailableOf derives the posted balance less the outstanding holds. This is
// the ONLY figure a hold is permitted to move (CLAUDE.md: holds "alter
// `available` only, never posted `balance`"), and keeping it a separate
// derivation is what makes that rule checkable rather than merely stated.
//
// THIS IS NOT THE FULL WITHDRAWABLE BALANCE, and it must not be named as such.
// Fineract's getWithdrawableBalance() [SavingsAccount.java:3319-3322] subtracts
// three things — the outstanding holds, the product's min_required_balance, and
// any guarantor on_hold_funds_derived — of which HeldOf covers only the first.
// A caller that needs the withdrawable figure must complete the derivation with
// those two product/guarantor facts; this function is only the hold-adjusted
// portion, and only ever the hold-adjusted portion.
func AvailableOf(txns []SavingsAccountTransaction) MinorUnits {
	return AccountBalanceOf(txns) - HeldOf(txns)
}

// RunningBalancesOf derives the POSTED balance as at each transaction in turn,
// returning one value per element of txns in the order given. It is the
// replacement for the deleted SavingsAccountTransaction.RunningBalance field:
// a statement view gets its running column by asking for it, from the postings,
// at the moment it renders — never by reading back a number some earlier write
// path decided.
//
// The invariant: RunningBalancesOf(txns)[i] is the POSTED BALANCE after applying
// postings 0..i. So a posting that does not move the posted balance — a hold, a
// release, an escheat, a void row, an unclassified type — leaves the running
// value unchanged, and the last element equals AccountBalanceOf(txns) by
// construction. The loop body is the same plain fold over Effect() that
// AccountBalanceOf runs, emitting the prefix each step.
//
// RATIFIED DEVIATION (ENGINEERING, recorded 2026-09-03). This is NOT Fineract's
// `running_balance_derived`. Fineract moves the running balance on a hold
// [SavingsAccount.java:902,912]; this port deliberately does not, because
// CLAUDE.md requires holds to "alter `available` only, never posted `balance`",
// and a running column that drops on a hold is a posted-balance figure. The
// first hold-bearing savings vector will therefore mismatch on this column and
// must be graded against this port's definition, not the oracle's — this note
// is what turns that mismatch from a port bug into a known deviation.
//
// The caller is responsible for passing the stream in the oracle's own order
// (PostgresTransactionRepository.FindByAccountID returns it ORDER BY id). A
// prefix fold of an unordered stream is a different number, so this function
// does not sort.
func RunningBalancesOf(txns []SavingsAccountTransaction) []MinorUnits {
	out := make([]MinorUnits, 0, len(txns))
	var debit, credit MinorUnits
	for _, t := range txns {
		switch e := t.Effect(); {
		case e < 0:
			debit += -e
		case e > 0:
			credit += e
		}
		out = append(out, credit-debit)
	}
	return out
}
