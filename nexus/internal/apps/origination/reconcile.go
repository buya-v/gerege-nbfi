package origination

import "fmt"

// The errors below are the pure rule-set outcomes of the linking service. They
// are typed so callers can match them without string comparison, and each maps
// to one Fineract exception.

// ErrOriginatorNotActive is LoanOriginatorNotActiveException: an originator
// must be ACTIVE to be attached [VERIFIED:
// AbstractLoanOriginatorLinkingServiceImpl.java:96-99,
// LoanOriginatorWritePlatformServiceImpl.java:210-212].
type ErrOriginatorNotActive struct {
	OriginatorID int64
	Status       string
}

func (e *ErrOriginatorNotActive) Error() string {
	return fmt.Sprintf("origination: originator %d is not active (status %s)", e.OriginatorID, e.Status)
}

// ErrLoanNotSubmitted is LoanNotInSubmittedStatusException: an originator may
// only be attached/detached while the loan is SUBMITTED_AND_PENDING_APPROVAL
// [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:197-199, 229-231].
type ErrLoanNotSubmitted struct {
	LoanID int64
	Status string
}

func (e *ErrLoanNotSubmitted) Error() string {
	return fmt.Sprintf("origination: loan %d is not submitted and pending approval (status %s)", e.LoanID, e.Status)
}

// ErrMappingAlreadyExists is LoanOriginatorMappingAlreadyExistsException
// [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:214-216].
type ErrMappingAlreadyExists struct {
	LoanID       int64
	OriginatorID int64
}

func (e *ErrMappingAlreadyExists) Error() string {
	return fmt.Sprintf("origination: originator %d is already attached to loan %d", e.OriginatorID, e.LoanID)
}

// ErrOriginatorCannotBeDeleted is LoanOriginatorCannotBeDeletedException: an
// originator that is still referenced by a mapping cannot be deleted
// [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:179-181].
type ErrOriginatorCannotBeDeleted struct {
	OriginatorID int64
}

func (e *ErrOriginatorCannotBeDeleted) Error() string {
	return fmt.Sprintf("origination: originator %d is still mapped to a loan and cannot be deleted", e.OriginatorID)
}

// ValidateAttach ports the attachOriginatorToLoan rule chain: loan must be
// submitted-and-pending, originator must be ACTIVE, and the mapping must not
// already exist [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:196-216].
// loanStatusName is the loan's status code for the error path.
func ValidateAttach(loanID int64, loanSubmittedAndPendingApproval bool, loanStatusName string, originator LoanOriginator, mappingExists bool) error {
	if !loanSubmittedAndPendingApproval {
		return &ErrLoanNotSubmitted{LoanID: loanID, Status: loanStatusName}
	}
	if !originator.Status.IsActive() {
		return &ErrOriginatorNotActive{OriginatorID: originator.ID, Status: originator.Status.StoredValue()}
	}
	if mappingExists {
		return &ErrMappingAlreadyExists{LoanID: loanID, OriginatorID: originator.ID}
	}
	return nil
}

// ValidateDetach ports the detachOriginatorFromLoan rule chain: loan must be
// submitted-and-pending (the originator-not-found and mapping-not-found checks
// are repository concerns the caller resolves before invoking this)
// [VERIFIED: LoanOriginatorWritePlatformServiceImpl.java:228-233].
func ValidateDetach(loanSubmittedAndPendingApproval bool, loanID int64, loanStatusName string) error {
	if !loanSubmittedAndPendingApproval {
		return &ErrLoanNotSubmitted{LoanID: loanID, Status: loanStatusName}
	}
	return nil
}

// ValidateDelete ports the delete rule: an originator referenced by any mapping
// cannot be deleted [VERIFIED:
// LoanOriginatorWritePlatformServiceImpl.java:179-181].
func ValidateDelete(originatorID int64, hasMappings bool) error {
	if hasMappings {
		return &ErrOriginatorCannotBeDeleted{OriginatorID: originatorID}
	}
	return nil
}

// ReconcileMappings ports reconcileOriginatorMappings: it computes the mapping
// delta that drives the loan's mapping set to exactly the requested originator
// IDs — remove those no longer requested, add those not yet present
// [VERIFIED: LoanOriginatorLinkingServiceImpl.java:119-136].
func ReconcileMappings(currentOriginatorIDs, requestedOriginatorIDs []int64) (toAdd, toRemove []int64) {
	current := make(map[int64]bool, len(currentOriginatorIDs))
	for _, id := range currentOriginatorIDs {
		current[id] = true
	}
	requested := make(map[int64]bool, len(requestedOriginatorIDs))
	for _, id := range requestedOriginatorIDs {
		requested[id] = true
	}
	for _, id := range currentOriginatorIDs {
		if !requested[id] {
			toRemove = append(toRemove, id)
		}
	}
	for _, id := range requestedOriginatorIDs {
		if !current[id] {
			toAdd = append(toAdd, id)
		}
	}
	return toAdd, toRemove
}
