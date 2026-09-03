package savings

import "fmt"

// SavingsAccountSummary is the read-only projection of the reference oracle's
// per-account running totals, the Go port of Fineract's SavingsAccountSummary
// [VERIFIED: SavingsAccountSummary.java:36-87 — an @Embeddable, so in Fineract
// these are columns of m_savings_account, not of a table of their own;
// @Embedded at SavingsAccount.java:306-307].
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

// THE THREE RATIFIED DIVERGENCES FROM THE REFERENCE ORACLE, STATED ONCE
//
// CLAUDE.md makes Fineract the oracle, so a place where these derivations
// deliberately do NOT reproduce a Fineract number has to be written down, or
// the first failing savings golden vector will be read as a port bug and
// "fixed" back into a defect. All three are routed as ENGINEERING gate entries
// G-25, G-26 and G-27 in .softhouse/gates.md so the vector harness expects them.
//
//	D-1  HOLDS DO NOT MOVE A RUNNING BALANCE (AccountBalanceOf, RunningBalancesOf)
//	     Fineract's recalculateDailyBalances moves running_balance_derived on
//	     AMOUNT_HOLD / AMOUNT_RELEASE — `if (transaction.isCredit() ||
//	     transaction.isAmountRelease())` … `else if (transaction.isDebit() ||
//	     transaction.isAmountOnHold())` [VERIFIED: SavingsAccount.java:902,912].
//	     We do not. CLAUDE.md is a non-negotiable here: holds "alter `available`
//	     only, never posted `balance`". Fineract's own STORED account balance
//	     agrees with us — neither type appears in any of the nine terms of
//	     updateSummary [SavingsAccountSummary.java:110-112] nor in any of the
//	     twelve calculators of SavingsAccountTransactionSummaryWrapper, and both
//	     fall to `default: break;` in updateSummaryWithPivotConfig [:182-183].
//	     So Fineract is internally inconsistent and we follow its account
//	     balance, not its running balance.
//
//	D-2  A VOID ROW CARRIES THE UNCHANGED PREFIX VALUE (RunningBalancesOf)
//	     Fineract calls zeroBalanceFields() on a reversed / reversal row, which
//	     sets runningBalance to NULL [VERIFIED: SavingsAccount.java:897-898;
//	     SavingsAccountTransaction.java:586-591]. Fineract therefore states NO
//	     running balance on such a row; we state the balance unchanged by it,
//	     because []MinorUnits has no NULL and a zero would read as "the account
//	     emptied here". Same rule as D-1: a posting that does not move the
//	     posted balance leaves the running value alone.
//
//	D-3  ESCHEAT DEBITS THE POSTED BALANCE (AccountBalanceOf, RunningBalancesOf)
//	     ESCHEAT(19) is TransactionEntryType.DEBIT in the oracle's own enum, and
//	     Fineract's running_balance_derived does debit on it (isDebit()). But it
//	     appears in NONE of the nine terms of updateSummary and falls to
//	     `default: break;` in updateSummaryWithPivotConfig, so Fineract's STORED
//	     account_balance_derived does NOT move: an account escheated for its
//	     whole balance still reports that balance [VERIFIED:
//	     SavingsAccount.escheat, :3382-3396, which appends the ESCHEAT
//	     transaction for the full balance and then calls updateSummary].
//	     We debit. Chosen because (a) two of the three Fineract authorities —
//	     the entry-type classification and the running-balance derivation —
//	     agree with us and only the stored aggregate does not; (b) that stored
//	     aggregate is precisely the artefact I-3 refuses; and (c) the other side
//	     leaves the full balance readable on a closed account whose funds have
//	     gone to the state, which is an overstatement of available funds in the
//	     permissive direction. Recorded, not hidden: a vector comparing
//	     AccountBalanceOf against account_balance_derived across an escheat WILL
//	     differ by the whole balance, and that is expected.

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
// REVERSALS ARE THE CORRECTION MECHANISM AND THEY CANCEL HERE. Effect() is
// zero for any row that is reversed or is itself a reversal, so an undone
// deposit contributes nothing from EITHER of the two rows Fineract leaves
// behind. See SavingsAccountTransaction.IsVoid for why both flags are needed
// and why honouring only one would double the error rather than cancel it.
//
// HOLDS ARE EXCLUDED, AND THAT IS A NON-NEGOTIABLE, NOT AN OPTIMISATION.
// CLAUDE.md: "Holds are postings and alter `available` only, never posted
// `balance`." Fineract's SavingsAccountTransactionType does classify HOLD as a
// DEBIT and RELEASE as a CREDIT [VERIFIED: SavingsAccountTransactionType.java:
// 35-54, ported at transactiontype.go EntryType], so a naive fold over
// Effect() would let placing a hold REDUCE the posted balance. It does not
// here: the hold/release pair is skipped, and its effect appears only in
// AvailableOf. See D-1 above.
//
// Amount is treated as a magnitude; the direction comes from the entry type, so
// a negative amount can never double-negate a debit. Types that carry no entry
// classification at all (INVALID, WAIVE_CHARGES, ACCRUAL, the transfer
// sub-states, WRITTEN_OFF — EntryType returns the zero value) move neither
// side.
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

// ErrOrphanRelease reports an AMOUNT_RELEASE posting that no AMOUNT_HOLD row
// claims. It is returned, rather than absorbed, because the alternative is to
// report a plausible number for a corrupt stream: the previous implementation
// summed hold and release magnitudes and floored the difference at zero, so a
// release row duplicated by a retry without an Idempotency-Key silently
// released the whole balance for withdrawal with no error anywhere. On money,
// a derivation that cannot be computed must fail closed and say so.
type ErrOrphanRelease struct {
	// TransactionID is m_savings_account_transaction.id of the release row, or
	// zero if the row was never persisted.
	TransactionID int64
	// Amount is the release row's amount, in minor units.
	Amount MinorUnits
}

func (e *ErrOrphanRelease) Error() string {
	return fmt.Sprintf("savings: AMOUNT_RELEASE transaction %d for %d minor units is "+
		"claimed by no AMOUNT_HOLD row (release_id_of_hold_amount): the hold stream "+
		"is inconsistent and the held amount cannot be derived",
		e.TransactionID, e.Amount)
}

// HeldOf derives the amount currently on hold, in integer minor units: the sum
// of hold postings that are neither void nor released.
//
// PAIRING IS BY IDENTITY, NOT BY ARITHMETIC. Fineract's definition of an
// outstanding hold is isAmountOnHoldNotReleased() — `isAmountOnHold() &&
// getReleaseIdOfHoldAmountTransaction() == null` [VERIFIED:
// SavingsAccountTransaction.java:898-899] — and the release path writes the
// release row's id onto the HOLD row [VERIFIED:
// SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953;
// InteropServiceImpl.java:451,494], with the validator refusing a second
// release against an already-paired hold [SavingsAccountTransactionDataValidator
// .java:321]. Summing hold magnitudes and subtracting release magnitudes gives
// the same answer only when every release exactly and completely matches a
// hold, which is the assumption a corrupt stream violates.
//
// A release row that no hold claims is therefore an ErrOrphanRelease, not a
// zero. The referenced set is built from ALL hold rows including void ones,
// because the pairing is a fact about the two rows and does not stop being true
// when the hold is reversed.
//
// KNOWN GAP, FAILING CLOSED (raised, not fixed here — T510 handoff). This port
// has no hold/release SERVICE and PostgresTransactionRepository.Insert does not
// write release_id_of_hold_amount, so a hold and release appended BY THIS PORT
// are unpaired. On such a stream HeldOf returns ErrOrphanRelease rather than a
// number — it over-holds rather than over-releases, which is the safe direction
// on money. Reading Fineract's own rows, which carry the FK, is the strangler
// path this function is built for and is exact.
func HeldOf(txns []SavingsAccountTransaction) (MinorUnits, error) {
	claimed := make(map[int64]struct{}, len(txns))
	for _, t := range txns {
		if t.Type.IsAmountHold() && t.ReleaseIDOfHoldAmount != 0 {
			claimed[t.ReleaseIDOfHoldAmount] = struct{}{}
		}
	}
	var held MinorUnits
	for _, t := range txns {
		switch {
		case t.IsHoldNotReleased():
			amount := t.Amount
			if amount < 0 {
				amount = -amount
			}
			held += amount
		case t.Type.IsAmountRelease() && !t.IsVoid():
			if _, ok := claimed[t.ID]; !ok {
				return 0, &ErrOrphanRelease{TransactionID: t.ID, Amount: t.Amount}
			}
		}
	}
	return held, nil
}

// AvailableOf derives the posted balance less the outstanding
// transaction-stream holds. A hold is the ONLY thing permitted to move this
// figure and not the posted balance (CLAUDE.md: holds "alter `available` only,
// never posted `balance`"), and keeping it a separate derivation is what makes
// that rule checkable rather than merely stated.
//
// ⚠ THIS IS NOT THE WITHDRAWABLE BALANCE, AND MUST NOT BE WIRED TO A WITHDRAWAL
// AUTHORISATION. Fineract's withdrawable balance has THREE subtrahends:
//
//	getWithdrawableBalance() = getAccountBalance()
//	    - minRequiredBalanceDerived(getCurrency())   // m_savings_account.min_required_balance
//	    - getOnHoldFunds()                           // m_savings_account.on_hold_funds_derived
//	    - getSavingsHoldAmount()                     // m_savings_account.total_savings_amount_on_hold
//
// [VERIFIED: SavingsAccount.java:3319-3322; schema :3712, :3718, :3727.]
// HeldOf covers only the third, and only its transaction-stream half. Neither
// min_required_balance nor on_hold_funds_derived is ported — on_hold_funds_derived
// carries guarantor and loan holds, which produce NO AMOUNT_HOLD row at all —
// so on an account with a 100,000₮ minimum balance and a 200,000₮ guarantor
// hold this function reports 300,000₮ MORE than Fineract would release. It
// overstates, i.e. it fails OPEN, which is why the limitation is stated at the
// top of the doc rather than the bottom.
//
// Completing it is an account-model port, not a ledger-invariant repair: it
// needs min_required_balance, on_hold_funds_derived, total_savings_amount_on_hold,
// enforce_min_required_balance, allow_overdraft and overdraft_limit on
// SavingsAccount (none are present) plus a faithful port of
// minRequiredBalanceDerived. Raised as backlog in the T510 handoff.
func AvailableOf(txns []SavingsAccountTransaction) (MinorUnits, error) {
	held, err := HeldOf(txns)
	if err != nil {
		return 0, err
	}
	return AccountBalanceOf(txns) - held, nil
}

// RunningBalancesOf derives the posted balance as at each transaction in turn,
// returning one value per element of txns in the order given. It is the
// replacement for the deleted SavingsAccountTransaction.RunningBalance field
// and for `running_balance_derived`: a statement view gets its running column
// by asking for it, from the postings, at the moment it renders — never by
// reading back a number some earlier write path decided.
//
// The invariant, stated once so the divergences below follow from it rather
// than being special cases: RunningBalancesOf(txns)[i] is the POSTED BALANCE
// after applying postings 0..i, so a posting that does not move the posted
// balance leaves the running value unchanged, and the last element equals
// AccountBalanceOf(txns) by construction.
//
// ⚠ THIS IS DELIBERATELY NOT `running_balance_derived`. It diverges on three
// classes of row — holds/releases (D-1), void rows (D-2) and ESCHEAT (D-3),
// all documented above and routed as gate entries G-25/G-26/G-27. Worked
// example, the fixture in TestRunningBalancesArePrefixFolds: for
// {DEPOSIT 1,000.00; AMOUNT_HOLD 400.00; WITHDRAWAL 250.00; INTEREST 3.21}
// this function returns {100000, 100000, 75000, 75321} and Fineract's
// running_balance_derived holds {100000, 60000, 35000, 35321}.
//
// The caller is responsible for passing the stream in the oracle's own order
// (PostgresTransactionRepository.FindByAccountID returns it ORDER BY id). A
// prefix fold of an unordered stream is a different number, so this function
// does not sort: silently reordering a caller's postings would hide the defect
// rather than surface it.
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
