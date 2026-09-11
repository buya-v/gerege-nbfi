package ledger

import "fmt"

// RevertJournalEntries ports the MANUAL journal-entry reversal path and nothing
// else. For every original leg it returns ONE counter-entry — the same office,
// GL account, currency, amount and transaction DATE, the OPPOSITE side, the
// caller's reversalTransactionID (one id for the whole batch), manual entry
// true and Reversed false — and the original with Reversed true and its link to
// that counter-entry set. NOTHING else on an original changes.
//
// Ported from Fineract
// fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java
// revertJournalEntry (lines 380-429, pinned commit 426a23544): it generates a
// fresh transaction id (:382), then for each original persists a counter-entry
// with the same office/account/currency/amount/date on that id, manual entry
// true, the opposite side (:402-422), and flags the original
// setReversed(true) (:423) and links it setReversalJournalEntry (:424). The
// counter-entry is never flagged.
//
// CONTRAST WITH THE LOAN PATH (loan/reversal.go): createJournalEntryForReversedLoanTransaction
// (lines 359-378) adds the same opposite-side counter-entries but on the SAME
// transaction id and flags NOTHING, whereas this manual path posts them on a
// FRESH id and flags every original.
//
// THE TRANSACTION ID IS AN INPUT, never generated here: the Java
// generateTransactionId(officeId) at :382 is deliberately not ported, both
// because a port must not invent an id and because the observed fresh id
// a2b7964aa51b is an oracle-assigned fact, not something this function could
// reproduce. An unknown side is refused rather than guessed. Amounts are
// integer minor units; there is no float, and this function mutates neither the
// input slice nor any element of it — the flagged entries are copies.
//
// THE LINK FIELD. JournalEntry had no field naming an entry's counter-entry;
// this port added ReversalEntry *JournalEntry to journalentry.go. The oracle
// records the link as the counter row's database id in
// acc_gl_journal_entry.reversal_id [VERIFIED: doc.go TRAP 3 lists reversal_id
// among acc_gl_journal_entry's columns; the capture read it as 143 and 144], but
// a pure builder cannot know a database-assigned row id and must never invent
// one, so this port links by identity: ReversalEntry points at the
// counter-entry it built for that original.
func RevertJournalEntries(originals []JournalEntry, reversalTransactionID string) (flagged []JournalEntry, counter []JournalEntry, err error) {
	flagged = make([]JournalEntry, len(originals))
	counter = make([]JournalEntry, len(originals))
	for i, original := range originals {
		opposite, oerr := oppositeReversalSide(original.Side)
		if oerr != nil {
			return nil, nil, fmt.Errorf("ledger: manual reversal of journal entry %d: %w", original.ID, oerr)
		}
		counter[i] = JournalEntry{
			AccountID:     original.AccountID,
			OfficeID:      original.OfficeID,
			CurrencyCode:  original.CurrencyCode,
			TransactionID: reversalTransactionID,
			Reversed:      false,
			ManualEntry:   true,
			EntryDate:     original.EntryDate,
			Side:          opposite,
			Amount:        original.Amount,
		}
		// The flagged original is a COPY: Reversed flips and the link is set,
		// every other cell is carried over untouched and the input is not written.
		f := original
		f.Reversed = true
		f.ReversalEntry = &counter[i]
		flagged[i] = f
	}
	return flagged, counter, nil
}

// oppositeReversalSide returns the side a MANUAL reversal counter-entry posts
// on: the mirror of the original. A debit is reversed by a credit and a credit
// by a debit; any other value has no mirror and is refused, the same
// refuse-don't-guess discipline the loan path applies to a side it never
// established. It is deliberately NOT OppositeSide, which guesses a debit for
// an unknown side because its caller (the opening-balance expansion) already
// holds a resolved leg.
func oppositeReversalSide(side EntrySide) (EntrySide, error) {
	switch side {
	case EntryDebit:
		return EntryCredit, nil
	case EntryCredit:
		return EntryDebit, nil
	}
	return 0, fmt.Errorf("journal-entry side has no opposite: the side was never established")
}
