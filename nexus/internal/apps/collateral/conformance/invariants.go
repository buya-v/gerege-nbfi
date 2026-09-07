package conformance

import "fmt"

// The property invariants this context can grade. The collateral slice's
// gradeable invariants are structural properties of the two read-back
// aggregates, asserted on an implementation's RESULT rather than re-derived
// here. They are always asserted, so a pass means the aggregate honours the
// NOT NULL / positive-key contract of the table it ports.

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

// AssertInvariants runs every gradeable collateral invariant against the result
// an implementation returned. The link seam asserts a different set than the
// product seam, so the seam decides the set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	if v != nil && v.Oracle.Seam == SeamCollateralLinkRead {
		return []InvariantResult{
			assertLinkIDPositive(got),
			assertLinkTypeIDPositive(got),
		}
	}
	return []InvariantResult{
		assertProductIDPositive(got),
		assertProductNameNonEmpty(got),
	}
}

// assertProductIDPositive: the m_collateral_management primary key is a positive
// integer. A product read that returns a non-positive id has not returned an
// aggregate the oracle could have produced.
func assertProductIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "product_id_positive", Assertions: 1}
	if got.ID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("product id %d is not positive", got.ID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("product id %d is positive", got.ID)
	return r
}

// assertProductNameNonEmpty: m_collateral_management.name is NOT NULL. A product
// read that returns an empty name cannot be a transcription of a real row.
func assertProductNameNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "product_name_non_empty", Assertions: 1}
	if got.Name == "" {
		r.Status = InvariantViolated
		r.Detail = "product name is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("product name %q is non-empty", got.Name)
	return r
}

// assertLinkIDPositive: the m_loan_collateral primary key is a positive integer.
func assertLinkIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "link_id_positive", Assertions: 1}
	if got.ID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("link id %d is not positive", got.ID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("link id %d is positive", got.ID)
	return r
}

// assertLinkTypeIDPositive: m_loan_collateral.type_cv_id is the LoanCollateral
// code value's primary key, a positive integer.
func assertLinkTypeIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "link_type_id_positive", Assertions: 1}
	if got.TypeID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("link type_id %d is not positive", got.TypeID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("link type_id %d is positive", got.TypeID)
	return r
}
