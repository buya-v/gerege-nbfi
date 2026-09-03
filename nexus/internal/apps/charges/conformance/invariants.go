package conformance

import "fmt"

// The property invariants this context can grade.
//
// The charges slice has no multi-leg balancing equation to assert the way the
// ledger does; its gradeable invariants are structural properties of an
// implementation's RESULT, asserted on the output rather than re-derived here.
// Both are asserted only when a fee is present, and reported N/A otherwise —
// an invariant that inspected nothing is not a pass.

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

// AssertInvariants runs every gradeable charges invariant against the result an
// implementation returned.
func AssertInvariants(v *Vector, got ChargeResult) []InvariantResult {
	return []InvariantResult{
		assertFeeRequiresValid(got),
		assertFeeNonNegative(got),
	}
}

// assertFeeRequiresValid: a fee implies the charge passed construction
// validation. A port that returns both a fee and a non-empty validation list has
// two inconsistent answers to one request, and neither can be trusted.
func assertFeeRequiresValid(got ChargeResult) InvariantResult {
	r := InvariantResult{Name: "fee_requires_valid"}
	if !got.FeePresent {
		r.Status = InvariantNotApplicable
		r.Detail = "no fee was computed; nothing to assert"
		return r
	}
	r.Assertions = 1
	if len(got.ValidationCodes) != 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf(
			"a fee (%d minor units) was computed despite %d construction-validation error(s)",
			got.FeeMinor, len(got.ValidationCodes))
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("fee %d minor units returned with an empty validation list", got.FeeMinor)
	return r
}

// assertFeeNonNegative: a charge fee is never negative in integer minor units.
// The port's PercentageOf returns zero for a non-positive base and HALF_UP
// rounds a non-negative product non-negatively, so a negative fee is a port
// defect wherever it comes from.
func assertFeeNonNegative(got ChargeResult) InvariantResult {
	r := InvariantResult{Name: "fee_non_negative"}
	if !got.FeePresent {
		r.Status = InvariantNotApplicable
		r.Detail = "no fee was computed; nothing to assert"
		return r
	}
	r.Assertions = 1
	if got.FeeMinor < 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("fee %d minor units is negative", got.FeeMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("fee %d minor units is non-negative", got.FeeMinor)
	return r
}
