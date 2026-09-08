package conformance

import "fmt"

// The property invariants this context can grade. The savings slice's gradeable
// invariant is the structural money-integrity property of the single-period
// interest result, asserted on an implementation's RESULT rather than re-derived
// here. It is always asserted, so a pass means the implementation returned a
// non-negative integer minor-unit amount, never a float or a negative.

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

// AssertInvariants runs every gradeable savings invariant against the result an
// implementation returned. The seam decides the set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	switch v.Oracle.Seam {
	case SeamSavingsDailyInterest:
		return []InvariantResult{assertInterestNonNegative(got)}
	case SeamSavingsDeposit, SeamSavingsTransactions:
		return []InvariantResult{
			assertRunningBalanceRowCount(v, got),
			assertRunningBalanceMoneyIntegrity(got),
		}
	default:
		return nil
	}
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

// assertRunningBalanceRowCount: the fold must return exactly one running
// balance per posted row — one balance cell per append-only row is the shape
// the oracle's read-back carries, and a fold that drops or doubles a row is a
// fold that is not over the same stream.
func assertRunningBalanceRowCount(v *Vector, got Expect) InvariantResult {
	want := 0
	if v.Request.Stream != nil {
		want = len(v.Request.Stream.Transactions)
	}
	r := InvariantResult{Name: "running_balances_per_row", Assertions: 1}
	if len(got.RunningBalances) != want {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("running_balances has %d cells for a %d-row stream", len(got.RunningBalances), want)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("running_balances has %d cells for a %d-row stream", len(got.RunningBalances), want)
	return r
}

// assertRunningBalanceMoneyIntegrity: every returned running balance is a
// non-negative integer minor-unit amount.
func assertRunningBalanceMoneyIntegrity(got Expect) InvariantResult {
	r := InvariantResult{Name: "running_balance_money_is_integer_minor", Assertions: len(got.RunningBalances)}
	for i, b := range got.RunningBalances {
		if !isIntegerMinorString(b) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("running_balances[%d] %q is not a non-negative integer minor amount", i, b)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("all %d running-balance cells are non-negative integer minor units", len(got.RunningBalances))
	return r
}
