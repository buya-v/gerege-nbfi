package loan

import "fmt"

// GoodwillCreditAccountMapping is the GL account each goodwill-credit portion
// slot touches for one loan product: the five credit slots (shared with an
// ordinary repayment) and the four goodwill debit slots the processor's
// debitAccountMapForGoodwillCredit resolves [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544].
//
// The CREDIT side is identical to an ordinary repayment: the principal portion
// credits LOAN_PORTFOLIO, interest credits INTEREST_RECEIVABLE, fees credit
// FEES_RECEIVABLE, penalties credit PENALTIES_RECEIVABLE and overpayment credits
// OVERPAYMENT, portions that resolve to the SAME account MERGING into one credit
// at the first slot's position (the processor's creditBalances is a
// LinkedHashMap) [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1720-1780].
//
// The DEBIT side is the goodwill-credit arm's own table, not a fund source: the
// principal portion debits GOODWILL_CREDIT, interest debits
// INCOME_FROM_GOODWILL_CREDIT_INTEREST, fees debit
// INCOME_FROM_GOODWILL_CREDIT_FEES, penalties debit
// INCOME_FROM_GOODWILL_CREDIT_PENALTY and overpayment debits GOODWILL_CREDIT
// again, merging with the principal debit when the product maps them to the
// same account (the processor's debitAccountMap is populated in slot order by
// LoanCommonAccountingHelper.populateDebitAccountEntry, which merges a portion
// into an existing entry whose GL account matches) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544].
//
// Every account is an id string, never a balance-named field: the caller reads
// them back from the product's accountingMappings and the port never invents
// one.
type GoodwillCreditAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, credited
	// with the principal portion.
	LoanPortfolio string
	// ReceivableInterest is the AccrualAccountsForLoan.RECEIVABLE_INTEREST slot,
	// credited with the interest portion.
	ReceivableInterest string
	// ReceivableFee is the AccrualAccountsForLoan.RECEIVABLE_FEE slot, credited
	// with the fee portion.
	ReceivableFee string
	// ReceivablePenalty is the AccrualAccountsForLoan.RECEIVABLE_PENALTY slot,
	// credited with the penalty portion.
	ReceivablePenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion.
	Overpayment string
	// GoodwillCredit is the AccrualAccountsForLoan.GOODWILL_CREDIT slot, debited
	// with the principal and overpayment portions (which merge when it is the
	// same account for both).
	GoodwillCredit string
	// IncomeFromGoodwillCreditInterest is the
	// AccrualAccountsForLoan.INCOME_FROM_GOODWILL_CREDIT_INTEREST slot, debited
	// with the interest portion.
	IncomeFromGoodwillCreditInterest string
	// IncomeFromGoodwillCreditFees is the
	// AccrualAccountsForLoan.INCOME_FROM_GOODWILL_CREDIT_FEES slot, debited with
	// the fee portion.
	IncomeFromGoodwillCreditFees string
	// IncomeFromGoodwillCreditPenalty is the
	// AccrualAccountsForLoan.INCOME_FROM_GOODWILL_CREDIT_PENALTY slot, debited
	// with the penalty portion.
	IncomeFromGoodwillCreditPenalty string
}

// CreateGoodwillCreditJournalEntryLegs ports the GOODWILL-CREDIT branch of
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanRepayments
// on a loan that is NOT charged off [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544]. It is a pure function: the transaction's five portions (integer
// minor units), the loan's charged-off state and the slot->account mapping in,
// journal-entry legs out — no clock, no I/O, no stored balance.
//
// It CREDITS exactly as an ordinary repayment: it visits the five slots in the
// processor's order (principal, interest, fees, penalties, overpayment) and for
// every slot whose portion is > 0 credits the slot's mapped account, MERGING
// into the first slot that already named the same account. It then DEBITs the
// same portions through the goodwill table — principal and overpayment to
// GOODWILL_CREDIT, interest to INCOME_FROM_GOODWILL_CREDIT_INTEREST, fees to
// INCOME_FROM_GOODWILL_CREDIT_FEES, penalties to
// INCOME_FROM_GOODWILL_CREDIT_PENALTY — merging debits that resolve to the same
// account, and posts every debit AFTER every credit in insertion order. A
// goodwill credit is NOT a transfer: no fund source is posted.
//
// This port models the NOT-charged-off goodwill arm only. The charged-off
// goodwill arm is a different method (createJournalEntriesForRepaymentWhenLoanIsChargedOff)
// and is NOT observed here: the port REFUSES a chargedOff input rather than
// guessing that arm.
//
// It refuses, rather than inventing, a negative portion, a positive portion
// whose slot maps to no credit account or no debit account, and a charged-off
// loan.
func CreateGoodwillCreditJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff bool, mapping GoodwillCreditAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: goodwill-credit journal entries need a transaction id")
	}
	if chargedOff {
		return nil, fmt.Errorf("loan: goodwill-credit journal entries refuse a charged-off loan")
	}

	// credits carry the repayment's five slots; debits carry the goodwill arm's
	// own five slots (principal and overpayment share GOODWILL_CREDIT).
	credits := []repaymentSlot{
		{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
		{"INTEREST_RECEIVABLE", portions.Interest, mapping.ReceivableInterest},
		{"FEES_RECEIVABLE", portions.Fee, mapping.ReceivableFee},
		{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.ReceivablePenalty},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}
	debits := []repaymentSlot{
		{"GOODWILL_CREDIT", portions.Principal, mapping.GoodwillCredit},
		{"INCOME_FROM_GOODWILL_CREDIT_INTEREST", portions.Interest, mapping.IncomeFromGoodwillCreditInterest},
		{"INCOME_FROM_GOODWILL_CREDIT_FEES", portions.Fee, mapping.IncomeFromGoodwillCreditFees},
		{"INCOME_FROM_GOODWILL_CREDIT_PENALTY", portions.Penalty, mapping.IncomeFromGoodwillCreditPenalty},
		{"GOODWILL_CREDIT", portions.Overpayment, mapping.GoodwillCredit},
	}

	// A positive portion needs BOTH sides mapped, so a negative portion is
	// refused once per side and a half-mapped slot never posts an unbalanced leg.
	if err := checkGoodwillPortions(credits, "credit"); err != nil {
		return nil, err
	}
	if err := checkGoodwillPortions(debits, "debit"); err != nil {
		return nil, err
	}

	legs := make([]JournalEntryLeg, 0, len(credits)+len(debits))
	legs = appendMergedLegs(legs, transactionID, JournalEntryCredit, credits)
	legs = appendMergedLegs(legs, transactionID, JournalEntryDebit, debits)
	return legs, nil
}

// checkGoodwillPortions refuses a negative portion and a positive portion whose
// slot maps to no account. The two sides are validated separately so the error
// names the side that is missing the mapping; a negative portion is refused on
// whichever side is checked, so it surfaces as a data error not a zero.
func checkGoodwillPortions(slots []repaymentSlot, side string) error {
	for _, s := range slots {
		if s.amount < 0 {
			return fmt.Errorf("loan: goodwill-credit %s slot %s carries a negative portion %d", side, s.name, s.amount)
		}
		if s.amount > 0 && s.account == "" {
			return fmt.Errorf("loan: goodwill-credit %s slot %s has a positive portion %d but no mapped account", side, s.name, s.amount)
		}
	}
	return nil
}

// appendMergedLegs posts one leg per distinct account in the slots' order,
// merging slots that resolve to the same account at the FIRST slot's position
// (the processor's LinkedHashMap), and appends them to legs.
func appendMergedLegs(legs []JournalEntryLeg, transactionID string, side JournalEntrySide, slots []repaymentSlot) []JournalEntryLeg {
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount == 0 {
			continue
		}
		if _, seen := byAccount[s.account]; !seen {
			order = append(order, s.account)
		}
		byAccount[s.account] += s.amount
	}
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          side,
			Amount:        byAccount[account],
		})
	}
	return legs
}
