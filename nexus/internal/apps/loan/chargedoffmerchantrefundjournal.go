package loan

import "fmt"

// ChargedOffMerchantRefundAccountMapping is the GL account each portion slot
// CREDITS when a MERCHANT-ISSUED REFUND or a PAYOUT REFUND posts on a loan
// ALREADY MARKED CHARGED OFF, plus the RESOLVED fund source every debit posts to
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1388-1615, pinned
// commit 426a23544].
//
// The refund arm of the charged-off dispatch credits the charge-off
// income/expense slots the earlier charge-off DEBITED: the principal portion
// credits CHARGE_OFF_FRAUD_EXPENSE when the loan is FRAUD and CHARGE_OFF_EXPENSE
// otherwise, the interest portion INCOME_FROM_CHARGE_OFF_INTEREST, the fees
// portion INCOME_FROM_CHARGE_OFF_FEES and the penalties portion
// INCOME_FROM_CHARGE_OFF_PENALTY; the overpayment portion credits OVERPAYMENT.
// Portions that resolve to the SAME account MERGE into one credit at the first
// slot's position (the processor's creditBalances is a LinkedHashMap).
//
// FundSource is the RESOLVED fund-source account: the transaction's
// paymentTypeId payment-channel account when the product maps that channel, else
// the product's FUND_SOURCE slot. The caller resolves the channel; this port
// carries only the already-resolved account. Every portion debits this same
// account, so the processor's debit map merges them into ONE debit.
type ChargedOffMerchantRefundAccountMapping struct {
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// credited with the principal portion of a NON-fraud loan.
	ChargeOffExpense string
	// ChargeOffFraudExpense is the AccrualAccountsForLoan.CHARGE_OFF_FRAUD_EXPENSE
	// slot, credited with the principal portion when the loan is FRAUD.
	ChargeOffFraudExpense string
	// IncomeFromChargeOffInterest is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_INTEREST slot, credited with
	// the interest portion.
	IncomeFromChargeOffInterest string
	// IncomeFromChargeOffFees is the AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_FEES
	// slot, credited with the fees portion.
	IncomeFromChargeOffFees string
	// IncomeFromChargeOffPenalty is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_PENALTY slot, credited with
	// the penalties portion.
	IncomeFromChargeOffPenalty string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion.
	Overpayment string
	// FundSource is the RESOLVED AccrualAccountsForLoan.FUND_SOURCE slot, debited
	// ONCE with the sum of every portion. Every portion debits this same account,
	// so the processor's debit map merges them too.
	FundSource string
}

// CreateChargedOffMerchantRefundJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForRepaymentWhenLoanIsChargedOff for a MERCHANT-ISSUED
// REFUND or a PAYOUT REFUND [VERIFIED: AccrualBasedAccountingProcessorForLoan
// .java:1388-1615, dispatch :1369-1377, pinned commit 426a23544]. It is a pure
// function: the refund transaction's type and five portions (integer minor
// units), the loan's fraud flag and the resolved slot->account mapping in,
// journal-entry legs out — no clock, no I/O, no stored balance.
//
// The two refund arms post IDENTICALLY: the method dispatches both
// MERCHANT_ISSUED_REFUND and PAYOUT_REFUND to this one branch, so the
// transaction type selects admission only and never changes a leg. It visits the
// slots in the processor's order (principal, interest, fees, penalties,
// overpayment). For every slot whose portion is > 0 it CREDITS that slot's
// charge-off account — principal to CHARGE_OFF_FRAUD_EXPENSE when the loan is
// fraud else CHARGE_OFF_EXPENSE, interest/fees/penalties to the matching
// INCOME_FROM_CHARGE_OFF_* slot, overpayment to OVERPAYMENT — MERGING into the
// first slot that already named that account. It then posts ONE DEBIT of the
// total to the resolved fund-source account. The credits are posted first (in
// insertion order) and the single debit follows them.
//
// The transactionType must be TransactionMerchantIssuedRefund or
// TransactionPayoutRefund; every other kind (the method's goodwill-credit arm and
// else branch, which have a different account table) is REFUSED rather than
// guessed.
//
// It refuses, rather than inventing, an unknown transaction kind, a negative
// portion, a positive portion whose slot maps to no account, and a positive
// total with no fund-source account.
func CreateChargedOffMerchantRefundJournalEntryLegs(transactionID string, transactionType LoanTransactionType, portions RepaymentPortions, fraud bool, mapping ChargedOffMerchantRefundAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: charged-off refund journal entries need a transaction id")
	}
	if !transactionType.IsMerchantIssuedRefund() && !transactionType.IsPayoutRefund() {
		return nil, fmt.Errorf("loan: charged-off refund journal entries accept only a merchant-issued refund or a payout refund, got %s", transactionType)
	}

	principalAccount := mapping.ChargeOffExpense
	principalSlot := "CHARGE_OFF_EXPENSE"
	if fraud {
		principalAccount = mapping.ChargeOffFraudExpense
		principalSlot = "CHARGE_OFF_FRAUD_EXPENSE"
	}

	slots := []repaymentSlot{
		{principalSlot, portions.Principal, principalAccount},
		{"INCOME_FROM_CHARGE_OFF_INTEREST", portions.Interest, mapping.IncomeFromChargeOffInterest},
		{"INCOME_FROM_CHARGE_OFF_FEES", portions.Fee, mapping.IncomeFromChargeOffFees},
		{"INCOME_FROM_CHARGE_OFF_PENALTY", portions.Penalty, mapping.IncomeFromChargeOffPenalty},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}

	// order/byAccount model the processor's LinkedHashMap: an ordered set of
	// accounts, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: charged-off refund slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.account == "" {
			return nil, fmt.Errorf("loan: charged-off refund slot %s has a positive portion %d but no mapped account", s.name, s.amount)
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
		return nil, fmt.Errorf("loan: charged-off refund total %d has no fund-source account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.FundSource,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
