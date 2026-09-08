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
// implementation returned. The invariants that apply depend on the seam the
// request names, so a vector never asserts a money-cell contract about cells its
// seam does not produce.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	seam := ""
	if v != nil {
		seam = requestSeam(&v.Request)
	}
	switch seam {
	case SeamCashierSummary:
		return []InvariantResult{
			assertAmountNonNegative("sum_cash_allocation", got.SumCashAllocation),
			assertAmountNonNegative("sum_cash_settlement", got.SumCashSettlement),
		}
	case SeamTellerStatus:
		return nil
	default: // SeamCashierTxnAmount (and a nil-vector unit test, which is movement)
		r := assertAmountNonNegative("txn_amount", got.TxnAmountMinor)
		r.Name = "txn_amount_non_negative"
		return []InvariantResult{r}
	}
}

// assertAmountNonNegative: a branch money cell is a non-negative integer count of
// minor units. The port's exact-money parser already refuses a fractional
// spelling; a violation here means the implementation produced a value the
// port's contract cannot produce.
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
