package conformance

import "fmt"

// The property invariants this context can grade.
//
// The provisioning slice's gradeable invariants are structural properties of the
// m_provision_category aggregate, asserted on an implementation's RESULT rather
// than re-derived here. They are always asserted (a category read always returns
// an id and a name), so a pass means the aggregate honours the NOT NULL contract
// of the table it ports.

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

// AssertInvariants runs every gradeable provisioning invariant against the
// result an implementation returned. The entry-reserve seam asserts a different
// set than the category-read seam, so the seam decides the set. A multi-entry
// reserve result asserts the reserve invariants on EVERY produced entry, so a
// merged or malformed entry cannot hide behind a well-formed sibling.
func AssertInvariants(v *Vector, got []Expect) []InvariantResult {
	if v != nil && v.Oracle.Seam == SeamProvisioningEntryReserve {
		var out []InvariantResult
		for _, e := range got {
			out = append(out, assertReserveCategoryIDPositive(e), assertReservedAmountInteger(e))
		}
		return out
	}
	if v != nil && v.Oracle.Seam == SeamProvisioningCriteriaBand {
		var out []InvariantResult
		for _, e := range got {
			out = append(out, assertBandCategoryIDPositive(e), assertBandPercentagePositive(e), assertBandAccountsPositive(e))
		}
		return out
	}
	if len(got) == 0 {
		return []InvariantResult{
			assertCategoryIDPositive(Expect{}),
			assertCategoryNameNonEmpty(Expect{}),
		}
	}
	return []InvariantResult{
		assertCategoryIDPositive(got[0]),
		assertCategoryNameNonEmpty(got[0]),
	}
}

// assertCategoryIDPositive: the m_provision_category primary key is a positive
// integer. A category read that returns a non-positive id has not returned an
// aggregate the oracle could have produced.
func assertCategoryIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "category_id_positive", Assertions: 1}
	if got.ID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("category id %d is not positive", got.ID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("category id %d is positive", got.ID)
	return r
}

// assertCategoryNameNonEmpty: m_provision_category.category_name is NOT NULL in
// the oracle schema. A category read that returns an empty name cannot be a
// transcription of a real row.
func assertCategoryNameNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "category_name_non_empty", Assertions: 1}
	if got.Name == "" {
		r.Status = InvariantViolated
		r.Detail = "category name is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("category name %q is non-empty", got.Name)
	return r
}

// assertReserveCategoryIDPositive: the reserve entry's category id is the
// m_provision_category primary key of the band, a positive integer.
func assertReserveCategoryIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "reserve_category_id_positive", Assertions: 1}
	if got.CategoryID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("reserve category id %d is not positive", got.CategoryID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("reserve category id %d is positive", got.CategoryID)
	return r
}

// assertReservedAmountInteger: the reserved amount is money in integer minor
// units, so it must be a non-negative integer. The comparator already decodes it
// into an integer; a violation here means the implementation produced a value it
// could not have produced under the port's contract.
func assertReservedAmountInteger(got Expect) InvariantResult {
	r := InvariantResult{Name: "reserved_amount_non_negative", Assertions: 1}
	if !isIntegerMinorString(got.ReservedAmountMinor) {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("reserved amount %q is not a non-negative integer minor-unit amount", got.ReservedAmountMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("reserved amount %q is a non-negative integer minor-unit amount", got.ReservedAmountMinor)
	return r
}

// assertBandCategoryIDPositive: the selected band's category id is the
// m_provision_category primary key, a positive integer.
func assertBandCategoryIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "band_category_id_positive", Assertions: 1}
	if got.CategoryID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("band category id %d is not positive", got.CategoryID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("band category id %d is positive", got.CategoryID)
	return r
}

// assertBandPercentagePositive: the selected band's reserve percentage is the
// oracle's provisioningPercentage, an integer micro-per-cent. Every observed band
// carries a positive percentage (1 % .. 100 %); a non-positive selection cannot
// be a transcription of a real criteria definition.
func assertBandPercentagePositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "band_percentage_positive", Assertions: 1}
	if got.Percentage <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("band percentage %d is not a positive micro-per-cent", got.Percentage)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("band percentage %d is a positive micro-per-cent", got.Percentage)
	return r
}

// assertBandAccountsPositive: the selected band's liability and expense GL
// account ids are positive integers (the oracle's provisioningLiabilityAccount
// and provisioningExpenseAccount).
func assertBandAccountsPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "band_accounts_positive", Assertions: 2}
	if got.LiabilityAccount <= 0 || got.ExpenseAccount <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("band accounts liability %d, expense %d: both must be positive", got.LiabilityAccount, got.ExpenseAccount)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("band accounts liability %d, expense %d are positive", got.LiabilityAccount, got.ExpenseAccount)
	return r
}
