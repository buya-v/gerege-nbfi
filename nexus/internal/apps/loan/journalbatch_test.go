package loan

import "testing"

// loan10Batch is the entityId 10 journal-entry batch observed in
// .softhouse/capture/gl-accounting-surface/out/journalentries-all-raw.json:
// a disbursement pair (L17, 100000.00 each way) plus a fee pair (L18, 100.00
// each way).
func loan10Batch() []JournalEntryLeg {
	return []JournalEntryLeg{
		{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", Side: JournalEntryDebit, Amount: 10000000},
		{TransactionID: "L17", Account: "OHLGR-Fund-Source", Side: JournalEntryCredit, Amount: 10000000},
		{TransactionID: "L18", Account: "OHLGR-Income-From-Fees", Side: JournalEntryCredit, Amount: 10000},
		{TransactionID: "L18", Account: "OHLGR-Fund-Source", Side: JournalEntryDebit, Amount: 10000},
	}
}

func TestSumJournalEntryBatchMultiPairBalances(t *testing.T) {
	totals, err := SumJournalEntryBatch(loan10Batch())
	if err != nil {
		t.Fatalf("SumJournalEntryBatch: %v", err)
	}
	if totals.Debits != 10010000 || totals.Credits != 10010000 {
		t.Fatalf("totals = %d/%d, want 10010000/10010000", totals.Debits, totals.Credits)
	}
	if !totals.Balances() {
		t.Fatal("multi-pair batch should balance")
	}
}

// TestSumJournalEntryBatchDoesNotNetAccount pins the defect the batch must not
// have: netting the two OHLGR-Fund-Source legs before summing keeps the
// difference zero while moving BOTH totals, so the equality alone cannot see
// it and the per-side sums must be compared.
func TestSumJournalEntryBatchDoesNotNetAccount(t *testing.T) {
	netted := []JournalEntryLeg{
		{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", Side: JournalEntryDebit, Amount: 10000000},
		{TransactionID: "L17+L18", Account: "OHLGR-Fund-Source", Side: JournalEntryCredit, Amount: 9990000},
		{TransactionID: "L18", Account: "OHLGR-Income-From-Fees", Side: JournalEntryCredit, Amount: 10000},
	}
	totals, err := SumJournalEntryBatch(netted)
	if err != nil {
		t.Fatalf("SumJournalEntryBatch: %v", err)
	}
	if !totals.Balances() {
		t.Fatal("netted batch still balances; the defect is invisible to equality alone")
	}
	if totals.Debits == 10010000 || totals.Credits == 10010000 {
		t.Fatal("netted totals should differ from the observed per-side sums")
	}
}

func TestSumJournalEntryBatchRefusesUnknownSide(t *testing.T) {
	_, err := SumJournalEntryBatch([]JournalEntryLeg{
		{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", Amount: 10000000},
	})
	if err == nil {
		t.Fatal("a leg with no established side must be refused, not summed as a debit")
	}
}

func TestSumJournalEntryBatchSinglePairBalances(t *testing.T) {
	// The loan-12 shape: one pair balances, which is why it cannot grade the
	// multi-pair property.
	totals, err := SumJournalEntryBatch([]JournalEntryLeg{
		{TransactionID: "L20", Account: "OHLGR-Loan-Portfolio", Side: JournalEntryDebit, Amount: 10000000},
		{TransactionID: "L20", Account: "OHLGR-Fund-Source", Side: JournalEntryCredit, Amount: 10000000},
	})
	if err != nil {
		t.Fatalf("SumJournalEntryBatch: %v", err)
	}
	if totals.Debits != 10000000 || totals.Credits != 10000000 {
		t.Fatalf("totals = %d/%d, want 10000000/10000000", totals.Debits, totals.Credits)
	}
}
