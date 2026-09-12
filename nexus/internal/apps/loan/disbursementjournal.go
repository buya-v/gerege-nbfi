package loan

import "fmt"

// DisbursementAccountMapping is the GL account each disbursement portion slot
// touches for one loan product: the loan portfolio the principal portion
// debits, the overpayment liability the overpayment portion debits, and the
// RESOLVED fund source the total credits [VERIFIED:
// AccrualBasedAccountingProcessorForLoan.java:1309-1345, pinned commit
// 426a23544].
//
// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot. Overpayment
// is the AccrualAccountsForLoan.OVERPAYMENT slot. FundSource is the RESOLVED
// AccrualAccountsForLoan.FUND_SOURCE slot: the transaction's paymentTypeId
// payment-channel account when the product maps that channel, else the
// product's FUND_SOURCE slot. The caller resolves the channel; this port
// carries only the already-resolved account, so it needs no payment-type lookup
// and no product state.
//
// Every account is an id string, never a balance-named field: the caller reads
// them back from the product's accountingMappings and the port never invents
// one.
type DisbursementAccountMapping struct {
	// LoanPortfolio is the AccrualAccountsForLoan.LOAN_PORTFOLIO slot, debited
	// with the principal portion.
	LoanPortfolio string
	// Overpayment is the AccrualAccountsForLoan.OVERPAYMENT slot, debited with
	// the overpayment portion.
	Overpayment string
	// FundSource is the RESOLVED AccrualAccountsForLoan.FUND_SOURCE slot,
	// credited ONCE with the whole transaction amount.
	FundSource string
}

// CreateDisbursementJournalEntryLegs ports
// AccrualBasedAccountingProcessorForLoan.createJournalEntriesForDisbursements
// [VERIFIED: AccrualBasedAccountingProcessorForLoan.java:1309-1345, pinned
// commit 426a23544]. It is a pure function: the disbursement transaction's
// amount and overpayment (integer minor units) and the resolved slot->account
// mapping in, journal-entry legs out — no clock, no I/O, no stored balance.
//
// The principal portion is amount minus overpayment — NOT the read-back
// transaction's principalPortion field, which every observed disbursement
// carries as 0. It DEBITS LOAN_PORTFOLIO with the principal portion when that
// is > 0, DEBITS OVERPAYMENT with the overpayment portion when that is > 0, and
// then CREDITS the resolved fund source with the whole amount when the amount
// is > 0. The debits come first, in that order, and the single credit last.
//
// This is NOT a transfer. A loan-to-loan transfer (ASSET_TRANSFER) and an
// account transfer (LIABILITY_TRANSFER) are the processor's other branches and
// are NOT observed here: the port takes no transfer flag, so the caller cannot
// express them and the port never guesses them. An overpayment portion > 0 is
// ported as the processor has it but is unobserved; every observed disbursement
// has overpayment 0, so the principal debit is the whole amount.
//
// It refuses, rather than inventing, a negative amount or overpayment, an
// overpayment larger than the amount, and a positive leg whose account is not
// mapped.
func CreateDisbursementJournalEntryLegs(transactionID string, amount, overpayment MinorUnits, mapping DisbursementAccountMapping) ([]JournalEntryLeg, error) {
	if transactionID == "" {
		return nil, fmt.Errorf("loan: disbursement journal entries need a transaction id")
	}
	if amount < 0 {
		return nil, fmt.Errorf("loan: disbursement amount %d is negative", amount)
	}
	if overpayment < 0 {
		return nil, fmt.Errorf("loan: disbursement overpayment %d is negative", overpayment)
	}
	if overpayment > amount {
		return nil, fmt.Errorf("loan: disbursement overpayment %d exceeds the amount %d", overpayment, amount)
	}

	principal := amount - overpayment

	legs := make([]JournalEntryLeg, 0, 3)
	if principal > 0 {
		if mapping.LoanPortfolio == "" {
			return nil, fmt.Errorf("loan: disbursement principal portion %d has no loan-portfolio account", principal)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.LoanPortfolio,
			Side:          JournalEntryDebit,
			Amount:        principal,
		})
	}
	if overpayment > 0 {
		if mapping.Overpayment == "" {
			return nil, fmt.Errorf("loan: disbursement overpayment portion %d has no overpayment account", overpayment)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.Overpayment,
			Side:          JournalEntryDebit,
			Amount:        overpayment,
		})
	}
	if amount > 0 {
		if mapping.FundSource == "" {
			return nil, fmt.Errorf("loan: disbursement amount %d has no fund-source account", amount)
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID,
			Account:       mapping.FundSource,
			Side:          JournalEntryCredit,
			Amount:        amount,
		})
	}
	return legs, nil
}
