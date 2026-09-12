package loan

import "fmt"

// ChargeAdjustmentAccountMapping is the GL account each charge-adjustment
// portion slot touches for one loan product: where the five portions CREDIT
// (which depend on the loan's charged-off state) and the single income account
// the total DEBITS [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:997-1214, pinned commit
// 426a23544].
//
// On a loan that is NOT charged off the CREDIT side is the receivable side of an
// ordinary repayment: principal credits LOAN_PORTFOLIO, interest credits
// INTEREST_RECEIVABLE, fees credit FEES_RECEIVABLE, penalties credit
// PENALTIES_RECEIVABLE and overpayment credits OVERPAYMENT. On a loan that IS
// charged off the credit side moves to the charge-off income table: principal,
// interest and fees all credit INCOME_FROM_CHARGE_OFF_FEES, penalties credit
// INCOME_FROM_CHARGE_OFF_PENALTY and overpayment credits OVERPAYMENT. Portions
// that resolve to the SAME account MERGE into one credit at the first slot's
// position (the processor's accountMap is a LinkedHashMap) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1015-1083 and 1103-1203].
//
// The DEBIT side is ONE leg of the total: when the adjusted charge is a penalty
// the total debits INCOME_FROM_PENALTIES, else it debits INCOME_FROM_FEES,
// posted AFTER every credit [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1085-1103 and 1205-1214].
//
// The Java resolves that debit account through
// AccountingProcessorHelper.createDebitJournalEntryForLoanCharges, which calls
// getLinkedGLAccountForLoanCharges(loanProductId, accountType, chargeId) and can
// honour a CHARGE-SPECIFIC override. This port REFUSES that charge-level
// mapping: it takes the PRODUCT accounts only and carries no charge id, so a
// charge whose debit account would differ from the product's INCOME_FROM_FEES /
// INCOME_FROM_PENALTIES is not modelled.
//
// Every account is an id string, never a balance-named field: the caller reads
// them back from the product's accountingMappings and the port never invents
// one.
type ChargeAdjustmentAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, credited
	// with the principal portion on a loan that is NOT charged off.
	LoanPortfolio string
	// ReceivableInterest is the AccrualAccountsForLoan.RECEIVABLE_INTEREST slot,
	// credited with the interest portion on a loan that is NOT charged off.
	ReceivableInterest string
	// ReceivableFee is the AccrualAccountsForLoan.RECEIVABLE_FEE slot, credited
	// with the fee portion on a loan that is NOT charged off.
	ReceivableFee string
	// ReceivablePenalty is the AccrualAccountsForLoan.RECEIVABLE_PENALTY slot,
	// credited with the penalty portion on a loan that is NOT charged off.
	ReceivablePenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion on either arm.
	Overpayment string
	// IncomeFromChargeOffFees is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_FEES slot, credited with the
	// principal, interest and fee portions on a loan that IS charged off.
	IncomeFromChargeOffFees string
	// IncomeFromChargeOffPenalty is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_PENALTY slot, credited with
	// the penalty portion on a loan that IS charged off.
	IncomeFromChargeOffPenalty string
	// IncomeFromFees is the AccrualAccountsForLoan.INCOME_FROM_FEES slot, debited
	// ONCE with the total when the adjusted charge is NOT a penalty.
	IncomeFromFees string
	// IncomeFromPenalties is the AccrualAccountsForLoan.INCOME_FROM_PENALTIES
	// slot, debited ONCE with the total when the adjusted charge IS a penalty.
	IncomeFromPenalties string
}

// CreateChargeAdjustmentJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeAdjustment
// — the createJournalEntriesForLoanChargeAdjustment and
// createJournalEntriesForChargeOffLoanChargeAdjustment arms [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:997-1214, pinned commit
// 426a23544]. It is a pure function: the adjustment transaction's five portions
// (integer minor units), the loan's charged-off state, whether the adjusted
// charge is a penalty, and the slot->account mapping in, journal-entry legs out
// — no clock, no I/O, no stored balance, no charge id.
//
// It CREDITS one leg per non-zero portion slot in the processor's fixed order
// (principal, interest, fees, penalties, overpayment), merging slots that
// resolve to the same account at the first slot's position. The credit accounts
// depend on the charged-off state: NOT charged off credits the receivables
// (LOAN_PORTFOLIO, INTEREST_RECEIVABLE, FEES_RECEIVABLE, PENALTIES_RECEIVABLE,
// OVERPAYMENT); charged off credits principal, interest and fees to
// INCOME_FROM_CHARGE_OFF_FEES, penalties to INCOME_FROM_CHARGE_OFF_PENALTY and
// overpayment to OVERPAYMENT. It then posts exactly ONE DEBIT of the total,
// after every credit: INCOME_FROM_PENALTIES when the adjusted charge is a
// penalty, else INCOME_FROM_FEES.
//
// It refuses, rather than inventing, a negative portion, a positive portion
// whose slot maps to no credit account, and a positive total whose selected
// debit account is unmapped.
func CreateChargeAdjustmentJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff, penaltyCharge bool, mapping ChargeAdjustmentAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: charge-adjustment journal entries need a transaction id")
	}

	// The credit side moves from the receivables to the charge-off income table
	// when the loan is marked charged off; either arm has five portion slots.
	var credits []repaymentSlot
	if chargedOff {
		credits = []repaymentSlot{
			{"INCOME_FROM_CHARGE_OFF_FEES", portions.Principal, mapping.IncomeFromChargeOffFees},
			{"INCOME_FROM_CHARGE_OFF_FEES", portions.Interest, mapping.IncomeFromChargeOffFees},
			{"INCOME_FROM_CHARGE_OFF_FEES", portions.Fee, mapping.IncomeFromChargeOffFees},
			{"INCOME_FROM_CHARGE_OFF_PENALTY", portions.Penalty, mapping.IncomeFromChargeOffPenalty},
			{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
		}
	} else {
		credits = []repaymentSlot{
			{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
			{"INTEREST_RECEIVABLE", portions.Interest, mapping.ReceivableInterest},
			{"FEES_RECEIVABLE", portions.Fee, mapping.ReceivableFee},
			{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.ReceivablePenalty},
			{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
		}
	}

	if err := checkChargeAdjustmentCredits(credits); err != nil {
		return nil, err
	}

	// ONE debit of the total to the income table the adjusted charge selects:
	// penalties debit INCOME_FROM_PENALTIES, every other charge
	// INCOME_FROM_FEES. A positive total needs that account mapped.
	total := portions.Total()
	debitAccount, debitName := mapping.IncomeFromFees, "INCOME_FROM_FEES"
	if penaltyCharge {
		debitAccount, debitName = mapping.IncomeFromPenalties, "INCOME_FROM_PENALTIES"
	}
	if total > 0 && debitAccount == "" {
		return nil, fmt.Errorf("loan: charge-adjustment has a positive total %d but no mapped %s account", total, debitName)
	}

	legs := make([]JournalEntryLeg, 0, len(credits)+1)
	legs = appendMergedLegs(legs, transactionID, JournalEntryCredit, credits)
	if total > 0 {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       debitAccount,
			Side:          JournalEntryDebit,
			Amount:        total,
		})
	}
	return legs, nil
}

// checkChargeAdjustmentCredits refuses a negative portion and a positive portion
// whose slot maps to no credit account, so a half-mapped slot never posts an
// unbalanced leg.
func checkChargeAdjustmentCredits(slots []repaymentSlot) error {
	for _, s := range slots {
		if s.amount < 0 {
			return fmt.Errorf("loan: charge-adjustment credit slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount > 0 && s.account == "" {
			return fmt.Errorf("loan: charge-adjustment credit slot %s has a positive portion %d but no mapped account", s.name, s.amount)
		}
	}
	return nil
}
