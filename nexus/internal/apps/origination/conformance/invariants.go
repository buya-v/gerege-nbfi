package conformance

import "fmt"

// InvariantStatus is the outcome of one invariant assertion.
type InvariantStatus string

const (
	InvariantHeld          InvariantStatus = "HOLD"
	InvariantViolated      InvariantStatus = "VIOLATED"
	InvariantNotApplicable InvariantStatus = "N/A"
)

// InvariantResult is one invariant's verdict on one vector.
type InvariantResult struct {
	Name       string
	Status     InvariantStatus
	Assertions int
	Detail     string
}

// AssertInvariants runs every gradeable origination invariant against the result
// an implementation returned. The one seam asserts the one property its enum
// carries: the stored string is a member of the LoanOriginatorStatus vocabulary.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	_ = v
	return []InvariantResult{assertStoredInVocabulary(got)}
}

// assertStoredInVocabulary: LoanOriginatorStatus is a three-value STRING enum.
// A stored value outside {ACTIVE, PENDING, INACTIVE} cannot have been produced
// by the oracle.
func assertStoredInVocabulary(got Expect) InvariantResult {
	r := InvariantResult{Name: "stored_in_vocabulary", Assertions: 1}
	switch got.Stored {
	case "ACTIVE", "PENDING", "INACTIVE":
		r.Status = InvariantHeld
		r.Detail = fmt.Sprintf("stored %q is in the LoanOriginatorStatus vocabulary", got.Stored)
	default:
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("stored %q is not in the LoanOriginatorStatus vocabulary", got.Stored)
	}
	return r
}
