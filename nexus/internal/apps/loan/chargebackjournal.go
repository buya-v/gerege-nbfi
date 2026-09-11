package loan

import "fmt"

// ChargebackAccountMapping is the GL account each chargeback leg slot resolves
// to for one loan product. The processor resolves the fund-source slot through
// the transaction's payment channel (falling back to the product's
// FUND_SOURCE), the overpayment slot through OVERPAYMENT, and the principal,
// fee and penalty slots through getPrincipalAccount / getFeeAccount /
// getPenaltyAccount: the ordinary portfolio/receivable accounts while the loan
// is not charged off, and the charge-off expense / charge-off income accounts
// once it is [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1215-1308, pinned commit
// 426a23544].
type ChargebackAccountMapping struct {
	// FundSource is the resolved AccrualAccountsForLoan.FUND_SOURCE slot: the
	// payment-channel account when the transaction's paymentTypeId has one, else
	// the product's fund source. It is credited with the chargeback amount.
	FundSource string
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, debited
	// with the principal the chargeback credits that the loan had already paid,
	// while the loan is NOT charged off.
	LoanPortfolio string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, debited with
	// the overpaid portion.
	Overpayment string
	// FeesReceivable is the AccrualAccountsForLoan.FEES_RECEIVABLE slot, debited
	// with the fee credited while the loan is NOT charged off.
	FeesReceivable string
	// PenaltiesReceivable is the AccrualAccountsForLoan.PENALTIES_RECEIVABLE
	// slot, debited with the penalty credited while the loan is NOT charged off.
	PenaltiesReceivable string
	// ChargeOffExpense is the AccrualAccountsForLoan.CHARGE_OFF_EXPENSE slot,
	// debited with the principal credited once the loan is charged off and NOT
	// fraud (the fraud charge-off expense is a separate, unobserved branch the
	// port refuses).
	ChargeOffExpense string
	// IncomeFromChargeOffFees is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_FEES slot, debited with the
	// fee credited once the loan is charged off.
	IncomeFromChargeOffFees string
	// IncomeFromChargeOffPenalty is the
	// AccrualAccountsForLoan.INCOME_FROM_CHARGE_OFF_PENALTY slot, debited with
	// the penalty credited once the loan is charged off.
	IncomeFromChargeOffPenalty string
}

// CreateChargebackJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeback
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1215-1308, pinned
// commit 426a23544]. It is a pure function: an amount (the chargeback the
// customer's bank pulled back), the principal, fee, penalty and overpayment
// portions the chargeback transaction credited, the charged-off and fraud loan
// facts, and the product's slot->account mapping in; journal-entry legs out —
// no clock, no I/O, no stored balance, integer minor units only.
//
// It visits the processor's slots in the processor's order and for every slot
// that is > 0 posts:
//
//  1. the amount to the fund-source account, CREDIT;
//  2. the overpayment portion to the overpayment account, DEBIT;
//  3. the principal portion to LOAN_PORTFOLIO, or to CHARGE_OFF_EXPENSE when
//     the loan is charged off (and NOT fraud), DEBIT
//     (principalCredited - principalPaid, and the observed domain has no paid
//     portion);
//  4. the fee portion to FEES_RECEIVABLE, or to INCOME_FROM_CHARGE_OFF_FEES
//     when the loan is charged off, DEBIT;
//  5. the penalty portion to PENALTIES_RECEIVABLE, or to
//     INCOME_FROM_CHARGE_OFF_PENALTY when the loan is charged off, DEBIT.
//
// Each slot is its own helper call in the processor, so no two slots merge even
// when they share an account: this port appends one leg per positive portion.
//
// THE OBSERVED DOMAIN IS NARROW AND THIS PORT REFUSES ANYTHING OUTSIDE IT, by
// construction rather than by guessing. The processor also reads a fee-paid /
// penalty-paid / principal-paid portion and posts debit-or-credit legs for the
// signed differences; there is no field for a paid portion, so it can never
// invent a "paid > credited" credit leg. A charged-off loan that is ALSO fraud
// selects the fraud charge-off expense account, which no capture observes, so
// that combination is refused rather than guessed.
//
// The observed chargebacks satisfy amount = principal + fee + penalty +
// overpayment (no paid portion). A mismatch means a portion this port does not
// model was left out, so it is refused rather than silently dropped: posting the
// residual somewhere would be a guess.
func CreateChargebackJournalEntryLegs(transactionID string, amount, principal, fee, penalty, overpayment MinorUnits, chargedOff, fraud bool, mapping ChargebackAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: chargeback journal entries need a transaction id")
	}
	if amount < 0 || principal < 0 || fee < 0 || penalty < 0 || overpayment < 0 {
		return nil, fmt.Errorf("loan: chargeback carries a negative amount (amount %d, principal %d, fee %d, penalty %d, overpayment %d)", amount, principal, fee, penalty, overpayment)
	}
	if chargedOff && fraud {
		return nil, fmt.Errorf("loan: chargeback on a charged-off fraudulent loan is not observed: the fraud CHARGE_OFF_FRAUD_EXPENSE branch has no capture and cannot be posted")
	}
	if amount != principal+fee+penalty+overpayment {
		return nil, fmt.Errorf("loan: chargeback amount %d is not principal %d + fee %d + penalty %d + overpayment %d: an unported portion cannot be posted", amount, principal, fee, penalty, overpayment)
	}

	legs := make([]JournalEntryLeg, 0, 5)
	if amount > 0 {
		if mapping.FundSource == "" {
			return nil, fmt.Errorf("loan: chargeback amount %d has no fund-source account", amount)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.FundSource,
			Side:          JournalEntryCredit,
			Amount:        amount,
		})
	}
	if overpayment > 0 {
		if mapping.Overpayment == "" {
			return nil, fmt.Errorf("loan: chargeback overpayment %d has no overpayment account", overpayment)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.Overpayment,
			Side:          JournalEntryDebit,
			Amount:        overpayment,
		})
	}
	if principal > 0 {
		account := mapping.LoanPortfolio
		if chargedOff {
			account = mapping.ChargeOffExpense
		}
		if account == "" {
			return nil, fmt.Errorf("loan: chargeback principal %d has no principal account (charged off %t)", principal, chargedOff)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        principal,
		})
	}
	if fee > 0 {
		account := mapping.FeesReceivable
		if chargedOff {
			account = mapping.IncomeFromChargeOffFees
		}
		if account == "" {
			return nil, fmt.Errorf("loan: chargeback fee %d has no fee account (charged off %t)", fee, chargedOff)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        fee,
		})
	}
	if penalty > 0 {
		account := mapping.PenaltiesReceivable
		if chargedOff {
			account = mapping.IncomeFromChargeOffPenalty
		}
		if account == "" {
			return nil, fmt.Errorf("loan: chargeback penalty %d has no penalty account (charged off %t)", penalty, chargedOff)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       account,
			Side:          JournalEntryDebit,
			Amount:        penalty,
		})
	}
	return legs, nil
}
