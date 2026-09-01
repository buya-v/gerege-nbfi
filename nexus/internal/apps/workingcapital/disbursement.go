package workingcapital

import (
	"time"

	"github.com/gerege/nexus/internal/apps/loan"
)

// WorkingCapitalLoanDisbursementDetails stores expected and actual disbursement
// facts per tranche. It is the Go port of Fineract's
// WorkingCapitalLoanDisbursementDetails [VERIFIED:
// WorkingCapitalLoanDisbursementDetails.java:24-70].
//
// Dates are calendar dates: only the yyyy-MM-dd portion is significant.
type WorkingCapitalLoanDisbursementDetails struct {
	ID     int64 // m_wc_loan_disbursement_detail.id
	LoanID int64 // wc_loan_id

	ExpectedDisbursementDate time.Time
	ExpectedAmount           loan.MinorUnits // expected_amount, in minor units
	ExpectedMaturityDate     time.Time

	ActualDisbursementDate time.Time
	ActualAmount           loan.MinorUnits // actual_amount, in minor units

	DisbursedByUserID int64 // disbursedon_userid
}
