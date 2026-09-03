package savings

import (
	"errors"
	"testing"
)

// The balance is no longer a field and no longer a column, so these tests are
// what stands in for the deleted write path: they assert the FOLD. Every
// fixture and every intermediate below is an integer count of MNT minor units;
// no float32, float64 or big.Float appears on any money path in this package.

func TestAccountBalanceIsFoldedFromPostings(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 5_000_00),
		txn(TxnWithdrawal, 1_250_00),
		txn(TxnInterestPosting, 12_34),
		txn(TxnWithdrawalFee, 5_00),
	}
	const want MinorUnits = 5_000_00 - 1_250_00 + 12_34 - 5_00
	if got := AccountBalanceOf(stream); got != want {
		t.Errorf("AccountBalanceOf = %d, want %d (minor units)", got, want)
	}
	// The empty stream is the zero balance: not an error, not a special case.
	if got := AccountBalanceOf(nil); got != 0 {
		t.Errorf("AccountBalanceOf(nil) = %d, want 0", got)
	}
}

// A negative Amount must not double-negate a debit: direction comes from the
// entry classification, the amount is a magnitude.
func TestAccountBalanceTreatsAmountAsMagnitude(t *testing.T) {
	positive := AccountBalanceOf([]SavingsAccountTransaction{txn(TxnWithdrawal, 700_00)})
	negative := AccountBalanceOf([]SavingsAccountTransaction{txn(TxnWithdrawal, -700_00)})
	if positive != negative {
		t.Errorf("a signed amount changed the fold: %d vs %d", positive, negative)
	}
	if positive != -700_00 {
		t.Errorf("withdrawal fold = %d, want -70000", positive)
	}
}

// CLAUDE.md: holds "alter `available` only, never posted `balance`". Fineract
// classifies HOLD as a DEBIT and RELEASE as a CREDIT, so this is precisely the
// case a naive fold over Effect() gets wrong.
//
// Pairing is by release_id_of_hold_amount, exactly as the oracle pairs it
// [SavingsAccountTransaction.java:898-899], so the fixtures below carry ids.
func TestHoldsMoveAvailableAndNeverThePostedBalance(t *testing.T) {
	held := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		withID(2, txn(TxnAmountHold, 300_00)),
	}
	if got := AccountBalanceOf(held); got != 1_000_00 {
		t.Errorf("a hold moved the posted balance: AccountBalanceOf = %d, want 100000", got)
	}
	assertHeld(t, held, 300_00)
	assertAvailable(t, held, 700_00)

	// The release row (id 3) and the hold that claims it, as Fineract writes
	// them: holdTransaction.updateReleaseId(releaseTransaction.getId()).
	released := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		releasedHold(2, 300_00, 3),
		withID(3, txn(TxnAmountRelease, 300_00)),
	}
	if got := AccountBalanceOf(released); got != 1_000_00 {
		t.Errorf("a release moved the posted balance: %d, want 100000", got)
	}
	assertHeld(t, released, 0)
	assertAvailable(t, released, 1_000_00)
}

// A release row that no hold claims is a DATA DEFECT and must be reported, not
// absorbed into a plausible number. The previous implementation summed
// magnitudes and floored the difference at zero, so a release duplicated by a
// retry without an Idempotency-Key silently reported the whole balance as
// drawable.
func TestAnUnclaimedReleaseIsRefusedRatherThanFlooredToZero(t *testing.T) {
	orphan := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		withID(2, txn(TxnAmountRelease, 50_00)),
	}
	var target *ErrOrphanRelease
	_, err := HeldOf(orphan)
	if !errors.As(err, &target) {
		t.Fatalf("HeldOf(unclaimed release) error = %v, want *ErrOrphanRelease", err)
	}
	if target.TransactionID != 2 || target.Amount != 50_00 {
		t.Errorf("ErrOrphanRelease = %+v, want {TransactionID:2 Amount:5000}", *target)
	}
	if _, err := AvailableOf(orphan); !errors.As(err, &target) {
		t.Errorf("AvailableOf must propagate the refusal, got %v", err)
	}

	// The duplicated-release shape the refusal exists for: hold 300.00 claims
	// release id 3; a retry appended release id 4 that nothing claims.
	duplicated := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		releasedHold(2, 300_00, 3),
		withID(3, txn(TxnAmountRelease, 300_00)),
		withID(4, txn(TxnAmountRelease, 300_00)),
	}
	if _, err := HeldOf(duplicated); !errors.As(err, &target) {
		t.Errorf("HeldOf(duplicated release) error = %v, want *ErrOrphanRelease", err)
	}

	// A release claimed by a hold that was later reversed is NOT an orphan:
	// the pairing is a fact about the two rows and survives the reversal.
	voidedPair := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		func() SavingsAccountTransaction {
			h := releasedHold(2, 300_00, 3)
			h.Reversed = true
			return h
		}(),
		withID(3, txn(TxnAmountRelease, 300_00)),
	}
	assertHeld(t, voidedPair, 0)
}

// A type carrying no entry classification (ACCRUAL, WAIVE_CHARGES, the transfer
// sub-states, WRITTEN_OFF) moves neither side of the fold.
func TestUnclassifiedTypesDoNotMoveTheBalance(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 400_00),
		txn(TxnAccrual, 999_99),
	}
	if got := AccountBalanceOf(stream); got != 400_00 {
		t.Errorf("an unclassified posting moved the balance: %d, want 40000", got)
	}
}

// RunningBalancesOf is NOT `running_balance_derived`, and this test pins the
// divergence AS a divergence. It previously asserted only the left-hand column,
// which made a deliberate departure from the reference oracle look like an
// ordinary passing test — so the first savings golden vector to fail on a
// hold-bearing account would have read as a port bug.
//
// Divergence D-1 (summary.go, gate G-25): Fineract's recalculateDailyBalances
// moves running_balance_derived on AMOUNT_HOLD / AMOUNT_RELEASE
// [SavingsAccount.java:902,912]; we do not, because CLAUDE.md forbids a hold
// moving a posted balance, and Fineract's own account_balance_derived agrees
// with us.
func TestRunningBalancesArePrefixFoldsAndDivergeFromTheOracleOnHolds(t *testing.T) {
	stream := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		withID(2, txn(TxnAmountHold, 400_00)),
		withID(3, txn(TxnWithdrawal, 250_00)),
		withID(4, txn(TxnInterestPosting, 3_21)),
	}
	want := []MinorUnits{1_000_00, 1_000_00, 750_00, 753_21}
	// What Fineract would have stored in running_balance_derived for the same
	// four rows, re-derived by hand from SavingsAccount.java:902,912: the hold
	// debits 400.00 and every later value carries that debit.
	oracleRunningBalanceDerived := []MinorUnits{1_000_00, 600_00, 350_00, 353_21}

	got := RunningBalancesOf(stream)
	if len(got) != len(want) {
		t.Fatalf("RunningBalancesOf returned %d values, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("running[%d] = %d, want %d", i, got[i], want[i])
		}
	}
	// The divergence is asserted, not assumed: if a later change makes this
	// function reproduce running_balance_derived, that is a decision to reverse
	// D-1 and it must be taken deliberately, not fall out of an edit.
	diverged := false
	for i := range want {
		if got[i] != oracleRunningBalanceDerived[i] {
			diverged = true
		}
	}
	if !diverged {
		t.Error("RunningBalancesOf now matches running_balance_derived on a " +
			"hold-bearing stream; divergence D-1 (gate G-25) is stale — either " +
			"the fold started moving on holds, which CLAUDE.md forbids, or the " +
			"gate entry must be retired")
	}

	// The last prefix fold IS the account balance, by construction.
	if got[len(got)-1] != AccountBalanceOf(stream) {
		t.Errorf("last running value %d != AccountBalanceOf %d",
			got[len(got)-1], AccountBalanceOf(stream))
	}
	if len(RunningBalancesOf(nil)) != 0 {
		t.Error("RunningBalancesOf(nil) must be empty")
	}
}

// Divergence D-3 (summary.go, gate G-27): ESCHEAT is DEBIT in the oracle's own
// enum and debits running_balance_derived, but appears in none of the nine
// terms of updateSummary, so Fineract's stored account_balance_derived does NOT
// move on it. We debit. This pins the choice so it cannot be flipped silently.
func TestEscheatDebitsThePostedBalance(t *testing.T) {
	stream := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 500_000_00)),
		withID(2, txn(TxnEscheat, 500_000_00)),
	}
	if got := AccountBalanceOf(stream); got != 0 {
		t.Errorf("AccountBalanceOf after escheat = %d, want 0. Fineract's stored "+
			"account_balance_derived would still read 50000000; that divergence "+
			"is D-3 / gate G-27 and is expected", got)
	}
}

// The summary is a category-total projection and must carry no balance field.
// This is a compile-time assertion in test form: if a later change reintroduces
// one, the struct literal below stops being exhaustive-by-name and the reviewer
// has a named place to look. It also pins the decoder's arity at twelve.
func TestSummaryCarriesNoBalanceField(t *testing.T) {
	s, err := decodeSummary("1.00", "2.00", "3.00", "4.00", "5.00", "6.00",
		"7.00", "8.00", "9.00", "10.00", "11.00", "12.00")
	if err != nil {
		t.Fatalf("decodeSummary(12 fields): %v", err)
	}
	if s.TotalDeposits != 100 || s.TotalWithholdTax != 1200 {
		t.Errorf("decodeSummary mis-mapped its columns: %+v", s)
	}
	if _, err := decodeSummary("1.00"); err == nil {
		t.Error("decodeSummary(1 field) = nil error; want an arity refusal")
	}
	// Thirteen fields must be refused too: a thirteenth would be the balance
	// column creeping back into the SELECT.
	if _, err := decodeSummary("1.00", "2.00", "3.00", "4.00", "5.00", "6.00",
		"7.00", "8.00", "9.00", "10.00", "11.00", "12.00", "13.00"); err == nil {
		t.Error("decodeSummary(13 fields) = nil error; want an arity refusal")
	}
}

// txn builds a transaction the way the repository decode does: the entry
// classification is derived from the type, never supplied by the caller.
func txn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	return SavingsAccountTransaction{Type: k, Entry: k.EntryType(), Amount: amount}
}

// withID stamps m_savings_account_transaction.id on a fixture. Hold pairing is
// by id, so a fixture that exercises holds must carry one.
func withID(id int64, t SavingsAccountTransaction) SavingsAccountTransaction {
	t.ID = id
	return t
}

// releasedHold is an AMOUNT_HOLD row that has been released: it carries the id
// of its AMOUNT_RELEASE row in release_id_of_hold_amount, which is where
// Fineract writes it [SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953].
func releasedHold(id int64, amount MinorUnits, releaseID int64) SavingsAccountTransaction {
	h := withID(id, txn(TxnAmountHold, amount))
	h.ReleaseIDOfHoldAmount = releaseID
	return h
}

func assertHeld(t *testing.T, txns []SavingsAccountTransaction, want MinorUnits) {
	t.Helper()
	got, err := HeldOf(txns)
	if err != nil {
		t.Fatalf("HeldOf: %v", err)
	}
	if got != want {
		t.Errorf("HeldOf = %d, want %d", got, want)
	}
}

func assertAvailable(t *testing.T, txns []SavingsAccountTransaction, want MinorUnits) {
	t.Helper()
	got, err := AvailableOf(txns)
	if err != nil {
		t.Fatalf("AvailableOf: %v", err)
	}
	if got != want {
		t.Errorf("AvailableOf = %d, want %d", got, want)
	}
}

// reversedTxn is the ORIGINAL row after undoTransaction: is_reversed = true.
func reversedTxn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	t := txn(k, amount)
	t.Reversed = true
	return t
}

// reversalTxn is the APPENDED correction row: is_reversal = true, same type,
// same amount [VERIFIED: SavingsAccountTransaction.reversal(), :352-358].
func reversalTxn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	t := txn(k, amount)
	t.Reversal = true
	return t
}

// RED TEST FOR T510, WRITTEN BEFORE THE FIX AND RUN RED.
//
// Fineract's undoTransaction sets reversed = true on the original row and,
// with postReversals, APPENDS SavingsAccountTransaction.reversal(original) —
// copyTransaction with reversed = false, reversalTransaction = true
// [VERIFIED: SavingsAccountTransaction.java:352-358]. The correction row is a
// SAME-TYPE, SAME-AMOUNT copy, so a fold that consults only the transaction
// TYPE doubles the error instead of cancelling it: a 100,000₮ deposit that was
// undone reads back as +200,000₮.
//
// CLAUDE.md: "Corrections are reversing entries." This is the one mechanism the
// non-negotiables name as the legal way to correct a posting, so a fold that is
// blind to it is wrong on the case that matters most.
func TestReversedAndReversalRowsAreVoidInEveryDerivation(t *testing.T) {
	// The exact two-row shape Fineract leaves in
	// m_savings_account_transaction after a mis-keyed deposit is undone.
	stream := []SavingsAccountTransaction{
		reversedTxn(TxnDeposit, 100_000_00),
		reversalTxn(TxnDeposit, 100_000_00),
	}
	if got := AccountBalanceOf(stream); got != 0 {
		t.Errorf("AccountBalanceOf(undone deposit) = %d, want 0 "+
			"(Fineract calculateTotalDeposits excludes both rows)", got)
	}
	running := RunningBalancesOf(stream)
	for i, got := range running {
		if got != 0 {
			t.Errorf("RunningBalancesOf(undone deposit)[%d] = %d, want 0", i, got)
		}
	}
	held, err := HeldOf(stream)
	if err != nil {
		t.Fatalf("HeldOf(undone deposit): %v", err)
	}
	if held != 0 {
		t.Errorf("HeldOf(undone deposit) = %d, want 0", held)
	}
	available, err := AvailableOf(stream)
	if err != nil {
		t.Fatalf("AvailableOf(undone deposit): %v", err)
	}
	if available != 0 {
		t.Errorf("AvailableOf(undone deposit) = %d, want 0", available)
	}

	// The surviving half of the account must be untouched by the correction:
	// a good deposit either side of the undone one still folds.
	mixed := []SavingsAccountTransaction{
		txn(TxnDeposit, 50_000_00),
		reversedTxn(TxnDeposit, 100_000_00),
		reversalTxn(TxnDeposit, 100_000_00),
		txn(TxnWithdrawal, 20_000_00),
	}
	if got := AccountBalanceOf(mixed); got != 30_000_00 {
		t.Errorf("AccountBalanceOf(mixed) = %d, want 3000000", got)
	}
	wantRunning := []MinorUnits{50_000_00, 50_000_00, 50_000_00, 30_000_00}
	gotRunning := RunningBalancesOf(mixed)
	for i := range wantRunning {
		if gotRunning[i] != wantRunning[i] {
			t.Errorf("running[%d] = %d, want %d", i, gotRunning[i], wantRunning[i])
		}
	}
}

// A reversed HOLD holds nothing. Fineract's own running-balance derivation
// agrees: recalculateDailyBalances tests isReversed()/isReversalTransaction()
// FIRST and calls zeroBalanceFields(), so the hold branch below it is never
// reached for a void row [VERIFIED: SavingsAccount.java:897-912].
func TestAReversedHoldHoldsNothing(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 1_000_00),
		reversedTxn(TxnAmountHold, 300_00),
	}
	held, err := HeldOf(stream)
	if err != nil {
		t.Fatalf("HeldOf: %v", err)
	}
	if held != 0 {
		t.Errorf("HeldOf(reversed hold) = %d, want 0", held)
	}
	available, err := AvailableOf(stream)
	if err != nil {
		t.Fatalf("AvailableOf: %v", err)
	}
	if available != 1_000_00 {
		t.Errorf("AvailableOf(reversed hold) = %d, want 100000", available)
	}
	if got := AccountBalanceOf(stream); got != 1_000_00 {
		t.Errorf("a reversed hold moved the posted balance: %d", got)
	}
}
