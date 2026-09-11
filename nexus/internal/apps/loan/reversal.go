package loan

import "fmt"

// ReverseLoanTransactionJournalEntries ports the journal-entry side of a
// loan-transaction reversal and nothing else. For every original leg of one
// reversed loan transaction it APPENDS one counter-leg: the same transaction
// id, the same GL account, the same amount in integer minor units, the same
// transaction date, and the OPPOSITE side. It never modifies, flags, deletes
// or re-dates an original leg — the input slice is not aliased into the result
// and no element of it is written.
//
// Ported from Fineract
// fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java
// createJournalEntryForReversedLoanTransaction (lines 359-378, pinned commit
// 426a23544): it reads every journal entry of the transaction id "L" + the loan
// transaction id and, for each, persists ONE new entry with the same office,
// GL account and currency, the same transaction id, manualEntry false, the
// reversed transaction's transaction date, the opposite side and the same
// amount. The originals are left untouched.
//
// This is NOT the manual reversal path
// (JournalEntryWritePlatformServiceJpaRepositoryImpl.revertJournalEntry,
// lines 380-429): that path posts its counter-entries on a FRESH generated
// transaction id and flags each original reversed = true (line 423). A port
// that borrows either of those two behaviours is wrong here; both are
// discriminated by the loan-transaction-reversal vector.
//
// The transaction date is the reversed TRANSACTION's date, passed in as a
// civil YYYY-MM-DD string and stamped on every counter-leg; it is never the
// business date the reversal command was dated at. An unknown side is refused
// rather than guessed, so a leg whose side was never established cannot be
// mirrored into a counter-leg on an invented side.
func ReverseLoanTransactionJournalEntries(legs []JournalEntryLeg, transactionDate string) ([]JournalEntryLeg, error) {
	out := make([]JournalEntryLeg, 0, 2*len(legs))
	// The originals are copied FIRST, unchanged and in order, so a caller can
	// read the result as "originals as they were, then the counter-legs".
	out = append(out, legs...)
	for i, leg := range legs {
		side, err := oppositeJournalEntrySide(leg.Side)
		if err != nil {
			return nil, fmt.Errorf("loan: reversal leg %d: %w", i, err)
		}
		out = append(out, JournalEntryLeg{
			TransactionID:   leg.TransactionID,
			Account:         leg.Account,
			Side:            side,
			Amount:          leg.Amount,
			TransactionDate: transactionDate,
			Reversed:        false,
		})
	}
	return out, nil
}

// oppositeJournalEntrySide returns the side a reversal entry posts on: the
// mirror of the original. A debit is reversed by a credit and a credit by a
// debit. The unknown zero side has no mirror and is refused, the same
// refuse-don't-guess discipline SumJournalEntryBatch applies to a side it never
// established.
func oppositeJournalEntrySide(side JournalEntrySide) (JournalEntrySide, error) {
	switch side {
	case JournalEntryDebit:
		return JournalEntryCredit, nil
	case JournalEntryCredit:
		return JournalEntryDebit, nil
	}
	return JournalEntrySideUnknown, fmt.Errorf("journal-entry side has no opposite: the side was never established")
}
