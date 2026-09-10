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

// TestJournalEntryAccountSidesTranscribesObservedSides pins the property the two
// totals cannot see: each ACCOUNT takes a SPECIFIC side in a SPECIFIC
// transaction. OHLGR-Fund-Source is NOT a fixed-side account — it takes CREDIT
// in L17 and DEBIT in L18 — so a port that keys a side off the account alone
// mis-states the oracle.
func TestJournalEntryAccountSidesTranscribesObservedSides(t *testing.T) {
	sides, err := JournalEntryAccountSides(loan10Batch())
	if err != nil {
		t.Fatalf("JournalEntryAccountSides: %v", err)
	}
	want := []JournalEntryAccountSide{
		{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", Side: "DEBIT"},
		{TransactionID: "L17", Account: "OHLGR-Fund-Source", Side: "CREDIT"},
		{TransactionID: "L18", Account: "OHLGR-Income-From-Fees", Side: "CREDIT"},
		{TransactionID: "L18", Account: "OHLGR-Fund-Source", Side: "DEBIT"},
	}
	if len(sides) != len(want) {
		t.Fatalf("sides has %d entries, want %d", len(sides), len(want))
	}
	for i := range want {
		if sides[i] != want[i] {
			t.Fatalf("sides[%d] = %+v, want %+v", i, sides[i], want[i])
		}
	}
	// The per-transaction property, stated as a behaviour: the same account moves
	// in opposite directions across the two transactions.
	var l17, l18 string
	for _, s := range sides {
		if s.Account == "OHLGR-Fund-Source" {
			switch s.TransactionID {
			case "L17":
				l17 = s.Side
			case "L18":
				l18 = s.Side
			}
		}
	}
	if l17 != "CREDIT" || l18 != "DEBIT" {
		t.Fatalf("OHLGR-Fund-Source = %s in L17, %s in L18; want CREDIT/DEBIT", l17, l18)
	}
}

// TestSwapFirstPairSidesBalancesButMovesAccountSides proves the hole the side
// property closes: reversing BOTH legs of the disbursement pair leaves
// sum(debits) == sum(credits) at the observed 10010000/10010000 — every totals
// check stays green — while the side each account takes is reversed.
func TestSwapFirstPairSidesBalancesButMovesAccountSides(t *testing.T) {
	swapped := loan10Batch()
	swapped[0].Side = JournalEntryCredit
	swapped[1].Side = JournalEntryDebit

	totals, err := SumJournalEntryBatch(swapped)
	if err != nil {
		t.Fatalf("SumJournalEntryBatch: %v", err)
	}
	if totals.Debits != 10010000 || totals.Credits != 10010000 {
		t.Fatalf("swapped totals = %d/%d, want the observed 10010000/10010000 (the swap is invisible to the totals)",
			totals.Debits, totals.Credits)
	}
	if !totals.Balances() {
		t.Fatal("a balanced pair swapped is still balanced")
	}

	sides, err := JournalEntryAccountSides(swapped)
	if err != nil {
		t.Fatalf("JournalEntryAccountSides: %v", err)
	}
	if sides[0].Side != "CREDIT" || sides[1].Side != "DEBIT" {
		t.Fatalf("swapped sides = %s/%s, want the pair reversed to CREDIT/DEBIT", sides[0].Side, sides[1].Side)
	}
	observed, _ := JournalEntryAccountSides(loan10Batch())
	if sides[0] == observed[0] || sides[1] == observed[1] {
		t.Fatal("the swap must move the observed account sides")
	}
}

func TestJournalEntryAccountSidesRefusesUnknownSide(t *testing.T) {
	_, err := JournalEntryAccountSides([]JournalEntryLeg{
		{TransactionID: "L17", Account: "OHLGR-Loan-Portfolio", Amount: 10000000},
	})
	if err == nil {
		t.Fatal("a leg with no established side must be refused, not labelled DEBIT")
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
