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

// WHERE THESE DERIVATIONS STAND RELATIVE TO THE REFERENCE ORACLE, STATED ONCE
//
// CLAUDE.md makes Fineract the oracle, so any place where these derivations do
// NOT reproduce a Fineract number has to be written down, or the first failing
// savings golden vector will be read as a port bug and "fixed" back into a
// defect. T510 recorded THREE such places and routed them as gate entries
// G-25, G-26 and G-27. T513's independent review found the load-bearing premise
// under all three — "Fineract's account_balance_derived and its
// running_balance_derived are computed by code that disagrees" — to be FALSE,
// and T515 confirmed it against the live instance rather than by argument.
// G-25 and G-27 are DELETED. What is left is written below.
//
// # THE PREMISE WAS FALSE BECAUSE THE CLASSIFICATION WAS HALF-PORTED
//
// Fineract's credit/debit test is three calls deep and this port stopped at
// two, binding itself to the RAW entryType field of the enum. The third call is
// SavingsAccountTransactionType.isCredit()/isDebit(), which subtract exactly the
// balance-neutral types, with the reason in the oracle's own inline comments
// [VERIFIED: SavingsAccountTransactionType.java:180-188]:
//
//	isCredit() = isCreditEntryType() && !isAmountRelease()
//	           // AMOUNT_RELEASE is not credit, because the account balance is not changed
//	isDebit()  = isDebitEntryType() && !isAmountOnHold() && !isEscheat()
//	           // AMOUNT_HOLD, ESCHEAT are not debit, because the account balance is not changed
//
// So the oracle had already implemented "a hold does not move the posted
// balance" — the very rule G-25 cited CLAUDE.md to justify diverging from it
// over. The port re-derived that rule by hand as an exclusion list at each fold
// site, got it right for AMOUNT_HOLD and AMOUNT_RELEASE, and omitted ESCHEAT,
// which the oracle excludes by name on the same line as AMOUNT_HOLD. T515
// ports the third call and DELETES the exclusion lists; see
// transactiontype.go IsCredit/IsDebit.
//
// # TWO CAPTURES, NOT TWO ARGUMENTS
//
// [VERIFIED: live oracle capture, Fineract @ 426a23544, tenant `default`,
// PostgreSQL `gerege-oracle-db`/`fineract_default`, 2026-09-03. Both accounts
// are on savings product 2 — MNT, currency_digits 2, nominal_annual_interest_rate
// 0.000000, so no interest posting perturbs the rows. Raw
// `m_savings_account_transaction` / `m_savings_account` output; amounts as
// stored, at 6 decimal places.]
//
// ⚠ THE INSTANCE IS NOT AT THE RATIFIED TENANT SETTINGS: one tenant, `default`,
// on **Asia/Kolkata**, with `c_configuration.rounding-mode = 6` — **HALF_EVEN**,
// where CLAUDE.md ratifies HALF_UP (ordinal 4) at precision 19 on
// Asia/Ulaanbaatar; no `gerege` tenant and no `fineract_gerege` database exist
// on it [VERIFIED: psql against `gerege-oracle-db`, this fire]. These captures
// are still sound for what they are used for here, because they engage neither
// setting: the amounts are exact two-decimal quantities added and subtracted at
// 0% interest, so no midpoint arises for a rounding mode to decide, and nothing
// below turns on a date. They establish WHICH TRANSACTION TYPES MOVE A BALANCE.
// They are **[UNVERIFIED at (19, HALF_UP) / Asia-Ulaanbaatar]**, are not in
// `.softhouse/vectors/`, and must be re-captured from a correctly configured
// tenant before any of them is treated as a parity vector.
//
//	CAPTURE-B — savings account 3, a hold and a withdrawal
//	  id 14  type  1 DEPOSIT        1000.000000   running_balance_derived 1000.000000
//	  id 15  type 20 AMOUNT_HOLD     400.000000   running_balance_derived  600.000000
//	  id 16  type  2 WITHDRAWAL      250.000000   running_balance_derived  350.000000
//	  account_balance_derived 750.000000   total_savings_amount_on_hold 400.000000
//
//	CAPTURE-A — savings account 2, escheated for its whole balance by the stock
//	  `Update Savings Dormant Accounts` job (jobId 21), the only caller of
//	  SavingsAccount.escheat [VERIFIED: UpdateSavingsDormantAccountsTasklet.java:63]
//	  id 12  type  1 DEPOSIT      500000.000000   running_balance_derived 500000.000000
//	  id 13  type 19 ESCHEAT      500000.000000   running_balance_derived 500000.000000
//	  account_balance_derived 500000.000000   status_enum 600 (CLOSED)  sub_status_enum 300 (ESCHEAT)
//
// Read together they settle both deleted gates:
//
//	G-27, DELETED. An ESCHEAT for the whole balance moves NEITHER stored column.
//	It matches neither branch of recalculateDailyBalances — isDebit() excludes it
//	by name, and the loop carries an explicit `|| transaction.isAmountOnHold()`
//	term to re-admit holds but NO `|| isEscheat()` term
//	[VERIFIED: SavingsAccount.java:902,912] — and it appears in none of the nine
//	terms of updateSummary [VERIFIED: SavingsAccountSummary.java:96-112], in no
//	calculator of SavingsAccountTransactionSummaryWrapper, and in no case of
//	updateSummaryWithPivotConfig's switch. Both derivations agree; there was
//	never a choice to make. T510 folded ESCHEAT as a debit and pinned
//	AccountBalanceOf = 0 where the oracle stores 500000.000000 — a 500,000₮
//	error on the operation that closes the account. AccountBalanceOf now
//	returns 50000000 minor units on CAPTURE-A.
//
//	G-25, DELETED. `account_balance_derived` and `running_balance_derived` are
//	not two answers to one question; they are two DIFFERENT QUANTITIES, and
//	CAPTURE-B measures the gap as exactly the hold: 750.00 posted against a
//	350.00 hold-net chain, differing by the 400.00 in
//	total_savings_amount_on_hold. `account_balance_derived` is the POSTED
//	balance and holds never touch it; `running_balance_derived` is a hold-net,
//	available-shaped, per-row chain. CLAUDE.md's "holds alter `available` only,
//	never posted `balance`" is therefore SATISFIED by AccountBalanceOf, which
//	now equals `account_balance_derived` on both captures — and G-25 had cited
//	that non-negotiable to refuse the one Fineract column that implements it.
//	Reproducing the hold-net chain breaches nothing, so it is no longer refused:
//	HoldNetRunningBalancesOf below is the faithful port, graded against
//	CAPTURE-B.
//
// # WHAT IS LEFT — ONE MINOR REPRESENTATION GAP (G-26)
//
//	R-1  A VOID ROW HAS NO RUNNING BALANCE, AND []MinorUnits HAS NO NULL.
//	     On a reversed or reversal row Fineract calls zeroBalanceFields(), which
//	     sets runningBalance to NULL [VERIFIED: SavingsAccount.java:897-898;
//	     SavingsAccountTransaction.java:586-591]. Fineract is UNAMBIGUOUS here —
//	     no second derivation disagrees — so this was never a divergence in the
//	     answer, only in how the answer can be spelled in Go.
//
//	     T513 identified the remedy and T515 applies it: HoldNetRunningBalancesOf
//	     returns []RunningBalance, whose Valid field carries the oracle's NULL
//	     exactly. RunningBalancesOf keeps returning []MinorUnits and states the
//	     unchanged prefix on a void row — which is correct for what IT computes,
//	     the posted-balance prefix, because a void row does not move the posted
//	     balance. It is not modelling `running_balance_derived` and no longer
//	     claims to, so the gap does not arise there either.
//
//	     G-26 is retained in .softhouse/gates.md as a MINOR note recording that
//	     the two functions represent the void row differently and why. It
//	     authorises no divergence.

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
// HOLDS AND ESCHEATS MOVE NOTHING HERE, AND THERE IS NO EXCLUSION LIST SAYING
// SO. CLAUDE.md: "Holds are postings and alter `available` only, never posted
// `balance`." Until T515 this function enforced that with a hand-written
// `if t.Type.IsAmountHold() || t.Type.IsAmountRelease() { continue }`, because
// the classification underneath it was the enum's RAW entryType field, which
// does mark HOLD a debit and RELEASE a credit. That list was a re-derivation of
// a rule the oracle already implements — and it omitted ESCHEAT, which the
// oracle excludes on the same line as AMOUNT_HOLD, so an escheated account read
// zero here and its full balance in the oracle.
//
// The list is gone. AMOUNT_HOLD, AMOUNT_RELEASE and ESCHEAT are excluded by
// SavingsAccountTransactionType.IsCredit/IsDebit, which is where Fineract
// excludes them, so this fold is now a plain sum over Effect() with no
// type-specific knowledge in it at all. A hold's effect appears only in
// AvailableOf, via HeldOf.
//
// THIS FUNCTION EQUALS `account_balance_derived`, MEASURED. On CAPTURE-B it
// returns 75000 minor units against the oracle's stored 750.000000; on
// CAPTURE-A, 50000000 against 500000.000000. Equal on both, and that is a
// parity result rather than a design claim — see the capture block above.
//
// Amount is treated as a magnitude; the direction comes from the classification,
// so a negative amount can never double-negate a debit. Types that carry no
// entry classification at all (INVALID, WAIVE_CHARGES, ACCRUAL, the transfer
// sub-states, WRITTEN_OFF — EntryType returns the zero value) move neither side.
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
//
// ⚠ IT DOES NOT FAIL CLOSED ON EVERYTHING, AND HERE IS THE ONE INPUT WHERE IT
// FAILS OPEN (T513 MINOR-3, measured on the T510 tree: `HeldOf(hold paired to a
// REVERSED release) = 0, err = <nil>`). A hold whose release row was later
// REVERSED still reads as discharged, because the discharge test is the FK
// alone — IsHoldNotReleased is `IsAmountHold() && !IsVoid() && ReleaseIDOfHoldAmount == 0`
// and the void flag it consults is the HOLD's, not the RELEASE's. The funds
// read as drawable. That is a fail-OPEN on money and the doc above should not
// be read as covering it.
//
// It is nonetheless LEFT AS IS, because it is what the oracle does and CLAUDE.md
// makes the oracle authoritative. Fineract's outstanding-hold test is
// `isAmountOnHold() && getReleaseIdOfHoldAmountTransaction() == null`
// [VERIFIED: SavingsAccountTransaction.java:898-899], which likewise never looks
// at the release row's reversal flags; and the FK is only ever assigned a
// release transaction id, never cleared — the three assignment sites are
// SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953 and
// InteropServiceImpl.java:451,494, and `updateReleaseId`
// [SavingsAccountTransaction.java:466-468] has no null-ing caller anywhere in
// the pinned tree [VERIFIED: grep for `updateReleaseId` across
// /Users/buv/fineract, 4 non-test sites, all passing a transaction id].
// Diverging here would be a unilateral safety improvement over the oracle, which
// is a decision for a hold/release service task with a vector behind it, not for
// a derivation. Pinned by TestAReversedReleaseStillDischargesItsHold so the
// behaviour cannot change by accident.
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
// The split between the two hold columns is the oracle's own, stated in its
// field comments [VERIFIED: SavingsAccountSummaryData.java:52-64 —
// on_hold_funds_derived is "guarantor" holds; total_savings_amount_on_hold is
// "user-initiated holds explicitly placed on the account, including lien
// holds … through hold/release transactions"; availableBalance is
// "accountBalance - onHoldFunds (guarantor holds) - savingsAmountOnHold
// (user/lien holds)"]. CAPTURE-B agrees: after a 400.00 holdAmount call,
// total_savings_amount_on_hold moved to 400.000000 while on_hold_funds_derived
// stayed NULL. So HeldOf is the transaction-stream derivation of the SECOND
// column, and the first is genuinely unported rather than merely mislabelled.
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

// RunningBalancesOf derives the POSTED balance as at each transaction in turn,
// returning one value per element of txns in the order given. It is the
// replacement for the deleted SavingsAccountTransaction.RunningBalance field: a
// statement view gets its running column by asking for it, from the postings, at
// the moment it renders — never by reading back a number some earlier write path
// decided.
//
// ⚠ IT IS NOT A PORT OF `running_balance_derived`, AND NO LONGER CLAIMS TO BE.
// T510's doc called it "the replacement … for `running_balance_derived`" and
// then listed three divergences from it; T513 showed that the two are different
// QUANTITIES rather than disagreeing answers, so the right repair was to stop
// conflating them, not to ratify a divergence. This function is the
// posted-balance prefix; HoldNetRunningBalancesOf below is the faithful port of
// the column, and it agrees with the oracle on CAPTURE-B.
//
// The invariant, stated once: RunningBalancesOf(txns)[i] is the POSTED BALANCE
// after applying postings 0..i. So a posting that does not move the posted
// balance — a hold, a release, an escheat, a void row, an unclassified type —
// leaves the running value unchanged, and the last element equals
// AccountBalanceOf(txns) by construction. That is now a property of the
// classification rather than of a skip list: the loop body is a plain fold over
// Effect(), the same one AccountBalanceOf runs, emitting the prefix each step.
//
// Worked example, CAPTURE-B's three rows: this function returns
// {100000, 100000, 75000} minor units — the posted balance, unmoved by the hold
// — while the oracle's `running_balance_derived` holds {100000, 60000, 35000},
// which HoldNetRunningBalancesOf reproduces exactly. Neither is wrong; they
// answer different questions, and the 40000 between them is the hold.
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

// RunningBalance is one element of the oracle's `running_balance_derived`
// column: a minor-unit value, or the absence of one.
//
// Valid = false is Fineract's NULL, which it writes on a void row via
// zeroBalanceFields() [VERIFIED: SavingsAccountTransaction.java:586-591, called
// from SavingsAccount.java:897-898]. It is a two-field struct rather than a
// *MinorUnits because a nil pointer on a money path is a dereference away from a
// panic and a shared backing array away from aliasing, while a zero-valued
// RunningBalance is unambiguously "no balance stated" and cannot be mistaken for
// a zero balance by a caller that forgot to check.
//
// This closes the representation gap T510 recorded as G-26 and T513 downgraded
// to a MINOR: []MinorUnits has no NULL, so a faithful port needed a type that
// does.
type RunningBalance struct {
	// Value is the running balance in integer minor units. It is meaningful
	// only when Valid is true.
	Value MinorUnits
	// Valid reports whether the oracle states a running balance on this row.
	// False is `running_balance_derived IS NULL`.
	Valid bool
}

// HoldNetRunningBalancesOf is the faithful port of Fineract's
// `running_balance_derived`: the hold-net, available-shaped per-row chain that
// recalculateDailyBalances writes [VERIFIED: SavingsAccount.java:895-919, the
// balance arm; the overdraft and interest arms of that loop are not ported here
// and are named below]. It returns one element per element of txns, in the order
// given, and opening is the oracle's `openingAccountBalance` argument — zero for
// a full recompute, as in SavingsAccount.escheat [:3396], and the pivot balance
// for a backdated run.
//
// It exists because T513 rejected the claim that reproducing this column would
// breach CLAUDE.md's "holds alter `available` only, never posted `balance`". It
// would not: this column is not the posted balance. The posted balance is
// AccountBalanceOf, which excludes holds and equals `account_balance_derived`.
// Refusing to port an available-shaped column in the name of a rule about
// available was the inversion at the centre of the deleted gate G-25.
//
// THE THREE BRANCHES, IN THE ORACLE'S OWN ORDER:
//
//	VOID ROW  -> zeroBalanceFields(): NO running balance is stated, and the
//	             chain does not advance. RunningBalance{Valid:false}.
//	CREDIT OR RELEASE -> `if (transaction.isCredit() || transaction.isAmountRelease())`
//	             [SavingsAccount.java:902]. isCredit() excludes AMOUNT_RELEASE at
//	             the type level and the `||` term re-admits it, which is how a
//	             release ADDS BACK here while moving no posted balance.
//	DEBIT OR HOLD -> `else if (transaction.isDebit() || transaction.isAmountOnHold())`
//	             [:912]. Same shape: isDebit() excludes AMOUNT_HOLD and the `||`
//	             term re-admits it.
//
// ESCHEAT MATCHES NO BRANCH, AND THAT IS THE ASYMMETRY THAT SETTLED G-27. The
// loop re-admits holds and releases by name and never re-admits ESCHEAT, so an
// escheat leaves the chain where it was and the row carries the unchanged
// prefix. CAPTURE-A observed exactly that: 500000.000000 on the DEPOSIT row and
// 500000.000000 again on the ESCHEAT row.
//
// GRADED, NOT ASSERTED. On CAPTURE-B this returns {100000, 60000, 35000} minor
// units against the oracle's stored {1000.000000, 600.000000, 350.000000}, and
// on CAPTURE-A {50000000, 50000000} against {500000.000000, 500000.000000}.
// Both are pinned by TestHoldNetRunningBalancesMatchTheCapturedOracleRows.
//
// NOT PORTED FROM THAT LOOP, DELIBERATELY: `overdraft_amount_derived`, the
// interest-recalculation copy path, and the `balance_end_date_derived` /
// `balance_number_of_days_derived` pair. They need the account's overdraft
// configuration and a business-date clock, neither of which exists in this
// package, and they do not affect the balance chain this function returns.
// Raised as backlog in the T515 handoff rather than guessed at.
func HoldNetRunningBalancesOf(opening MinorUnits, txns []SavingsAccountTransaction) []RunningBalance {
	out := make([]RunningBalance, 0, len(txns))
	running := opening
	for _, t := range txns {
		if t.IsVoid() {
			out = append(out, RunningBalance{})
			continue
		}
		amount := t.Amount
		if amount < 0 {
			amount = -amount
		}
		switch {
		case t.IsCredit() || t.Type.IsAmountRelease():
			running += amount
		case t.IsDebit() || t.Type.IsAmountHold():
			running -= amount
		}
		out = append(out, RunningBalance{Value: running, Valid: true})
	}
	return out
}
