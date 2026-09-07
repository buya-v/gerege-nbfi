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

// AssertInvariants runs every gradeable branch invariant against the result an
// implementation returned.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	_ = v
	return []InvariantResult{
		assertTxnAmountNonNegative(got),
	}
}

// assertTxnAmountNonNegative: a cash movement amount is a non-negative integer
// count of minor units. The port's exact-money parser already refuses a negative
// or fractional spelling; a violation here means the implementation produced a
// value the port's contract cannot produce.
func assertTxnAmountNonNegative(got Expect) InvariantResult {
	r := InvariantResult{Name: "txn_amount_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.TxnAmountMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("txn_amount_minor %q is not a non-negative integer minor-unit amount", got.TxnAmountMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("txn_amount_minor %q is a non-negative integer minor-unit amount", got.TxnAmountMinor)
	return r
}
