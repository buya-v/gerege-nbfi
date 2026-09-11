package loan

import "fmt"

// WriteOffPortions is the money a loan write-off discharges per ledger slot, in
// integer minor units. It is the Go port of the five BigDecimal fields
// createJournalEntriesForLoanWriteOffs reads off the write-off transaction
// toRepaymentScheduleMapping — principal, interest, fees, penalties and
// overPayment [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1884-1889,
// pinned commit 426a23544].
//
// A slot is discharged only when its portion is > 0 (MathUtil
// .isGreaterThanZero); a zero or negative portion contributes neither an amount
// nor an account to the posting. Every field is an integer MinorUnits value:
// no float and no sub-minor residue can enter this path (G-19 / DEC-2 G-08).
type WriteOffPortions struct {
	Principal   MinorUnits
	Interest    MinorUnits
	Fee         MinorUnits
	Penalty     MinorUnits
	Overpayment MinorUnits
}

// Total returns the sum of every portion, in integer minor units. It is the
// amount of the ONE debit a write-off posts to the losses-written-off account.
func (p WriteOffPortions) Total() MinorUnits {
	return p.Principal + p.Interest + p.Fee + p.Penalty + p.Overpayment
}

// WriteOffAccountMapping is the GL account each write-off portion slot maps to
// for one loan product, as GET /loanproducts/{id}.accountingMappings returns it
// (the AccrualAccountsForLoan slots the processor resolves through
// getLinkedGLAccountForLoanProduct).
//
// The first five accounts are credited with their slot's portion;
// LossesWrittenOff is debited ONCE with the sum of every discharged portion
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1893-1975].
type WriteOffAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot,
	// credited with the principal portion.
	LoanPortfolio string
	// InterestReceivable is the AccrualAccountsForLoan.INTEREST_RECEIVABLE
	// slot, credited with the interest portion.
	InterestReceivable string
	// FeesReceivable is the AccrualAccountsForLoan.FEES_RECEIVABLE slot,
	// credited with the fee portion.
	FeesReceivable string
	// PenaltiesReceivable is the AccrualAccountsForLoan.PENALTIES_RECEIVABLE
	// slot, credited with the penalty portion.
	PenaltiesReceivable string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited
	// with the overpayment portion.
	Overpayment string
	// LossesWrittenOff is the AccrualAccountsForLoan.LOSSES_WRITTEN_OFF slot,
	// debited ONCE with the sum of every discharged portion. When the oracle
	// resolves a write-off-reason mapping (advanced accounting) this slot is
	// replaced by that mapping's account; the loan slice reads no reason here,
	// so the caller passes the product's losses-written-off account.
	LossesWrittenOff string
}

// writeOffSlot is one portion/account pair in the processor's fixed visitation
// order.
type writeOffSlot struct {
	name    string
	amount  MinorUnits
	account string
}

// CreateWriteOffJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanWriteOffs
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1872-1976, pinned
// commit 426a23544]. It is a pure function: portions (integer minor units) plus
// a slot->account mapping in, journal-entry legs out — no clock, no I/O, no
// stored balance.
//
// It visits the five slots in the processor's order (principal, interest, fees,
// penalties, overpayment), and for every slot whose portion is > 0:
//
//   - adds the portion to the write-off total, and
//   - credits the slot's mapped account, MERGING into the first slot that
//     already named the same account (the LinkedHashMap accountMap), so two
//     portion slots that resolve to one GL account post ONE credit for their
//     sum at the first slot's position.
//
// It then posts the credits in that insertion order, followed by ONE debit of
// the total to the losses-written-off account. The debit is LAST: the oracle
// posts it after the credit loop
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1952-1974], which is
// why the observed L54 id order reads four credits then the debit.
//
// It refuses, rather than inventing, a positive portion whose slot maps to no
// account, a non-positive portion carrying a negative (never a genuine
// discharge) and a positive total with no losses-written-off account.
func CreateWriteOffJournalEntryLegs(transactionID string, portions WriteOffPortions, mapping WriteOffAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: write-off journal entries need a transaction id")
	}

	slots := []writeOffSlot{
		{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
		{"INTEREST_RECEIVABLE", portions.Interest, mapping.InterestReceivable},
		{"FEES_RECEIVABLE", portions.Fee, mapping.FeesReceivable},
		{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.PenaltiesReceivable},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}

	// accountMap is a LinkedHashMap: an ordered set of accounts keyed by the
	// account, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: write-off slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.account == "" {
			return nil, fmt.Errorf("loan: write-off slot %s has a positive portion %d but no mapped account", s.name, s.amount)
		}
		if _, seen := byAccount[s.account]; !seen {
			order = append(order, s.account)
		}
		byAccount[s.account] += s.amount
	}

	legs := make([]JournalEntryLeg, 0, len(order)+1)
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryCredit,
			Amount:        byAccount[account],
		})
	}

	total := portions.Total()
	if total == 0 {
		return legs, nil
	}
	if mapping.LossesWrittenOff == "" {
		return nil, fmt.Errorf("loan: write-off total %d has no losses-written-off account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.LossesWrittenOff,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
