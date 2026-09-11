package ledger

import (
	"reflect"
	"testing"
)

// THESE ARE UNIT TESTS GROUNDED IN SOURCE AND IN OBSERVED ROWS, NOT PARITY
// VECTORS. There is no oracle-written trial balance to grade against on this
// build: job 30 dies before insert at UpdateTrialBalanceDetailsTasklet.java:80
// and m_trial_balance stays at 0 rows
// [.softhouse/capture/tb-manual-reversal/; capabilities-ledger.json,
// ledger.trial.balance]. What IS observed is the manual reversal's journal rows,
// and DeriveTrialBalance is a pure function of journal rows, so the rows below
// are the whole input and the expected net is checked by hand from them.

// observedReversalAmount is the one amount in the capture, wire "12345.67",
// stored as 12345.670000, integer minor units 1234567.
const observedReversalAmount MinorUnits = 1234567

// observedManualReversalRows is the observed manual reversal, transcribed from
// the live oracle's acc_gl_journal_entry readback
// [.softhouse/capture/tb-manual-reversal/step03-readback/sql-rows.txt]:
//
//	141 acct 6  txn a2b795dca42b DEBIT  1234567 reversed=true  (original)
//	142 acct 10 txn a2b795dca42b CREDIT 1234567 reversed=true  (original)
//	143 acct 6  txn a2b7964aa51b CREDIT 1234567 reversed=false (counter-entry)
//	144 acct 10 txn a2b7964aa51b DEBIT  1234567 reversed=false (counter-entry)
//
// The flag values are the OBSERVED ones. A test that normalised them would not
// exercise the defect.
func observedManualReversalRows() []JournalEntry {
	return []JournalEntry{
		{ID: 141, AccountID: 6, OfficeID: 1, CurrencyCode: "MNT", TransactionID: "a2b795dca42b",
			Reversed: true, ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
			Amount: observedReversalAmount},
		{ID: 142, AccountID: 10, OfficeID: 1, CurrencyCode: "MNT", TransactionID: "a2b795dca42b",
			Reversed: true, ManualEntry: true, EntryDate: "2026-06-15", Side: EntryCredit,
			Amount: observedReversalAmount},
		{ID: 143, AccountID: 6, OfficeID: 1, CurrencyCode: "MNT", TransactionID: "a2b7964aa51b",
			Reversed: false, ManualEntry: true, EntryDate: "2026-06-15", Side: EntryCredit,
			Amount: observedReversalAmount},
		{ID: 144, AccountID: 10, OfficeID: 1, CurrencyCode: "MNT", TransactionID: "a2b7964aa51b",
			Reversed: false, ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
			Amount: observedReversalAmount},
	}
}

// TestDeriveTrialBalanceManualReversalNetsToZero is the defect as a unit test.
//
// The oracle's trial balance sums every row and has no `reversed` predicate
// [JournalEntryRepository.java:52-66]. On the observed rows each account is one
// original leg and its counter-entry, opposite sides, equal amounts, so each
// account nets to 0. A port that skipped the flagged originals produced -1234567
// for account 6 and +1234567 for account 10 (OWNER.md), which this fails on.
func TestDeriveTrialBalanceManualReversalNetsToZero(t *testing.T) {
	got := DeriveTrialBalance(observedManualReversalRows())

	if len(got) != 2 {
		t.Fatalf("DeriveTrialBalance returned %d account line(s), want 2 (accounts 6 and 10): %+v",
			len(got), got)
	}

	for _, want := range []struct {
		account int64
		debits  MinorUnits
		credits MinorUnits
	}{
		{account: 6, debits: observedReversalAmount, credits: observedReversalAmount},
		{account: 10, debits: observedReversalAmount, credits: observedReversalAmount},
	} {
		line, ok := got[want.account]
		if !ok {
			t.Fatalf("no line for account %d; got %+v", want.account, got)
		}
		if line.AccountID != want.account {
			t.Errorf("account %d line carries AccountID %d", want.account, line.AccountID)
		}
		if line.TotalDebits != want.debits || line.TotalCredits != want.credits {
			t.Errorf("account %d = debits %d credits %d, want debits %d credits %d. Both legs of "+
				"the reversed pair must be summed — the counter-entry cancels the original, and "+
				"skipping the flagged row removes the position twice",
				want.account, line.TotalDebits, line.TotalCredits, want.debits, want.credits)
		}
		if net := line.Net(); net != 0 {
			t.Errorf("account %d nets %d, want 0. The oracle sums every entry and a reversed pair "+
				"is equal and opposite, so it must cancel", want.account, net)
		}
	}
}

// TestReversedFlagDoesNotChangeAnyLine pins the rule directly: toggling Reversed
// on ANY observed row must leave the derived lines identical. Every observed row
// is covered, one at a time and all together, because the defect was asymmetric —
// it only bit on the flagged originals, and a per-row assertion is what proves
// the flag is inert rather than merely proofed on one row.
func TestReversedFlagDoesNotChangeAnyLine(t *testing.T) {
	base := DeriveTrialBalance(observedManualReversalRows())

	rows := observedManualReversalRows()
	for i := range rows {
		flipped := observedManualReversalRows()
		flipped[i].Reversed = !flipped[i].Reversed
		got := DeriveTrialBalance(flipped)
		if !reflect.DeepEqual(got, base) {
			t.Fatalf("flipping Reversed on JE id %d changed the derived lines:\n got  %+v\n want %+v",
				rows[i].ID, got, base)
		}
	}

	all := observedManualReversalRows()
	for i := range all {
		all[i].Reversed = !all[i].Reversed
	}
	if got := DeriveTrialBalance(all); !reflect.DeepEqual(got, base) {
		t.Fatalf("flipping Reversed on every row changed the derived lines:\n got  %+v\n want %+v",
			got, base)
	}
}

// TestDeriveTrialBalanceCountsASingleReversedEntry is the smallest statement of
// the rule: a lone entry flagged Reversed is still summed. Nothing about the flag
// may short-circuit the loop.
func TestDeriveTrialBalanceCountsASingleReversedEntry(t *testing.T) {
	got := DeriveTrialBalance([]JournalEntry{{
		ID: 141, AccountID: 6, OfficeID: 1, TransactionID: "a2b795dca42b",
		Reversed: true, ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
		Amount: observedReversalAmount,
	}})

	line, ok := got[6]
	if !ok {
		t.Fatalf("a single entry flagged Reversed was dropped entirely: %+v", got)
	}
	if line.TotalDebits != observedReversalAmount || line.Net() != observedReversalAmount {
		t.Fatalf("a single entry flagged Reversed = %+v, want debits %d and net %d. The flag is a "+
			"marker, not a sign; only the counter-entry cancels", line, observedReversalAmount,
			observedReversalAmount)
	}
}
