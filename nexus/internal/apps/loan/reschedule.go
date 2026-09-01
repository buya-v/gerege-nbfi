package loan

import "fmt"

// RescheduleRequestStatus is the status of a loan reschedule request. Fineract
// deliberately reuses the LoanStatus enum for it [VERIFIED:
// LoanRescheduleRequestStatusEnumData.java:33-36 "Same status types/states for
// loan accounts are used in here"], so the stored values are the LoanStatus
// values [VERIFIED: LoanStatus.java:27-39]: SUBMITTED_AND_PENDING_APPROVAL(100),
// APPROVED(200), REJECTED(500).
type RescheduleRequestStatus int32

const (
	RescheduleSubmittedAndPendingApproval RescheduleRequestStatus = 100
	RescheduleApproved                    RescheduleRequestStatus = 200
	RescheduleRejected                    RescheduleRequestStatus = 500
)

var rescheduleRequestStatusName = map[RescheduleRequestStatus]string{
	RescheduleSubmittedAndPendingApproval: "SUBMITTED_AND_PENDING_APPROVAL",
	RescheduleApproved:                    "APPROVED",
	RescheduleRejected:                    "REJECTED",
}

// StoredValue returns the underlying LoanStatus stored value (status_enum).
func (s RescheduleRequestStatus) StoredValue() int32 { return int32(s) }

func (s RescheduleRequestStatus) String() string {
	if n, ok := rescheduleRequestStatusName[s]; ok {
		return n
	}
	return fmt.Sprintf("RescheduleRequestStatus(%d)", int32(s))
}

// IsPendingApproval mirrors LoanRescheduleRequestStatusEnumData.isPendingApproval
// [VERIFIED: LoanRescheduleRequestStatusEnumData.java:43-45].
func (s RescheduleRequestStatus) IsPendingApproval() bool {
	return s == RescheduleSubmittedAndPendingApproval
}

// IsApproved mirrors LoanRescheduleRequestStatusEnumData.isApproved
// [VERIFIED: LoanRescheduleRequestStatusEnumData.java:47-49].
func (s RescheduleRequestStatus) IsApproved() bool { return s == RescheduleApproved }

// IsRejected mirrors LoanRescheduleRequestStatusEnumData.isRejected
// [VERIFIED: LoanRescheduleRequestStatusEnumData.java:51-53].
func (s RescheduleRequestStatus) IsRejected() bool { return s == RescheduleRejected }

// RescheduleRequest is the Go port of LoanRescheduleRequest reduced to the
// state and arithmetic the loan lifecycle owns [VERIFIED:
// LoanRescheduleRequest.java:37-60]. The schedule recomputation that a
// reschedule triggers lives in the loanschedule package (the oracle's
// LoanScheduleGenerator.rescheduleNextInstallments), not here.
type RescheduleRequest struct {
	Status RescheduleRequestStatus
	// RecalculateInterest is the nullable recalculate_interest column. Fineract
	// models it as Boolean and treats null as false.
	RecalculateInterest *bool
}

// GetRecalculateInterest ports LoanRescheduleRequest.getRecalculateInterest
// [VERIFIED: LoanRescheduleRequest.java:110-121]: false when the field is null.
func (r RescheduleRequest) GetRecalculateInterest() bool {
	if r.RecalculateInterest == nil {
		return false
	}
	return *r.RecalculateInterest
}

// Approve ports LoanRescheduleRequest.approve [VERIFIED:
// LoanRescheduleRequest.java:131-137]: only transitions to APPROVED when a date
// is present (approvedOnDate != null).
func (r *RescheduleRequest) Approve(datePresent bool) {
	if datePresent {
		r.Status = RescheduleApproved
	}
}

// Reject ports LoanRescheduleRequest.reject [VERIFIED:
// LoanRescheduleRequest.java:147-153]: only transitions to REJECTED when a date
// is present (rejectedOnDate != null).
func (r *RescheduleRequest) Reject(datePresent bool) {
	if datePresent {
		r.Status = RescheduleRejected
	}
}
