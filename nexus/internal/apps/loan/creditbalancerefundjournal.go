package loan

import "fmt"

// CreditBalanceRefundAccountMapping is the GL account each credit-balance-refund
// leg slot resolves to for one loan product. The processor resolves the
// fund-source slot through the transaction's payment channel (falling back to
// the product's FUND_SOURCE), the principal slot through
// determineAccrualAccountForCBR — LOAN_PORTFOLIO while the loan is not charged
// off, CHARGE_OFF_EXPENSE once it is, and CHARGE_OFF_FRAUD_EXPENSE when it is
// also fraud — and the overpayment slot through OVERPAYMENT, which the
// charged-off and fraud flags never change [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:2113-2170, pinned commit
// 426a23544].
type CreditBalanceRefundAccountMapping struct {
	// FundSource is the resolved AccrualAccountsForLoan.FUND_SOURCE slot: the
	// payment-channel account when the transaction's paymentTypeId has one, else
	// the product's fund source. It is credited ONCE with the total.
	FundSource string
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, debited
	// with the principal portion while the loan is NOT charged off.
	LoanPortfolio string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, debited with
	// the overpayment portion, whatever the charged-off and fraud flags.
	Overpayment string
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// debited with the principal portion once the loan is charged off and NOT
	// fraud.
	ChargeOffExpense string
	// ChargeOffFraudExpense is the AccrualAccountsForLoan.CHARGE_OFF_FRAUD_EXPENSE
	// slot, debited with the principal portion once the loan is charged off AND
	// fraud.
	ChargeOffFraudExpense string
}

// CreateCreditBalanceRefundJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanCreditBalanceRefund
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:2120-2155, dispatched
// from createJournalEntriesForCreditBalanceRefund :2113-2118, pinned commit
// 426a23544]. It is a pure function: the principal and overpayment portions the
// refund transaction carried, the loan's charged-off and fraud facts, and the
// product's slot->account mapping in; journal-entry legs out — no clock, no
// I/O, no stored balance, integer minor units only.
//
// It mirrors the processor's order. For each positive portion it adds a DEBIT
// leg to the account determineAccrualAccountForCBR selects:
//
//  1. the principal portion to LOAN_PORTFOLIO, or to CHARGE_OFF_EXPENSE once
//     the loan is charged off, or to CHARGE_OFF_FRAUD_EXPENSE when it is also
//     fraud, DEBIT;
//  2. the overpayment portion to OVERPAYMENT, DEBIT (the charged-off and fraud
//     flags are not read for this slot);
//
// then posts ONE CREDIT of the total to the RESOLVED fund source.
//
// The observed domain is narrow and this port refuses anything outside it,
// rather than guessing. It refuses a negative portion, a positive portion whose
// slot maps to no account, and a positive total with no fund-source account.
// When both portions are zero it posts nothing.
func CreateCreditBalanceRefundJournalEntryLegs(transactionID string, principal, overpayment MinorUnits, chargedOff, fraud bool, mapping CreditBalanceRefundAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: credit-balance-refund journal entries need a transaction id")
	}
	if principal < 0 || overpayment < 0 {
		return nil, fmt.Errorf("loan: credit-balance-refund carries a negative portion (principal %d, overpayment %d)", principal, overpayment)
	}

	legs := make([]JournalEntryLeg, 0, 3)
	if principal > 0 {
		account := mapping.LoanPortfolio
		if chargedOff {
			account = mapping.ChargeOffExpense
			if fraud {
				account = mapping.ChargeOffFraudExpense
			}
		}
		if account == "" {
			return nil, fmt.Errorf("loan: credit-balance-refund principal %d has no principal account (charged off %t, fraud %t)", principal, chargedOff, fraud)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        principal,
		})
	}
	if overpayment > 0 {
		if mapping.Overpayment == "" {
			return nil, fmt.Errorf("loan: credit-balance-refund overpayment %d has no overpayment account", overpayment)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.Overpayment,
			Side:          JournalEntryDebit,
			Amount:        overpayment,
		})
	}

	total := principal + overpayment
	if total == 0 {
		return legs, nil
	}
	if mapping.FundSource == "" {
		return nil, fmt.Errorf("loan: credit-balance-refund total %d has no fund-source account", total)
	}
	legs = append(legs, JournalEntryLeg{
		TransactionID: transactionID,
		Account:       mapping.FundSource,
		Side:          JournalEntryCredit,
		Amount:        total,
	})
	return legs, nil
}
