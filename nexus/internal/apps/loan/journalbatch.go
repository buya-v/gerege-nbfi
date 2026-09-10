package loan

import "fmt"

// JournalEntrySide is the side of one leg of a double-entry journal-entry
// batch, as the loan read-back serialises it (journalEntryType.debit /
// journalEntryType.credit). The zero value is deliberately an UNKNOWN side so
// a leg that omits its side is refused rather than silently summed as a debit.
type JournalEntrySide int

const (
	// JournalEntrySideUnknown is the zero value: a leg whose side was never
	// established. It is never a valid side and SumJournalEntryBatch refuses it.
	JournalEntrySideUnknown JournalEntrySide = iota
	// JournalEntryDebit is the debit side (the oracle's entryType id 2).
	JournalEntryDebit
	// JournalEntryCredit is the credit side (the oracle's entryType id 1).
	JournalEntryCredit
)

// JournalEntryLeg is one observed leg of a loan-produced journal-entry batch:
// the transaction id the oracle grouped it under, the GL account it touched,
// its side, and its amount in integer minor units.
//
// The transaction id is READ-BACK metadata, not command input: a loan
// disbursement GENERATES the legs; nobody submits them. A batch carries more
// than one pair when more than one transaction id appears, which is exactly the
// shape a single-pair read-back cannot discriminate.
type JournalEntryLeg struct {
	TransactionID string
	Account       string
	Side          JournalEntrySide
	Amount        MinorUnits
}

// JournalEntryBatchTotals is the derived debit and credit totals of a batch,
// in integer minor units.
type JournalEntryBatchTotals struct {
	Debits  MinorUnits
	Credits MinorUnits
}

// Balances reports the double-entry property this batch must hold:
// sum(debits) == sum(credits), exactly, in integer minor units (I-1).
func (t JournalEntryBatchTotals) Balances() bool { return t.Debits == t.Credits }

// SumJournalEntryBatch sums the debit legs and the credit legs of a
// loan-produced journal-entry batch INDEPENDENTLY, over EVERY leg.
//
// It never nets a debit against a credit on the same account, and it never
// stops after the first transaction id: either would move both totals while
// preserving their difference, so a netted or truncated batch would still
// "balance" while being wrong about the money actually posted. The batch's
// balance is the observed equality of the two sums, not a property of any
// single pair.
func SumJournalEntryBatch(legs []JournalEntryLeg) (JournalEntryBatchTotals, error) {
	var totals JournalEntryBatchTotals
	for i, leg := range legs {
		switch leg.Side {
		case JournalEntryDebit:
			totals.Debits += leg.Amount
		case JournalEntryCredit:
			totals.Credits += leg.Amount
		default:
			return JournalEntryBatchTotals{}, fmt.Errorf(
				"loan: journal-entry leg %d has an unknown side", i)
		}
	}
	return totals, nil
}
