package loan

import "fmt"

// LoanStatus is m_loan.loan_status_id — Fineract's LoanStatus.
// [VERIFIED: LoanStatus.java:27-39 — INVALID(0), SUBMITTED_AND_PENDING_APPROVAL(100),
// APPROVED(200), ACTIVE(300), TRANSFER_IN_PROGRESS(303), TRANSFER_ON_HOLD(304),
// WITHDRAWN_BY_CLIENT(400), REJECTED(500), CLOSED_OBLIGATIONS_MET(600),
// CLOSED_WRITTEN_OFF(601), CLOSED_RESCHEDULE_OUTSTANDING_AMOUNT(602), OVERPAID(700)]
//
// The stored values are NOT contiguous: the active band lives around 300 with
// transfer sub-states at 303/304, and the closed band carries three distinct
// 6xx values. A port that encodes these as an iota would silently collapse the
// transfer and closed sub-states; the explicit StoredValue table below is the
// contract.
type LoanStatus int32

const (
	StatusInvalid LoanStatus = iota
	StatusSubmittedAndPendingApproval
	StatusApproved
	StatusActive
	StatusTransferInProgress
	StatusTransferOnHold
	StatusWithdrawnByClient
	StatusRejected
	StatusClosedObligationsMet
	StatusClosedWrittenOff
	StatusClosedRescheduleOutstandingAmount
	StatusOverpaid
)

var loanStatusStoredValue = map[LoanStatus]int32{
	StatusInvalid:                           0,
	StatusSubmittedAndPendingApproval:       100,
	StatusApproved:                          200,
	StatusActive:                            300,
	StatusTransferInProgress:                303,
	StatusTransferOnHold:                    304,
	StatusWithdrawnByClient:                 400,
	StatusRejected:                          500,
	StatusClosedObligationsMet:              600,
	StatusClosedWrittenOff:                  601,
	StatusClosedRescheduleOutstandingAmount: 602,
	StatusOverpaid:                          700,
}

var loanStatusCode = map[LoanStatus]string{
	StatusInvalid:                           "loanStatusType.invalid",
	StatusSubmittedAndPendingApproval:       "loanStatusType.submitted.and.pending.approval",
	StatusApproved:                          "loanStatusType.approved",
	StatusActive:                            "loanStatusType.active",
	StatusTransferInProgress:                "loanStatusType.transfer.in.progress",
	StatusTransferOnHold:                    "loanStatusType.transfer.on.hold",
	StatusWithdrawnByClient:                 "loanStatusType.withdrawn.by.client",
	StatusRejected:                          "loanStatusType.rejected",
	StatusClosedObligationsMet:              "loanStatusType.closed.obligations.met",
	StatusClosedWrittenOff:                  "loanStatusType.closed.written.off",
	StatusClosedRescheduleOutstandingAmount: "loanStatusType.closed.reschedule.outstanding.amount",
	StatusOverpaid:                          "loanStatusType.overpaid",
}

var loanStatusName = map[LoanStatus]string{
	StatusInvalid:                           "INVALID",
	StatusSubmittedAndPendingApproval:       "SUBMITTED_AND_PENDING_APPROVAL",
	StatusApproved:                          "APPROVED",
	StatusActive:                            "ACTIVE",
	StatusTransferInProgress:                "TRANSFER_IN_PROGRESS",
	StatusTransferOnHold:                    "TRANSFER_ON_HOLD",
	StatusWithdrawnByClient:                 "WITHDRAWN_BY_CLIENT",
	StatusRejected:                          "REJECTED",
	StatusClosedObligationsMet:              "CLOSED_OBLIGATIONS_MET",
	StatusClosedWrittenOff:                  "CLOSED_WRITTEN_OFF",
	StatusClosedRescheduleOutstandingAmount: "CLOSED_RESCHEDULE_OUTSTANDING_AMOUNT",
	StatusOverpaid:                          "OVERPAID",
}

var loanStatusFromStored = map[int32]LoanStatus{}

// StoredValue returns m_loan.loan_status_id.
func (s LoanStatus) StoredValue() int32 {
	v, ok := loanStatusStoredValue[s]
	if !ok {
		panic(fmt.Sprintf("loan: unknown LoanStatus %d", int32(s)))
	}
	return v
}

// Code returns the i18n code emitted on the loan read.
func (s LoanStatus) Code() string { return loanStatusCode[s] }

func (s LoanStatus) String() string {
	if n, ok := loanStatusName[s]; ok {
		return n
	}
	return fmt.Sprintf("LoanStatus(%d)", int32(s))
}

// LoanStatusFromStoredValue decodes m_loan.loan_status_id. ok is false outside
// the 12 legal values, matching LoanStatus.fromInt's INVALID fallback
// [VERIFIED: LoanStatus.java:42-59].
func LoanStatusFromStoredValue(v int32) (LoanStatus, bool) {
	s, ok := loanStatusFromStored[v]
	return s, ok
}

// Predicates below mirror LoanStatus's boolean helpers [VERIFIED:
// LoanStatus.java:74-140]. They compare the stored value, never the Go ordinal.

func (s LoanStatus) IsSubmittedAndPendingApproval() bool {
	return s == StatusSubmittedAndPendingApproval
}
func (s LoanStatus) IsApproved() bool          { return s == StatusApproved }
func (s LoanStatus) IsActive() bool            { return s == StatusActive }
func (s LoanStatus) IsWithdrawnByClient() bool { return s == StatusWithdrawnByClient }
func (s LoanStatus) IsRejected() bool          { return s == StatusRejected }
func (s LoanStatus) IsOverpaid() bool          { return s == StatusOverpaid }

func (s LoanStatus) IsClosedObligationsMet() bool { return s == StatusClosedObligationsMet }
func (s LoanStatus) IsClosedWrittenOff() bool     { return s == StatusClosedWrittenOff }
func (s LoanStatus) IsClosedRescheduleOutstandingAmount() bool {
	return s == StatusClosedRescheduleOutstandingAmount
}

// IsClosed is the union of the three closed states
// [VERIFIED: LoanStatus.java:86-88].
func (s LoanStatus) IsClosed() bool {
	return s.IsClosedObligationsMet() || s.IsClosedWrittenOff() || s.IsClosedRescheduleOutstandingAmount()
}

func (s LoanStatus) IsTransferInProgress() bool { return s == StatusTransferInProgress }
func (s LoanStatus) IsTransferOnHold() bool     { return s == StatusTransferOnHold }

// IsUnderTransfer is the union of the two transfer states
// [VERIFIED: LoanStatus.java:107-109].
func (s LoanStatus) IsUnderTransfer() bool { return s.IsTransferInProgress() || s.IsTransferOnHold() }

// IsActiveOrAwaitingApprovalOrDisbursal mirrors the oracle helper
// [VERIFIED: LoanStatus.java:98-100].
func (s LoanStatus) IsActiveOrAwaitingApprovalOrDisbursal() bool {
	return s.IsApproved() || s.IsSubmittedAndPendingApproval() || s.IsActive()
}

// HasStateOf mirrors LoanStatus.hasStateOf: stored-value equality
// [VERIFIED: LoanStatus.java:61-63].
func (s LoanStatus) HasStateOf(other LoanStatus) bool { return s == other }

func init() {
	for s, v := range loanStatusStoredValue {
		if _, dup := loanStatusFromStored[v]; dup {
			panic(fmt.Sprintf("loan: loan status encode table is not injective at %d", v))
		}
		loanStatusFromStored[v] = s
	}
}
