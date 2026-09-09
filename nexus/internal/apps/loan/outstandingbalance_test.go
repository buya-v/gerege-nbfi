package loan

import (
	"errors"
	"testing"
)

// Transcription checks: the SEED-L01 post-waiver and SEED-L03 post-repayment
// transaction streams of the committed captures, in integer minor units.
func TestDeriveOutstandingBalancesWaiverDoesNotMovePrincipal(t *testing.T) {
	// loan-1-transactions-after-raw.json: id 1 disbursement 100000.00,
	// id 2 accrual 6618.53 (row serializes NO outstandingLoanBalance), id 13
	// Waive interest 1000.00, outstandingLoanBalance 100000.0 — unchanged from
	// the disbursement, because the waiver recognises no principal portion.
	postings := []OutstandingBalancePosting{
		{Type: TransactionDisbursement, Amount: 10000000},
		{Type: TransactionAccrual, Amount: 661853},
		{Type: TransactionWaiveInterest, Amount: 100000},
	}
	rows, err := DeriveOutstandingBalances(postings)
	if err != nil {
		t.Fatalf("DeriveOutstandingBalances() error = %v", err)
	}
	want := []OutstandingBalanceRow{
		{Serialized: true, BalanceMinor: 10000000},
		{Serialized: false},
		{Serialized: true, BalanceMinor: 10000000},
	}
	if len(rows) != len(want) {
		t.Fatalf("DeriveOutstandingBalances() len = %d, want %d", len(rows), len(want))
	}
	for i := range want {
		if rows[i] != want[i] {
			t.Errorf("row %d = %+v, want %+v", i, rows[i], want[i])
		}
	}
}

func TestDeriveOutstandingBalancesRepaymentMovesPrincipalOnly(t *testing.T) {
	// loan-3-transactions-after-raw.json: id 5 disbursement 100000.00,
	// id 6 accrual 6618.53 (no balance cell), id 12 repayment 8884.88 with
	// interestPortion 1000.00 and principalPortion 7884.88; the read-back row's
	// outstandingLoanBalance is 92115.12 = 100000.00 - 7884.88. A derivation
	// that folded the interest portion (or the full payment) into the balance
	// would read 91115.12.
	postings := []OutstandingBalancePosting{
		{Type: TransactionDisbursement, Amount: 10000000},
		{Type: TransactionAccrual, Amount: 661853},
		{Type: TransactionRepayment, Amount: 888488, PrincipalPortion: 788488},
	}
	rows, err := DeriveOutstandingBalances(postings)
	if err != nil {
		t.Fatalf("DeriveOutstandingBalances() error = %v", err)
	}
	want := []OutstandingBalanceRow{
		{Serialized: true, BalanceMinor: 10000000},
		{Serialized: false},
		{Serialized: true, BalanceMinor: 9211512},
	}
	for i := range want {
		if rows[i] != want[i] {
			t.Errorf("row %d = %+v, want %+v", i, rows[i], want[i])
		}
	}
}

func TestDeriveOutstandingBalancesDisbursementOnly(t *testing.T) {
	rows, err := DeriveOutstandingBalances([]OutstandingBalancePosting{
		{Type: TransactionDisbursement, Amount: 10000000},
	})
	if err != nil {
		t.Fatalf("DeriveOutstandingBalances() error = %v", err)
	}
	want := OutstandingBalanceRow{Serialized: true, BalanceMinor: 10000000}
	if rows[0] != want {
		t.Errorf("row = %+v, want %+v", rows[0], want)
	}
}

func TestDeriveOutstandingBalancesRefusesUntranscribedType(t *testing.T) {
	// No committed capture observes a write-off posting on the balance path;
	// the derivation must refuse rather than invent the oracle's rule for it.
	_, err := DeriveOutstandingBalances([]OutstandingBalancePosting{
		{Type: TransactionWriteoff, Amount: 100000},
	})
	if !errors.Is(err, ErrNotTranscribed) {
		t.Errorf("DeriveOutstandingBalances() error = %v, want ErrNotTranscribed", err)
	}
}
