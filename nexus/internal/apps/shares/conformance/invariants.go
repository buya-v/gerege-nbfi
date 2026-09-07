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

// AssertInvariants runs every gradeable shares invariant against the result an
// implementation returned.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	_ = v
	switch got.Kind {
	case KindAccount:
		return []InvariantResult{
			assertAmountNonNegative("purchased_price_minor", got.PurchasedPriceMinor),
			assertAmountNonNegative("purchased_amount_minor", got.PurchasedAmountMinor),
		}
	case KindDividend:
		return []InvariantResult{
			assertAmountNonNegative("dividend_amount_minor", got.DividendAmountMinor),
		}
	default:
		return nil
	}
}

// assertAmountNonNegative: a share money amount is a non-negative integer count
// of minor units. The port's exact-money parser already refuses a negative or
// fractional spelling; a violation here means the implementation produced a value
// the port's contract cannot produce.
func assertAmountNonNegative(field, value string) InvariantResult {
	r := InvariantResult{Name: field + "_non_negative", Assertions: 1}
	if !isIntegerMinorString(value) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("%s %q is not a non-negative integer minor-unit amount", field, value)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("%s %q is a non-negative integer minor-unit amount", field, value)
	return r
}
