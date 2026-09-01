package cob

// Loan COB job identifiers, ported from org.apache.fineract.cob.loan.LoanCOBConstant.
const (
	// LoanJobName is the internal bean/scheduler job key ("LOAN_COB").
	LoanJobName = "LOAN_COB"
	// LoanJobHumanReadableName is the display name surfaced to operators.
	LoanJobHumanReadableName = "Loan COB"
	// LoanCOBJobName is the configured business-step job name stored in
	// m_batch_business_steps ("LOAN_CLOSE_OF_BUSINESS").
	LoanCOBJobName = "LOAN_CLOSE_OF_BUSINESS"
	// InlineLoanCOBJobName is the job name used for inline (API-triggered) COB.
	InlineLoanCOBJobName = "INLINE_LOAN_COB"
)

// Loan business-step names and their human-readable labels. These are the
// enum-styled names returned by each org.apache.fineract.cob.loan.*BusinessStep
// implementation.
const (
	StepApplyChargeToOverdueLoans     = "APPLY_CHARGE_TO_OVERDUE_LOANS"
	StepLoanDelinquencyClassification = "LOAN_DELINQUENCY_CLASSIFICATION"
	StepCheckLoanRepaymentDue         = "CHECK_LOAN_REPAYMENT_DUE"
	StepCheckLoanRepaymentOverdue     = "CHECK_LOAN_REPAYMENT_OVERDUE"
	StepUpdateLoanArrearsAging        = "UPDATE_LOAN_ARREARS_AGING"
	StepAddPeriodicAccrualEntries     = "ADD_PERIODIC_ACCRUAL_ENTRIES"
)

// DefaultLoanConfig returns the out-of-the-box loan COB step order seeded by
// Fineract's tenant changelog (parts 0022, 0047, 0067, 0089, 0092).
func DefaultLoanConfig() Config {
	return Config{
		BusinessSteps: []StepConfig{
			{StepName: StepApplyChargeToOverdueLoans, StepOrder: 1},
			{StepName: StepLoanDelinquencyClassification, StepOrder: 2},
			{StepName: StepCheckLoanRepaymentDue, StepOrder: 3},
			{StepName: StepCheckLoanRepaymentOverdue, StepOrder: 4},
			{StepName: StepUpdateLoanArrearsAging, StepOrder: 5},
			{StepName: StepAddPeriodicAccrualEntries, StepOrder: 6},
		},
	}
}
