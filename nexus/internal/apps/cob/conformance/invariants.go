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

// AssertInvariants runs every gradeable cob invariant against the result an
// implementation returned. The single cob seam asserts the one property its
// table carries: the business-step order is a positive integer.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
_ = v
return []InvariantResult{assertStepOrderPositive(got)}
}

// assertStepOrderPositive: m_batch_business_steps.step_order is a positive
// 1-based sequence. A step read that returns a non-positive order has not
// returned a configuration the oracle could have produced.
func assertStepOrderPositive(got Expect) InvariantResult {
r := InvariantResult{Name: "step_order_positive", Assertions: 1}
if got.StepOrder <= 0 {
r.Status = InvariantViolated
r.Detail = fmt.Sprintf("step order %d is not positive", got.StepOrder)
return r
}
r.Status = InvariantHeld
r.Detail = fmt.Sprintf("step order %d is positive", got.StepOrder)
return r
}
