package loan

import "fmt"

// ChargebackAccountMapping is the GL account each chargeback leg slot resolves
// to for one loan product. The processor resolves the fund-source slot through
// the transaction's payment channel (falling back to the product's
// FUND_SOURCE), the overpayment slot through OVERPAYMENT and the principal slot
// through LOAN_PORTFOLIO (the not-charged-off, not-fraud branch of
// getPrincipalAccount) [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1215-1308, pinned commit
// 426a23544].
type ChargebackAccountMapping struct {
	// FundSource is the resolved AccrualAccountsForLoan.FUND_SOURCE slot: the
	// payment-channel account when the transaction's paymentTypeId has one, else
	// the product's fund source. It is credited with the chargeback amount.
	FundSource string
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, debited
	// with the principal the chargeback credits that the loan had already paid.
	LoanPortfolio string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, debited with
	// the overpaid portion.
	Overpayment string
}

// CreateChargebackJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForChargeback
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1215-1308, pinned
// commit 426a23544]. It is a pure function: an amount (the chargeback the
// customer's bank pulled back), the principal and overpayment portions the
// chargeback transaction credited, and the product's slot->account mapping in;
// journal-entry legs out — no clock, no I/O, no stored balance, integer minor
// units only.
//
// It visits the processor's slots in the processor's order and for every slot
// that is > 0 posts:
//
//  1. the amount to the fund-source account, CREDIT;
//  2. the overpayment portion to the overpayment account, DEBIT;
//  3. the principal portion to the loan-portfolio account, DEBIT
//     (principalCredited - principalPaid, and the observed domain has no paid
//     portion).
//
// THE OBSERVED DOMAIN IS NARROW AND THIS PORT REFUSES ANYTHING OUTSIDE IT, by
// construction rather than by guessing. createJournalEntriesForChargeback also
// reads a fee portion, a penalty portion, a fee-paid / penalty-paid / principal-
// paid portion and a charged-off flag, and posts debit-or-credit legs for the
// signed differences. None of those inputs can be expressed to this function:
// there is no field for a fee, a penalty, a paid portion or a charged-off loan,
// so it can never invent the CHARGE_OFF_EXPENSE / INCOME_FROM_CHARGE_OFF_*
// account switch or a "paid > credited" credit leg. Any such input needs its
// OWN port and its own observation; a caller that has one has already left this
// function's domain.
//
// The observed chargeback satisfies amount = principal + overpayment (no fee,
// no penalty, no paid portion). A mismatch means a portion this port does not
// model was left out, so it is refused rather than silently dropped: posting the
// residual somewhere would be a guess.
func CreateChargebackJournalEntryLegs(transactionID string, amount, principal, overpayment MinorUnits, mapping ChargebackAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: chargeback journal entries need a transaction id")
	}
	if amount < 0 || principal < 0 || overpayment < 0 {
		return nil, fmt.Errorf("loan: chargeback carries a negative amount (amount %d, principal %d, overpayment %d)", amount, principal, overpayment)
	}
	if amount != principal+overpayment {
		return nil, fmt.Errorf("loan: chargeback amount %d is not principal %d + overpayment %d: an unported portion cannot be posted", amount, principal, overpayment)
	}

	legs := make([]JournalEntryLeg, 0, 3)
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
		if mapping.LoanPortfolio == "" {
			return nil, fmt.Errorf("loan: chargeback principal %d has no loan-portfolio account", principal)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.LoanPortfolio,
			Side:          JournalEntryDebit,
			Amount:        principal,
		})
	}
	return legs, nil
}
