package loan

import "fmt"

// GoodwillCreditAccountMapping is the GL account each goodwill-credit portion
// slot touches for one loan product: the five credit slots (shared with an
// ordinary repayment) and the four goodwill debit slots the processor's
// debitAccountMapForGoodwillCredit resolves [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544].
//
// The CREDIT side is identical to an ordinary repayment on a loan that is NOT
// charged off: the principal portion credits LOAN_PORTFOLIO, interest credits
// INTEREST_RECEIVABLE, fees credit FEES_RECEIVABLE, penalties credit
// PENALTIES_RECEIVABLE and overpayment credits OVERPAYMENT, portions that
// resolve to the SAME account MERGING into one credit at the first slot's
// position (the processor's creditBalances is a LinkedHashMap) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1720-1780]. On a CHARGED-OFF loan
// the same four non-overpayment portions instead credit INCOME_FROM_RECOVERY
// (merging into one credit at the principal slot) and only overpayment keeps its
// own account [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1433-1435,
// 1461-1464, 1491-1493, 1529-1532, 1564-1566, pinned commit 426a23544].
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
	// IncomeFromRecovery is the AccrualAccountsForLoan.INCOME_FROM_RECOVERY slot,
	// credited with the principal, interest, fee and penalty portions on a
	// CHARGED-OFF loan (they merge into one credit at the principal slot). It is
	// not read on a loan that is not charged off.
	IncomeFromRecovery string
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
// on a loan that is NOT charged off and of
// createJournalEntriesForRepaymentWhenLoanIsChargedOff when it is [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1369-1376, 1695-1871, pinned
// commit 426a23544]. It is a pure function: the transaction's five portions
// (integer minor units), the loan's charged-off state and the slot->account
// mapping in, journal-entry legs out — no clock, no I/O, no stored balance.
//
// It CREDITS the five slots in the processor's order (principal, interest,
// fees, penalties, overpayment) and for every slot whose portion is > 0 credits
// the slot's mapped account, MERGING into the first slot that already named the
// same account. On a loan that is NOT charged off the four non-overpayment
// slots credit LOAN_PORTFOLIO, INTEREST_RECEIVABLE, FEES_RECEIVABLE and
// PENALTIES_RECEIVABLE and overpayment credits OVERPAYMENT, exactly as an
// ordinary repayment. On a CHARGED-OFF loan the four non-overpayment slots
// instead credit INCOME_FROM_RECOVERY (merging into one credit at the principal
// slot) and overpayment still credits OVERPAYMENT. The goodwill branch does NOT
// read the fraud flag.
//
// It then DEBITs the same portions through the goodwill table — principal and
// overpayment to GOODWILL_CREDIT, interest to
// INCOME_FROM_GOODWILL_CREDIT_INTEREST, fees to
// INCOME_FROM_GOODWILL_CREDIT_FEES, penalties to
// INCOME_FROM_GOODWILL_CREDIT_PENALTY — merging debits that resolve to the same
// account, and posts every debit AFTER every credit in insertion order. The
// debit table is the same in both arms. A goodwill credit is NOT a transfer: no
// fund source is posted.
//
// It refuses, rather than inventing, a negative portion and a positive portion
// whose slot maps to no credit account or no debit account. On a charged-off
// loan the principal, interest, fee and penalty credits all need
// INCOME_FROM_RECOVERY, so a positive one of those with no recovery mapping is
// refused.
func CreateGoodwillCreditJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff bool, mapping GoodwillCreditAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: goodwill-credit journal entries need a transaction id")
	}

	// credits carry the repayment's five slots: the portfolio/receivables on a
	// loan that is NOT charged off, the recovery account (with overpayment still
	// separate) on a charged-off loan. debits carry the goodwill arm's own five
	// slots (principal and overpayment share GOODWILL_CREDIT) in both arms.
	var credits []repaymentSlot
	if chargedOff {
		credits = []repaymentSlot{
			{"INCOME_FROM_RECOVERY", portions.Principal, mapping.IncomeFromRecovery},
			{"INCOME_FROM_RECOVERY", portions.Interest, mapping.IncomeFromRecovery},
			{"INCOME_FROM_RECOVERY", portions.Fee, mapping.IncomeFromRecovery},
			{"INCOME_FROM_RECOVERY", portions.Penalty, mapping.IncomeFromRecovery},
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
