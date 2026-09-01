package workingcapital

import (
	"time"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalLoanTransactionAllocation is the money split of one
// working-capital transaction. It is the Go port of Fineract's
// WorkingCapitalLoanTransactionAllocation [VERIFIED:
// WorkingCapitalLoanTransactionAllocation.java:24-120].
//
// It carries exactly four portions — principal, fee, penalty, overpayment —
// and never an interest portion. The overpayment portion is disjoint from the
// principal portion, so for a money-moving transaction the four portions sum to
// the transaction amount.
type WorkingCapitalLoanTransactionAllocation struct {
	PrincipalPortion      loan.MinorUnits // principal_portion
	FeeChargesPortion     loan.MinorUnits // fee_charges_portion
	PenaltyChargesPortion loan.MinorUnits // penalty_charges_portion
	OverpaymentPortion    loan.MinorUnits // overpayment_portion
}

// Total returns the sum of the four portions.
func (a WorkingCapitalLoanTransactionAllocation) Total() loan.MinorUnits {
	return a.PrincipalPortion + a.FeeChargesPortion + a.PenaltyChargesPortion + a.OverpaymentPortion
}

// ForPrincipalAllocation ports forPrincipalAllocation: principal-only, the other
// three portions zeroed [VERIFIED: WorkingCapitalLoanTransactionAllocation.java:62-71].
func ForPrincipalAllocation(principal loan.MinorUnits) WorkingCapitalLoanTransactionAllocation {
	return WorkingCapitalLoanTransactionAllocation{PrincipalPortion: principal}
}

// ForPortions ports forPortions: explicit principal/fee/penalty/overpayment
// [VERIFIED: WorkingCapitalLoanTransactionAllocation.java:73-83].
func ForPortions(principal, fee, penalty, overpayment loan.MinorUnits) WorkingCapitalLoanTransactionAllocation {
	return WorkingCapitalLoanTransactionAllocation{
		PrincipalPortion:      principal,
		FeeChargesPortion:     fee,
		PenaltyChargesPortion: penalty,
		OverpaymentPortion:    overpayment,
	}
}

// ForChargeAccrual ports forChargeAccrual: the amount lands in fee (isPenalty
// false) or penalty (isPenalty true), everything else zero
// [VERIFIED: WorkingCapitalLoanTransactionAllocation.java:98-107].
func ForChargeAccrual(amount loan.MinorUnits, isPenalty bool) WorkingCapitalLoanTransactionAllocation {
	if isPenalty {
		return WorkingCapitalLoanTransactionAllocation{PenaltyChargesPortion: amount}
	}
	return WorkingCapitalLoanTransactionAllocation{FeeChargesPortion: amount}
}

// ForCreditBalanceRefund ports forCreditBalanceRefund: excess principal becomes
// newly-lent principal, overpaymentConsumed is taken back out of the overpayment
// [VERIFIED: WorkingCapitalLoanTransactionAllocation.java:112-121].
func ForCreditBalanceRefund(excessPrincipal, overpaymentConsumed loan.MinorUnits) WorkingCapitalLoanTransactionAllocation {
	return WorkingCapitalLoanTransactionAllocation{
		PrincipalPortion:   excessPrincipal,
		OverpaymentPortion: overpaymentConsumed,
	}
}

// WorkingCapitalLoanTransaction is the Go port of the working-capital loan
// transaction's core identity: which transaction type, on which date, for how
// much, and how that amount was split [VERIFIED:
// WorkingCapitalLoanTransaction.java:51-103].
//
// It is the read model a posting slice consumes, not the double-entry posting
// itself (that belongs to tierA-gl-accounting).
type WorkingCapitalLoanTransaction struct {
	ID     int64 // m_wc_loan_transaction.id
	LoanID int64 // wc_loan_id

	// TransactionType is m_wc_loan_transaction.transaction_type_enum. Working
	// capital reuses the core LoanTransactionType enum
	// [VERIFIED: WorkingCapitalLoanTransaction.java:59].
	TransactionType loan.LoanTransactionType

	TransactionDate   time.Time
	TransactionAmount loan.MinorUnits

	Reversed           bool
	ReversalExternalID string

	Allocation WorkingCapitalLoanTransactionAllocation
}
