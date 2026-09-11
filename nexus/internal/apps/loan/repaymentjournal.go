package loan

import "fmt"

// RepaymentPortions is the money an ordinary loan repayment applies per ledger
// slot, in integer minor units. It is the Go port of the five BigDecimal fields
// createJournalEntriesForLoanRepayments reads off the repayment transaction —
// principalPortion, interestPortion, feeChargesPortion, penaltyChargesPortion
// and overpaymentPortion [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544].
//
// A slot is credited only when its portion is > 0 (MathUtil.isGreaterThanZero);
// a zero portion contributes neither an amount nor an account to the posting.
// Every field is an integer MinorUnits value: no float and no sub-minor residue
// can enter this path (G-19 / DEC-2 G-08).
type RepaymentPortions struct {
	Principal   MinorUnits
	Interest    MinorUnits
	Fee         MinorUnits
	Penalty     MinorUnits
	Overpayment MinorUnits
}

// Total returns the sum of every portion, in integer minor units. It is the
// amount of the ONE debit an ordinary repayment posts to the fund source.
func (p RepaymentPortions) Total() MinorUnits {
	return p.Principal + p.Interest + p.Fee + p.Penalty + p.Overpayment
}

// RepaymentAccountMapping is the GL account each repayment portion slot CREDITS
// for one loan product, plus the RESOLVED fund source the single total debit
// posts to, as the processor resolves them [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned commit
// 426a23544].
//
// The principal portion credits LOAN_PORTFOLIO, the interest, fee and penalty
// portions credit the corresponding receivable accounts and the overpayment
// portion credits OVERPAYMENT; portions that resolve to the SAME account MERGE
// into one credit at the first slot's position (the processor's accountMap is a
// LinkedHashMap) [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1720-1850].
//
// FundSource is the RESOLVED fund-source account: the transaction's
// paymentTypeId payment-channel account when the product maps that channel, else
// the product's FUND_SOURCE slot. The caller resolves the channel; this port
// carries only the already-resolved account, so it needs no payment-type lookup
// and no product state.
type RepaymentAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, credited
	// with the principal portion.
	LoanPortfolio string
	// ReceivableInterest is the AccrualAccountsForLoan.RECEIVABLE_INTEREST
	// slot, credited with the interest portion.
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
	// FundSource is the RESOLVED AccrualAccountsForLoan.FUND_SOURCE slot, debited
	// ONCE with the sum of every portion.
	FundSource string
}

// repaymentSlot is one portion/account pair in the processor's fixed visitation
// order.
type repaymentSlot struct {
	name    string
	amount  MinorUnits
	account string
}

// CreateRepaymentJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanRepayments
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1695-1871, pinned
// commit 426a23544]. It is a pure function: the repayment transaction's five
// portions (integer minor units) and the resolved slot->account mapping in,
// journal-entry legs out — no clock, no I/O, no stored balance.
//
// It visits the five slots in the processor's order (principal, interest, fees,
// penalties, overpayment), and for every slot whose portion is > 0 CREDITS the
// slot's mapped account, MERGING into the first slot that already named the
// same account (the LinkedHashMap accountMap), so two portion slots that resolve
// to one GL account post ONE credit for their sum at the first slot's position.
// It then posts ONE DEBIT of the total to the resolved fund-source account. The
// debit is LAST: the credits are posted in insertion order and the single debit
// follows them.
//
// This port models the ORDINARY repayment branch only. The processor's other
// branches — goodwill credit, a loan-to-loan or account transfer, repayment at
// disbursement (isIncomeFromFee), a charge refund, tax — are NOT observed here
// and have NO input: the caller cannot express them, so the port never guesses
// them.
//
// It refuses, rather than inventing, a negative portion, a positive portion
// whose slot maps to no account, and a positive total with no fund-source
// account.
func CreateRepaymentJournalEntryLegs(transactionID string, portions RepaymentPortions, mapping RepaymentAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: repayment journal entries need a transaction id")
	}

	slots := []repaymentSlot{
		{"LOAN_PORTFOLIO", portions.Principal, mapping.LoanPortfolio},
		{"INTEREST_RECEIVABLE", portions.Interest, mapping.ReceivableInterest},
		{"FEES_RECEIVABLE", portions.Fee, mapping.ReceivableFee},
		{"PENALTIES_RECEIVABLE", portions.Penalty, mapping.ReceivablePenalty},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}

	// order/byAccount model the processor's LinkedHashMap: an ordered set of
	// accounts, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: repayment slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.account == "" {
			return nil, fmt.Errorf("loan: repayment slot %s has a positive portion %d but no mapped account", s.name, s.amount)
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
	if mapping.FundSource == "" {
		return nil, fmt.Errorf("loan: repayment total %d has no fund-source account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.FundSource,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
