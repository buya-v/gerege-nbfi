package loan

import (
	"reflect"
	"testing"
)

// l46BeforeLegs are the two journal-entry legs of loan-transaction L46 (the
// 2026-09-02 interest accrual on loan 11) as read back BEFORE the write-off
// reversed it. Transcribed from
// .softhouse/capture/loan11-writeoff-four-bucket/out/loan-11-before-journalentries-raw.json
// (JE 84 DEBIT OHLGR-10012 11.56, JE 86 CREDIT OHLGR-40010 11.56; amounts in
// integer minor units).
func l46BeforeLegs() []JournalEntryLeg {
	return []JournalEntryLeg{
		{TransactionID: "L46", Account: "OHLGR-10012", Side: JournalEntryDebit, Amount: 1156, TransactionDate: "2026-09-02", Reversed: false},
		{TransactionID: "L46", Account: "OHLGR-40010", Side: JournalEntryCredit, Amount: 1156, TransactionDate: "2026-09-02", Reversed: false},
	}
}

// TestReverseLoanTransactionJournalEntriesAddsCounterLegs pins the one property
// the seam grades: one counter-leg per original, same transaction id, account,
// amount and transaction date, OPPOSITE side, originals left in place and
// unflagged, in order. Transcribed from the AFTER read-back
// (loan-11-after-journalentries-raw.json: originals JE 84/86 byte-identical,
// plus JE 134 CREDIT OHLGR-10012 11.56 and JE 135 DEBIT OHLGR-40010 11.56).
func TestReverseLoanTransactionJournalEntriesAddsCounterLegs(t *testing.T) {
	got, err := ReverseLoanTransactionJournalEntries(l46BeforeLegs(), "2026-09-02")
	if err != nil {
		t.Fatalf("ReverseLoanTransactionJournalEntries: %v", err)
	}
	want := []JournalEntryLeg{
		{TransactionID: "L46", Account: "OHLGR-10012", Side: JournalEntryDebit, Amount: 1156, TransactionDate: "2026-09-02"},
		{TransactionID: "L46", Account: "OHLGR-40010", Side: JournalEntryCredit, Amount: 1156, TransactionDate: "2026-09-02"},
		{TransactionID: "L46", Account: "OHLGR-10012", Side: JournalEntryCredit, Amount: 1156, TransactionDate: "2026-09-02"},
		{TransactionID: "L46", Account: "OHLGR-40010", Side: JournalEntryDebit, Amount: 1156, TransactionDate: "2026-09-02"},
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("reversal = %+v, want %+v (originals as they were, then the two counter-legs)", got, want)
	}
}

// TestReverseLoanTransactionJournalEntriesIsAppendOnly pins the non-negotiable
// append-only property: the port must never mutate an input leg. The input is
// deep-copied before the call and must be byte-identical afterwards; the
// originals in the result must equal the input unchanged.
func TestReverseLoanTransactionJournalEntriesIsAppendOnly(t *testing.T) {
	in := l46BeforeLegs()
	before := append([]JournalEntryLeg(nil), in...)

	got, err := ReverseLoanTransactionJournalEntries(in, "2026-09-02")
	if err != nil {
		t.Fatalf("ReverseLoanTransactionJournalEntries: %v", err)
	}
	if !reflect.DeepEqual(in, before) {
		t.Fatalf("the port mutated its input: %+v, want %+v", in, before)
	}
	if !reflect.DeepEqual(got[:len(in)], before) {
		t.Fatalf("the result's originals are not the input unchanged: %+v, want %+v", got[:len(in)], before)
	}
	// Mutating the result's appended counter-legs must not reach the input: the
	// two slices must not share backing storage.
	got[len(in)].Account = "MUTATED"
	if in[0].Account == "MUTATED" {
		t.Fatal("the result aliases the input's backing array")
	}
}

// TestReverseLoanTransactionJournalEntriesSingleLeg pins the "one counter-leg
// per original leg" cardinality on a one-leg transaction, so a port that adds a
// fixed number of counters (or none) is caught.
func TestReverseLoanTransactionJournalEntriesSingleLeg(t *testing.T) {
	in := []JournalEntryLeg{
		{TransactionID: "L99", Account: "OHLGR-10012", Side: JournalEntryCredit, Amount: 500, TransactionDate: "2026-01-05"},
	}
	got, err := ReverseLoanTransactionJournalEntries(in, "2026-01-05")
	if err != nil {
		t.Fatalf("ReverseLoanTransactionJournalEntries: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("result has %d legs, want 2 (one original + one counter)", len(got))
	}
	if got[1].Side != JournalEntryDebit || got[1].Amount != 500 || got[1].Account != "OHLGR-10012" ||
		got[1].TransactionID != "L99" || got[1].TransactionDate != "2026-01-05" || got[1].Reversed {
		t.Fatalf("counter-leg = %+v, want the original mirrored on the opposite side", got[1])
	}
}

// TestReverseLoanTransactionJournalEntriesRefusesUnknownSide: a leg whose side
// was never established has no mirror and is refused rather than guessed.
func TestReverseLoanTransactionJournalEntriesRefusesUnknownSide(t *testing.T) {
	_, err := ReverseLoanTransactionJournalEntries([]JournalEntryLeg{
		{TransactionID: "L99", Account: "OHLGR-10012", Amount: 500},
	}, "2026-01-05")
	if err == nil {
		t.Fatal("a leg with no established side must be refused, not mirrored onto an invented side")
	}
}

// TestReverseLoanTransactionJournalEntriesStampsTransactionDate pins the
// counter-leg date to the reversed transaction's date, NOT the original leg's
// date and NOT any other date the caller might hold. A port that keeps the
// original's date would be inert here (they coincide in the capture), so the
// input legs deliberately carry a DIFFERENT date and the counter-legs must
// still take the passed transaction date.
func TestReverseLoanTransactionJournalEntriesStampsTransactionDate(t *testing.T) {
	in := []JournalEntryLeg{
		{TransactionID: "L77", Account: "OHLGR-10012", Side: JournalEntryDebit, Amount: 700, TransactionDate: "2026-03-09"},
	}
	got, err := ReverseLoanTransactionJournalEntries(in, "2026-03-01")
	if err != nil {
		t.Fatalf("ReverseLoanTransactionJournalEntries: %v", err)
	}
	if got[1].TransactionDate != "2026-03-01" {
		t.Fatalf("counter-leg date = %q, want the reversed transaction date 2026-03-01", got[1].TransactionDate)
	}
	if got[0].TransactionDate != "2026-03-09" {
		t.Fatalf("original date was re-dated to %q; the port must change no original", got[0].TransactionDate)
	}
}
