package conformance

import "fmt"

// The property invariants this context can grade. The working-capital slice's
// gradeable invariants are structural properties of the loan list read-back,
// asserted on an implementation's RESULT rather than re-derived here. They are
// always asserted, so a pass means the list honours the contract of the table it
// ports. With the single seeded loan the total-elements agreement is the one
// invariant that applies; the money/schedule invariants stay N/A until the
// breach and delinquency-range schedules are ported and captured.

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

// AssertInvariants runs every gradeable working-capital invariant against the
// result an implementation returned.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	return []InvariantResult{
		assertTotalElementsMatchesList(v, got),
	}
}

// assertTotalElementsMatchesList: the totalElements count the oracle returns
// must agree with the length of the loan list in the same read-back.
func assertTotalElementsMatchesList(v *Vector, got Expect) InvariantResult {
	r := InvariantResult{Name: "total_elements_matches_list", Assertions: 1}
	if got.TotalElements != int64(len(got.Loans)) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("total_elements %d disagrees with loan list length %d", got.TotalElements, len(got.Loans))
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("total_elements %d matches loan list length %d", got.TotalElements, len(got.Loans))
	return r
}
