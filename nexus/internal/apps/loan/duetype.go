package loan

import "fmt"

// DueType classifies a repayment instalment relative to the transaction date.
// It is the Go port of Fineract's DueType
// [VERIFIED: DueType.java:24-29 — PAST_DUE(0), DUE(1), IN_ADVANCE(2)].
//
// DueType never selects a money bucket on its own: it selects WHICH instalment
// a payment-allocation type applies to (the oldest past-due instalment, the
// instalment falling due on the transaction date, or a future instalment).
// The bucket is chosen by the paired AllocationType carried on the enclosing
// PaymentAllocationType.
//
// There is no integer stored value: like AllocationType, the oracle persists
// the enum name. The String() name is the authoritative identity.
type DueType int32

const (
	DuePastDue DueType = iota
	DueDue
	DueInAdvance
)

var dueTypeName = map[DueType]string{
	DuePastDue:   "PAST_DUE",
	DueDue:       "DUE",
	DueInAdvance: "IN_ADVANCE",
}

// String returns the Java enum constant name.
func (d DueType) String() string {
	if n, ok := dueTypeName[d]; ok {
		return n
	}
	return fmt.Sprintf("DueType(%d)", int32(d))
}
