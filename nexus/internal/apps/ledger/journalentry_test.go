package ledger

import (
	"reflect"
	"testing"
)

// These tests hold the A1 engine's two structural invariants directly — the
// double-entry check and the refusal precedence — plus the persistence layer's
// argument builder, without a database. The end-to-end parity and mutation grading
// lives in the conformance harness; these pin the engine the harness now calls.

func testAccount(id int64, code string) GLAccount {
	return GLAccount{
		ID:                   id,
		GLCode:               code,
		Name:                 code,
		ManualEntriesAllowed: true,
		Usage:                UsageDetail,
	}
}

func testLeg(account GLAccount, side EntrySide, amount MinorUnits) JournalEntryLeg {
	return JournalEntryLeg{Account: account, Side: side, Amount: amount}
}

// TestPosterRefusesUnbalancedPosting drives the double-entry invariant through
// the engine rather than through DoubleEntryBalances directly.
func TestPosterRefusesUnbalancedPosting(t *testing.T) {
	asset := testAccount(2, "1000")
	income := testAccount(4, "4000")
	cmd := PostingCommand{
		TransactionID: "T1",
		Legs: []JournalEntryLeg{
			testLeg(asset, EntryDebit, 100),
			testLeg(income, EntryCredit, 99),
		},
	}
	_, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal == nil || refusal.Code != CodeDebitCreditMismatch {
		t.Fatalf("refusal = %+v, want the debit/credit mismatch code", refusal)
	}
	if refusal.HTTPStatus != 403 {
		t.Errorf("HTTP status = %d, want 403", refusal.HTTPStatus)
	}
}

// TestPosterOpeningBalanceRefusalPrecedesBalanceRule pins the observed refusal
// precedence: OB-01's request is UNBALANCED by one minor unit yet the oracle
// returned the opening-balance refusal, because that rule runs before the
// balance check.
func TestPosterOpeningBalanceRefusalPrecedesBalanceRule(t *testing.T) {
	asset := testAccount(2, "1000")
	income := testAccount(4, "4000")
	cmd := PostingCommand{
		Command:       "defineOpeningBalance",
		TransactionID: "OB-01",
		Legs: []JournalEntryLeg{
			testLeg(asset, EntryDebit, 100),
			testLeg(income, EntryCredit, 99),
		},
		PostedNonContraTransactionIDs: []string{"X", "Y"},
	}
	_, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal == nil || refusal.Code != CodeOpeningBalanceNotAllowed {
		t.Fatalf("refusal = %+v, want the opening-balance code (balance check must NOT fire first)", refusal)
	}
}

// TestPosterExpandsOpeningBalanceContraPerLeg holds the accepted-opening-balance
// shape: every leg gets its own opposite-side contra on the financial-activity
// account, debits are emitted before credits, and the expansion stays balanced.
func TestPosterExpandsOpeningBalanceContraPerLeg(t *testing.T) {
	contra := testAccount(1, "3000")
	gl2 := testAccount(2, "1000")
	gl3 := testAccount(3, "1100")
	gl4 := testAccount(4, "2000")
	cmd := PostingCommand{
		Command:       "defineOpeningBalance",
		TransactionID: "OB-ACCEPT",
		ContraAccount: contra,
		Legs: []JournalEntryLeg{
			testLeg(gl2, EntryDebit, 25000025),
			testLeg(gl3, EntryDebit, 10000037),
			testLeg(gl4, EntryCredit, 35000062),
		},
	}

	result, refusal, err := NewPoster().Post(cmd)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if refusal != nil {
		t.Fatalf("unexpected refusal: %+v", refusal)
	}
	if len(result.Legs) != 6 {
		t.Fatalf("expanded legs = %d, want 6 (one contra per leg)", len(result.Legs))
	}
	// Debits before credits, contra per leg.
	wantFirst := []struct {
		account int64
		side    EntrySide
		amount  MinorUnits
	}{
		{2, EntryDebit, 25000025},
		{1, EntryCredit, 25000025},
		{3, EntryDebit, 10000037},
		{1, EntryCredit, 10000037},
		{4, EntryCredit, 35000062},
		{1, EntryDebit, 35000062},
	}
	for i, w := range wantFirst {
		l := result.Legs[i]
		if l.Account.ID != w.account || l.Side != w.side || l.Amount != w.amount {
			t.Errorf("leg %d = (%d, %v, %d), want (%d, %v, %d)",
				i, l.Account.ID, l.Side, l.Amount, w.account, w.side, w.amount)
		}
	}
	// After contra expansion every original leg contributes one debit AND one
	// credit of its amount, so both totals equal the sum of all three legs.
	if result.TotalDebitsMinor != 70000124 || result.TotalCreditsMinor != 70000124 {
		t.Errorf("totals = %d / %d, want 70000124 / 70000124 (balanced after contra)",
			result.TotalDebitsMinor, result.TotalCreditsMinor)
	}
}

// TestBuildJournalEntryInsertArgsPinsTheColumnArrays asserts the arguments the
// persistence layer binds — ELEVEN parallel column arrays, one element per
// entry, with the amount rendered back to exact decimal text — without touching
// a database.
//
// WHAT THIS TEST NO LONGER PINS, AND WHY THAT IS NOT A LOSS. [T503] It used to
// reconstruct the SQL string and assert its shape, because the statement was
// assembled at run time and existed nowhere a reader could see it. The
// statement is now a fixed literal at the single call site in
// journalentry_postgres.go Append, so it is read directly from source — by a
// reviewer and by the I-3/I-4 guard, which is what the guard demanded. A test
// that re-derived it would only be asserting a copy against itself. The row
// count moved out of the SQL and into these arrays, which is exactly what this
// test now pins.
func TestBuildJournalEntryInsertArgsPinsTheColumnArrays(t *testing.T) {
	entries := []JournalEntry{
		{
			AccountID:     2,
			OfficeID:      1,
			CurrencyCode:  "MNT",
			TransactionID: "T1",
			EntryDate:     "2026-08-24",
			Side:          EntryDebit,
			Amount:        25000025,
		},
		{
			AccountID:     1,
			OfficeID:      1,
			CurrencyCode:  "MNT",
			TransactionID: "T1",
			EntryDate:     "2026-08-24",
			Side:          EntryCredit,
			Amount:        25000025,
		},
	}

	args := buildJournalEntryInsertArgs(entries, 1, 1)
	if got := len(args); got != 11 {
		t.Fatalf("arg count = %d, want 11 column arrays ($1..$11)", got)
	}

	// Every array must be the same length as the batch, or unnest would zip
	// rows out of alignment and a leg would be written against another leg's
	// account.
	for i, a := range args {
		n := reflect.ValueOf(a).Len()
		if n != len(entries) {
			t.Errorf("arg $%d has %d elements, want %d (one per entry)", i+1, n, len(entries))
		}
	}

	if got := args[3].([]string); got[0] != "T1" || got[1] != "T1" {
		t.Errorf("transaction_id array = %q, want both legs on T1", got)
	}
	if got := args[8].([]string); got[0] != "250000.25" || got[1] != "250000.25" {
		t.Errorf("amount array = %q, want exact decimal text for 25000025 minor units", got)
	}
	if got := args[0].([]int64); got[0] != 2 || got[1] != 1 {
		t.Errorf("account_id array = %v, want [2 1] in entry order", got)
	}
	if got := args[7].([]int32); got[0] != int32(EntryDebit) || got[1] != int32(EntryCredit) {
		t.Errorf("type_enum array = %v, want [debit credit] in entry order", got)
	}
	if got := args[6].([]string); got[0] != "2026-08-24" || got[1] != "2026-08-24" {
		t.Errorf("entry_date array = %q, want the strict yyyy-MM-dd text both legs carry", got)
	}
}
