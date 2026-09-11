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
	case SeamSavingsHoldRelease:
		return []InvariantResult{
			assertHoldReleaseMoneyIntegrity(got),
			assertHoldReleaseAvailableRelation(got),
			assertHoldReleaseIsObserved(v, got),
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

// assertHoldReleaseMoneyIntegrity: all three hold/release cells — the posted
// balance, held and available — are non-negative integer minor-unit amounts.
// This is the G-19 money-integrity property at the hold seam; a port that
// returns any of them as a float, or a negative amount, is refused here.
func assertHoldReleaseMoneyIntegrity(got Expect) InvariantResult {
	r := InvariantResult{Name: "hold_release_money_is_integer_minor", Assertions: 3}
	for _, c := range []struct {
		name string
		v    string
	}{
		{"account_balance", got.AccountBalanceMinor},
		{"held", got.HeldMinor},
		{"available", got.AvailableMinor},
	} {
		if !isIntegerMinorString(c.v) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("%s %q is not a non-negative integer minor amount", c.name, c.v)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = "account_balance, held and available are non-negative integer minor units"
	return r
}

// assertHoldReleaseAvailableRelation: available == account_balance - held, in
// integer minor units. This is the algebra the oracle's own hold path encodes
// (running balance = accountBalance - amount, and summary.availableBalance =
// balance less held); it must hold in BOTH observed states, and it is what
// makes a port that folds the hold into the posted balance relationally
// consistent yet still wrong — the relation alone cannot see it, which is why
// the cells are graded against the oracle.
func assertHoldReleaseAvailableRelation(got Expect) InvariantResult {
	r := InvariantResult{Name: "hold_release_available_is_balance_minus_held", Assertions: 1}
	bal, err1 := parseMinorText(got.AccountBalanceMinor)
	held, err2 := parseMinorText(got.HeldMinor)
	avail, err3 := parseMinorText(got.AvailableMinor)
	if err1 != nil || err2 != nil || err3 != nil {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("cannot evaluate available == balance - held over (%q, %q, %q)", got.AccountBalanceMinor, got.HeldMinor, got.AvailableMinor)
		return r
	}
	if want := bal - held; want != avail {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("available %d != balance %d - held %d = %d", avail, bal, held, want)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("available %d == balance %d - held %d", avail, bal, held)
	return r
}

// assertHoldReleaseIsObserved: a stream that carries an OUTSTANDING AMOUNT_HOLD
// must report a non-zero held amount, and a stream whose hold names a release
// row must report zero. This is the structural half of "the hold is seen": it
// does not re-derive the amount, only that the implementation did not ignore the
// hold row entirely (the second natural mistake), so a stream with a hold and a
// zero held cell is refused.
func assertHoldReleaseIsObserved(v *Vector, got Expect) InvariantResult {
	released := false
	if v != nil && v.Request.HoldRelease != nil {
		for _, row := range v.Request.HoldRelease.Transactions {
			if row.TypeStoredValue == 20 {
				released = row.ReleaseIDOfHoldAmount != 0
			}
		}
	}
	r := InvariantResult{Name: "hold_release_is_observed", Assertions: 1}
	if !isIntegerMinorString(got.HeldMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("held %q is not an integer minor amount", got.HeldMinor)
		return r
	}
	held, _ := parseMinorText(got.HeldMinor)
	if !released && held == 0 {
		r.Status = InvariantViolated
		r.Detail = "the stream carries an outstanding AMOUNT_HOLD but held is 0: the implementation ignored the hold"
		return r
	}
	if released && held != 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("the stream's AMOUNT_HOLD is released but held is %d, want 0", held)
		return r
	}
	r.Status = InvariantHeld
	if released {
		r.Detail = "released hold reported as held 0"
	} else {
		r.Detail = fmt.Sprintf("outstanding hold reported as held %d", held)
	}
	return r
}
