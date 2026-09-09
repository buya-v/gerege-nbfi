package conformance

import "fmt"

// The property invariants this context can grade. The collateral slice's
// gradeable invariants are structural properties of the read-back aggregates,
// asserted on an implementation's RESULT rather than re-derived here. They are
// always asserted, so a pass means the aggregate honours the NOT NULL /
// positive-key contract of the table it ports (and, for the valuation read, the
// pct_to_base-percentage bound that keeps total_collateral under total).

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
// an implementation returned. Each seam asserts its own set, so the seam decides
// the set.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	if v != nil {
		switch v.Oracle.Seam {
		case SeamCollateralLinkRead:
			return []InvariantResult{
				assertLinkIDPositive(got),
				assertLinkTypeIDPositive(got),
			}
		case SeamClientCollateralRead:
			return []InvariantResult{
				assertClientCollateralRead(got),
			}
		case SeamClientCollateralValuationRead:
			return []InvariantResult{
				assertValuationIDPositive(got),
				assertTotalCollateralNotAboveTotal(got),
			}
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

// assertClientCollateralRead: the client-collateral seam grades PAGE PRESENCE,
// not a row. The only observed client read-back returned content [], so no
// holding-row invariant is gradeable: an answer is either the empty page the
// oracle observed (graded green by the page-presence comparison) or a holding
// row the oracle never returned (graded red by that same comparison). Nothing
// here claims a row that could break a NOT NULL / positive-key contract, so the
// one invariant slot is NotApplicable in both cases.
func assertClientCollateralRead(got Expect) InvariantResult {
	r := InvariantResult{Name: "client_collateral_page_presence", Status: InvariantNotApplicable, Assertions: 0}
	if got.Empty {
		r.Detail = "client read-back returned the empty page the oracle observed (content []); page presence is graded by comparison"
	} else {
		r.Detail = fmt.Sprintf("client read-back returned holding id %d, a row the oracle never returned; page presence is graded by comparison", got.ID)
	}
	return r
}

// assertValuationIDPositive: the m_client_collateral_management primary key is a
// positive integer. A valuation read that returns a non-positive id has not
// returned the holding the oracle observed.
func assertValuationIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "valuation_id_positive", Assertions: 1}
	if got.ID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("holding id %d is not positive", got.ID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("holding id %d is positive", got.ID)
	return r
}

// assertTotalCollateralNotAboveTotal: the oracle's total_collateral is total
// scaled by pct_to_base/100 (ClientCollateralManagementReadServiceImpl.java),
// and pct_to_base is a percentage (SQL-verified NOT NULL numeric(19,5)); the
// graded corpus's product has pct_to_base = 50.00000, so total_collateral =
// total * 50/100 can never exceed total. A valuation read that reports more
// collateral than total cannot be a transcription of the oracle's read path for
// this holding.
func assertTotalCollateralNotAboveTotal(got Expect) InvariantResult {
	r := InvariantResult{Name: "total_collateral_lte_total", Assertions: 1}
	if got.Total == "" || got.TotalCollateral == "" {
		r.Status = InvariantViolated
		r.Detail = "total or total_collateral is empty"
		return r
	}
	total, errT := parseIntCell(got.Total)
	val, errV := parseIntCell(got.TotalCollateral)
	if errT != nil || errV != nil {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("total %q or total_collateral %q is not an integer count", got.Total, got.TotalCollateral)
		return r
	}
	if val > total {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("total_collateral %d exceeds total %d, impossible for pct_to_base <= 100", val, total)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("total_collateral %d <= total %d", val, total)
	return r
}

// parseIntCell parses a cell that must be a non-negative integer string (money
// and quantity cells are integer minor-unit or scale-5 counts, never floats).
func parseIntCell(s string) (int64, error) {
	var n int64
	if s == "" {
		return 0, fmt.Errorf("empty")
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return 0, fmt.Errorf("non-digit %q", c)
		}
		if n > (1<<63-1)/10 {
			return 0, fmt.Errorf("overflow")
		}
		n = n*10 + int64(c-'0')
	}
	return n, nil
}
