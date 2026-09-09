package conformance

import "fmt"

// The property invariants this context can grade. The investor slice's
// gradeable invariants are structural properties of the transfer read-back,
// asserted on an implementation's RESULT rather than re-derived here. They are
// always asserted, so a pass means the transfer honours the NOT NULL /
// positive-key contract of the table it ports.

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

// AssertInvariants runs every gradeable investor invariant against the result an
// implementation returned.
//
// The row invariants apply to a transfer ROW. An empty page (loan has no
// transfer) has no row, so each invariant is NotApplicable rather than
// Violated: nothing in the response claims to be a row that breaks the NOT
// NULL / positive-key contract.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	if got.Empty {
		return []InvariantResult{
			{Name: "transfer_id_positive", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "owner_external_id_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "transfer_external_id_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "status_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
		}
	}
	return []InvariantResult{
		assertTransferIDPositive(got),
		assertOwnerExternalIDNonEmpty(got),
		assertTransferExternalIDNonEmpty(got),
		assertStatusNonEmpty(got),
	}
}

// assertTransferIDPositive: m_external_asset_owner_transfer.id is a positive
// integer. A transfer read that returns a non-positive id has not returned an
// aggregate the oracle could have produced.
func assertTransferIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "transfer_id_positive", Assertions: 1}
	if got.TransferID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("transfer id %d is not positive", got.TransferID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("transfer id %d is positive", got.TransferID)
	return r
}

// assertOwnerExternalIDNonEmpty: m_external_asset_owner.external_id is NOT NULL.
func assertOwnerExternalIDNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "owner_external_id_non_empty", Assertions: 1}
	if got.OwnerExternalID == "" {
		r.Status = InvariantViolated
		r.Detail = "owner external id is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("owner external id %q is non-empty", got.OwnerExternalID)
	return r
}

// assertTransferExternalIDNonEmpty: m_external_asset_owner_transfer.external_id
// is NOT NULL.
func assertTransferExternalIDNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "transfer_external_id_non_empty", Assertions: 1}
	if got.TransferExternalID == "" {
		r.Status = InvariantViolated
		r.Detail = "transfer external id is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("transfer external id %q is non-empty", got.TransferExternalID)
	return r
}

// assertStatusNonEmpty: m_external_asset_owner_transfer.status is NOT NULL and
// is persisted by name.
func assertStatusNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "status_non_empty", Assertions: 1}
	if got.Status == "" {
		r.Status = InvariantViolated
		r.Detail = "status is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("status %q is non-empty", got.Status)
	return r
}
