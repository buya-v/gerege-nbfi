package ledger

import (
	"reflect"
	"testing"
)

// THESE ARE UNIT TESTS GROUNDED IN OBSERVED ROWS, NOT PARITY VECTORS. The
// manual reversal's write path was observed live, before and after, on tenant
// gerege [.softhouse/capture/tb-manual-reversal/]. The before state is the step
// 1 readback [step01-post/readback-rest.json]; the after state is the step 3
// readback [step03-readback/rest-orig.json, rest-rev.json, sql-rows.txt]:
//
//	141 acct 6  txn a2b795dca42b DEBIT  1234567 reversed=true  reversal_id=143
//	142 acct 10 txn a2b795dca42b CREDIT 1234567 reversed=true  reversal_id=144
//	143 acct 6  txn a2b7964aa51b CREDIT 1234567 reversed=false no reversal_id
//	144 acct 10 txn a2b7964aa51b DEBIT  1234567 reversed=false no reversal_id
//
// The counter-entry rows 143/144 have database-assigned ids. A pure builder
// must never invent an id, so this port cannot reproduce 143/144; the tests
// below compare every counter-entry CELL except that row id, exactly as the
// capture allows. The originals' reversal_id link (143/144) is represented in
// the port by ReversalEntry pointing at the counter-entry it built.

// observedManualReversalTxnID is the fresh transaction id the oracle assigned
// to the counter-entry pair, transcribed from the reversal response
// [step02-reverse/response.json: {"transactionId":"a2b7964aa51b"}] and the
// step 3 readback.
const observedManualReversalTxnID = "a2b7964aa51b"

// observedManualReversalOriginalTxnID is the original pair's transaction id,
// unchanged by the reversal.
const observedManualReversalOriginalTxnID = "a2b795dca42b"

// observedReversalOriginalsBefore transcribes the OBSERVED before-state of JE
// 141/142: both legs manual, reversed=false, no counter-entry link.
func observedReversalOriginalsBefore() []JournalEntry {
	return []JournalEntry{
		{ID: 141, AccountID: 6, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalOriginalTxnID, Reversed: false,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
			Amount: observedReversalAmount},
		{ID: 142, AccountID: 10, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalOriginalTxnID, Reversed: false,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryCredit,
			Amount: observedReversalAmount},
	}
}

// TestRevertJournalEntriesMatchesObservedManualReversal is the manual path as a
// unit test: one counter-entry per original, opposite side, same office,
// account, currency, amount and transaction date, the observed fresh
// transaction id, manual entry true and unflagged; each original flagged
// reversed and linked to its counter-entry, with every other cell unchanged.
func TestRevertJournalEntriesMatchesObservedManualReversal(t *testing.T) {
	before := observedReversalOriginalsBefore()
	snapshot := append([]JournalEntry(nil), before...)

	flagged, counter, err := RevertJournalEntries(before, observedManualReversalTxnID)
	if err != nil {
		t.Fatalf("RevertJournalEntries: %v", err)
	}
	if len(flagged) != 2 || len(counter) != 2 {
		t.Fatalf("got %d flagged and %d counter entries, want 2 and 2", len(flagged), len(counter))
	}

	// The observed after-state cells. Counter rows 143/144 carry no ID here:
	// their database row id is not knowable to a pure builder and is not graded.
	wantFlagged := []JournalEntry{
		{ID: 141, AccountID: 6, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalOriginalTxnID, Reversed: true,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
			Amount: observedReversalAmount},
		{ID: 142, AccountID: 10, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalOriginalTxnID, Reversed: true,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryCredit,
			Amount: observedReversalAmount},
	}
	wantCounter := []JournalEntry{
		{AccountID: 6, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalTxnID, Reversed: false,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryCredit,
			Amount: observedReversalAmount},
		{AccountID: 10, OfficeID: 1, CurrencyCode: "MNT",
			TransactionID: observedManualReversalTxnID, Reversed: false,
			ManualEntry: true, EntryDate: "2026-06-15", Side: EntryDebit,
			Amount: observedReversalAmount},
	}
	// The link is part of the observed after-state; express it on the expected
	// originals so the comparison is cell for cell, including the link.
	wantFlagged[0].ReversalEntry = &wantCounter[0]
	wantFlagged[1].ReversalEntry = &wantCounter[1]

	if !reflect.DeepEqual(flagged, wantFlagged) {
		t.Errorf("flagged originals:\n got  %+v\n want %+v", flagged, wantFlagged)
	}
	if !reflect.DeepEqual(counter, wantCounter) {
		t.Errorf("counter-entries:\n got  %+v\n want %+v", counter, wantCounter)
	}

	// The link must point at the PORT'S OWN counter-entry, not merely hold an
	// equal value: identity is what makes it a link.
	for i := range flagged {
		if flagged[i].ReversalEntry != &counter[i] {
			t.Errorf("original JE %d links to %p, want the counter-entry at index %d (%p)",
				flagged[i].ID, flagged[i].ReversalEntry, i, &counter[i])
		}
		if flagged[i].ReversalEntry != nil && flagged[i].ReversalEntry.Reversed {
			t.Errorf("original JE %d links to a counter-entry flagged reversed; the counter-entry is never flagged",
				flagged[i].ID)
		}
	}

	if !reflect.DeepEqual(before, snapshot) {
		t.Fatalf("the port mutated its input:\n got  %+v\n want %+v", before, snapshot)
	}
}

// TestRevertJournalEntriesCounterEntriesNetOriginalsToZero is the TBFIX-Z
// property end to end: DeriveTrialBalance over the before rows unioned with the
// port's counter-entries nets every account to 0, because each counter-entry is
// the original's equal and opposite. The oracle's own trial balance sums every
// row with no `reversed` predicate [JournalEntryRepository.java:52-66].
func TestRevertJournalEntriesCounterEntriesNetOriginalsToZero(t *testing.T) {
	before := observedReversalOriginalsBefore()
	_, counter, err := RevertJournalEntries(before, observedManualReversalTxnID)
	if err != nil {
		t.Fatalf("RevertJournalEntries: %v", err)
	}

	combined := append(append([]JournalEntry(nil), before...), counter...)
	lines := DeriveTrialBalance(combined)

	for _, account := range []int64{6, 10} {
		line, ok := lines[account]
		if !ok {
			t.Fatalf("no trial-balance line for account %d; got %+v", account, lines)
		}
		if line.TotalDebits != observedReversalAmount || line.TotalCredits != observedReversalAmount {
			t.Errorf("account %d = debits %d credits %d, want both %d: the counter-entry is the original's equal and opposite",
				account, line.TotalDebits, line.TotalCredits, observedReversalAmount)
		}
		if net := line.Net(); net != 0 {
			t.Errorf("account %d nets %d, want 0 — the manual reversal's counter-entry must cancel the original",
				account, net)
		}
	}
}

// TestRevertJournalEntriesRefusesUnknownSide: an original whose side was never
// established has no mirror and is refused rather than guessed, and the refusal
// yields no partial output.
func TestRevertJournalEntriesRefusesUnknownSide(t *testing.T) {
	flagged, counter, err := RevertJournalEntries([]JournalEntry{{
		ID: 141, AccountID: 6, OfficeID: 1, CurrencyCode: "MNT",
		TransactionID: observedManualReversalOriginalTxnID, ManualEntry: true,
		EntryDate: "2026-06-15", Amount: observedReversalAmount,
	}}, observedManualReversalTxnID)
	if err == nil {
		t.Fatal("an original with no established side must be refused, not mirrored onto an invented side")
	}
	if flagged != nil || counter != nil {
		t.Fatalf("a refused reversal returned partial output: flagged=%+v counter=%+v", flagged, counter)
	}
}

// TestRevertJournalEntriesTakesItsTransactionIDFromTheInput pins that the
// reversal transaction id is an INPUT, never generated: a distinct id must
// appear on every counter-entry and on no original. This is what kills a port
// that reuses the originals' transaction id (the loan path's shape) or invents
// a fresh one (the Java generateTransactionId at :382).
func TestRevertJournalEntriesTakesItsTransactionIDFromTheInput(t *testing.T) {
	const inputID = "ffffffffffff"
	before := observedReversalOriginalsBefore()

	flagged, counter, err := RevertJournalEntries(before, inputID)
	if err != nil {
		t.Fatalf("RevertJournalEntries: %v", err)
	}
	for i := range counter {
		if counter[i].TransactionID != inputID {
			t.Errorf("counter-entry %d transaction id = %q, want the input id %q",
				i, counter[i].TransactionID, inputID)
		}
		if counter[i].TransactionID == observedManualReversalOriginalTxnID {
			t.Errorf("counter-entry %d reused the original transaction id %q; the manual path posts on a fresh id",
				i, observedManualReversalOriginalTxnID)
		}
	}
	for i := range flagged {
		if flagged[i].TransactionID != observedManualReversalOriginalTxnID {
			t.Errorf("original %d transaction id = %q, want its own unchanged %q",
				i, flagged[i].TransactionID, observedManualReversalOriginalTxnID)
		}
	}
}

// TestRevertJournalEntriesIsAppendOnly pins the non-negotiable: the flag and the
// link live on COPIES, so writing the result after the call must not reach the
// input slice, and no result slice may alias it.
func TestRevertJournalEntriesIsAppendOnly(t *testing.T) {
	before := observedReversalOriginalsBefore()
	snapshot := append([]JournalEntry(nil), before...)

	flagged, counter, err := RevertJournalEntries(before, observedManualReversalTxnID)
	if err != nil {
		t.Fatalf("RevertJournalEntries: %v", err)
	}

	counter[0].AccountID = 999
	counter[0].Side = EntryDebit
	flagged[0].Amount = 999
	flagged[0].Reversed = false

	if !reflect.DeepEqual(before, snapshot) {
		t.Fatalf("mutating the result reached the input:\n got  %+v\n want %+v", before, snapshot)
	}
}
