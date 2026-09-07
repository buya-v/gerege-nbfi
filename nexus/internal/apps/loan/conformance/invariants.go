package conformance

import "fmt"

// The property invariants this context can grade. The loan slice's gradeable
// invariants are structural money-integrity properties of the allocation and
// disbursement results, asserted on an implementation's RESULT rather than
// re-derived here. They are always asserted, so a pass means the implementation
// returned non-negative integer minor-unit money, never a float or a negative.

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

// AssertInvariants runs every gradeable loan invariant against the result an
// implementation returned. The seam decides the set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation:
		return []InvariantResult{assertAllocationNonNegative(got)}
	case SeamLoanScheduleInterest:
		return []InvariantResult{assertInterestNonNegative(got)}
	default:
		return []InvariantResult{assertNetDisbursalNonNegative(got)}
	}
}

// assertAllocationNonNegative: every allocated bucket and the leftover are
// non-negative integer minor-unit amounts. A bucket or leftover that is
// negative, empty or fractional cannot be a transcription of a greedy
// allocation the oracle could have produced.
func assertAllocationNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "allocation_non_negative", Assertions: 5}
	if got.Allocation == nil {
		r.Status = InvariantViolated
		r.Detail = "allocation is nil"
		return r
	}
	for name, val := range map[string]string{
		"penalty":   got.Allocation.Penalty,
		"fee":       got.Allocation.Fee,
		"interest":  got.Allocation.Interest,
		"principal": got.Allocation.Principal,
		"leftover":  got.LeftoverMinor,
	} {
		if !isIntegerMinorString(val) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("allocation %s %q is not a non-negative integer minor amount", name, val)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = "all five allocation cells are non-negative integer minor units"
	return r
}

// assertInterestNonNegative: the single-period interest is a non-negative
// integer minor-unit amount.
func assertInterestNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "interest_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.InterestMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("interest %q is not a non-negative integer minor amount", got.InterestMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("interest %q is a non-negative integer minor amount", got.InterestMinor)
	return r
}

// assertNetDisbursalNonNegative: the net disbursal amount is a non-negative
// integer minor-unit amount.
func assertNetDisbursalNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "net_disbursal_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.NetDisbursalMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("net_disbursal %q is not a non-negative integer minor amount", got.NetDisbursalMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("net_disbursal %q is a non-negative integer minor amount", got.NetDisbursalMinor)
	return r
}
