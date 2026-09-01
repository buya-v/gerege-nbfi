package origination

// LoanOriginatorMapping links one amortising loan to one originator. It is the
// Go port of Fineract's LoanOriginatorMapping (m_loan_originator_mapping)
// [VERIFIED: LoanOriginatorMapping.java:24-46].
type LoanOriginatorMapping struct {
	ID           int64
	LoanID       int64 // loan_id
	OriginatorID int64 // originator_id
}

// NewLoanOriginatorMapping ports the create factory
// [VERIFIED: LoanOriginatorMapping.java:38-43].
func NewLoanOriginatorMapping(loanID, originatorID int64) LoanOriginatorMapping {
	return LoanOriginatorMapping{LoanID: loanID, OriginatorID: originatorID}
}

// WorkingCapitalLoanOriginatorMapping links one working-capital loan to one
// originator. It is the Go port of Fineract's WorkingCapitalLoanOriginatorMapping
// (m_wc_loan_originator_mapping) [VERIFIED:
// WorkingCapitalLoanOriginatorMapping.java:24-46]. The shape is identical to
// LoanOriginatorMapping; only the table and loan target differ.
type WorkingCapitalLoanOriginatorMapping struct {
	ID           int64
	LoanID       int64 // loan_id
	OriginatorID int64 // originator_id
}

// NewWorkingCapitalLoanOriginatorMapping ports the create factory
// [VERIFIED: WorkingCapitalLoanOriginatorMapping.java:38-43].
func NewWorkingCapitalLoanOriginatorMapping(loanID, originatorID int64) WorkingCapitalLoanOriginatorMapping {
	return WorkingCapitalLoanOriginatorMapping{LoanID: loanID, OriginatorID: originatorID}
}
