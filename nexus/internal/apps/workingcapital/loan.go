package workingcapital

import (
	"time"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalLoan is the Go port of the working-capital loan aggregate
// [VERIFIED: WorkingCapitalLoan.java:55-210]. It is the identity, status and
// product facts the repayment write path reads from and writes to.
//
// It is a pure model with no database dependency. The aggregate references its
// child balance and the loan-status/transaction-type vocabulary from the loan
// package, so a status or transaction type has exactly one Go home.
//
// Dates are calendar dates: only the yyyy-MM-dd portion is significant,
// matching java.time.LocalDate; the time portion is ignored.
type WorkingCapitalLoan struct {
	ID            int64  // m_wc_loan.id
	AccountNumber string // m_wc_loan.account_no
	ExternalID    string // m_wc_loan.external_id

	ClientID      int64 // client_id
	FundID        int64 // fund_id (0 = none)
	LoanProductID int64 // product_id

	// LoanStatus is m_wc_loan.loan_status_id. Working capital reuses the core
	// LoanStatus enum [VERIFIED: WorkingCapitalLoan.java:45,89-90].
	LoanStatus loan.LoanStatus

	LoanCounter        int // loan_counter
	LoanProductCounter int // loan_product_counter

	SubmittedOnDate      time.Time
	RejectedOnDate       time.Time
	ApprovedOnDate       time.Time
	ClosedOnDate         time.Time
	ExpectedMaturityDate time.Time
	MaturedOnDate        time.Time

	ProposedPrincipal loan.MinorUnits
	ApprovedPrincipal loan.MinorUnits

	Balance WorkingCapitalLoanBalance

	PaymentAllocationRules []WorkingCapitalLoanPaymentAllocationRule
	DisbursementDetails    []WorkingCapitalLoanDisbursementDetails

	LoanProductRelatedDetails *WorkingCapitalLoanProductRelatedDetails

	TotalPaymentVolume loan.MinorUnits
	ChargedOff         bool
	Fraud              bool
}
