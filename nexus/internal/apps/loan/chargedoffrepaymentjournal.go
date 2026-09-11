package loan

import "fmt"

// ChargedOffRepaymentAccountMapping is the GL account each repayment portion
// slot CREDITS when the loan is ALREADY MARKED CHARGED OFF, plus the RESOLVED
// fund source every debit posts to [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1388-1615, pinned commit
// 426a23544].
//
// On a charged-off loan the processor's repayment arm sends EVERY positive
// principal, interest, fee and penalty portion to INCOME_FROM_RECOVERY —
// whatever the loan's fraud flag, which this branch never reads — and the
// overpayment portion to OVERPAYMENT. Portions that resolve to the SAME account
// MERGE into one credit at the first slot's position (the processor's
// creditBalances is a LinkedHashMap).
//
// FundSource is the RESOLVED fund-source account: the transaction's
// paymentTypeId payment-channel account when the product maps that channel, else
// the product's FUND_SOURCE slot. The caller resolves the channel; this port
// carries only the already-resolved account.
type ChargedOffRepaymentAccountMapping struct {
	// IncomeFromRecovery is the AccrualAccountsForLoan.INCOME_FROM_RECOVERY slot,
	// credited with every positive principal, interest, fee and penalty portion.
	IncomeFromRecovery string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, credited with
	// the overpayment portion.
	Overpayment string
	// FundSource is the RESOLVED AccrualAccountsForLoan.FUND_SOURCE slot, debited
	// ONCE with the sum of every portion. Every portion debits this same account,
	// so the processor's debit map merges them too.
	FundSource string
}

// CreateChargedOffRepaymentJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan
// .createJournalEntriesForRepaymentWhenLoanIsChargedOff for a REPAYMENT
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1388-1615, dispatch
// :1369-1377, pinned commit 426a23544]. It is a pure function: the repayment
// transaction's five portions (integer minor units) and the resolved
// slot->account mapping in, journal-entry legs out — no clock, no I/O, no stored
// balance.
//
// It visits the slots in the processor's order (principal, interest, fees,
// penalties, overpayment). For every slot whose portion is > 0 it CREDITS
// INCOME_FROM_RECOVERY — principal, interest, fees and penalties all land on the
// same recovery account, regardless of the fraud flag — MERGING into the first
// slot that already named that account; a positive overpayment portion credits
// OVERPAYMENT. It then posts ONE DEBIT of the total to the resolved fund-source
// account. The credits are posted first (in insertion order) and the single
// debit follows them.
//
// This port models the REPAYMENT arm only. The method's merchant-issued-refund,
// payout-refund, goodwill-credit and else branches are NOT observed on a
// charged-off loan and have NO input — there is no transaction-type parameter —
// so the port never guesses them.
//
// It refuses, rather than inventing, a negative portion, a positive portion
// whose slot maps to no account, and a positive total with no fund-source
// account.
func CreateChargedOffRepaymentJournalEntryLegs(transactionID string, portions RepaymentPortions, mapping ChargedOffRepaymentAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: charged-off repayment journal entries need a transaction id")
	}

	slots := []repaymentSlot{
		{"INCOME_FROM_RECOVERY", portions.Principal, mapping.IncomeFromRecovery},
		{"INCOME_FROM_RECOVERY", portions.Interest, mapping.IncomeFromRecovery},
		{"INCOME_FROM_RECOVERY", portions.Fee, mapping.IncomeFromRecovery},
		{"INCOME_FROM_RECOVERY", portions.Penalty, mapping.IncomeFromRecovery},
		{"OVERPAYMENT", portions.Overpayment, mapping.Overpayment},
	}

	// order/byAccount model the processor's LinkedHashMap: an ordered set of
	// accounts, each accumulating every portion that resolves to it, with the
	// position of the FIRST slot that named it. The four recovery slots share one
	// account, so their portions merge into ONE credit at the principal slot.
	var order []string
	byAccount := map[string]MinorUnits{}
	for _, s := range slots {
		if s.amount < 0 {
			return nil, fmt.Errorf("loan: charged-off repayment slot %s carries a negative portion %d", s.name, s.amount)
		}
		if s.amount == 0 {
			continue
		}
		if s.account == "" {
			return nil, fmt.Errorf("loan: charged-off repayment slot %s has a positive portion %d but no mapped account", s.name, s.amount)
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
		return nil, fmt.Errorf("loan: charged-off repayment total %d has no fund-source account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.FundSource,
		Side:          JournalEntryDebit,
		Amount:        total,
	})
	return legs, nil
}
