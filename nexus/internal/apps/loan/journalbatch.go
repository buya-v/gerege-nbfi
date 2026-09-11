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
// its side, its amount in integer minor units, the transaction date it was
// posted under, and whether the oracle has flagged the leg reversed.
//
// The transaction id is READ-BACK metadata, not command input: a loan
// disbursement GENERATES the legs; nobody submits them. A batch carries more
// than one pair when more than one transaction id appears, which is exactly the
// shape a single-pair read-back cannot discriminate.
//
// TransactionDate and Reversed are the two read-back cells a loan-transaction
// REVERSAL is graded on beyond the batch sums: the reversal dates its counter
// legs at the reversed transaction's date (not the business date that triggered
// the reversal) and must leave every original leg unflagged, so a port that
// sets Reversed on an original or stamps a wrong date diverges where the side
// and amount cells cannot see it. Both are carried through unchanged by
// SumJournalEntryBatch and JournalEntryAccountSides, which read only Side and
// Amount.
type JournalEntryLeg struct {
	TransactionID string
	Account       string
	Side          JournalEntrySide
	Amount        MinorUnits
	// TransactionDate is the leg's transaction date as a civil YYYY-MM-DD
	// string (no clock, no offset). It is empty for legs a caller did not read a
	// date for; the batch derivations never read it.
	TransactionDate string
	// Reversed is the persisted reversed flag the read-back serialises. A loan
	// reversal ADDS counter-legs and leaves this false on every original.
	Reversed bool
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

// JournalEntryAccountSide is the side ONE account takes in ONE transaction of a
// loan-produced journal-entry batch. The property it pins is
// per-(transaction, account), not per-account globally: OHLGR-Fund-Source takes
// CREDIT in the disbursement transaction L17 and DEBIT in the fee transaction
// L18, so a port that assigns one fixed side to an account would be wrong about
// the oracle even before it is wrong about a single pair.
//
// Side is carried in its OBSERVED code form ("DEBIT"/"CREDIT"), the same
// spelling the capture emitted, not a decoded enum another layer could reorder.
type JournalEntryAccountSide struct {
	TransactionID string
	Account       string
	Side          string
}

// JournalEntryAccountSides reports which side each observed leg's account takes,
// in the order the legs were read back. It is a TRANSCRIPTION of the read-back,
// never a side inferred from an account's normal balance.
//
// This is the property SumJournalEntryBatch cannot see. Swapping the two legs of
// a balanced pair moves equal amounts across the two sides, so the totals are
// unchanged and the batch still "balances" while the money posted to each
// account has been reversed. The per-(transaction, account) side list is what
// moves under that swap.
func JournalEntryAccountSides(legs []JournalEntryLeg) ([]JournalEntryAccountSide, error) {
	sides := make([]JournalEntryAccountSide, len(legs))
	for i, leg := range legs {
		var code string
		switch leg.Side {
		case JournalEntryDebit:
			code = "DEBIT"
		case JournalEntryCredit:
			code = "CREDIT"
		default:
			return nil, fmt.Errorf("loan: journal-entry leg %d has an unknown side", i)
		}
		sides[i] = JournalEntryAccountSide{
			TransactionID: leg.TransactionID,
			Account:       leg.Account,
			Side:          code,
		}
	}
	return sides, nil
}
