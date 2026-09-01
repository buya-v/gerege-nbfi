package loan

import "fmt"

// AllocationType is one of the four buckets a repayment or credit transaction
// is broken into. It is the Go port of Fineract's AllocationType
// [VERIFIED: AllocationType.java:24-31 — PENALTY(0), FEE(1), PRINCIPAL(2),
// INTEREST(3)].
//
// Unlike LoanStatus and LoanTransactionType there is no integer stored value:
// the oracle persists these as their enum name (EnumType.STRING) and inside the
// comma-joined list converters [VERIFIED: AllocationTypeListConverter.java:25-33,
// GenericEnumListConverter.java:36-63]. The ordinal is therefore significant
// only for the API-facing EnumOptionData value (ordinal + 1)
// [VERIFIED: AllocationType.java:39-43]; the authoritative identity is the
// String() name, which is what the persistence and allocation-order lists
// round-trip through.
type AllocationType int32

const (
	AllocationPenalty AllocationType = iota
	AllocationFee
	AllocationPrincipal
	AllocationInterest
)

var allocationTypeName = map[AllocationType]string{
	AllocationPenalty:   "PENALTY",
	AllocationFee:       "FEE",
	AllocationPrincipal: "PRINCIPAL",
	AllocationInterest:  "INTEREST",
}

var allocationTypeHuman = map[AllocationType]string{
	AllocationPenalty:   "Penalty",
	AllocationFee:       "Fee",
	AllocationPrincipal: "Principal",
	AllocationInterest:  "Interest",
}

// String returns the Java enum constant name, the value the oracle persists and
// the key used by the allocation-order converters.
func (t AllocationType) String() string {
	if n, ok := allocationTypeName[t]; ok {
		return n
	}
	return fmt.Sprintf("AllocationType(%d)", int32(t))
}

// HumanReadableName returns getHumanReadableName
// [VERIFIED: AllocationType.java:24-31].
func (t AllocationType) HumanReadableName() string { return allocationTypeHuman[t] }

// The predicates mirror AllocationType's identity checks, which compare enum
// equality and never an ordinal.

func (t AllocationType) IsPenalty() bool   { return t == AllocationPenalty }
func (t AllocationType) IsFee() bool       { return t == AllocationFee }
func (t AllocationType) IsPrincipal() bool { return t == AllocationPrincipal }
func (t AllocationType) IsInterest() bool  { return t == AllocationInterest }
