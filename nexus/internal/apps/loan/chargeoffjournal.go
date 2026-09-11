package loan

import "fmt"

// ChargeOffPortions is the money a loan charge-off discharges per ledger slot,
// in integer minor units. It is the Go port of the four BigDecimal fields
// createJournalEntriesForChargeOff reads off the charge-off transaction
// toRepaymentScheduleMapping — principal, interest, fees and penalties
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:890-975, pinned commit
// 426a23544].
//
// A slot is discharged only when its portion is > 0 (MathUtil
// .isGreaterThanZero); a zero portion contributes neither an amount nor an
// account to the posting. Every field is an integer MinorUnits value: no float
// and no sub-minor residue can enter this path (G-19 / DEC-2 G-08).
type ChargeOffPortions struct {
	Principal MinorUnits
	Interest  MinorUnits
	Fee       MinorUnits
	Penalty   MinorUnits
}

// Total returns the sum of every portion, in integer minor units. It is the
// amount a charge-off debits, split across the expense accounts its slots map
// to.
func (p ChargeOffPortions) Total() MinorUnits {
	return p.Principal + p.Interest + p.Fee + p.Penalty
}

// ChargeOffAccountMapping is the GL account each charge-off slot maps to for
// one loan product, as GET /loanproducts/{id}.accountingMappings returns it
// (the AccrualAccountsForLoan slots the processor resolves through
// getLinkedGLAccountForLoanProduct).
//
// A charge-off CREDITS the principal to the loan portfolio, the interest to
// interest-receivable, the fee to fees-receivable and the penalty to
// penalties-receivable. It DEBITS the principal to the fraud expense account
// when the loan is marked fraud and to the ordinary charge-off expense account
// otherwise; it debits the interest, fee and penalty to the three
// income-from-charge-off accounts
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:930-975].
type ChargeOffAccountMapping struct {
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
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// debited with the principal portion of a NON-fraud charge-off.
	ChargeOffExpense string
	// ChargeOffFraudExpense is the
	// AccrualAccountsForLoan.CHARGE_OFF_FRAUD_EXPENSE slot, debited with the
	// principal portion of a FRAUD charge-off.
	ChargeOffFraudExpense string
	// IncomeFromChargeOffInterest is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_INTEREST slot, debited
	// with the interest portion.
	IncomeFromChargeOffInterest string
	// IncomeFromChargeOffFees is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_FEES slot, debited with
	// the fee portion.
	IncomeFromChargeOffFees string
	// IncomeFromChargeOffPenalty is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_PENALTY slot, debited
	// with the penalty portion.
	IncomeFromChargeOffPenalty string
	// ChargeOffReason is the account an advanced (charge-off-reason) mapping
	// would substitute. The loan slice has NOT observed that branch, so a
	// non-empty value is refused rather than guessed
	// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:900-929].
	ChargeOffReason string
}

// chargeOffSlot is one credit/debit pair in the processor's fixed visitation
// order. creditAccount receives the amount as a CREDIT; debitAccount receives it
// as a DEBIT.
type chargeOffSlot struct {
	name          string
	amount        MinorUnits
	creditAccount string
	debitAccount  string
}

// CreateChargeOffJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeOff
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:890-975, pinned commit
// 426a23544]. It is a pure function: portions (integer minor units), the loan's
// fraud flag and a slot->account mapping in, journal-entry legs out — no clock,
// no I/O, no stored balance.
//
// It visits the four slots in the processor's order (principal, interest, fees,
// penalties) and, for every slot whose portion is > 0:
//
//   - credits the slot's receivable/portfolio account, MERGING into the first
//     slot that already named the same account (the LinkedHashMap accountMap),
//     so two portion slots that resolve to one GL account post ONE credit for
//     their sum at the first slot's position;
//   - debits the slot's expense/income account (the fraud expense account for
//     the principal when fraud is set), MERGING the same way.
//
// It then posts every credit in insertion order, followed by every debit in
// insertion order. The credits come first and the debits after: the observed
// non-fraud charge-off reads two credits (portfolio 100000, receivable 14300)
// then three debits (expense 100000, interest 3000, fee/penalty 11300).
//
// It refuses, rather than inventing, a charge-off-reason mapping (never
// observed), a negative portion (never a genuine discharge), a positive portion
// whose slot maps to no account, and a positive portion whose credit and debit
// accounts are both unmapped.
func CreateChargeOffJournalEntryLegs(transactionID string, portions ChargeOffPortions, fraud bool, mapping ChargeOffAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: charge-off journal entries need a transaction id")
	}
	if mapping.ChargeOffReason != "" {
		return nil, fmt.Errorf("loan: charge-off journal entries refuse a charge-off-reason mapping %q: that branch is not observed", mapping.ChargeOffReason)
	}

	principalDebit := mapping.ChargeOffExpense
	if fraud {
		principalDebit = mapping.ChargeOffFraudExpense
	}

	slots := []chargeOffSlot{
		{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio, principalDebit},
		{"INTEREST_RECEIVABLE", portions.Interest, mapping.InterestReceivable, mapping.IncomeFromChargeOffInterest},
		{"FEES_RECEIVABLE", portions.Fee, mapping.FeesReceivable, mapping.IncomeFromChargeOffFees},
		{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.PenaltiesReceivable, mapping.IncomeFromChargeOffPenalty},
	}

	// accountMaps are LinkedHashMaps: ordered sets of accounts keyed by the
	// account, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var creditOrder, debitOrder []string
	creditByAccount := map[string]MinorUnits{}
	debitByAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: charge-off slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.creditAccount == "" {
			return nil, fmt.Errorf("loan: charge-off slot %s has a positive portion %d but no mapped credit account", s.name, s.amount)
		}
		if s.debitAccount == "" {
			return nil, fmt.Errorf("loan: charge-off slot %s has a positive portion %d but no mapped debit account", s.name, s.amount)
		}
		if _, seen := creditByAccount[s.creditAccount]; !seen {
			creditOrder = append(creditOrder, s.creditAccount)
		}
		creditByAccount[s.creditAccount] += s.amount
		if _, seen := debitByAccount[s.debitAccount]; !seen {
			debitOrder = append(debitOrder, s.debitAccount)
		}
		debitByAccount[s.debitAccount] += s.amount
	}

	legs := make([]JournalEntryLeg, 0, len(creditOrder)+len(debitOrder))
	for _, account := range creditOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryCredit,
			Amount:        creditByAccount[account],
		})
	}
	for _, account := range debitOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        debitByAccount[account],
		})
	}
	return legs, nil
}
