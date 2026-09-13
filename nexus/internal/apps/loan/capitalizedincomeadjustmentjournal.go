package loan

import "fmt"

// CapitalizedIncomeAdjustmentAccountMapping is the GL account each
// capitalized-income-adjustment portion slot touches for one loan product:
// where the five portion slots CREDIT and the single DEFERRED_INCOME_LIABILITY
// account the transaction amount DEBITS [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:232-306, pinned commit
// 426a23544].
//
// Unlike a charge adjustment the credit side has NO charged-off arm: the
// processor resolves every slot through getLinkedGLAccountForLoanProduct with
// the slot's AccrualAccountsForLoan value and credits principal to
// LOAN_PORTFOLIO, interest to INTEREST_RECEIVABLE, fees to FEES_RECEIVABLE,
// penalties to PENALTIES_RECEIVABLE and overpayment to OVERPAYMENT. Portions
// that resolve to the SAME account MERGE into one credit at the first slot's
// position (the processor's accountMap is a LinkedHashMap) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:248-279].
//
// The DEBIT side is ONE leg of the transaction AMOUNT — not of the summed
// portions — posted AFTER every credit to DEFERRED_INCOME_LIABILITY [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:280-292]. The Java never
// reconciles the amount against the portions, so a transaction whose portions
// do not sum to its amount would post a batch whose credits and debit differ;
// this port refuses that mismatch rather than reproducing an unbalanced
// posting, and the observations never exercise it.
//
// Every account is an id string, never a balance-named field: the caller reads
// them back from the product's accountingMappings and the port never invents
// one.
type CapitalizedIncomeAdjustmentAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, credited
	// with the principal portion.
	LoanPortfolio string
	// ReceivableInterest is the AccrualAccountsForLoan.INTEREST_RECEIVABLE slot,
	// credited with the interest portion.
	ReceivableInterest string
	// ReceivableFee is the AccrualAccountsForLoan.FEES_RECEIVABLE slot, credited
	// with the fee portion.
	ReceivableFee string
	// ReceivablePenalty is the AccrualAccountsForLoan.PENALTIES_RECEIVABLE slot,
	// credited with the penalty portion.
	ReceivablePenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion.
	Overpayment string
	// DeferredIncomeLiability is the
	// AccrualAccountsForLoan.DEFERRED_INCOME_LIABILITY slot, debited ONCE with
	// the transaction amount.
	DeferredIncomeLiability string
}

// CreateCapitalizedIncomeAdjustmentJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForCapitalizedIncomeAdjustment [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:232-306, pinned commit
// 426a23544]. It is a pure function: the adjustment transaction's amount and
// five portions (integer minor units) and the slot->account mapping in,
// journal-entry legs out — no clock, no I/O, no stored balance.
//
// When the amount is greater than zero it CREDITS one leg per non-zero portion
// slot in the processor's fixed order (principal, interest, fees, penalties,
// overpayment), merging slots that resolve to the same account at the first
// slot's position, then posts exactly ONE DEBIT of the transaction AMOUNT,
// after every credit, to DEFERRED_INCOME_LIABILITY.
//
// It refuses, rather than inventing, a negative amount, a negative portion, a
// positive portion whose slot maps to no credit account, a positive amount
// whose DEFERRED_INCOME_LIABILITY account is unmapped, and portions whose sum
// differs from the amount. The last is a strictness the Java does not have
// (the Java never reconciles them); it is refused so the port cannot post an
// unbalanced batch, and no observation exercises it.
func CreateCapitalizedIncomeAdjustmentJournalEntryLegs(transactionID string, amount MinorUnits, portions RepaymentPortions, mapping CapitalizedIncomeAdjustmentAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: capitalized-income-adjustment journal entries need a transaction id")
	}
	if amount < 0 {
		return nil, fmt.Errorf("loan: capitalized-income-adjustment amount %d is negative", amount)
	}

	// The credit side is fixed: there is no charged-off arm, so every slot
	// credits its receivable/portfolio account.
	credits := []repaymentSlot{
		{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
		{"INTEREST_RECEIVABLE", portions.Interest, mapping.ReceivableInterest},
		{"FEES_RECEIVABLE", portions.Fee, mapping.ReceivableFee},
		{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.ReceivablePenalty},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}
	if err := checkCapitalizedIncomeAdjustmentCredits(credits); err != nil {
		return nil, err
	}

	// The debit is the transaction AMOUNT, not the summed portions: the Java
	// passes transactionAmount to addToDebit unconditionally once it is
	// positive. Refuse a mismatch instead of posting an unbalanced batch.
	total := portions.Total()
	if total != amount {
		return nil, fmt.Errorf("loan: capitalized-income-adjustment portions sum to %d but the transaction amount is %d", total, amount)
	}
	if amount > 0 && mapping.DeferredIncomeLiability == "" {
		return nil, fmt.Errorf("loan: capitalized-income-adjustment has a positive amount %d but no mapped DEFERRED_INCOME_LIABILITY account", amount)
	}

	legs := make([]JournalEntryLeg, 0, len(credits)+1)
	legs = appendMergedLegs(legs, transactionID, JournalEntryCredit, credits)
	if amount > 0 {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.DeferredIncomeLiability,
			Side:          JournalEntryDebit,
			Amount:        amount,
		})
	}
	return legs, nil
}

// checkCapitalizedIncomeAdjustmentCredits refuses a negative portion and a
// positive portion whose slot maps to no credit account, so a half-mapped slot
// never posts an unbalanced leg.
func checkCapitalizedIncomeAdjustmentCredits(slots []repaymentSlot) error {
	for _, s := range slots {
		if s.amount < 0 {
			return fmt.Errorf("loan: capitalized-income-adjustment credit slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount > 0 && s.account == "" {
			return fmt.Errorf("loan: capitalized-income-adjustment credit slot %s has a positive portion %d but no mapped account", s.name, s.amount)
		}
	}
	return nil
}
