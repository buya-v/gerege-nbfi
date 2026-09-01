package origination

import (
	"fmt"
	"strings"
)

// LoanOriginatorStatus is the lifecycle of a loan originator, stored as an
// EnumType.STRING in m_loan_originator.status. It is the Go port of Fineract's
// LoanOriginatorStatus [VERIFIED: LoanOriginatorStatus.java:24-52]:
//
//	ACTIVE, PENDING, INACTIVE
//
// The stored value is the enum name (there is no integer ordinal column), so
// StoredValue returns the name and the decoder is case-insensitive on that name.
type LoanOriginatorStatus int32

const (
	OriginatorActive LoanOriginatorStatus = iota
	OriginatorPending
	OriginatorInactive
)

var originatorStatusName = map[LoanOriginatorStatus]string{
	OriginatorActive:   "ACTIVE",
	OriginatorPending:  "PENDING",
	OriginatorInactive: "INACTIVE",
}

// StoredValue returns the EnumType.STRING value (the enum name).
func (s LoanOriginatorStatus) StoredValue() string { return s.String() }

func (s LoanOriginatorStatus) String() string {
	if n, ok := originatorStatusName[s]; ok {
		return n
	}
	return fmt.Sprintf("LoanOriginatorStatus(%d)", int32(s))
}

// IsActive reports whether an originator in this status may be attached to a
// loan. Only ACTIVE qualifies
// [VERIFIED: AbstractLoanOriginatorLinkingServiceImpl.java:96-99].
func (s LoanOriginatorStatus) IsActive() bool { return s == OriginatorActive }

// LoanOriginatorStatusFromString resolves a status by name, case-insensitively,
// mirroring fromString [VERIFIED: LoanOriginatorStatus.java:44-52]. The oracle
// throws IllegalArgumentException on an unknown name; the port returns ok=false.
func LoanOriginatorStatusFromString(text string) (LoanOriginatorStatus, bool) {
	for s, n := range originatorStatusName {
		if strings.EqualFold(text, n) {
			return s, true
		}
	}
	return 0, false
}
