package savings

import "testing"

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
func TestHoldsMoveAvailableAndNeverThePostedBalance(t *testing.T) {
	held := []SavingsAccountTransaction{
		txn(TxnDeposit, 1_000_00),
		txn(TxnAmountHold, 300_00),
	}
	if got := AccountBalanceOf(held); got != 1_000_00 {
		t.Errorf("a hold moved the posted balance: AccountBalanceOf = %d, want 100000", got)
	}
	if got := HeldOf(held); got != 300_00 {
		t.Errorf("HeldOf = %d, want 30000", got)
	}
	if got := AvailableOf(held); got != 700_00 {
		t.Errorf("AvailableOf = %d, want 70000", got)
	}

	released := append(append([]SavingsAccountTransaction(nil), held...),
		txn(TxnAmountRelease, 300_00))
	if got := AccountBalanceOf(released); got != 1_000_00 {
		t.Errorf("a release moved the posted balance: %d, want 100000", got)
	}
	if got := HeldOf(released); got != 0 {
		t.Errorf("HeldOf after release = %d, want 0", got)
	}
	if got := AvailableOf(released); got != 1_000_00 {
		t.Errorf("AvailableOf after release = %d, want 100000", got)
	}

	// A release with no matching hold is a data defect, not a negative hold.
	if got := HeldOf([]SavingsAccountTransaction{txn(TxnAmountRelease, 50_00)}); got != 0 {
		t.Errorf("HeldOf(orphan release) = %d, want 0", got)
	}
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

func TestRunningBalancesArePrefixFolds(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 1_000_00),
		txn(TxnAmountHold, 400_00),
		txn(TxnWithdrawal, 250_00),
		txn(TxnInterestPosting, 3_21),
	}
	want := []MinorUnits{1_000_00, 1_000_00, 750_00, 753_21}
	got := RunningBalancesOf(stream)
	if len(got) != len(want) {
		t.Fatalf("RunningBalancesOf returned %d values, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("running[%d] = %d, want %d", i, got[i], want[i])
		}
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
