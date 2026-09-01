package savings

import "fmt"

// SavingsAccountStatusType is m_savings_account.status_enum — Fineract's
// SavingsAccountStatusType.
// [VERIFIED: SavingsAccountStatusType.java:24-35]
//
//	INVALID(0)
//	SUBMITTED_AND_PENDING_APPROVAL(100)
//	APPROVED(200)
//	ACTIVE(300)
//	TRANSFER_IN_PROGRESS(303)
//	TRANSFER_ON_HOLD(304)
//	WITHDRAWN_BY_APPLICANT(400)
//	REJECTED(500)
//	CLOSED(600)
//	PRE_MATURE_CLOSURE(700)
//	MATURED(800)
//
// The stored values are NOT contiguous and NOT the declaration ordinal: the
// active band lives around 300 with transfer sub-states at 303/304, and the
// terminal band carries three distinct 7xx/8xx values. A port that encodes
// these as an iota would silently collapse the transfer sub-states and every
// band after 300, so the explicit storedValue table below is the contract.
type SavingsAccountStatusType int32

const (
	StatusInvalid SavingsAccountStatusType = iota
	StatusSubmittedAndPendingApproval
	StatusApproved
	StatusActive
	StatusTransferInProgress
	StatusTransferOnHold
	StatusWithdrawnByApplicant
	StatusRejected
	StatusClosed
	StatusPreMatureClosure
	StatusMatured
)

var savingsStatusStoredValue = map[SavingsAccountStatusType]int32{
	StatusInvalid:                     0,
	StatusSubmittedAndPendingApproval: 100,
	StatusApproved:                    200,
	StatusActive:                      300,
	StatusTransferInProgress:          303,
	StatusTransferOnHold:              304,
	StatusWithdrawnByApplicant:        400,
	StatusRejected:                    500,
	StatusClosed:                      600,
	StatusPreMatureClosure:            700,
	StatusMatured:                     800,
}

var savingsStatusName = map[SavingsAccountStatusType]string{
	StatusInvalid:                     "INVALID",
	StatusSubmittedAndPendingApproval: "SUBMITTED_AND_PENDING_APPROVAL",
	StatusApproved:                    "APPROVED",
	StatusActive:                      "ACTIVE",
	StatusTransferInProgress:          "TRANSFER_IN_PROGRESS",
	StatusTransferOnHold:              "TRANSFER_ON_HOLD",
	StatusWithdrawnByApplicant:        "WITHDRAWN_BY_APPLICANT",
	StatusRejected:                    "REJECTED",
	StatusClosed:                      "CLOSED",
	StatusPreMatureClosure:            "PRE_MATURE_CLOSURE",
	StatusMatured:                     "MATURED",
}

var savingsStatusFromStored = map[int32]SavingsAccountStatusType{}

// StoredValue returns m_savings_account.status_enum.
func (s SavingsAccountStatusType) StoredValue() int32 {
	v, ok := savingsStatusStoredValue[s]
	if !ok {
		panic(fmt.Sprintf("savings: unknown SavingsAccountStatusType %d", int32(s)))
	}
	return v
}

// String returns the Java enum constant name.
func (s SavingsAccountStatusType) String() string {
	if n, ok := savingsStatusName[s]; ok {
		return n
	}
	return fmt.Sprintf("SavingsAccountStatusType(%d)", int32(s))
}

// SavingsAccountStatusTypeFromStoredValue decodes m_savings_account.status_enum.
// ok is false outside the 11 legal values, matching SavingsAccountStatusType
// .fromInt's INVALID fallback [VERIFIED: SavingsAccountStatusType.java:38-73].
func SavingsAccountStatusTypeFromStoredValue(v int32) (SavingsAccountStatusType, bool) {
	s, ok := savingsStatusFromStored[v]
	return s, ok
}

// Predicates below mirror SavingsAccountStatusType's boolean helpers
// [VERIFIED: SavingsAccountStatusType.java:75-128]. They compare the Go
// ordinal, which is a faithful index into the same fixed 11-value universe,
// never the stored value.

func (s SavingsAccountStatusType) IsSubmittedAndPendingApproval() bool {
	return s == StatusSubmittedAndPendingApproval
}
func (s SavingsAccountStatusType) IsApproved() bool { return s == StatusApproved }
func (s SavingsAccountStatusType) IsActive() bool   { return s == StatusActive }
func (s SavingsAccountStatusType) IsWithdrawnByApplicant() bool {
	return s == StatusWithdrawnByApplicant
}
func (s SavingsAccountStatusType) IsRejected() bool { return s == StatusRejected }
func (s SavingsAccountStatusType) IsClosed() bool   { return s == StatusClosed }

func (s SavingsAccountStatusType) IsTransferInProgress() bool { return s == StatusTransferInProgress }
func (s SavingsAccountStatusType) IsTransferOnHold() bool     { return s == StatusTransferOnHold }

// IsUnderTransfer is the union of the two transfer states
// [VERIFIED: SavingsAccountStatusType.java:95-97].
func (s SavingsAccountStatusType) IsUnderTransfer() bool {
	return s.IsTransferInProgress() || s.IsTransferOnHold()
}

// IsActiveOrAwaitingApprovalOrDeposit mirrors the oracle helper
// [VERIFIED: SavingsAccountStatusType.java:90-92].
func (s SavingsAccountStatusType) IsActiveOrAwaitingApprovalOrDeposit() bool {
	return s.IsSubmittedAndPendingApproval() || s.IsApproved() || s.IsActive()
}

func init() {
	for s, v := range savingsStatusStoredValue {
		if _, dup := savingsStatusFromStored[v]; dup {
			panic(fmt.Sprintf("savings: status encode table is not injective at %d", v))
		}
		savingsStatusFromStored[v] = s
	}
}
