package loan

import "fmt"

// InterestPaymentWaiverAccountMapping is the GL account each portion slot of an
// interest-payment waiver CREDITS for one loan product, plus the single account
// every portion DEBITS, as the processor resolves them [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:793-889, pinned commit 426a23544].
//
// The port models the TWO observed branches of
// createJournalEntriesForInterestPaymentWaiverOrInterestRefund that the
// interestPaymentWaiver transaction type reaches, switched by the loan's
// charged-off state:
//
//   - loan NOT charged off: principal credits LoanPortfolio,
//     interest credits ReceivableInterest, fees credit ReceivableFee, penalties
//     credit ReceivablePenalty and overpayment credits Overpayment;
//   - loan CHARGED OFF: principal, interest, fees AND penalties all credit
//     IncomeFromChargeOffInterest, while overpayment still credits Overpayment.
//
// In BOTH branches every portion debits InterestOnLoan, merged into one total
// debit. Portions that resolve to the SAME account MERGE into one credit at the
// first slot's position (the processor's accountMap is a LinkedHashMap, and the
// charged-off branch deliberately routes four slots onto one account).
//
// The interest-refund arm shares the Java method but is NOT this port: its
// transaction type and account slots are not observed.
type InterestPaymentWaiverAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, credited
	// with the principal portion when the loan is NOT charged off.
	LoanPortfolio string
	// ReceivableInterest is the AccrualAccountsForLoan.RECEIVABLE_INTEREST slot,
	// credited with the interest portion when the loan is NOT charged off.
	ReceivableInterest string
	// ReceivableFee is the AccrualAccountsForLoan.RECEIVABLE_FEE slot, credited
	// with the fee portion when the loan is NOT charged off.
	ReceivableFee string
	// ReceivablePenalty is the AccrualAccountsForLoan.RECEIVABLE_PENALTY slot,
	// credited with the penalty portion when the loan is NOT charged off.
	ReceivablePenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion in both branches.
	Overpayment string
	// InterestOnLoan is the AccrualAccountsForLoan.INTEREST_ON_LOANS slot,
	// debited ONCE with the sum of every portion in both branches.
	InterestOnLoan string
	// IncomeFromChargeOffInterest is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_INTEREST slot, credited with
	// a positive principal, interest, fee or penalty portion when the loan IS
	// charged off.
	IncomeFromChargeOffInterest string
}

// interestPaymentWaiverSlot is one portion/account pair in the processor's fixed
// visitation order.
type interestPaymentWaiverSlot struct {
	name          string
	amount        MinorUnits
	creditAccount string
}

// CreateInterestPaymentWaiverJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForInterestPaymentWaiverOrInterestRefund
// for the INTEREST_PAYMENT_WAIVER transaction type [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:793-889, pinned commit 426a23544].
// It is a pure function: the transaction's five portions (integer minor units),
// the loan's charged-off state and the resolved slot->account mapping in,
// journal-entry legs out — no clock, no I/O, no stored balance.
//
// It visits the five slots in the processor's order (principal, interest, fees,
// penalties, overpayment). For every slot whose portion is > 0 it CREDITS that
// slot's account for the loan's branch, MERGING into the first slot that named
// the same account (the LinkedHashMap accountMap), so a charged-off loan merges
// all four principal/interest/fee/penalty portions into ONE
// income-from-charge-off-interest credit. It then posts ONE DEBIT of the total
// to InterestOnLoan. The credits come first, in insertion order, and the single
// debit is last.
//
// The account ids are the product's accountingMappings read back from the
// reference server, never invented. The port refuses, rather than guessing, a
// negative portion, a positive portion whose slot maps to no credit account, and
// a positive total with no interest-on-loan account.
func CreateInterestPaymentWaiverJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff bool, mapping InterestPaymentWaiverAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: interest-payment-waiver journal entries need a transaction id")
	}

	var slots []interestPaymentWaiverSlot
	if chargedOff {
		slots = []interestPaymentWaiverSlot{
			{"LOAN_PORTFOLIO", portions.Principal, mapping.IncomeFromChargeOffInterest},
			{"INTEREST_RECEIVABLE", portions.Interest, mapping.IncomeFromChargeOffInterest},
			{"FEES_RECEIVABLE", portions.Fee, mapping.IncomeFromChargeOffInterest},
			{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.IncomeFromChargeOffInterest},
			{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
		}
	} else {
		slots = []interestPaymentWaiverSlot{
			{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
			{"INTEREST_RECEIVABLE", portions.Interest, mapping.ReceivableInterest},
			{"FEES_RECEIVABLE", portions.Fee, mapping.ReceivableFee},
			{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.ReceivablePenalty},
			{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
		}
	}

	// order/byAccount model the processor's LinkedHashMap: an ordered set of
	// accounts, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: interest-payment-waiver slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.creditAccount == "" {
			return nil, fmt.Errorf("loan: interest-payment-waiver slot %s has a positive portion %d but no mapped account", s.name, s.amount)
		}
		if _, seen := byAccount[s.creditAccount]; !seen {
			order = append(order, s.creditAccount)
		}
		byAccount[s.creditAccount] += s.amount
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
	if mapping.InterestOnLoan == "" {
		return nil, fmt.Errorf("loan: interest-payment-waiver total %d has no interest-on-loan account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.InterestOnLoan,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
