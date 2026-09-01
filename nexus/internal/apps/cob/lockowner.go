package cob

// LockOwner controls which run of the COB job is permitted to operate on an
// item. It mirrors org.apache.fineract.cob.loan.LoanCOBBusinessStep's lock
// owner concept: the loan COB pipeline acquires a lock owned by the batch job
// (LOAN_COB) so that inline COB invocations from the API layer do not race it.
type LockOwner string

const (
	// LockOwnerLoanCOB is the lock owner for the scheduled loan COB job.
	LockOwnerLoanCOB LockOwner = "LOAN_COB"
	// LockOwnerLoanInlineCOB is the lock owner for inline (API-triggered) COB.
	LockOwnerLoanInlineCOB LockOwner = "LOAN_INLINE_COB"
)

// String returns the lock owner identifier.
func (l LockOwner) String() string {
	return string(l)
}
