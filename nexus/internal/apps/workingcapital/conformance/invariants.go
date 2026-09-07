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
// result an implementation returned. The list seam's total-elements agreement
// applies only to list read-backs; the detail seam's invariant guards the money
// integrity of the balance read-back instead.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	switch v.Oracle.Seam {
	case SeamWorkingCapitalLoansDetail:
		return []InvariantResult{assertBalanceMoneyIntegrity(got)}
	default:
		return []InvariantResult{
			assertTotalElementsMatchesList(v, got),
		}
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

// assertBalanceMoneyIntegrity: every money cell of a detail balance read-back is
// a non-negative integer minor-unit amount. A float, a negative, an empty or a
// fractional cell cannot be a transcription of the m_wc_loan_balance row the
// oracle serialised.
func assertBalanceMoneyIntegrity(got Expect) InvariantResult {
	r := InvariantResult{Name: "balance_money_is_integer_minor", Assertions: 9}
	if got.Detail == nil {
		r.Status = InvariantViolated
		r.Detail = "detail is nil"
		return r
	}
	b := got.Detail.Balance
	for name, val := range map[string]string{
		"principal":                           b.Principal,
		"principal_paid":                      b.PrincipalPaid,
		"total_disbursement":                  b.TotalDisbursement,
		"total_discount_fee":                  b.TotalDiscountFee,
		"principal_outstanding":               b.PrincipalOutstanding,
		"total_expected_repayment":            b.TotalExpectedRepayment,
		"total_repayment":                     b.TotalRepayment,
		"total_outstanding":                   b.TotalOutstanding,
		"unrealized_income_from_discount_fee": b.UnrealizedIncomeFromDiscountFee,
	} {
		if !isIntegerMinorString(val) {
			r.Status = InvariantViolated
			r.Detail = fmt.Sprintf("balance %s %q is not a non-negative integer minor amount", name, val)
			return r
		}
	}
	r.Status = InvariantHeld
	r.Detail = "all nine balance money cells are non-negative integer minor units"
	return r
}
